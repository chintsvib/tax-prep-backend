from typing import Dict, Any

# 2025 TAX PARAMETERS (IRS Rev. Proc. 2024-40)
STANDARD_DEDUCTION = {
    "Single": 15750.0,
    "Married filing jointly": 31500.0,
    "Head of household": 23625.0,
    "Married filing separately": 15750.0,
}

# 2025 Tax Brackets (Marginal Rates)
TAX_BRACKETS = {
    "Single": [
        (11925, 0.10), (48475, 0.12), (103350, 0.22),
        (197300, 0.24), (250525, 0.32), (626350, 0.35), (float('inf'), 0.37)
    ],
    "Married filing jointly": [
        (23850, 0.10), (96950, 0.12), (206700, 0.22),
        (394600, 0.24), (501050, 0.32), (751600, 0.35), (float('inf'), 0.37)
    ],
    "Head of household": [
        (17000, 0.10), (64850, 0.12), (103350, 0.22),
        (197300, 0.24), (250500, 0.32), (626350, 0.35), (float('inf'), 0.37)
    ],
    "Married filing separately": [
        (11925, 0.10), (48475, 0.12), (103350, 0.22),
        (197300, 0.24), (250525, 0.32), (375800, 0.35), (float('inf'), 0.37)
    ],
}

# 2025 Self-Employment Tax Parameters
SS_WAGE_BASE_2025 = 176100.0
SS_RATE = 0.124        # 12.4% Social Security
MEDICARE_RATE = 0.029  # 2.9% Medicare
SE_RATE = SS_RATE + MEDICARE_RATE  # 15.3%

# Additional Medicare Tax (0.9%) thresholds by filing status
ADDITIONAL_MEDICARE_THRESHOLD = {
    "Single": 200000.0,
    "Head of household": 200000.0,
    "Married filing jointly": 250000.0,
    "Married filing separately": 125000.0,
}

# 2025 Child Tax Credit Parameters
CTC_PER_CHILD = 2200.0
CTC_REFUNDABLE_MAX = 1700.0
CTC_EARNED_INCOME_FLOOR = 2500.0
CTC_REFUNDABLE_RATE = 0.15  # 15% of earned income above floor
CTC_PHASEOUT_THRESHOLD = {
    "Single": 200000.0,
    "Head of household": 200000.0,
    "Married filing jointly": 400000.0,
    "Married filing separately": 200000.0,
}
CTC_PHASEOUT_RATE = 50.0  # $50 reduction per $1,000 over threshold

