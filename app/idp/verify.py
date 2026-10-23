import json
from datetime import date
from rapidfuzz import fuzz
from app.idp.textutil import norm_text, norm_id, parse_iso
from app.idp.validators import validate_td3_mrz

CHECKS = {}          # kind -> function(params, severity, ctx) -> list of check dicts


def check_kind(name):
    def deco(fn):
        CHECKS[name] = fn
        return fn
    return deco


def _c(name, status, detail=""):
    return {"check": name, "status": status, "detail": detail}


def rule_params(rule) -> dict:
    p = rule.params
    return json.loads(p) if isinstance(p, str) else (p or {})


def _policy(policy, sev):
    """How to report a missing value: 'pass', 'warn' or 'fail' (= the rule's severity)."""
    return {"pass": "pass", "warn": "warn"}.get(policy, sev)


_ROOTS = {"customer", "details", "profile", "doc"}


def _resolve(path, ctx):
    """Looks up a value like 'details.date_of_birth'. 'a|b' tries b if a is empty."""
    for option in path.split("|"):
        option = option.strip()
        if option == "expected_name":
            value = getattr(ctx["details"], "owner_name", None) or ctx["customer"].full_name
        else:
            root, _, attr = option.partition(".")
            obj = ctx.get(root) if root in _ROOTS else None
            ok = obj is not None and attr and not attr.startswith("_")
            value = getattr(obj, attr, None) if ok else None
        if value not in (None, ""):
            return value
    return None


def _match(matcher, found, expected, s):
    """Returns ('pass' | 'warn' | 'miss', detail)."""
    if matcher == "name":
        score = fuzz.token_sort_ratio(norm_text(str(expected)), norm_text(str(found)))
        level = "pass" if score >= s["name_pass"] else "warn" if score >= s["name_review"] else "miss"
        return level, f"similarity {score:.0f}"
    if matcher == "address":
        score = fuzz.token_set_ratio(norm_text(str(expected)), norm_text(str(found)))
        return ("pass" if score >= s["address_pass"] else "warn"), f"similarity {score:.0f}"
    if matcher == "id":
        same = norm_id(str(found)) == norm_id(str(expected))
    elif matcher == "date":
        a = parse_iso(found)
        same = a is not None and a == parse_iso(expected)
    else:
        same = norm_text(str(found)) == norm_text(str(expected))
    return ("pass" if same else "miss"), ""


@check_kind("extraction_confidence")
def _confidence(p, sev, ctx):
    """params: min (number) or min_setting (settings key). Fails when the model's confidence is lower."""
    minimum = p["min"] if "min" in p else ctx["settings"][p.get("min_setting", "confidence_min")]
    conf = ctx["extracted"].get("confidence") or 0.0
    return [_c("extraction_confidence", "pass" if conf >= minimum else sev, f"{conf:.2f}")]


@check_kind("document_type_matches")
def _type_matches(p, sev, ctx):
    """No params. The document's detected type must equal the claimed type."""
    detected = ctx["extracted"].get("document_type_detected")
    return [_c("document_type_matches", "pass" if detected == ctx["claimed"] else sev,
               f"claimed {ctx['claimed']}, detected {detected}")]


@check_kind("mrz_td3")
def _mrz(p, sev, ctx):
    """Passport MRZ checksums and MRZ-vs-printed comparison. params: line1, line2 (field names)."""
    ex = ctx["extracted"]
    l1, l2 = ex.get(p.get("line1", "mrz_line_1")), ex.get(p.get("line2", "mrz_line_2"))
    if not (l1 and l2):
        return [_c("mrz_present", "warn", "no MRZ read from passport")]
    m = validate_td3_mrz(l1, l2, ctx["today"])
    out = []
    for ch in m["checks"]:
        if ch["check"].startswith("mrz_") or ch["check"] == "birth_date_valid":
            out.append(_c(ch["check"], "pass" if ch["passed"] else sev, ch["detail"]))
    f = m["fields"]
    if f:
        ctx["mrz"] = f
        pairs = [("mrz_matches_document_number", norm_id(f["document_number"]), norm_id(ex.get("document_number"))),
                 ("mrz_matches_birth_date", f["date_of_birth"], ex.get("date_of_birth")),
                 ("mrz_matches_expiry_date", f["expiry_date"], ex.get("expiry_date"))]
        for name, a, b in pairs:
            if a and b:
                out.append(_c(name, "pass" if a == b else sev))
    return out


@check_kind("not_expired")
def _not_expired(p, sev, ctx):
    """params: field (default expiry_date), missing (pass|warn|fail). Falls back to the MRZ expiry."""
    exp = (parse_iso(ctx["extracted"].get(p.get("field", "expiry_date")))
           or parse_iso((ctx.get("mrz") or {}).get("expiry_date")))
    if exp is None:
        return [_c("not_expired", _policy(p.get("missing", "warn"), sev), "no expiry date on document")]
    return [_c("not_expired", "pass" if exp >= ctx["today"] else sev, f"expires {exp}")]


@check_kind("max_age_days")
def _max_age(p, sev, ctx):
    """params: field, days. The date must be in the past and no older than N days."""
    d = parse_iso(ctx["extracted"].get(p["field"]))
    name = f"{p['field']}_recent"
    if d is None:
        return [_c(name, sev, "date missing or unreadable")]
    age = (ctx["today"] - d).days
    return [_c(name, "pass" if 0 <= age <= p["days"] else sev, f"{age} days old")]


@check_kind("field_present")
def _present(p, sev, ctx):
    """params: field. The field must have been read from the document."""
    return [_c(f"{p['field']}_present", "pass" if ctx["extracted"].get(p["field"]) else sev)]


@check_kind("matches_record")
def _matches(p, sev, ctx):
    """params: field, record ('details.x', 'profile.x', 'customer.x', 'doc.x', 'expected_name'; 'a|b' fallback),
    matcher (name|address|id|date|text), missing (skip|warn|fail)."""
    field, record = p["field"], p["record"]
    found = ctx["extracted"].get(field)
    expected = _resolve(record, ctx)
    name = f"{field}_matches_{record.split('|')[0].replace('.', '_')}"
    if found in (None, "") or expected is None:
        policy = p.get("missing", "skip")
        return [] if policy == "skip" else [_c(name, _policy(policy, sev), "missing on one side")]
    level, detail = _match(p.get("matcher", "text"), found, expected, ctx["settings"])
    return [_c(name, sev if level == "miss" else level, detail)]


@check_kind("manual_review")
def _manual(p, sev, ctx):
    """No params. Always sends the document to a person."""
    return [_c("manual_review_required", "warn", "this document type cannot be verified automatically")]


def verify_document(doc, extracted, customer, details, profile, rules, settings, today=None):
    """Runs the configured rules. Returns (status, checks); status: verified | review | expired.
    The system never auto-rejects; a person decides that."""
    ctx = {"doc": doc, "extracted": extracted, "customer": customer, "details": details, "profile": profile,
           "settings": settings, "today": today or date.today(),
           "claimed": getattr(doc.document_type, "value", doc.document_type)}
    checks = []
    for rule in rules:
        fn = CHECKS.get(rule.kind)
        if fn is None:
            checks.append(_c(f"unknown_rule:{rule.kind}", "warn", "rule kind not recognised"))
            continue
        checks.extend(fn(rule_params(rule), rule.severity, ctx))

    fails = [c for c in checks if c["status"] == "fail"]
    warns = [c for c in checks if c["status"] == "warn"]
    if fails and not warns and all(c["check"] == "not_expired" for c in fails):
        status = "expired"
    elif fails or warns:
        status = "review"
    else:
        status = "verified"
    return status, checks