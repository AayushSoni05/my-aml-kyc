import json
import logging
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from app.config import settings
from app.database import get_session
from app.models import (KYCDocument, KYCIndividual, KYCCompany, Customer, KYCDocumentType,
                        VerificationStatus, now_utc)
from app.idp.extractor import extract_document
from app.idp.verify import verify_document
from app.idp.context import load_kyc_context
from app.idp.store import load_settings, load_rules, active_type_codes
from app.idp.textutil import parse_iso
from app.schemas import (
    Creation_KYCDocument, Updation_KYCDocument, Read_KYCDocument,
    Creation_KYCIndividual, Updation_KYCIndividual, Read_KYCIndividual,
    Creation_KYCCompany, Updation_KYCCompany, Read_KYCCompany,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/kyc", tags=["KYC"])

def _check_customer(customer_id: str, session: Session):
    if not session.get(Customer, customer_id):
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")

# --- KYC Documents ---

@router.post("/documents", response_model=Read_KYCDocument)
def create_document(data: Creation_KYCDocument, session: Session = Depends(get_session)):
    if session.get(KYCDocument, data.id):
        raise HTTPException(status_code=400, detail=f"Document id '{data.id}' already exists")
    _check_customer(data.customer_id, session)
    dt = session.get(KYCDocumentType, data.document_type)
    if not dt or not dt.active:
        raise HTTPException(status_code=400, detail=f"Unknown or inactive document type '{data.document_type}'")
    record = KYCDocument(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/documents", response_model=List[Read_KYCDocument])
def list_documents(session: Session = Depends(get_session)):
    return session.exec(select(KYCDocument)).all()

@router.get("/documents/{doc_id}", response_model=Read_KYCDocument)
def get_document(doc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCDocument, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    return record

@router.patch("/documents/{doc_id}", response_model=Read_KYCDocument)
def update_document(doc_id: str, data: Updation_KYCDocument, session: Session = Depends(get_session)):
    record = session.get(KYCDocument, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
_SIGNATURES = {            # file type -> the first bytes a real file of that type starts with
    ".pdf": b"%PDF",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".png": b"\x89PNG\r\n\x1a\n",
}


@router.post("/documents/{doc_id}/upload", response_model=Read_KYCDocument)
def upload_document(doc_id: str, file: UploadFile = File(...), session: Session = Depends(get_session)):
    record = session.get(KYCDocument, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in _SIGNATURES:
        raise HTTPException(status_code=400, detail="Only PDF, JPG and PNG files are allowed")

    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")
    if not content.startswith(_SIGNATURES[ext]):
        raise HTTPException(status_code=400, detail="File content does not match its extension")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved = upload_dir / f"{uuid.uuid4().hex}{ext}"     # random name: never the client's name or your ids
    saved.write_bytes(content)

    record.file_path = str(saved)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.post("/documents/{doc_id}/process", response_model=Read_KYCDocument)
def process_document(doc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCDocument, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    if not record.file_path or not Path(record.file_path).exists():
        raise HTTPException(status_code=400, detail="Upload a file for this document first")
    customer = session.get(Customer, record.customer_id)

    doc_type = session.get(KYCDocumentType, record.document_type)
    if not doc_type or not doc_type.active:
        raise HTTPException(status_code=400, detail=f"Unknown or inactive document type '{record.document_type}'")
    try:
        extracted = extract_document(record.file_path, json.loads(doc_type.extract_fields),
                                     active_type_codes(session))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        log.exception("Document extraction failed")
        raise HTTPException(status_code=502, detail="Document extraction failed")

    details, kyc_profile = load_kyc_context(session, customer)
    rules = load_rules(session, "document", [record.document_type, "*"])
    status, checks = verify_document(record, extracted, customer, details, kyc_profile,
                                     rules, load_settings(session))

    # fill blank fields on the record from what was read
    record.document_number = record.document_number or extracted.get("document_number")
    record.issuing_country = record.issuing_country or extracted.get("issuing_country")
    record.issue_date = record.issue_date or parse_iso(extracted.get("issue_date"))
    record.expiry_date = record.expiry_date or parse_iso(extracted.get("expiry_date"))

    record.extracted_data = json.dumps(extracted)
    record.extraction_confidence = extracted.get("confidence")
    record.verification_checks = json.dumps({"model": settings.extraction_model,
                                             "processed_at": now_utc().isoformat(), "checks": checks})
    record.verification_status = VerificationStatus(status)
    record.verified_at = now_utc() if status == "verified" else None
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCDocument, doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "doc_id": doc_id}


# --- KYC Individual ---

@router.post("/individuals", response_model=Read_KYCIndividual)
def create_kyc_individual(data: Creation_KYCIndividual, session: Session = Depends(get_session)):
    if session.get(KYCIndividual, data.id):
        raise HTTPException(status_code=400, detail=f"KYC individual id '{data.id}' already exists")
    _check_customer(data.customer_id, session)
    record = KYCIndividual(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/individuals", response_model=List[Read_KYCIndividual])
def list_kyc_individuals(session: Session = Depends(get_session)):
    return session.exec(select(KYCIndividual)).all()

@router.get("/individuals/{kyc_id}", response_model=Read_KYCIndividual)
def get_kyc_individual(kyc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCIndividual, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC individual not found")
    return record

@router.patch("/individuals/{kyc_id}", response_model=Read_KYCIndividual)
def update_kyc_individual(kyc_id: str, data: Updation_KYCIndividual, session: Session = Depends(get_session)):
    record = session.get(KYCIndividual, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC individual not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/individuals/{kyc_id}")
def delete_kyc_individual(kyc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCIndividual, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC individual not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "kyc_id": kyc_id}


# --- KYC Company ---

@router.post("/companies", response_model=Read_KYCCompany)
def create_kyc_company(data: Creation_KYCCompany, session: Session = Depends(get_session)):
    if session.get(KYCCompany, data.id):
        raise HTTPException(status_code=400, detail=f"KYC company id '{data.id}' already exists")
    _check_customer(data.customer_id, session)
    record = KYCCompany(**data.model_dump())
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.get("/companies", response_model=List[Read_KYCCompany])
def list_kyc_companies(session: Session = Depends(get_session)):
    return session.exec(select(KYCCompany)).all()

@router.get("/companies/{kyc_id}", response_model=Read_KYCCompany)
def get_kyc_company(kyc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCCompany, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC company not found")
    return record

@router.patch("/companies/{kyc_id}", response_model=Read_KYCCompany)
def update_kyc_company(kyc_id: str, data: Updation_KYCCompany, session: Session = Depends(get_session)):
    record = session.get(KYCCompany, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC company not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record

@router.delete("/companies/{kyc_id}")
def delete_kyc_company(kyc_id: str, session: Session = Depends(get_session)):
    record = session.get(KYCCompany, kyc_id)
    if not record:
        raise HTTPException(status_code=404, detail="KYC company not found")
    session.delete(record)
    session.commit()
    return {"deleted": True, "kyc_id": kyc_id}