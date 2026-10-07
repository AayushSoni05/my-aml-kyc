from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import CompanyDetails, CompanyPartner, Customer
from app.schemas import (
    Creation_Company, Updation_Company, Read_Company,
    Creation_CompanyPartner, Updation_CompanyPartner, Read_CompanyPartner,
)

router = APIRouter(prefix="/api/v1/companies", tags=["Company Details & Partners"])

# --- Company Details ---

@router.post("/", response_model=Read_Company)
def create_company(data: Creation_Company, session: Session = Depends(get_session)):
    if session.get(CompanyDetails, data.id):
        raise HTTPException(status_code=400, detail=f"Company details id '{data.id}' already exists")
    if not session.get(Customer, data.customer_id):
        raise HTTPException(status_code=404, detail=f"Customer '{data.customer_id}' not found")
    record = CompanyDetails(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/", response_model=List[Read_Company])
def list_companies(session: Session = Depends(get_session)):
    return session.exec(select(CompanyDetails)).all()

@router.get("/{company_id}", response_model=Read_Company)
def get_company(company_id: str, session: Session = Depends(get_session)):
    record = session.get(CompanyDetails, company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Company details not found")
    return record

@router.patch("/{company_id}", response_model=Read_Company)
def update_company(company_id: str, data: Updation_Company, session: Session = Depends(get_session)):
    record = session.get(CompanyDetails, company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Company details not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/{company_id}")
def delete_company(company_id: str, session: Session = Depends(get_session)):
    record = session.get(CompanyDetails, company_id)
    if not record:
        raise HTTPException(status_code=404, detail="Company details not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "company_id": company_id}


# --- Company Partners (nested under company) ---

@router.post("/{company_id}/partners", response_model=Read_CompanyPartner)
def create_partner(company_id: str, data: Creation_CompanyPartner, session: Session = Depends(get_session)):
    if data.company_id != company_id:
        raise HTTPException(status_code=400, detail="company_id in body must match the URL")
    if session.get(CompanyPartner, data.id):
        raise HTTPException(status_code=400, detail=f"Partner id '{data.id}' already exists")
    if not session.get(CompanyDetails, company_id):
        raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found")
    record = CompanyPartner(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/{company_id}/partners", response_model=List[Read_CompanyPartner])
def list_partners(company_id: str, session: Session = Depends(get_session)):
    return session.exec(
        select(CompanyPartner).where(CompanyPartner.company_id == company_id)
    ).all()

@router.get("/partners/{partner_id}", response_model=Read_CompanyPartner)
def get_partner(partner_id: str, session: Session = Depends(get_session)):
    record = session.get(CompanyPartner, partner_id)
    if not record:
        raise HTTPException(status_code=404, detail="Partner not found")
    return record

@router.patch("/partners/{partner_id}", response_model=Read_CompanyPartner)
def update_partner(partner_id: str, data: Updation_CompanyPartner, session: Session = Depends(get_session)):
    record = session.get(CompanyPartner, partner_id)
    if not record:
        raise HTTPException(status_code=404, detail="Partner not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/partners/{partner_id}")
def delete_partner(partner_id: str, session: Session = Depends(get_session)):
    record = session.get(CompanyPartner, partner_id)
    if not record:
        raise HTTPException(status_code=404, detail="Partner not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "partner_id": partner_id}