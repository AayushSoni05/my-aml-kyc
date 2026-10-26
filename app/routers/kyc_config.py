import json
from typing import Any, List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from app.database import get_session
from app.models import KYCDocumentType, KYCRule, KYCSetting, KYCDocument, CustomerType
from app.idp.verify import CHECKS
from app.idp.extractor import RESERVED_FIELDS
from app.idp.kyc_scan import SCAN_CHECKS
# TEMPORARY until steps 5 and 6: replace these three lines with the real imports
#   from app.idp.verify import CHECKS
#   from app.idp.kyc_scan import SCAN_CHECKS
#   from app.idp.extractor import RESERVED_FIELDS
CHECKS =  {}
RESERVED_FIELDS = {"document_type_detected", "confidence", "notes"}

router = APIRouter(prefix="/api/v1/kyc-config", tags=["KYC Config"])
_NAME = r"^[a-z][a-z0-9_]{0,40}$"


class FieldDef(BaseModel):
    name: str = Field(pattern=_NAME)
    description: str = ""


class DocTypeIn(BaseModel):
    code: str = Field(pattern=_NAME)
    label: str
    extract_fields: List[FieldDef] = []
    active: bool = True


class DocTypeUpdate(BaseModel):
    label: Optional[str] = None
    extract_fields: Optional[List[FieldDef]] = None
    active: Optional[bool] = None


class DocTypeOut(DocTypeIn):
    pass


class RuleIn(BaseModel):
    scope: Literal["document", "scan"]
    applies_to: str = "*"
    kind: str
    params: dict = {}
    severity: str
    description: Optional[str] = None
    active: bool = True


class RuleUpdate(BaseModel):
    applies_to: Optional[str] = None
    params: Optional[dict] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


class RuleOut(RuleIn):
    id: int


class SettingIn(BaseModel):
    value: Any
    description: Optional[str] = None


def _check_fields(fields):
    bad = [f.name for f in fields if f.name in RESERVED_FIELDS]
    if bad:
        raise HTTPException(status_code=400, detail=f"Reserved field names: {bad}")


def _dt_out(r):
    return DocTypeOut(code=r.code, label=r.label, extract_fields=json.loads(r.extract_fields), active=r.active)


def _rule_out(r):
    return RuleOut(id=r.id, scope=r.scope, applies_to=r.applies_to, kind=r.kind, params=json.loads(r.params),
                   severity=r.severity, description=r.description, active=r.active)


def _validate_rule(scope, applies_to, kind, severity, session):
    kinds = CHECKS if scope == "document" else SCAN_CHECKS
    if kind not in kinds:
        raise HTTPException(status_code=400, detail=f"Unknown kind '{kind}'. Allowed: {sorted(kinds)}")
    allowed = {"fail", "warn"} if scope == "document" else {"high", "medium", "low"}
    if severity not in allowed:
        raise HTTPException(status_code=400, detail=f"severity must be one of {sorted(allowed)}")
    if scope == "document" and applies_to != "*" and session.get(KYCDocumentType, applies_to) is None:
        raise HTTPException(status_code=400, detail=f"Unknown document type '{applies_to}'")
    if scope == "scan" and applies_to not in {"*", *[t.value for t in CustomerType]}:
        raise HTTPException(status_code=400, detail="applies_to must be '*' or a customer type")


@router.get("/kinds")
def list_kinds():
    """What check kinds exist and the parameters each takes."""
    return {"document": {k: (f.__doc__ or "").strip() for k, f in CHECKS.items()},
            "scan": {k: (f.__doc__ or "").strip() for k, f in SCAN_CHECKS.items()}}


# --- document types ---

@router.get("/document-types", response_model=List[DocTypeOut])
def list_document_types(session: Session = Depends(get_session)):
    return [_dt_out(r) for r in session.exec(select(KYCDocumentType)).all()]


