"""Seed data used only to fill an empty database. After seeding, everything here is
edited through /api/v1/kyc-config, never in code."""

DEFAULT_SETTINGS = [
    {"key": "confidence_min", "value": 0.8, "description": "Minimum extraction confidence (0-1)"},
    {"key": "name_pass", "value": 85, "description": "Name similarity (0-100) at or above which names match"},
    {"key": "name_review", "value": 70, "description": "Name similarity below which it is a hard mismatch"},
    {"key": "address_pass", "value": 75, "description": "Address similarity at or above which addresses match"},
    {"key": "ubo_threshold", "value": 25.0, "description": "Ownership % that makes a partner a beneficial owner"},
    {"key": "severity_points", "value": {"high": 25, "medium": 10, "low": 2},
     "description": "Gap score points per finding severity"},
    {"key": "status_by_severity", "value": {"high": "Incomplete", "medium": "Review", "low": "Complete"},
     "description": "KYC status from the worst finding severity"},
]

_DESC = {
    "date_of_birth": "YYYY-MM-DD", "issue_date": "YYYY-MM-DD", "expiry_date": "YYYY-MM-DD",
    "bill_date": "YYYY-MM-DD", "incorporation_date": "YYYY-MM-DD",
    "mrz_line_1": "first machine readable line, copied exactly",
    "mrz_line_2": "second machine readable line, copied exactly",
}


def _fields(*names):
    return [{"name": n, "description": _DESC.get(n, "")} for n in names]


DEFAULT_DOCUMENT_TYPES = [
    {"code": "passport", "label": "Passport", "extract_fields": _fields(
        "full_name", "surname", "given_names", "date_of_birth", "document_number", "nationality",
        "issuing_country", "issue_date", "expiry_date", "mrz_line_1", "mrz_line_2")},
    {"code": "national_id", "label": "National ID", "extract_fields": _fields(
        "full_name", "date_of_birth", "document_number", "issuing_country", "issue_date", "expiry_date", "address")},
    {"code": "driving_license", "label": "Driving licence", "extract_fields": _fields(
        "full_name", "date_of_birth", "document_number", "issuing_country", "issue_date", "expiry_date", "address")},
    {"code": "utility_bill", "label": "Utility bill", "extract_fields": _fields("full_name", "address", "bill_date")},
    {"code": "certificate_of_incorporation", "label": "Certificate of incorporation", "extract_fields": _fields(
        "company_name", "registration_number", "incorporation_date", "jurisdiction")},
    {"code": "other", "label": "Other", "extract_fields": []},
]

DEFAULT_RULES = []


def _doc(applies_to, kind, severity, params=None, description=""):
    DEFAULT_RULES.append({"scope": "document", "applies_to": applies_to, "kind": kind,
                          "severity": severity, "params": params or {}, "description": description})


def _scan(applies_to, kind, severity, params=None, description=""):
    DEFAULT_RULES.append({"scope": "scan", "applies_to": applies_to, "kind": kind,
                          "severity": severity, "params": params or {}, "description": description})


ID_TYPES = ["passport", "national_id", "driving_license"]

# --- document checks ---
_doc("*", "extraction_confidence", "fail", {"min_setting": "confidence_min"})
_doc("*", "document_type_matches", "fail")
_doc("passport", "mrz_td3", "fail")
for _t in ID_TYPES:
    _doc(_t, "not_expired", "fail", {"field": "expiry_date", "missing": "pass" if _t == "national_id" else "warn"})
    _doc(_t, "matches_record", "fail", {"field": "full_name", "record": "expected_name", "matcher": "name", "missing": "warn"})
    _doc(_t, "matches_record", "fail", {"field": "date_of_birth", "record": "details.date_of_birth", "matcher": "date"})
    _doc(_t, "matches_record", "fail", {"field": "document_number", "record": "doc.document_number", "matcher": "id"})
