from datetime import datetime, date, timezone
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field

# Customers ------->
class CustomerType(str, Enum):
    individual = "individual"
    sole_proprietor = "sole_proprietor"
    company = "company"

class CustomerStatus(str, Enum):
    All_Clear = "Clear"
    Possible_Match = "Review"
    Match = "Match"

class CompanyPartnerRole(str, Enum):
    owner = "owner"
    controller = "controller"
    director = "director"
    authorized_person = "authorized_person"
    authorized_signatory = "authorized_signatory"
    shareholder = "shareholder"
    ubo = "ubo"

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Customer(SQLModel, table=True):
    __tablename__ = "customer"
    id: str = Field(primary_key=True)
    full_name: str
    customer_type: CustomerType = Field(default=CustomerType.individual)
    country: Optional[str] = None
    customer_status: Optional[CustomerStatus] = Field(default=CustomerStatus.All_Clear)
    recommendation: Optional[str] = None
    Generated_on: datetime = Field(default_factory=now_utc)

# Customer Types ------->
class IndividualDetails(SQLModel, table=True):
    __tablename__ = "individual_details"
    id: Optional[str] = Field(primary_key=True)
    customer_id: str = Field(foreign_key="customer.id")
    date_of_birth: Optional[date] = None
    identifier: Optional[str] = None
    occupation: Optional[str] = None
    gender: Optional[str] = None

class SoleProprietorDetails(SQLModel, table=True):
    __tablename__ = "sole_proprietor_details"
    id: Optional[str] = Field(default=None, primary_key=True)
    customer_id: str = Field(foreign_key="customer.id")
    owner_name: str
    date_of_birth: Optional[date] = None
    identifier: Optional[str] = None
    business_registration_number: Optional[str] = None
    business_type: Optional[str] = None

class CompanyDetails(SQLModel, table=True):
    __tablename__ = "company_details"
    id: Optional[str] = Field(default=None, primary_key=True)
    customer_id: str = Field(foreign_key="customer.id")
    registration_number: Optional[str] = None
    incorporation_date: Optional[date] = None
    industry: Optional[str] = None

# Partners — NOT customers, but screenable in their own right
class CompanyPartner(SQLModel, table=True):
    __tablename__ = "company_partner"
    id: Optional[str] = Field(default=None, primary_key=True)
    company_id: str = Field(foreign_key="company_details.id")
    partner_name: str
    partner_role: CompanyPartnerRole
    ownership_percent: Optional[float] = None
    date_of_birth: Optional[date] = None
    identifier: Optional[str] = None
    country: Optional[str] = None

# KYC Documents ------->
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
    __tablename__ = "kyc_document"
    id: Optional[str] = Field(default=None, primary_key=True)
    customer_id: str = Field(foreign_key="customer.id")
    document_type: DocumentType
    document_number: Optional[str] = None
    issuing_country: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    file_path: Optional[str] = None
    extracted_data: Optional[str] = None
    verification_status: VerificationStatus = Field(default=VerificationStatus.pending)
    verified_at: Optional[datetime] = None

# KYC Types ------->
class KYCIndividual(SQLModel, table=True):
    __tablename__ = "kyc_individual"
    id: Optional[str] = Field(default=None, primary_key=True)
    customer_id: str = Field(foreign_key="customer.id")
    residential_address: Optional[str] = None
    proof_of_address_verified: bool = False
    source_of_funds: Optional[str] = None
    employment_status: Optional[str] = None
    politically_exposed: bool = False

class KYCCompany(SQLModel, table=True):
    __tablename__ = "kyc_company"
    id: Optional[str] = Field(default=None, primary_key=True)
    customer_id: str = Field(foreign_key="customer.id")
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
    __tablename__ = "sanctions"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[str] = Field(default=None, foreign_key="customer.id")
    partner_id: Optional[str] = Field(default=None, foreign_key="company_partner.id")
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
    __tablename__ = "pep"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[str] = Field(default=None, foreign_key="customer.id")
    partner_id: Optional[str] = Field(default=None, foreign_key="company_partner.id")
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
    __tablename__ = "adverse_media"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[str] = Field(default=None, foreign_key="customer.id")
    partner_id: Optional[str] = Field(default=None, foreign_key="company_partner.id")
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
    __tablename__ = "country_risk_reference"
    id: Optional[int] = Field(default=None, primary_key=True)
    country: str
    risk_level: RiskBand
    score: int
    reason: Optional[str] = None
    last_reviewed: Optional[date] = None

class CountryRisk(SQLModel, table=True):
    __tablename__ = "country_risk"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[str] = Field(default=None, foreign_key="customer.id")
    partner_id: Optional[str] = Field(default=None, foreign_key="company_partner.id")
    country: str
    reference_id: int = Field(foreign_key="country_risk_reference.id")
    score_applied: int
    screened_at: datetime = Field(default_factory=now_utc)

# Overall Score ------->
class OverallScore(SQLModel, table=True):
    __tablename__ = "overall_score"
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: Optional[str] = Field(default=None, foreign_key="customer.id")
    partner_id: Optional[str] = Field(default=None, foreign_key="company_partner.id")
    cri: float
    risk_band: RiskBand
    sanctions_score: Optional[float] = None
    pep_score: Optional[float] = None
    adverse_media_score: Optional[float] = None
    country_risk_score: Optional[float] = None
    weights_used: Optional[str] = None
    calculated_at: datetime = Field(default_factory=now_utc)