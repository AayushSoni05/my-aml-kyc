"""
Creates one fully-connected example: a company with a partner, both
screened, with KYC and an overall score — proving the whole schema works
together end to end.
Run with: python scripts/seed_example.py
"""
from datetime import date
from app import models
from app.database import engine, init_db
from sqlmodel import Session, select

init_db()

with Session(engine) as session:

    # Skip entirely if this demo data already exists
    existing = session.exec(
        select(models.Customer).where(models.Customer.full_name == "Acme Trading Ltd")
    ).first()
    if existing:
        print("Seed data already exists, skipping.")
    else:
        # 1. The company itself
        company_customer = models.Customer(
            full_name="Acme Trading Ltd",
            customer_type=models.CustomerType.company,
            country="Ghana",
        )
        session.add(company_customer)
        session.commit()
        session.refresh(company_customer)

        company_detail = models.CompanyDetails(
            customer_id=company_customer.id,
            registration_number="GH-REG-2024-001",
            incorporation_date=date(2024, 1, 15),
            industry="Import/Export Trading",
        )
        session.add(company_detail)
        session.commit()
        session.refresh(company_detail)

        # 2. The partner — their own customer row (type = individual)
        partner_customer = models.Customer(
            full_name="Sang Jun Ji",
            customer_type=models.CustomerType.individual,
            country="Russia",
        )
        session.add(partner_customer)
        session.commit()
        session.refresh(partner_customer)

        individual_detail = models.IndividualDetails(
            customer_id=partner_customer.id,
            date_of_birth=date(1971, 5, 3),
            identifier="RU-PASSPORT-001",
            occupation="Bank representative",
            gender="M",
        )
        session.add(individual_detail)

        # 3. Link the partner to the company
        link = models.CompanyPartner(
            company_id=company_detail.id,
            partner_customer_id=partner_customer.id,
            ownership_percent=60.0,
            role="Director",
        )
        session.add(link)

        # 4. KYC for the company
        kyc_company = models.KYCCompany(
            customer_id=company_customer.id,
            registered_address="123 Independence Ave, Accra, Ghana",
            business_nature="Import/export trading",
            ultimate_beneficial_owner_identified=True,
        )
        session.add(kyc_company)

        # 5. Screen the PARTNER against sanctions (real example from our walkthrough)
        sanctions_hit = models.Sanctions(
            customer_id=partner_customer.id,
            source_name="OFAC SDN List",
            source_country="USA",
            matched_name="JI, Sang Jun (a.k.a. CHI, Sang-chun)",
            match_score=0.95,
            status=models.MatchStatus.matched,
            found_via=models.FoundVia.api,
            explanation="Moscow-based representative of Korea Kumgang Group Bank, sanctioned under North Korea Sanctions Regulations.",
        )
        session.add(sanctions_hit)

        # 6. Country risk reference data + result for the company (Ghana)
        ghana_risk = session.exec(
            select(models.CountryRiskReference).where(models.CountryRiskReference.country == "Ghana")
        ).first()
        if not ghana_risk:
            ghana_risk = models.CountryRiskReference(
                country="Ghana",
                risk_level=models.RiskBand.medium,
                score=45,
                reason="FATF monitoring, moderate corruption index",
                last_reviewed=date(2026, 1, 1),
            )
            session.add(ghana_risk)
            session.commit()
            session.refresh(ghana_risk)

        country_result = models.CountryRisk(
            customer_id=company_customer.id,
            country="Ghana",
            reference_id=ghana_risk.id,
            score_applied=ghana_risk.score,
        )
        session.add(country_result)

        # 7. Overall score for the PARTNER (driven by the sanctions hit)
        partner_score = models.OverallScore(
            customer_id=partner_customer.id,
            cri=95.0,
            risk_band=models.RiskBand.critical,
            sanctions_score=95.0,
            pep_score=0.0,
            adverse_media_score=0.0,
            country_risk_score=30.0,
        )
        session.add(partner_score)

        # 8. Overall score for the COMPANY itself (clean sanctions, but flagged via partner)
        company_score = models.OverallScore(
            customer_id=company_customer.id,
            cri=70.0,
            risk_band=models.RiskBand.high,
            sanctions_score=0.0,
            pep_score=0.0,
            adverse_media_score=0.0,
            country_risk_score=45.0,
        )
        session.add(company_score)

        session.commit()
        print(f"Seeded: company id={company_customer.id}, partner id={partner_customer.id}")

# Read back and print a summary
with Session(engine) as session:
    company = session.exec(
        select(models.Customer).where(models.Customer.full_name == "Acme Trading Ltd")
    ).first()
    partner = session.exec(
        select(models.Customer).where(models.Customer.full_name == "Sang Jun Ji")
    ).first()

    print("\n--- Summary ---")
    print(f"Company: {company.full_name} ({company.customer_type})")
    print(f"Partner: {partner.full_name} ({partner.customer_type})")

    partner_sanctions = session.exec(
        select(models.Sanctions).where(models.Sanctions.customer_id == partner.id)
    ).all()
    for s in partner_sanctions:
        print(f"  Sanctions hit on partner: {s.status} — {s.matched_name} ({s.source_name})")

    partner_overall = session.exec(
        select(models.OverallScore).where(models.OverallScore.customer_id == partner.id)
    ).first()
    company_overall = session.exec(
        select(models.OverallScore).where(models.OverallScore.customer_id == company.id)
    ).first()
    print(f"  Partner CRI: {partner_overall.cri} ({partner_overall.risk_band})")
    print(f"  Company CRI: {company_overall.cri} ({company_overall.risk_band})")

print("\nPhase 2 full-schema check: PASSED")