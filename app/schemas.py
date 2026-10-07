from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel
from app.models import (
    CustomerType,
    CustomerStatus,
    CompanyPartnerRole,
    DocumentType,
    VerificationStatus,
    MatchStatus,
    FoundVia,
    RiskBand
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
    recommendation: Optional[str] = None
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

class Creation_Company(BaseModel):
    id: str
    customer_id: str
    registration_number: Optional[str] = None
    incorporation_date: Optional[datetime] = None
    industry: Optional[str] = None

class Updation_Company(BaseModel):
    registration_number: Optional[str] = None
    incorporation_date: Optional[datetime] = None
    industry: Optional[str] = None

class Read_Company(BaseModel):
    id: str
    customer_id: str
    registration_number: Optional[str] = None
    incorporation_date: Optional[datetime] = None
    industry: Optional[str] = None
    class Config:
        from_attributes = True


class Creation_CompanyPartner(BaseModel):
    id: str
    company_id: str
    partner_name: str
    partner_role: CompanyPartnerRole
    ownership_percent: Optional[float] = None
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    country: Optional[str] = None

class Updation_CompanyPartner(BaseModel):
    partner_name: Optional[str] = None
    partner_role: Optional[CompanyPartnerRole] = None
    ownership_percent: Optional[float] = None
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    country: Optional[str] = None

class Read_CompanyPartner(BaseModel):
    id: str
    company_id: str
    partner_name: str
    partner_role: CompanyPartnerRole
    ownership_percent: Optional[float] = None
    date_of_birth: Optional[datetime] = None
    identifier: Optional[str] = None
    country: Optional[str] = None
    class Config:
        from_attributes = True

class Creation_KYCDocument(BaseModel):
    id: str
    customer_id: str
    document_type: DocumentType
    document_number: Optional[str] = None
    issuing_country: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    file_path: Optional[str] = None
    extracted_data: Optional[str] = None
    verification_status: VerificationStatus = VerificationStatus.pending
    verified_at: Optional[datetime] = None

class Updation_KYCDocument(BaseModel):
    document_type: Optional[DocumentType] = None
    document_number: Optional[str] = None
    issuing_country: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    file_path: Optional[str] = None
    extracted_data: Optional[str] = None
    verification_status: Optional[VerificationStatus] = None
    verified_at: Optional[datetime] = None

class Read_KYCDocument(BaseModel):
    id: str
    customer_id: str
    document_type: DocumentType
    document_number: Optional[str] = None
    issuing_country: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    file_path: Optional[str] = None
    extracted_data: Optional[str] = None
    verification_status: VerificationStatus
    verified_at: Optional[datetime] = None
    class Config:
        from_attributes = True


class Creation_KYCIndividual(BaseModel):
    id: str
    customer_id: str
    residential_address: Optional[str] = None
    proof_of_address_verified: bool = False
    source_of_funds: Optional[str] = None
    employment_status: Optional[str] = None
    politically_exposed: bool = False

class Updation_KYCIndividual(BaseModel):
    residential_address: Optional[str] = None
    proof_of_address_verified: Optional[bool] = None
    source_of_funds: Optional[str] = None
    employment_status: Optional[str] = None
    politically_exposed: Optional[bool] = None

class Read_KYCIndividual(BaseModel):
    id: str
    customer_id: str
    residential_address: Optional[str] = None
    proof_of_address_verified: bool
    source_of_funds: Optional[str] = None
    employment_status: Optional[str] = None
    politically_exposed: bool
    class Config:
        from_attributes = True


class Creation_KYCCompany(BaseModel):
    id: str
    customer_id: str
    registered_address: Optional[str] = None
    business_nature: Optional[str] = None
    source_of_funds: Optional[str] = None
    ultimate_beneficial_owner_identified: bool = False
    regulatory_license_no: Optional[str] = None

class Updation_KYCCompany(BaseModel):
    registered_address: Optional[str] = None
    business_nature: Optional[str] = None
    source_of_funds: Optional[str] = None
    ultimate_beneficial_owner_identified: Optional[bool] = None
    regulatory_license_no: Optional[str] = None

class Read_KYCCompany(BaseModel):
    id: str
    customer_id: str
    registered_address: Optional[str] = None
    business_nature: Optional[str] = None
    source_of_funds: Optional[str] = None
    ultimate_beneficial_owner_identified: bool
    regulatory_license_no: Optional[str] = None
    class Config:
        from_attributes = True

# --- Sanctions ---
class Creation_Sanctions(BaseModel):
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    source_name: str
    source_country: Optional[str] = None
    matched_name: Optional[str] = None
    match_score: Optional[float] = None
    status: MatchStatus
    attribute_scores: Optional[str] = None
    found_via: FoundVia
    explanation: Optional[str] = None

class Read_Sanctions(BaseModel):
    id: int
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    source_name: str
    source_country: Optional[str] = None
    matched_name: Optional[str] = None
    match_score: Optional[float] = None
    status: MatchStatus
    attribute_scores: Optional[str] = None
    found_via: FoundVia
    explanation: Optional[str] = None
    screened_at: datetime
    class Config:
        from_attributes = True

# --- PEP (identical shape to Sanctions) ---
class Creation_PEP(BaseModel):
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    source_name: str
    source_country: Optional[str] = None
    matched_name: Optional[str] = None
    match_score: Optional[float] = None
    status: MatchStatus
    attribute_scores: Optional[str] = None
    found_via: FoundVia
    explanation: Optional[str] = None

class Read_PEP(BaseModel):
    id: int
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    source_name: str
    source_country: Optional[str] = None
    matched_name: Optional[str] = None
    match_score: Optional[float] = None
    status: MatchStatus
    attribute_scores: Optional[str] = None
    found_via: FoundVia
    explanation: Optional[str] = None
    screened_at: datetime
    class Config:
        from_attributes = True

# --- Adverse Media ---
class Creation_AdverseMedia(BaseModel):
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    headline: str
    source_url: Optional[str] = None
    published_date: Optional[date] = None
    relevance_score: Optional[float] = None
    status: MatchStatus
    explanation: Optional[str] = None
    found_via: FoundVia = FoundVia.web_search

class Read_AdverseMedia(BaseModel):
    id: int
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    headline: str
    source_url: Optional[str] = None
    published_date: Optional[date] = None
    relevance_score: Optional[float] = None
    status: MatchStatus
    explanation: Optional[str] = None
    found_via: FoundVia
    screened_at: datetime
    class Config:
        from_attributes = True

# --- Country Risk Reference (static lookup) ---
class Creation_CountryRiskReference(BaseModel):
    country: str
    risk_level: RiskBand
    score: int
    reason: Optional[str] = None
    last_reviewed: Optional[date] = None

class Read_CountryRiskReference(BaseModel):
    id: int
    country: str
    risk_level: RiskBand
    score: int
    reason: Optional[str] = None
    last_reviewed: Optional[date] = None
    class Config:
        from_attributes = True

# --- Country Risk (applied result) ---
class Creation_CountryRisk(BaseModel):
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    country: str
    reference_id: int
    score_applied: int

class Read_CountryRisk(BaseModel):
    id: int
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    country: str
    reference_id: int
    score_applied: int
    screened_at: datetime
    class Config:
        from_attributes = True

class Creation_OverallScore(BaseModel):
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    cri: float
    risk_band: RiskBand
    sanctions_score: Optional[float] = None
    pep_score: Optional[float] = None
    adverse_media_score: Optional[float] = None
    country_risk_score: Optional[float] = None
    weights_used: Optional[str] = None

class Read_OverallScore(BaseModel):
    id: int
    customer_id: Optional[str] = None
    partner_id: Optional[str] = None
    cri: float
    risk_band: RiskBand
    sanctions_score: Optional[float] = None
    pep_score: Optional[float] = None
    adverse_media_score: Optional[float] = None
    country_risk_score: Optional[float] = None
    weights_used: Optional[str] = None
    calculated_at: datetime
    class Config:
        from_attributes = True