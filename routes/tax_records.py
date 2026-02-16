import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from core.database import get_session
from core.models import User, TaxRecord
from core.auth import get_current_user
from core.schemas import TaxRecordCreate, TaxRecordResponse

router = APIRouter(prefix="/tax-records", tags=["tax-records"])


@router.post("/upload", response_model=dict)
async def upload_tax_return(
    file: UploadFile = File(...),
    tax_year: int = 2024,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Upload a 1040 PDF, extract data via AI, and save as a tax record."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    from agents.extraction_agent import ExtractionAgent
    extractor = ExtractionAgent(api_key=api_key)

    pdf_bytes = await file.read()
    extracted = await extractor.run(pdf_bytes)

    if extracted.get("status") == "error":
        raise HTTPException(status_code=422, detail=extracted.get("message", "Extraction failed"))

    # Save to TaxRecord
    record = TaxRecord(
        user_id=user.id,
        tax_year=tax_year,
        filing_status=extracted.get("filing_status", "Single"),
        dependents_count=extracted.get("dependents_count") or 0,
        wages=extracted.get("wages") or 0,
        schedule_1_income=extracted.get("other_income") or 0,
        w2_withholding=extracted.get("w2_withholding") or 0,
        schedule_3_total=extracted.get("schedule_3_total") or 0,
        total_deductions=extracted.get("total_deductions") or 0,
        deduction_type=extracted.get("deduction_type", "Standard"),
        self_employment_tax=extracted.get("self_employment_tax") or 0,
        qbi_deduction=extracted.get("qbi_deduction") or 0,
        schedule_2_total=extracted.get("schedule_2_total") or 0,
        estimated_tax_payments=extracted.get("estimated_tax_payments") or 0,
        other_income=extracted.get("other_income") or 0,
        child_tax_credit=extracted.get("child_tax_credit") or 0,
        taxable_interest=extracted.get("taxable_interest") or 0,
        ordinary_dividends=extracted.get("ordinary_dividends") or 0,
        capital_gain_or_loss=extracted.get("capital_gain_or_loss") or 0,
        withholding_1099=extracted.get("withholding_1099") or 0,
        agi=extracted.get("agi") or 0,
        taxable_income=extracted.get("taxable_income") or 0,
        total_tax=extracted.get("total_tax") or 0,
        refund_amount=extracted.get("refund_amount") or 0,
        owed_amount=extracted.get("owed_amount") or 0,
        source="pdf_upload",
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    return {
        "status": "success",
        "record_id": record.id,
        "tax_year": record.tax_year,
        "extracted_data": extracted,
        "message": "Tax return uploaded and extracted successfully. Review the data below.",
    }


@router.post("", response_model=TaxRecordResponse)
def create_tax_record(
    req: TaxRecordCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Manually create or update a tax record (e.g., after user reviews extracted data)."""
    record = TaxRecord(
        user_id=user.id,
        tax_year=req.tax_year,
        filing_status=req.filing_status,
        dependents_count=req.dependents_count,
        wages=req.wages,
        schedule_1_income=req.schedule_1_income,
        w2_withholding=req.w2_withholding,
        schedule_3_total=req.schedule_3_total,
        total_deductions=req.total_deductions,
        deduction_type=req.deduction_type,
        self_employment_tax=req.self_employment_tax,
        qbi_deduction=req.qbi_deduction,
        schedule_2_total=req.schedule_2_total,
        estimated_tax_payments=req.estimated_tax_payments,
        other_income=req.other_income,
        child_tax_credit=req.child_tax_credit,
        taxable_interest=req.taxable_interest,
        ordinary_dividends=req.ordinary_dividends,
        capital_gain_or_loss=req.capital_gain_or_loss,
        withholding_1099=req.withholding_1099,
        source="manual",
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@router.get("", response_model=list[TaxRecordResponse])
def list_tax_records(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List all tax records for the current user."""
    records = session.exec(
        select(TaxRecord).where(TaxRecord.user_id == user.id).order_by(TaxRecord.tax_year.desc())
    ).all()
    return records


@router.get("/{record_id}", response_model=TaxRecordResponse)
def get_tax_record(
    record_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    record = session.get(TaxRecord, record_id)
    if not record or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Tax record not found")
    return record


@router.put("/{record_id}", response_model=TaxRecordResponse)
def update_tax_record(
    record_id: int,
    req: TaxRecordCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update a tax record (e.g., user corrects extracted data)."""
    record = session.get(TaxRecord, record_id)
    if not record or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Tax record not found")

    record.tax_year = req.tax_year
    record.filing_status = req.filing_status
    record.dependents_count = req.dependents_count
    record.wages = req.wages
    record.schedule_1_income = req.schedule_1_income
    record.w2_withholding = req.w2_withholding
    record.schedule_3_total = req.schedule_3_total
    record.total_deductions = req.total_deductions
    record.deduction_type = req.deduction_type
    record.self_employment_tax = req.self_employment_tax
    record.qbi_deduction = req.qbi_deduction
    record.schedule_2_total = req.schedule_2_total
    record.estimated_tax_payments = req.estimated_tax_payments
    record.other_income = req.other_income
    record.child_tax_credit = req.child_tax_credit
    record.taxable_interest = req.taxable_interest
    record.ordinary_dividends = req.ordinary_dividends
    record.capital_gain_or_loss = req.capital_gain_or_loss
    record.withholding_1099 = req.withholding_1099

    session.add(record)
    session.commit()
    session.refresh(record)
    return record