_doc("utility_bill", "max_age_days", "fail", {"field": "bill_date", "days": 90})
_doc("utility_bill", "field_present", "fail", {"field": "address"})
_doc("utility_bill", "matches_record", "fail", {"field": "full_name", "record": "expected_name", "matcher": "name", "missing": "warn"})
_doc("utility_bill", "matches_record", "fail", {"field": "address",
     "record": "profile.residential_address|profile.registered_address", "matcher": "address"})
_doc("certificate_of_incorporation", "field_present", "fail", {"field": "company_name"})
_doc("certificate_of_incorporation", "field_present", "fail", {"field": "registration_number"})
_doc("certificate_of_incorporation", "matches_record", "fail", {"field": "company_name", "record": "customer.full_name", "matcher": "name", "missing": "warn"})
_doc("certificate_of_incorporation", "matches_record", "fail", {"field": "registration_number", "record": "details.registration_number", "matcher": "id"})
_doc("certificate_of_incorporation", "matches_record", "fail", {"field": "incorporation_date", "record": "details.incorporation_date", "matcher": "date"})
_doc("other", "manual_review", "warn")

# --- scan rules ---
for _t in ("individual", "sole_proprietor"):
    _scan(_t, "required_document", "high", {"label": "identity document", "document_types": ID_TYPES})
    _scan(_t, "required_document", "high", {"label": "proof of address", "document_types": ["utility_bill"]})
    _scan(_t, "record_exists", "high", {"target": "details", "code": "missing_details", "label": "customer details"})
    _scan(_t, "record_exists", "high", {"target": "profile", "code": "missing_kyc_profile", "label": "KYC profile"})
    _scan(_t, "required_field", "medium", {"target": "details", "field": "date_of_birth", "label": "Date of birth"})
    _scan(_t, "required_field", "medium", {"target": "details", "field": "identifier", "label": "Identifier"})
    _scan(_t, "required_field", "medium", {"target": "profile", "field": "residential_address", "label": "Residential address"})
    _scan(_t, "required_field", "medium", {"target": "profile", "field": "source_of_funds", "label": "Source of funds"})
    _scan(_t, "required_field", "low", {"target": "profile", "field": "employment_status", "label": "Employment status"})
    _scan(_t, "required_true", "medium", {"target": "profile", "field": "proof_of_address_verified",
          "code": "proof_of_address_not_verified", "message": "Proof of address not marked verified"})
    _scan(_t, "flag_if_true", "low", {"target": "profile", "field": "politically_exposed",
          "code": "declared_pep", "message": "Customer declared themselves politically exposed"})
_scan("sole_proprietor", "required_field", "medium", {"target": "details", "field": "business_registration_number",
      "label": "Business registration number"})

_scan("company", "required_document", "high", {"label": "certificate of incorporation",
      "document_types": ["certificate_of_incorporation"]})
_scan("company", "record_exists", "high", {"target": "details", "code": "missing_details", "label": "customer details"})
_scan("company", "record_exists", "high", {"target": "profile", "code": "missing_kyc_profile", "label": "KYC profile"})
_scan("company", "required_field", "high", {"target": "details", "field": "registration_number", "label": "Registration number"})
_scan("company", "required_field", "low", {"target": "details", "field": "incorporation_date", "label": "Incorporation date"})
_scan("company", "required_field", "medium", {"target": "profile", "field": "registered_address", "label": "Registered address"})
_scan("company", "required_field", "medium", {"target": "profile", "field": "source_of_funds", "label": "Source of funds"})
_scan("company", "required_field", "low", {"target": "profile", "field": "business_nature", "label": "Nature of business"})
_scan("company", "partners_exist", "high")
_scan("company", "ownership_total", "high", {"max": 100})
_scan("company", "ubo_identified", "high", {"ubo_roles": ["ubo"]})
_scan("company", "partner_details_complete", "medium", {"fields": ["date_of_birth", "identifier"]})
_scan("company", "registry_gleif", "low")