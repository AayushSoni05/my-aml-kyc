from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import IndividualDetails, Customer
from app.schemas import Creation_Individual, Upadation_Individual, Read_Individual

router = APIRouter(prefix="/api/v1/individuals", tags=["Individual Details"])

@router.post("/", response_model=Read_Individual)
def create_individual(data: Creation_Individual, session: Session = Depends(get_session)):
    if session.get(IndividualDetails, data.id):
        raise HTTPException(status_code=400, detail=f"Individual details id '{data.id}' already exists")
    if not session.get(Customer, data.customer_id):
        raise HTTPException(status_code=404, detail=f"Customer '{data.customer_id}' not found")
    record = IndividualDetails(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/", response_model=List[Read_Individual])
def list_individuals(session: Session = Depends(get_session)):
    return session.exec(select(IndividualDetails)).all()

@router.get("/{individual_id}", response_model=Read_Individual)
def get_individual(individual_id: str, session: Session = Depends(get_session)):
    record = session.get(IndividualDetails, individual_id)
    if not record:
        raise HTTPException(status_code=404, detail="Individual details not found")
    return record

@router.patch("/{individual_id}", response_model=Read_Individual)
def update_individual(individual_id: str, data: Upadation_Individual, session: Session = Depends(get_session)):
    record = session.get(IndividualDetails, individual_id)
    if not record:
        raise HTTPException(status_code=404, detail="Individual details not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/{individual_id}")
def delete_individual(individual_id: str, session: Session = Depends(get_session)):
    record = session.get(IndividualDetails, individual_id)
    if not record:
        raise HTTPException(status_code=404, detail="Individual details not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "individual_id": individual_id}