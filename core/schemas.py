from pydantic import BaseModel
from typing import Optional, List

class TaxYearData(BaseModel):
    filing_status: str
    wages: float = 0.0
    qbi_deduction: float = 0.0
    schedule_2_total: float = 0.0
    schedule_3_total: float = 0.0
    other_income: float = 0.0
    self_employment_tax: float = 0.0
    w2_withholding: float = 0.0
    withholding_1099: float = 0.0
    estimated_tax_payments: float = 0.0
    agi: float = 0.0
    taxable_income: float = 0.0
    total_tax: float = 0.0
    refund_amount: float = 0.0
    owed_amount: float = 0.0

class ComparisonResponse(BaseModel):
    last_year: TaxYearData
    this_year_estimate: TaxYearData
    insights: List[str]
    refund_or_owe: float

    # Inside schemas/tax_schemas.py
from pydantic import BaseModel
from typing import Optional

class ReconciliationRequest(BaseModel):
    filing_status: str = "Single"
    wages: float = 0.0
    schedule_1_income: float = 0.0
    w2_withholding: float = 0.0
    schedule_3_total: float = 0.0
    total_deductions: Optional[float] = None # For itemizers