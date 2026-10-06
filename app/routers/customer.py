from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Customer
from app.schemas import Creation_Customer, Upadation_Customer, Read_Customer

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])

@router.post("/", response_model=Read_Customer)
def create_customer(data: Creation_Customer, session: Session = Depends(get_session)):
    existing = session.get(Customer, data.id)
    if existing:
        raise HTTPException(status_code=400, detail=F"Customer id'{data.id}' already exists.")
    customer = Customer(**data.model_dump())
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer

@router.get("/", response_model=List[Read_Customer])
def list_customers(session: Session = Depends(get_session)):
    return session.exec(select(Customer)).all()

@router.get("/{customer_id}", response_model=Read_Customer)
def get_customer(customer_id: str, session:Session = Depends(get_session)):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=F"Customer not found.")
    return customer

@router.patch("/{customer_id}", response_model=Read_Customer)
def update_customer(customer_id: str, data: Upadation_Customer, session: Session = Depends(get_session)):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(customer, key, value)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer

@router.delete("/{customer_id}")
def delete_customer(customer_id: str, session: Session = Depends(get_session)):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    session.delete(customer)
    session.commit()
    return {"deleted": True, "customer_id": customer_id}