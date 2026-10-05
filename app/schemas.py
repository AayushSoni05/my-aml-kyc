from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models import CustomerType, CustomerStatus

class Creation_Customer(BaseModel):
    id: str 
    full_name: str
    customer_type: CustomerType = CustomerType.individual
    country: Optional[str] = None

class Upadation_Customer(BaseModel):
    full_name: Optional[str] = None
    country: Optional[str] = None
    customer_status: Optional[CustomerStatus] = None

class Read_Customer(BaseModel):
    id: str
    full_nmae: str
    customer_type: CustomerType
    country: Optional[str] = None
    customer_status: CustomerStatus
    generated_on: datetime

    class config:
        from_attributes  = True