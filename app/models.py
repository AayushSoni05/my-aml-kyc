from datetime import datetime, date, timezone
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field

# Customers creation ------->
class CustomerType(str, Enum):
    indivudual = "individual"
    sole_proprietor = "sole_proprietor"
    company = "company"

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Customer(SQLModel, table = True):
    id : Optional[int] = Field(default = None, primary_key = True)
    full_name : str
    customer_type : CustomerType = Field(default = CustomerType.individual)
    country : Optional[str] = None
    Generated_on : datetime = Field(default_factory=now_utc)

# Customer_Types ------->
class individualDetails(SQLModel, table = True):
    id = Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="Customer.id")
    date_of_birth: Optional[date] = None
    identifier: Optional[str] = None
    occupation = Optional[str] = None
    gender = Optional[str] = None

class SoleProprietorDetails(SQLModel, Table = True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="Customer.id")
    owner_name: str
    date_of_birth: Optional[date] = None
    identifier: Optional[str] = None
    business_registration_number: Optional[str] = None
    business_type: Optional[str] = None

class CompanyDetails(SQLModel, Table = True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="Customer.id")
    registration_number: Optional[str] = None
    incorporation_date: Optional[date] = None
    industry:Optional[str] = None

class CompanyPartner(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company_id: int = Field(foreign_key="companydetail.id")
    partner_customer_id: int = Field(foreign_key="customer.id")
    ownership_percent: float
    role: Optional[str] = None

# KYC Details ------->
class DocumentType(str, Enum):
    passport = "passport"
    national_id = "national_id"
    driving_license = "driving_license"
    utility_bill = "utility_bill"
    certificate_of_incorporation = "certificate_of_incorporation"
    other = "other"

class VerificationStatus(str, Enum):
    pending = "pending"
    verified = "verified"
    rejected = "rejected"
    expired = "expired"

class KYCDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    document_type: DocumentType
    document_number: Optional[str] = None
    issuing_country: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    file_path: Optional[str] = None
    extracted_data: Optional[str] = None  # JSON string
    verification_status: VerificationStatus = Field(default=VerificationStatus.pending)
    verified_at: Optional[datetime] = None

# KYC Types ------->
class KYCIndividual(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    residential_address: Optional[str] = None
    proof_of_address_verified: bool = False
    source_of_funds: Optional[str] = None
    employment_status: Optional[str] = None
    politically_exposed: bool = False


class KYCCompany(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    registered_address: Optional[str] = None
    business_nature: Optional[str] = None
    source_of_funds: Optional[str] = None
    ultimate_beneficial_owner_identified: bool = False
    regulatory_license_no: Optional[str] = None

# Screening Tables ------->
class MatchStatus(str, Enum):
    matched = "matched"
    possible_match = "possible_match"
    not_matched = "not_matched"


class FoundVia(str, Enum):
    api = "api"
    web_search = "web_search"
    lookup = "lookup"

class Sanctions(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    source_name: str
    source_country: Optional[str] = None
    matched_name: Optional[str] = None
    match_score: Optional[float] = None
    status: MatchStatus
    attribute_scores: Optional[str] = None
    found_via: FoundVia
    explanation: Optional[str] = None
    screened_at: datetime = Field(default_factory=now_utc)

class PEP(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    source_name: str
    source_country: Optional[str] = None
    matched_name: Optional[str] = None
    match_score: Optional[float] = None
    status: MatchStatus
    attribute_scores: Optional[str] = None
    found_via: FoundVia
    explanation: Optional[str] = None
    screened_at: datetime = Field(default_factory=now_utc)

class AdverseMedia(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    headline: str
    source_url: Optional[str] = None
    published_date: Optional[date] = None
    relevance_score: Optional[float] = None
    status: MatchStatus
    explanation: Optional[str] = None
    found_via: FoundVia = Field(default=FoundVia.web_search)
    screened_at: datetime = Field(default_factory=now_utc)

class RiskBand(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"

class CountryRiskReference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    country: str
    risk_level: RiskBand
    score: int
    reason: Optional[str] = None
    last_reviewed: Optional[date] = None

class CountryRisk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    country: str
    reference_id: int = Field(foreign_key="countryriskreference.id")
    score_applied: int
    screened_at: datetime = Field(default_factory=now_utc)

# Overall Score ------->
class OverallScore(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    cri: float
    risk_band: RiskBand
    sanctions_score: Optional[float] = None
    pep_score: Optional[float] = None
    adverse_media_score: Optional[float] = None
    country_risk_score: Optional[float] = None
    weights_used: Optional[str] = None  # JSON string
    calculated_at: datetime = Field(default_factory=now_utc)