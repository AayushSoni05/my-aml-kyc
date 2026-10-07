from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import (
    Sanctions, PEP, AdverseMedia, CountryRisk, CountryRiskReference,
    Customer, CompanyPartner, CustomerStatus, MatchStatus, OverallScore
)
from app.schemas import (
    Creation_Sanctions, Read_Sanctions,
    Creation_PEP, Read_PEP,
    Creation_AdverseMedia, Read_AdverseMedia,
    Creation_CountryRiskReference, Read_CountryRiskReference,
    Creation_CountryRisk, Read_CountryRisk,
    Creation_OverallScore, Read_OverallScore
)

router = APIRouter(prefix="/api/v1/screening", tags=["Screening"])


def _validate_subject(customer_id: Optional[str], partner_id: Optional[str], session: Session):
    """Exactly one of customer_id / partner_id must be set, and must exist."""
    if bool(customer_id) == bool(partner_id):
        raise HTTPException(status_code=400, detail="Provide exactly one of customer_id or partner_id")
    if customer_id and not session.get(Customer, customer_id):
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    if partner_id and not session.get(CompanyPartner, partner_id):
        raise HTTPException(status_code=404, detail=f"Partner '{partner_id}' not found")


CRI_REVIEW_THRESHOLD = 60.0
CRI_BLOCK_THRESHOLD = 80.0

_RANK = {
    CustomerStatus.All_Clear: 0,
    CustomerStatus.Possible_Match: 1,
    CustomerStatus.Match: 2,
}


def _recompute_customer_status(customer_id: str, session: Session):
    """Final status = most severe of: latest sanctions/PEP/adverse media result,
    and the latest CRI. Also writes a plain-English recommendation."""
    customer = session.get(Customer, customer_id)
    if not customer:
        return

    status = CustomerStatus.All_Clear
    reasons = []

    def escalate(new_status, reason):
        nonlocal status
        reasons.append(reason)
        if _RANK[new_status] > _RANK[status]:
            status = new_status

    for model, label in ((Sanctions, "sanctions"), (PEP, "PEP"), (AdverseMedia, "adverse media")):
        latest = session.exec(
            select(model)
            .where(model.customer_id == customer_id)
            .order_by(model.screened_at.desc())
        ).first()
        if latest and latest.status == MatchStatus.matched:
            escalate(CustomerStatus.Match, f"{label} match")
        elif latest and latest.status == MatchStatus.possible_match:
            escalate(CustomerStatus.Possible_Match, f"{label} possible match")

    score = session.exec(
        select(OverallScore)
        .where(OverallScore.customer_id == customer_id)
        .order_by(OverallScore.calculated_at.desc())
    ).first()
    if score:
        if score.cri >= CRI_BLOCK_THRESHOLD:
            escalate(CustomerStatus.Match, f"CRI {score.cri:.1f} is at or above {CRI_BLOCK_THRESHOLD:g}")
        elif score.cri >= CRI_REVIEW_THRESHOLD:
            escalate(CustomerStatus.Possible_Match, f"CRI {score.cri:.1f} is at or above {CRI_REVIEW_THRESHOLD:g}")

    if status == CustomerStatus.Match:
        text = "Reject / block onboarding"
    elif status == CustomerStatus.Possible_Match:
        text = "Hold for manual review by a compliance analyst"
    else:
        text = "Approve - no adverse findings"
    if reasons:
        text += " (" + "; ".join(reasons) + ")"

    customer.customer_status = status
    customer.recommendation = text
    session.add(customer)
    session.commit()


# --- Sanctions ---

