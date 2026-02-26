// --- Tax Data (mirrors backend TaxRecord input fields) ---

export type FilingStatus =
  | "Single"
  | "Married filing jointly"
  | "Head of household"
  | "Married filing separately";

export interface TaxData {
  tax_year: number;
  filing_status: FilingStatus;
  wages: number;
  schedule_1_income: number;
  w2_withholding: number;
  schedule_3_total: number;
  total_deductions: number | null;
  deduction_type: "Standard" | "Itemized";
  dependents_count: number;
  child_tax_credit: number;
  other_income: number;
  taxable_interest: number;
  ordinary_dividends: number;
  capital_gain_or_loss: number;
  self_employment_tax: number;
  qbi_deduction: number;
  schedule_2_total: number;
  estimated_tax_payments: number;
  withholding_1099: number;
}

export const DEFAULT_TAX_DATA: TaxData = {
  tax_year: new Date().getFullYear() - 1,
  filing_status: "Single",
  wages: 0,
  schedule_1_income: 0,
  w2_withholding: 0,
  schedule_3_total: 0,
  total_deductions: null,
  deduction_type: "Standard",
  dependents_count: 0,
  child_tax_credit: 0,
  other_income: 0,
  taxable_interest: 0,
  ordinary_dividends: 0,
  capital_gain_or_loss: 0,
  self_employment_tax: 0,
  qbi_deduction: 0,
  schedule_2_total: 0,
  estimated_tax_payments: 0,
  withholding_1099: 0,
};

// --- Refund Explainer ---

export type DriverCategory =
  | "income"
  | "deduction"
  | "tax"
  | "credit"
  | "payment"
  | "structural"
  | "interaction";

export type ChangeDirection = "increased_refund" | "decreased_refund";

export interface RefundChangeDriver {
  field: string;
  label: string;
  category: DriverCategory;
  prior_value: number | string | null;
  current_value: number | string | null;
  impact_on_balance: number;
  direction: ChangeDirection;
  explanation: string;
}

export interface RefundExplainerRequest {
  prior_data: TaxData;
  current_data: TaxData;
}

export interface RefundExplainerResponse {
  prior_year: number;
  current_year: number;
  prior_balance: number;
  prior_balance_type: "refund" | "owe";
  current_balance: number;
  current_balance_type: "refund" | "owe";
  total_change: number;
  total_change_direction: ChangeDirection;
  drivers: RefundChangeDriver[];
  ai_summary: string | null;
}

// --- Life Events ---

export interface LifeEventPreset {
  key: string;
  name: string;
  description: string;
  fields_affected: string[];
}

export interface LifeEventApplyRequest {
  event_key: string;
  base_data: Record<string, unknown>;
  custom_values?: Record<string, unknown>;
}

export interface LifeEventApplyResponse {
  event: string;
  before: Record<string, number | string>;
  after: Record<string, number | string>;
  diff: Record<string, number>;
}

// --- Auth ---

export interface AuthRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: number;
  email: string;
}
