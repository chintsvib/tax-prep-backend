import os
from typing import Dict, Any, List
from core.tax_math import TaxMath

# Fields to walk in 1040 line-item order:
# income -> structural -> deductions -> taxes -> credits -> payments
WATERFALL_FIELDS = [
    ("wages", "W-2 wages", "income"),
    ("schedule_1_income", "self-employment / Schedule 1 income", "income"),
    ("other_income", "other income", "income"),
    ("taxable_interest", "taxable interest", "income"),
    ("ordinary_dividends", "ordinary dividends", "income"),
    ("capital_gain_or_loss", "capital gains or losses", "income"),
    ("filing_status", "filing status", "structural"),
    ("dependents_count", "number of dependents", "structural"),
    ("total_deductions", "total deductions", "deduction"),
    ("deduction_type", "deduction type", "structural"),
    ("qbi_deduction", "Qualified Business Income deduction", "deduction"),
    ("self_employment_tax", "self-employment tax", "tax"),
    ("schedule_2_total", "Schedule 2 additional taxes", "tax"),
    ("child_tax_credit", "Child Tax Credit", "credit"),
    ("schedule_3_total", "Schedule 3 credits", "credit"),
    ("w2_withholding", "W-2 withholding", "payment"),
    ("withholding_1099", "1099 withholding", "payment"),
    ("estimated_tax_payments", "estimated tax payments", "payment"),
]