@router.post("/document-types", response_model=DocTypeOut)
def create_document_type(data: DocTypeIn, session: Session = Depends(get_session)):
    if session.get(KYCDocumentType, data.code):
        raise HTTPException(status_code=400, detail="Document type already exists")
    _check_fields(data.extract_fields)
    row = KYCDocumentType(code=data.code, label=data.label, active=data.active,
                          extract_fields=json.dumps([f.model_dump() for f in data.extract_fields]))
    session.add(row)
    session.commit()
    return _dt_out(row)


@router.patch("/document-types/{code}", response_model=DocTypeOut)
def update_document_type(code: str, data: DocTypeUpdate, session: Session = Depends(get_session)):
    row = session.get(KYCDocumentType, code)
    if not row:
        raise HTTPException(status_code=404, detail="Document type not found")
    if data.label is not None:
        row.label = data.label
    if data.active is not None:
        row.active = data.active
    if data.extract_fields is not None:
        _check_fields(data.extract_fields)
        row.extract_fields = json.dumps([f.model_dump() for f in data.extract_fields])
    session.add(row)
    session.commit()
    return _dt_out(row)


@router.delete("/document-types/{code}")
def delete_document_type(code: str, session: Session = Depends(get_session)):
    row = session.get(KYCDocumentType, code)
    if not row:
        raise HTTPException(status_code=404, detail="Document type not found")
    if session.exec(select(KYCDocument).where(KYCDocument.document_type == code)).first():
        raise HTTPException(status_code=400, detail="Documents use this type; deactivate it instead")
    session.delete(row)
    session.commit()
    return {"deleted": True, "code": code}


# --- rules ---

@router.get("/rules", response_model=List[RuleOut])
def list_rules(scope: Optional[str] = None, session: Session = Depends(get_session)):
    q = select(KYCRule).order_by(KYCRule.id)
    if scope:
        q = q.where(KYCRule.scope == scope)
    return [_rule_out(r) for r in session.exec(q).all()]


@router.post("/rules", response_model=RuleOut)
def create_rule(data: RuleIn, session: Session = Depends(get_session)):
    _validate_rule(data.scope, data.applies_to, data.kind, data.severity, session)
    row = KYCRule(scope=data.scope, applies_to=data.applies_to, kind=data.kind, params=json.dumps(data.params),
                  severity=data.severity, description=data.description, active=data.active)
    session.add(row)
    session.commit()
    session.refresh(row)
    return _rule_out(row)


@router.patch("/rules/{rule_id}", response_model=RuleOut)
def update_rule(rule_id: int, data: RuleUpdate, session: Session = Depends(get_session)):
    row = session.get(KYCRule, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    changes = data.model_dump(exclude_unset=True)
    _validate_rule(row.scope, changes.get("applies_to", row.applies_to), row.kind,
                   changes.get("severity", row.severity), session)
    if "params" in changes:
        changes["params"] = json.dumps(changes["params"])
    for k, v in changes.items():
        setattr(row, k, v)
    session.add(row)
    session.commit()
    session.refresh(row)
    return _rule_out(row)


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, session: Session = Depends(get_session)):
    row = session.get(KYCRule, rule_id)
    if not row:
        raise HTTPException(status_code=404, detail="Rule not found")
    session.delete(row)
    session.commit()
    return {"deleted": True, "rule_id": rule_id}


# --- settings ---

@router.get("/settings")
def list_settings(session: Session = Depends(get_session)):
    return [{"key": r.key, "value": json.loads(r.value), "description": r.description}
            for r in session.exec(select(KYCSetting)).all()]


@router.put("/settings/{key}")
def put_setting(key: str, data: SettingIn, session: Session = Depends(get_session)):
    row = session.get(KYCSetting, key) or KYCSetting(key=key, value="null")
    row.value = json.dumps(data.value)
    if data.description is not None:
        row.description = data.description
    session.add(row)
    session.commit()
    return {"key": key, "value": data.value, "description": row.description}