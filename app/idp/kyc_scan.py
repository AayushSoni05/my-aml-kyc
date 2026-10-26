from sqlmodel import Session, select
from app.models import Customer, CompanyPartner, CompanyDetails, KYCDocument
from app.idp.context import load_kyc_context
from app.idp.registry import find_company_in_gleif
from app.idp.store import load_rules, load_settings
from app.idp.textutil import norm_id
from app.idp.verify import rule_params

SCAN_CHECKS = {}
_RANK = {"verified": 0, "review": 1, "pending": 2, "expired": 3, "rejected": 4}   # lower = better


def scan_kind(name):
    def deco(fn):
        SCAN_CHECKS[name] = fn
        return fn
    return deco


def _f(code, severity, message):
    return {"code": code, "severity": severity, "message": message}


def _val(x):
    return getattr(x, "value", x)


class ScanContext:
    def __init__(self, session, customer, details, profile, docs, settings):
        self.session, self.customer, self.details = session, customer, details
        self.profile, self.docs, self.settings = profile, docs, settings
        self._partners = None

    def target(self, name):
        return {"details": self.details, "profile": self.profile}.get(name)

    def partners(self):
        if self._partners is None:
            if isinstance(self.details, CompanyDetails):
                self._partners = self.session.exec(
                    select(CompanyPartner).where(CompanyPartner.company_id == self.details.id)).all()
            else:
                self._partners = []
        return self._partners


@scan_kind("required_document")
def _required_document(p, sev, ctx):
    """params: label, document_types[], status_severity{} (per document status). Needs a verified document."""
    types, label = set(p["document_types"]), p.get("label", "document")
    docs = [d for d in ctx.docs if _val(d.document_type) in types]
    if not docs:
        return [_f("missing_document", sev, f"No {label} on file")]
    st = _val(min(docs, key=lambda d: _RANK[_val(d.verification_status)]).verification_status)
    if st == "verified":
        return []
    by_status = {"review": "medium", "pending": "medium", "expired": sev, "rejected": sev}
    by_status.update(p.get("status_severity", {}))
    text = {"review": "needs manual review", "pending": "uploaded but not yet verified",
            "expired": "has expired", "rejected": "was rejected"}[st]
    return [_f(f"document_{st}", by_status[st], f"{label.capitalize()} {text}")]


@scan_kind("record_exists")
def _record_exists(p, sev, ctx):
    """params: target (details|profile), code, label."""
    if ctx.target(p["target"]) is None:
        return [_f(p.get("code", f"missing_{p['target']}"), sev, f"No {p.get('label', p['target'])} on file")]
    return []


@scan_kind("required_field")
def _required_field(p, sev, ctx):
    """params: target (details|profile), field, label. Flags an empty value."""
    obj = ctx.target(p["target"])
    if obj is not None and not getattr(obj, p["field"], None):
        return [_f(f"missing_{p['field']}", sev, f"{p.get('label', p['field'])} is missing")]
    return []


@scan_kind("required_true")
def _required_true(p, sev, ctx):
    """params: target, field, code, message. Flags when a yes/no field is not true."""
    obj = ctx.target(p["target"])
    if obj is not None and not getattr(obj, p["field"], False):
        return [_f(p["code"], sev, p["message"])]
    return []


@scan_kind("flag_if_true")
def _flag_if_true(p, sev, ctx):
    """params: target, field, code, message. Records a finding when a yes/no field is true."""
    obj = ctx.target(p["target"])
    if obj is not None and getattr(obj, p["field"], False):
        return [_f(p["code"], sev, p["message"])]
    return []


@scan_kind("partners_exist")
def _partners_exist(p, sev, ctx):
    """No params. A company needs at least one listed owner, director or partner."""
    if ctx.details is not None and not ctx.partners():
        return [_f("no_partners_listed", sev, "No owners, directors or partners listed")]
    return []


@scan_kind("ownership_total")
def _ownership_total(p, sev, ctx):
    """params: max (percent, default 100)."""
    total, mx = sum(x.ownership_percent or 0 for x in ctx.partners()), p.get("max", 100)
    if total > mx + 1e-4:
        return [_f("ownership_exceeds_max", sev, f"Listed ownership totals {total:g}% (maximum {mx:g}%)")]
    return []


