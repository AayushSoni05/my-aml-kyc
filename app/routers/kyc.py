from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import KYCDocument, KYCIndividual, KYCCompany, Customer
from app.schemas import (
    Creation_KYCDocument, Updation_KYCDocument, Read_KYCDocument,
    Creation_KYCIndividual, Updation_KYCIndividual, Read_KYCIndividual,
    Creation_KYCCompany, Updation_KYCCompany, Read_KYCCompany,
)

router = APIRouter(prefix="/api/v1/kyc", tags=["KYC"])

def _check_customer(customer_id: str, session: Session):
    if not session.get(Customer, customer_id):
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

# --- KYC Documents ---

@router.post("/documents", response_model=Read_KYCDocument)
def create_document(data: Creation_KYCDocument, session: Session = Depends(get_session)):
    if session.get(KYCDocument, data.id):
        raise HTTPException(status_code=400, detail=f"Document id '{data.id}' already exists")
    _check_customer(data.customer_id, session)
    record = KYCDocument(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/documents", response_model=List[Read_KYCDocument])
def list_documents(session: Session = Depends(get_session)):
    return session.exec(select(KYCDocument)).all()

@router.get("/documents/{doc_id}", response_model=Read_KYCDocument)
def get_document(doc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCDocument, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    return record

@router.patch("/documents/{doc_id}", response_model=Read_KYCDocument)
def update_document(doc_id: str, data: Updation_KYCDocument, session: Session = Depends(get_session)):
    record = session.get(KYCDocument, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCDocument, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "doc_id": doc_id}


# --- KYC Individual ---

@router.post("/individuals", response_model=Read_KYCIndividual)
def create_kyc_individual(data: Creation_KYCIndividual, session: Session = Depends(get_session)):
    if session.get(KYCIndividual, data.id):
        raise HTTPException(status_code=400, detail=f"KYC individual id '{data.id}' already exists")
    _check_customer(data.customer_id, session)
    record = KYCIndividual(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/individuals", response_model=List[Read_KYCIndividual])
def list_kyc_individuals(session: Session = Depends(get_session)):
    return session.exec(select(KYCIndividual)).all()

@router.get("/individuals/{kyc_id}", response_model=Read_KYCIndividual)
def get_kyc_individual(kyc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCIndividual, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC individual not found")
    return record

@router.patch("/individuals/{kyc_id}", response_model=Read_KYCIndividual)
def update_kyc_individual(kyc_id: str, data: Updation_KYCIndividual, session: Session = Depends(get_session)):
    record = session.get(KYCIndividual, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC individual not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/individuals/{kyc_id}")
def delete_kyc_individual(kyc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCIndividual, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC individual not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "kyc_id": kyc_id}


# --- KYC Company ---

@router.post("/companies", response_model=Read_KYCCompany)
def create_kyc_company(data: Creation_KYCCompany, session: Session = Depends(get_session)):
    if session.get(KYCCompany, data.id):
        raise HTTPException(status_code=400, detail=f"KYC company id '{data.id}' already exists")
    _check_customer(data.customer_id, session)
    record = KYCCompany(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/companies", response_model=List[Read_KYCCompany])
def list_kyc_companies(session: Session = Depends(get_session)):
    return session.exec(select(KYCCompany)).all()

@router.get("/companies/{kyc_id}", response_model=Read_KYCCompany)
def get_kyc_company(kyc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCCompany, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC company not found")
    return record

@router.patch("/companies/{kyc_id}", response_model=Read_KYCCompany)
def update_kyc_company(kyc_id: str, data: Updation_KYCCompany, session: Session = Depends(get_session)):
    record = session.get(KYCCompany, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC company not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/companies/{kyc_id}")
def delete_kyc_company(kyc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCCompany, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC company not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "kyc_id": kyc_id}