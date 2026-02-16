from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaxRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    tax_year: int
    filing_status: str = "Single"
    dependents_count: int = 0
    wages: float = 0.0
    schedule_1_income: float = 0.0
    w2_withholding: float = 0.0
    schedule_3_total: float = 0.0
    total_deductions: Optional[float] = None
    deduction_type: str = "Standard"
    self_employment_tax: float = 0.0
    qbi_deduction: float = 0.0
    schedule_2_total: float = 0.0
    estimated_tax_payments: float = 0.0
    other_income: float = 0.0
    child_tax_credit: float = 0.0
    taxable_interest: float = 0.0
    ordinary_dividends: float = 0.0
    capital_gain_or_loss: float = 0.0
    withholding_1099: float = 0.0
    agi: float = 0.0
    taxable_income: float = 0.0
    total_tax: float = 0.0
    refund_amount: float = 0.0
    owed_amount: float = 0.0
    source: str = "manual"  # "manual" or "pdf_upload"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Scenario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str
    description: Optional[str] = None
    base_record_id: Optional[int] = Field(default=None, foreign_key="taxrecord.id")
    # Tax data fields (snapshot of inputs)
    filing_status: str = "Single"
    wages: float = 0.0
    schedule_1_income: float = 0.0
    w2_withholding: float = 0.0
    schedule_3_total: float = 0.0
    total_deductions: Optional[float] = None
    # Calculated results
    agi: Optional[float] = None
    taxable_income: Optional[float] = None
    total_tax: Optional[float] = None
    balance: Optional[float] = None
    balance_type: Optional[str] = None  # "refund" or "owe"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
