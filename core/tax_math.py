from typing import Dict, Any

# 2025 TAX PARAMETERS
STANDARD_DEDUCTION = {
    "Single": 15000.0,
    "Married filing jointly": 30000.0,
    "Head of household": 22500.0,
    "Married filing separately": 15000.0
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
    ]
}

class TaxMath:
    @staticmethod
    def calculate_se_tax(net_business_income: float) -> Dict[str, float]:
        """Calculates Self-Employment Tax (Schedule 2) and the Deductible portion."""
        # SE Tax is calculated on 92.35% of net profit
        taxable_se_income = net_business_income * 0.9235
        
        # 15.3% rate up to Social Security Wage Base ($176,100 for 2025)
        # For MVP simplicity, we apply a flat 15.3% (SS + Medicare)
        total_se_tax = taxable_se_income * 0.153
        
        return {
            "total_se_tax": round(total_se_tax, 2),
            "deductible_portion": round(total_se_tax * 0.5, 2)
        }

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

    def run_reconciliation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """The main engine to calculate 2025 AGI, Total Tax, and Refund/Owe."""
        # 1. Gather Inputs (None-safe)
        status = data.get("filing_status", "Single")
        wages = data.get("wages") or 0.0
        sch1_income = data.get("schedule_1_income") or 0.0
        withholding = data.get("w2_withholding") or 0.0
        sch3_credits = data.get("schedule_3_total") or 0.0
        
        # 2. Above-the-line Adjustments (SE Tax)
        se_results = self.calculate_se_tax(sch1_income) if sch1_income > 0 else {"total_se_tax": 0, "deductible_portion": 0}
        
        # 3. Calculate AGI
        # AGI = Total Income - Adjustments (1/2 SE Tax)
        gross_income = wages + sch1_income
        agi = gross_income - se_results["deductible_portion"]
        
        # 4. Taxable Income
        # We compare standard vs user's itemized from last year
        deduction = max(data.get("total_deductions") or 0.0, STANDARD_DEDUCTION.get(status, 15000.0))
        taxable_income = max(0, agi - deduction)
        
        # 5. Total Tax Liability
        income_tax = self.calculate_income_tax(taxable_income, status)
        total_tax_liability = income_tax + se_results["total_se_tax"]
        
        # 6. Final Result (Refund or Owe)
        # Result = Payments - Liability
        final_balance = (withholding + sch3_credits) - total_tax_liability
        
        return {
            "agi_2025": round(agi, 2),
            "taxable_income_2025": round(taxable_income, 2),
            "total_tax_2025": round(total_tax_liability, 2),
            "balance": round(final_balance, 2),
            "type": "refund" if final_balance >= 0 else "owe"
        }