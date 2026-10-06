from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models import (
    CustomerType,
    CustomerStatus,
)

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
    full_name: str
    customer_type: CustomerType
    country: Optional[str] = None
    customer_status: Optional[CustomerStatus] = None
    Generated_on: datetime

    class config:
        from_attributes  = True

class Creation_Individual(BaseModel):
    id: str
    customer_id: str
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    occupation: Optional[str] = None

class Upadation_Individual(BaseModel):
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    occupation: Optional[str] = None
    gender: Optional[str] = None

class Read_Individual(BaseModel):
    id: str
    customer_id: str
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    occupation: Optional[str] = None
    gender: Optional[str] = None

    class config:
        from_attributes  = True

class Creation_SoleProprietor(BaseModel):
    id: str
    customer_id: str
    owner_name: str
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    business_registration_number: Optional[str] = None
    business_type: Optional[str] = None

class Updation_SoleProprietor(BaseModel):
    owner_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    business_registration_number: Optional[str] = None
    business_type: Optional[str] = None

class Read_SoleProprietor(BaseModel):
    id: str
    customer_id: str
    owner_name: str
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    business_registration_number: Optional[str] = None
    business_type: Optional[str] = None
    class Config:
        from_attributes = True