from sqlmodel import Session, select
from app.models import (Customer, CustomerType, IndividualDetails, SoleProprietorDetails,
                        CompanyDetails, KYCIndividual, KYCCompany)


def load_kyc_context(session: Session, customer: Customer):
    cid = customer.id
    if customer.customer_type == CustomerType.company:
        details = session.exec(select(CompanyDetails).where(CompanyDetails.customer_id == cid)).first()
        profile = session.exec(select(KYCCompany).where(KYCCompany.customer_id == cid)).first()
    elif customer.customer_type == CustomerType.sole_proprietor:
        details = session.exec(select(SoleProprietorDetails).where(SoleProprietorDetails.customer_id == cid)).first()
        profile = session.exec(select(KYCIndividual).where(KYCIndividual.customer_id == cid)).first()
    else:
        details = session.exec(select(IndividualDetails).where(IndividualDetails.customer_id == cid)).first()
        profile = session.exec(select(KYCIndividual).where(KYCIndividual.customer_id == cid)).first()
    return details, profile