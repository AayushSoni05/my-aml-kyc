from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import SoleProprietorDetails, Customer
from app.schemas import Creation_SoleProprietor, Updation_SoleProprietor, Read_SoleProprietor

router = APIRouter(prefix="/api/v1/sole-proprietors", tags=["Sole Proprietor Details"])

@router.post("/", response_model=Read_SoleProprietor)
def create_sole_proprietor(data: Creation_SoleProprietor, session: Session = Depends(get_session)):
    if session.get(SoleProprietorDetails, data.id):
        raise HTTPException(status_code=400, detail=f"Sole proprietor details id '{data.id}' already exists")
    if not session.get(Customer, data.customer_id):
        raise HTTPException(status_code=404, detail=f"Customer '{data.customer_id}' not found")
    record = SoleProprietorDetails(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/", response_model=List[Read_SoleProprietor])
def list_sole_proprietors(session: Session = Depends(get_session)):
    return session.exec(select(SoleProprietorDetails)).all()

@router.get("/{record_id}", response_model=Read_SoleProprietor)
def get_sole_proprietor(record_id: str, session: Session = Depends(get_session)):
    record = session.get(SoleProprietorDetails, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sole proprietor details not found")
    return record

@router.patch("/{record_id}", response_model=Read_SoleProprietor)
def update_sole_proprietor(record_id: str, data: Updation_SoleProprietor, session: Session = Depends(get_session)):
    record = session.get(SoleProprietorDetails, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sole proprietor details not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/{record_id}")
def delete_sole_proprietor(record_id: str, session: Session = Depends(get_session)):
    record = session.get(SoleProprietorDetails, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Sole proprietor details not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "record_id": record_id}