@router.post("/sanctions", response_model=Read_Sanctions)
def create_sanctions(data: Creation_Sanctions, session: Session = Depends(get_session)):
    _validate_subject(data.customer_id, data.partner_id, session)
    record = Sanctions(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    if data.customer_id:
        _recompute_customer_status(data.customer_id, session)
    return record

@router.get("/sanctions", response_model=List[Read_Sanctions])
def list_sanctions(session: Session = Depends(get_session)):
    return session.exec(select(Sanctions)).all()

@router.get("/sanctions/{record_id}", response_model=Read_Sanctions)
def get_sanctions(record_id: int, session: Session = Depends(get_session)):
    record = session.get(Sanctions, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sanctions record not found")
    return record

@router.delete("/sanctions/{record_id}")
def delete_sanctions(record_id: int, session: Session = Depends(get_session)):
    record = session.get(Sanctions, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sanctions record not found")
    customer_id = record.customer_id
    session.delete(record)
    session.commit()
    if customer_id:
        _recompute_customer_status(customer_id, session)
    return {"deleted": True, "record_id": record_id}


# --- PEP ---

@router.post("/pep", response_model=Read_PEP)
def create_pep(data: Creation_PEP, session: Session = Depends(get_session)):
    _validate_subject(data.customer_id, data.partner_id, session)
    record = PEP(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    if data.customer_id:
        _recompute_customer_status(data.customer_id, session)
    return record

@router.get("/pep", response_model=List[Read_PEP])
def list_pep(session: Session = Depends(get_session)):
    return session.exec(select(PEP)).all()

@router.get("/pep/{record_id}", response_model=Read_PEP)
def get_pep(record_id: int, session: Session = Depends(get_session)):
    record = session.get(PEP, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="PEP record not found")
    return record

@router.delete("/pep/{record_id}")
def delete_pep(record_id: int, session: Session = Depends(get_session)):
    record = session.get(PEP, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="PEP record not found")
    customer_id = record.customer_id
    session.delete(record)
    session.commit()
    if customer_id:
        _recompute_customer_status(customer_id, session)
    return {"deleted": True, "record_id": record_id}


# --- Adverse Media ---

@router.post("/adverse-media", response_model=Read_AdverseMedia)
def create_adverse_media(data: Creation_AdverseMedia, session: Session = Depends(get_session)):
    _validate_subject(data.customer_id, data.partner_id, session)
    record = AdverseMedia(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    if data.customer_id:
        _recompute_customer_status(data.customer_id, session)
    return record

@router.get("/adverse-media", response_model=List[Read_AdverseMedia])
def list_adverse_media(session: Session = Depends(get_session)):
    return session.exec(select(AdverseMedia)).all()

@router.get("/adverse-media/{record_id}", response_model=Read_AdverseMedia)
def get_adverse_media(record_id: int, session: Session = Depends(get_session)):
    record = session.get(AdverseMedia, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Adverse media record not found")
    return record

@router.delete("/adverse-media/{record_id}")
def delete_adverse_media(record_id: int, session: Session = Depends(get_session)):
    record = session.get(AdverseMedia, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Adverse media record not found")
    customer_id = record.customer_id
    session.delete(record)
    session.commit()
    if customer_id:
        _recompute_customer_status(customer_id, session)
    return {"deleted": True, "record_id": record_id}


# --- Country Risk Reference (static lookup, managed separately) ---

@router.post("/country-risk-reference", response_model=Read_CountryRiskReference)
def create_country_risk_reference(data: Creation_CountryRiskReference, session: Session = Depends(get_session)):
    existing = session.exec(
        select(CountryRiskReference).where(CountryRiskReference.country == data.country)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Reference for '{data.country}' already exists")
    record = CountryRiskReference(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/country-risk-reference", response_model=List[Read_CountryRiskReference])
def list_country_risk_reference(session: Session = Depends(get_session)):
    return session.exec(select(CountryRiskReference)).all()


# --- Country Risk (applied result) ---

@router.post("/country-risk", response_model=Read_CountryRisk)
def create_country_risk(data: Creation_CountryRisk, session: Session = Depends(get_session)):
    _validate_subject(data.customer_id, data.partner_id, session)
    if not session.get(CountryRiskReference, data.reference_id):
        raise HTTPException(status_code=404, detail=f"Reference id {data.reference_id} not found")
    record = CountryRisk(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/country-risk", response_model=List[Read_CountryRisk])
def list_country_risk(session: Session = Depends(get_session)):
    return session.exec(select(CountryRisk)).all()

# --- Overall Score ---

@router.post("/scores", response_model=Read_OverallScore)
def create_score(data: Creation_OverallScore, session: Session = Depends(get_session)):
    _validate_subject(data.customer_id, data.partner_id, session)
    record = OverallScore(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    if data.customer_id:
        _recompute_customer_status(data.customer_id, session)
    return record

@router.get("/scores", response_model=List[Read_OverallScore])
def list_scores(session: Session = Depends(get_session)):
    return session.exec(select(OverallScore)).all()

@router.get("/scores/customer/{customer_id}/latest", response_model=Read_OverallScore)
def latest_customer_score(customer_id: str, session: Session = Depends(get_session)):
    record = session.exec(
        select(OverallScore)
        .where(OverallScore.customer_id == customer_id)
        .order_by(OverallScore.calculated_at.desc())
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="No score found for this customer")
    return record

@router.get("/scores/partner/{partner_id}/latest", response_model=Read_OverallScore)
def latest_partner_score(partner_id: str, session: Session = Depends(get_session)):
    record = session.exec(
        select(OverallScore)
        .where(OverallScore.partner_id == partner_id)
        .order_by(OverallScore.calculated_at.desc())
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="No score found for this partner")
    return record

@router.get("/scores/{score_id}", response_model=Read_OverallScore)
def get_score(score_id: int, session: Session = Depends(get_session)):
    record = session.get(OverallScore, score_id)
    if not record:
        raise HTTPException(status_code=404, detail="Score not found")
    return record

@router.delete("/scores/{score_id}")
def delete_score(score_id: int, session: Session = Depends(get_session)):
    record = session.get(OverallScore, score_id)
    if not record:
        raise HTTPException(status_code=404, detail="Score not found")
    customer_id = record.customer_id
    session.delete(record)
    session.commit()
    if customer_id:
        _recompute_customer_status(customer_id, session)
    return {"deleted": True, "score_id": score_id}