@scan_kind("ubo_identified")
def _ubo(p, sev, ctx):
    """params: ubo_roles[], inconsistent_severity, flag_unset_severity. Threshold comes from settings.ubo_threshold."""
    partners = ctx.partners()
    if not partners:
        return []
    threshold, roles = ctx.settings["ubo_threshold"], set(p.get("ubo_roles", ["ubo"]))
    ubos = [x for x in partners if (x.ownership_percent or 0) >= threshold or _val(x.partner_role) in roles]
    flag = bool(ctx.profile is not None and getattr(ctx.profile, "ultimate_beneficial_owner_identified", False))
    if not ubos:
        if flag:
            return [_f("ubo_flag_inconsistent", p.get("inconsistent_severity", "medium"),
                       "UBO marked identified but no partner meets the ownership threshold")]
        return [_f("ubo_not_identified", sev, f"No beneficial owner identified (owner of {threshold:g}% or more)")]
    if not flag and ctx.profile is not None:
        return [_f("ubo_flag_not_set", p.get("flag_unset_severity", "low"),
                   "A beneficial owner exists but the KYC flag is not set")]
    return []


@scan_kind("partner_details_complete")
def _partner_details(p, sev, ctx):
    """params: fields[] each partner must have (needed for screening)."""
    fields = p.get("fields", ["date_of_birth", "identifier"])
    bad = [x.partner_name for x in ctx.partners() if any(not getattr(x, f, None) for f in fields)]
    if bad:
        return [_f("partner_missing_details", sev,
                   f"Partners missing {', '.join(fields)} (needed for screening): " + ", ".join(bad))]
    return []


@scan_kind("registry_gleif")
def _registry(p, sev, ctx):
    """params: not_found_severity, inactive_severity, mismatch_severity, unavailable_severity. Checks the GLEIF LEI registry."""
    try:
        match = find_company_in_gleif(ctx.customer.full_name)
    except Exception:
        return [_f("registry_unavailable", p.get("unavailable_severity", "low"), "GLEIF lookup failed; skipped")]
    if match is None:
        return [_f("company_not_in_gleif", p.get("not_found_severity", sev),
                   "No matching LEI record (many legitimate companies have none)")]
    out = []
    if match["status"] != "ACTIVE":
        out.append(_f("registry_status_not_active", p.get("inactive_severity", "medium"),
                      f"GLEIF status: {match['status']}"))
    reg = getattr(ctx.details, "registration_number", None)
    if reg and match["registered_as"] and norm_id(reg) != norm_id(match["registered_as"]):
        out.append(_f("registry_number_mismatch", p.get("mismatch_severity", "medium"),
                      "Registration number differs from the registry record; check the format"))
    return out


def run_kyc_scan(session: Session, customer: Customer, skip_kinds=()):
    """Returns (kyc_status, score, findings), driven entirely by the configured rules and settings."""
    settings = load_settings(session)
    details, profile = load_kyc_context(session, customer)
    docs = session.exec(select(KYCDocument).where(KYCDocument.customer_id == customer.id)).all()
    ctx = ScanContext(session, customer, details, profile, docs, settings)

    findings = []
    for rule in load_rules(session, "scan", [_val(customer.customer_type), "*"]):
        if rule.kind in skip_kinds:
            continue
        fn = SCAN_CHECKS.get(rule.kind)
        if fn is None:
            findings.append(_f("unknown_rule", "low", f"Unknown rule kind: {rule.kind}"))
            continue
        findings.extend(fn(rule_params(rule), rule.severity, ctx))

    points = settings["severity_points"]
    score = min(100.0, float(sum(points.get(f["severity"], 0) for f in findings)))
    worst = next((s for s in ("high", "medium", "low") if any(f["severity"] == s for f in findings)), None)
    status = settings["status_by_severity"].get(worst, "Complete") if worst else "Complete"
    return status, score, findings