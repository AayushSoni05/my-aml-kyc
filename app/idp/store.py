import json
from sqlmodel import Session, select
from app.models import KYCDocumentType, KYCRule, KYCSetting
from app.idp import defaults


def load_settings(session: Session) -> dict:
    s = {d["key"]: d["value"] for d in defaults.DEFAULT_SETTINGS}     # fallback if a row was deleted
    for row in session.exec(select(KYCSetting)).all():
        s[row.key] = json.loads(row.value)
    return s


def load_rules(session: Session, scope: str, applies_to: list) -> list:
    rows = session.exec(select(KYCRule).where(KYCRule.scope == scope, KYCRule.active == True)  # noqa: E712
                        .order_by(KYCRule.id)).all()
    return [r for r in rows if r.applies_to in applies_to]


def active_type_codes(session: Session) -> list:
    rows = session.exec(select(KYCDocumentType).where(KYCDocumentType.active == True)).all()  # noqa: E712
    return [r.code for r in rows]


def seed_kyc_config(session: Session):
    """Fills missing settings and document types, and the rules only if the rule table is empty."""
    for d in defaults.DEFAULT_SETTINGS:
        if session.get(KYCSetting, d["key"]) is None:
            session.add(KYCSetting(key=d["key"], value=json.dumps(d["value"]), description=d["description"]))
    for t in defaults.DEFAULT_DOCUMENT_TYPES:
        if session.get(KYCDocumentType, t["code"]) is None:
            session.add(KYCDocumentType(code=t["code"], label=t["label"],
                                        extract_fields=json.dumps(t["extract_fields"])))
    if session.exec(select(KYCRule)).first() is None:
        for r in defaults.DEFAULT_RULES:
            session.add(KYCRule(scope=r["scope"], applies_to=r["applies_to"], kind=r["kind"],
                                severity=r["severity"], params=json.dumps(r["params"]),
                                description=r["description"] or None))
    session.commit()