class RefundExplainerAgent:
    def __init__(self, math_engine: TaxMath = None, api_key: str = None):
        self.math = math_engine or TaxMath()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    @staticmethod
    def _record_to_recon_dict(record_data: dict) -> dict:
        """Convert a TaxRecord's fields into the dict that run_reconciliation expects."""
        return {
            "filing_status": record_data.get("filing_status", "Single"),
            "wages": record_data.get("wages") or 0.0,
            "schedule_1_income": record_data.get("schedule_1_income") or 0.0,
            "w2_withholding": record_data.get("w2_withholding") or 0.0,
            "schedule_3_total": record_data.get("schedule_3_total") or 0.0,
            "total_deductions": record_data.get("total_deductions"),
            "dependents_count": record_data.get("dependents_count") or 0,
            "child_tax_credit": record_data.get("child_tax_credit") or 0.0,
            "other_income": record_data.get("other_income") or 0.0,
            "taxable_interest": record_data.get("taxable_interest") or 0.0,
            "ordinary_dividends": record_data.get("ordinary_dividends") or 0.0,
            "capital_gain_or_loss": record_data.get("capital_gain_or_loss") or 0.0,
            "self_employment_tax": record_data.get("self_employment_tax") or 0.0,
            "qbi_deduction": record_data.get("qbi_deduction") or 0.0,
            "schedule_2_total": record_data.get("schedule_2_total") or 0.0,
            "estimated_tax_payments": record_data.get("estimated_tax_payments") or 0.0,
            "withholding_1099": record_data.get("withholding_1099") or 0.0,
            "deduction_type": record_data.get("deduction_type", "Standard"),
        }

    @staticmethod
    def _build_explanation(
        label: str, prior_val, current_val, impact: float
    ) -> str:
        impact_dir = "increased" if impact > 0 else "decreased"
        impact_abs = abs(impact)

        if isinstance(prior_val, str):
            return (
                f"Your {label} changed from '{prior_val}' to '{current_val}', "
                f"which {impact_dir} your refund by ~${impact_abs:,.0f}."
            )

        delta = (current_val or 0) - (prior_val or 0)
        delta_dir = "increased" if delta > 0 else "decreased"
        delta_abs = abs(delta)

        return (
            f"Your {label} {delta_dir} by ${delta_abs:,.0f} "
            f"(from ${(prior_val or 0):,.0f} to ${(current_val or 0):,.0f}), "
            f"which {impact_dir} your refund by ~${impact_abs:,.0f}."
        )

    def explain(self, prior_record: dict, current_record: dict) -> Dict[str, Any]:
        """Pure math-based refund change explanation. No AI needed."""
        prior_data = self._record_to_recon_dict(prior_record)
        current_data = self._record_to_recon_dict(current_record)

        baseline_result = self.math.run_reconciliation(prior_data)
        baseline_balance = baseline_result["balance"]

        final_result = self.math.run_reconciliation(current_data)
        final_balance = final_result["balance"]

        total_change = round(final_balance - baseline_balance, 2)

        # Walk the waterfall: swap one field at a time
        running_data = dict(prior_data)
        running_balance = baseline_balance
        drivers: List[Dict[str, Any]] = []

        for field, label, category in WATERFALL_FIELDS:
            prior_val = prior_data.get(field)
            current_val = current_data.get(field)

            pv = prior_val if prior_val is not None else 0
            cv = current_val if current_val is not None else 0
            if pv == cv:
                continue

            running_data[field] = current_val
            new_result = self.math.run_reconciliation(running_data)
            new_balance = new_result["balance"]
            marginal_impact = round(new_balance - running_balance, 2)

            if abs(marginal_impact) < 0.01:
                running_balance = new_balance
                continue

            drivers.append({
                "field": field,
                "label": label,
                "category": category,
                "prior_value": prior_val,
                "current_value": current_val,
                "impact_on_balance": marginal_impact,
                "direction": "increased_refund" if marginal_impact > 0 else "decreased_refund",
                "explanation": self._build_explanation(label, prior_val, current_val, marginal_impact),
            })

            running_balance = new_balance

        # Capture residual interaction effects
        residual = round(final_balance - running_balance, 2)
        if abs(residual) >= 1.00:
            drivers.append({
                "field": "_interaction",
                "label": "interaction effects",
                "category": "interaction",
                "prior_value": None,
                "current_value": None,
                "impact_on_balance": residual,
                "direction": "increased_refund" if residual > 0 else "decreased_refund",
                "explanation": (
                    f"Combined interaction of multiple changes "
                    f"{'added' if residual > 0 else 'subtracted'} "
                    f"~${abs(residual):,.0f} to your refund."
                ),
            })

        # Sort by absolute impact descending
        drivers.sort(key=lambda d: abs(d["impact_on_balance"]), reverse=True)

        return {
            "prior_year": prior_record.get("tax_year"),
            "current_year": current_record.get("tax_year"),
            "prior_balance": baseline_balance,
            "prior_balance_type": baseline_result["type"],
            "current_balance": final_balance,
            "current_balance_type": final_result["type"],
            "total_change": total_change,
            "total_change_direction": "increased_refund" if total_change > 0 else "decreased_refund",
            "drivers": drivers,
            "ai_summary": None,
        }

    async def explain_with_ai_summary(
        self, prior_record: dict, current_record: dict
    ) -> Dict[str, Any]:
        """Run explanation and add an LLM-generated narrative summary."""
        result = self.explain(prior_record, current_record)

        if not self.api_key or not result["drivers"]:
            return result

        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)

            drivers_text = "\n".join(
                f"- {d['explanation']}" for d in result["drivers"][:5]
            )

            prior_label = (
                f"refund of ${result['prior_balance']:,.2f}"
                if result["prior_balance_type"] == "refund"
                else f"owed ${abs(result['prior_balance']):,.2f}"
            )
            current_label = (
                f"refund of ${result['current_balance']:,.2f}"
                if result["current_balance_type"] == "refund"
                else f"owe ${abs(result['current_balance']):,.2f}"
            )

            prompt = f"""Explain why a taxpayer's outcome changed year over year.

Last year ({result['prior_year']}): {prior_label}
This year ({result['current_year']}): {current_label}
Net change: ${result['total_change']:+,.2f}

Key drivers:
{drivers_text}

Write a 3-4 sentence plain-English summary. Be specific about the biggest factors and mention dollar amounts. Keep the tone neutral and factual. Do NOT give legal or financial advice. Do NOT say "we're here to help" or make any promises about support — this is a self-service tool. Do NOT use filler phrases."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
            )
            result["ai_summary"] = response.choices[0].message.content.strip()
        except Exception:
            result["ai_summary"] = None

        return result
