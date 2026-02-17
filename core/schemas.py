from pydantic import BaseModel, field_validator
from typing import Optional, List


# --- Existing schemas (preserved) ---

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


class ReconciliationRequest(BaseModel):
    filing_status: str = "Single"
    wages: float = 0.0
    schedule_1_income: float = 0.0
    w2_withholding: float = 0.0
    schedule_3_total: float = 0.0
    total_deductions: Optional[float] = None


# --- Auth schemas ---

class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str


# --- Tax record schemas ---

class TaxRecordCreate(BaseModel):
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

    @field_validator(
        "wages", "schedule_1_income", "w2_withholding", "schedule_3_total",
        "self_employment_tax", "qbi_deduction", "schedule_2_total",
        "estimated_tax_payments", "other_income", "child_tax_credit",
        "taxable_interest", "ordinary_dividends", "capital_gain_or_loss",
        "withholding_1099", "dependents_count",
        mode="before",
    )
    @classmethod
    def coerce_none_to_zero(cls, v):
        """Frontend may pass null for numeric fields extracted as None by AI."""
        return v if v is not None else 0


class TaxRecordUpdate(TaxRecordCreate):
    """For PUT — all fields optional. Only provided fields get updated."""
    tax_year: Optional[int] = None


class TaxRecordResponse(BaseModel):
    id: int
    tax_year: int
    filing_status: str
    dependents_count: int
    wages: float
    schedule_1_income: float
    w2_withholding: float
    schedule_3_total: float
    total_deductions: Optional[float]
    deduction_type: str
    self_employment_tax: float
    qbi_deduction: float
    schedule_2_total: float
    estimated_tax_payments: float
    other_income: float
    child_tax_credit: float
    taxable_interest: float
    ordinary_dividends: float
    capital_gain_or_loss: float
    withholding_1099: float
    agi: float
    taxable_income: float
    total_tax: float
    refund_amount: float
    owed_amount: float
    source: str


# --- Scenario schemas ---

class ScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_record_id: Optional[int] = None
    filing_status: str = "Single"
    wages: float = 0.0
    schedule_1_income: float = 0.0
    w2_withholding: float = 0.0
    schedule_3_total: float = 0.0
    total_deductions: Optional[float] = None


class ScenarioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    filing_status: str
    wages: float
    schedule_1_income: float
    w2_withholding: float
    schedule_3_total: float
    total_deductions: Optional[float]
    agi: Optional[float]
    taxable_income: Optional[float]
    total_tax: Optional[float]
    balance: Optional[float]
    balance_type: Optional[str]


class ScenarioCompareResponse(BaseModel):
    scenario_a: ScenarioResponse
    scenario_b: ScenarioResponse
    diff: dict


class WhatIfRequest(BaseModel):
    base_scenario_id: Optional[int] = None
    overrides: dict


class WhatIfResponse(BaseModel):
    baseline: dict
    modified: dict
    diff: dict


# --- Life event schemas ---

class LifeEventPreset(BaseModel):
    key: str
    name: str
    description: str
    fields_affected: List[str]


class LifeEventApplyRequest(BaseModel):
    event_key: str
    base_scenario_id: Optional[int] = None
    base_data: Optional[dict] = None
    custom_values: Optional[dict] = None


class LifeEventApplyResponse(BaseModel):
    event: str
    before: dict
    after: dict
    diff: dict


# --- Optimization schemas ---

class OptimizationRequest(BaseModel):
    filing_status: str = "Single"
    wages: float = 0.0
    schedule_1_income: float = 0.0
    w2_withholding: float = 0.0
    schedule_3_total: float = 0.0
    total_deductions: Optional[float] = None


class Recommendation(BaseModel):
    strategy: str
    description: str
    tax_savings: float
    annual_cost: float
    priority: str  # "high", "medium", "low"


class OptimizationResponse(BaseModel):
    current_tax: float
    current_balance: float
    current_type: str
    recommendations: List[Recommendation]
    total_potential_savings: float
    ai_summary: Optional[str] = None