class TaxMath:
    @staticmethod
    def calculate_se_tax(net_business_income: float) -> Dict[str, float]:
        """Calculates Self-Employment Tax (Schedule 2) and the Deductible portion.
        Properly caps SS at the 2025 wage base ($176,100) and applies
        uncapped Medicare (2.9%) on all SE earnings."""
        taxable_se_income = net_business_income * 0.9235

        # Social Security: 12.4% up to wage base
        ss_taxable = min(taxable_se_income, SS_WAGE_BASE_2025)
        ss_tax = ss_taxable * SS_RATE

        # Medicare: 2.9% on all SE income (no cap)
        medicare_tax = taxable_se_income * MEDICARE_RATE

        total_se_tax = ss_tax + medicare_tax

        return {
            "total_se_tax": round(total_se_tax, 2),
            "deductible_portion": round(total_se_tax * 0.5, 2),
        }

    @staticmethod
    def calculate_additional_medicare_tax(
        wages: float, se_income: float, filing_status: str
    ) -> float:
        """0.9% Additional Medicare Tax on combined earnings above threshold."""
        threshold = ADDITIONAL_MEDICARE_THRESHOLD.get(filing_status, 200000.0)
        combined = wages + (se_income * 0.9235 if se_income > 0 else 0.0)
        excess = max(0, combined - threshold)
        return round(excess * 0.009, 2)

    @staticmethod
    def calculate_income_tax(taxable_income: float, filing_status: str) -> float:
        """Calculates progressive federal income tax based on 2025 brackets."""
        brackets = TAX_BRACKETS.get(filing_status, TAX_BRACKETS["Single"])
        tax = 0.0
        previous_limit = 0.0

        for limit, rate in brackets:
            if taxable_income > previous_limit:
                taxable_in_bracket = min(taxable_income, limit) - previous_limit
                tax += taxable_in_bracket * rate
                previous_limit = limit
            else:
                break
        return round(tax, 2)

    @staticmethod
    def calculate_child_tax_credit(
        num_children: int, agi: float, earned_income: float,
        filing_status: str, tax_liability: float,
    ) -> Dict[str, float]:
        """Calculates the 2025 Child Tax Credit with phase-out.
        Returns non-refundable and refundable (ACTC) portions."""
        if num_children <= 0:
            return {"ctc_nonrefundable": 0.0, "ctc_refundable": 0.0, "ctc_total": 0.0}

        # Max credit before phase-out
        max_ctc = CTC_PER_CHILD * num_children

        # Phase-out: reduce by $50 per $1,000 (or fraction) over threshold
        threshold = CTC_PHASEOUT_THRESHOLD.get(filing_status, 200000.0)
        excess_agi = max(0, agi - threshold)
        # Round up to nearest $1,000
        phaseout_units = -(-int(excess_agi) // 1000) if excess_agi > 0 else 0
        phaseout_amount = phaseout_units * CTC_PHASEOUT_RATE
        ctc_after_phaseout = max(0, max_ctc - phaseout_amount)

        # Non-refundable portion: limited to tax liability
        ctc_nonrefundable = min(ctc_after_phaseout, tax_liability)

        # Refundable portion (ACTC): 15% of earned income above $2,500,
        # capped at $1,700 per child and the remaining credit
        remaining = ctc_after_phaseout - ctc_nonrefundable
        if remaining > 0 and earned_income > CTC_EARNED_INCOME_FLOOR:
            actc_earned = (earned_income - CTC_EARNED_INCOME_FLOOR) * CTC_REFUNDABLE_RATE
            actc_cap = CTC_REFUNDABLE_MAX * num_children
            ctc_refundable = min(remaining, actc_earned, actc_cap)
        else:
            ctc_refundable = 0.0

        return {
            "ctc_nonrefundable": round(ctc_nonrefundable, 2),
            "ctc_refundable": round(ctc_refundable, 2),
            "ctc_total": round(ctc_nonrefundable + ctc_refundable, 2),
        }

    def run_reconciliation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """The main engine to calculate 2025 AGI, Total Tax, and Refund/Owe."""
        # 1. Gather Inputs (None-safe)
        status = data.get("filing_status", "Single")
        wages = data.get("wages") or 0.0
        sch1_income = data.get("schedule_1_income") or 0.0
        withholding = data.get("w2_withholding") or 0.0
        sch3_credits = data.get("schedule_3_total") or 0.0
        dependents = data.get("dependents_count") or 0
        child_tax_credit_override = data.get("child_tax_credit")

        # 2. Above-the-line Adjustments (SE Tax)
        se_results = self.calculate_se_tax(sch1_income) if sch1_income > 0 else {"total_se_tax": 0, "deductible_portion": 0}

        # 3. Calculate AGI
        gross_income = wages + sch1_income
        agi = gross_income - se_results["deductible_portion"]

        # 4. Taxable Income
        deduction = max(data.get("total_deductions") or 0.0, STANDARD_DEDUCTION.get(status, 15750.0))
        taxable_income = max(0, agi - deduction)

        # 5. Tax Liability
        income_tax = self.calculate_income_tax(taxable_income, status)
        additional_medicare = self.calculate_additional_medicare_tax(wages, sch1_income, status)
        total_tax_liability = income_tax + se_results["total_se_tax"] + additional_medicare

        # 6. Child Tax Credit
        if child_tax_credit_override is not None and child_tax_credit_override > 0:
            # Use the value provided (e.g. from PDF extraction of prior-year return)
            ctc = {"ctc_nonrefundable": min(child_tax_credit_override, total_tax_liability),
                   "ctc_refundable": 0.0,
                   "ctc_total": min(child_tax_credit_override, total_tax_liability)}
        else:
            earned_income = wages + max(0, sch1_income)
            ctc = self.calculate_child_tax_credit(
                dependents, agi, earned_income, status, total_tax_liability
            )

        # 7. Final Result (Refund or Owe)
        # Non-refundable credits reduce tax liability; refundable credits add to payments
        tax_after_credits = max(0, total_tax_liability - ctc["ctc_nonrefundable"])
        total_payments = withholding + sch3_credits + ctc["ctc_refundable"]
        final_balance = total_payments - tax_after_credits

        return {
            "agi_2025": round(agi, 2),
            "taxable_income_2025": round(taxable_income, 2),
            "total_tax_2025": round(tax_after_credits, 2),
            "child_tax_credit": round(ctc["ctc_total"], 2),
            "balance": round(final_balance, 2),
            "type": "refund" if final_balance >= 0 else "owe",
        }