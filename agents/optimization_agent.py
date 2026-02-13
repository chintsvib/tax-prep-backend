import os
import json
from typing import List, Dict, Any, Optional
from core.tax_math import TaxMath

# 2025 contribution limits
MAX_401K = 23500
MAX_IRA = 7000
MAX_HSA_INDIVIDUAL = 4300
MAX_HSA_FAMILY = 8550


class OptimizationAgent:
    def __init__(self, math_engine: TaxMath = None, api_key: str = None):
        self.math = math_engine or TaxMath()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def analyze(self, tax_data: dict) -> Dict[str, Any]:
        baseline = self.math.run_reconciliation(tax_data)
        recommendations = []

        wages = tax_data.get("wages") or 0
        sch1 = tax_data.get("schedule_1_income") or 0
        status = tax_data.get("filing_status", "Single")

        # --- Strategy 1: Max 401(k) ---
        if wages > MAX_401K:
            modified = {**tax_data, "wages": wages - MAX_401K}
            result = self.math.run_reconciliation(modified)
            savings = baseline["total_tax_2025"] - result["total_tax_2025"]
            if savings > 0:
                recommendations.append({
                    "strategy": "Max Out 401(k)",
                    "description": f"Contribute the full ${MAX_401K:,} to your employer 401(k). This reduces your taxable wages dollar-for-dollar and grows tax-deferred.",
                    "tax_savings": round(savings, 2),
                    "annual_cost": MAX_401K,
                    "priority": "high",
                })

        # --- Strategy 2: Traditional IRA ---
        if wages > 0:
            modified = {**tax_data, "wages": wages - MAX_IRA}
            result = self.math.run_reconciliation(modified)
            savings = baseline["total_tax_2025"] - result["total_tax_2025"]
            if savings > 0:
                recommendations.append({
                    "strategy": "Traditional IRA Contribution",
                    "description": f"Contribute up to ${MAX_IRA:,} to a Traditional IRA for an above-the-line deduction. Check income limits for deductibility if you have an employer plan.",
                    "tax_savings": round(savings, 2),
                    "annual_cost": MAX_IRA,
                    "priority": "high",
                })

        # --- Strategy 3: HSA Contribution ---
        if wages > 0:
            hsa_limit = MAX_HSA_INDIVIDUAL
            modified = {**tax_data, "wages": wages - hsa_limit}
            result = self.math.run_reconciliation(modified)
            savings = baseline["total_tax_2025"] - result["total_tax_2025"]
            if savings > 0:
                recommendations.append({
                    "strategy": "HSA Contribution",
                    "description": f"If you have an HDHP, contribute up to ${hsa_limit:,} to an HSA. Triple tax advantage: deductible, grows tax-free, and withdrawals for medical expenses are tax-free.",
                    "tax_savings": round(savings, 2),
                    "annual_cost": hsa_limit,
                    "priority": "high",
                })

        # --- Strategy 4: Filing Status Optimization ---
        if status == "Single":
            for alt_status in ["Head of household"]:
                modified = {**tax_data, "filing_status": alt_status}
                result = self.math.run_reconciliation(modified)
                savings = baseline["total_tax_2025"] - result["total_tax_2025"]
                if savings > 0:
                    recommendations.append({
                        "strategy": f"File as {alt_status}",
                        "description": f"If you qualify (unmarried with a dependent), filing as {alt_status} gives you a higher standard deduction and wider tax brackets.",
                        "tax_savings": round(savings, 2),
                        "annual_cost": 0,
                        "priority": "high",
                    })

        # --- Strategy 5: Increase Withholding (if owing) ---
        if baseline["type"] == "owe":
            owed = abs(baseline["balance"])
            monthly_increase = round(owed / 12, 2)
            recommendations.append({
                "strategy": "Increase W-4 Withholding",
                "description": f"You're projected to owe ${owed:,.2f}. Increase your W-4 withholding by ~${monthly_increase:,.2f}/month to avoid a lump-sum payment and potential underpayment penalty.",
                "tax_savings": 0,
                "annual_cost": 0,
                "priority": "high" if owed > 1000 else "medium",
            })

        # --- Strategy 6: SEP-IRA for Self-Employed ---
        if sch1 > 0:
            sep_limit = min(sch1 * 0.25, 69000)  # 2025 SEP limit
            modified = {**tax_data, "schedule_1_income": sch1 - sep_limit}
            result = self.math.run_reconciliation(modified)
            savings = baseline["total_tax_2025"] - result["total_tax_2025"]
            if savings > 0:
                recommendations.append({
                    "strategy": "SEP-IRA Contribution",
                    "description": f"As self-employed, you can contribute up to ${sep_limit:,.0f} (25% of net income, max $69,000) to a SEP-IRA. This directly reduces your SE income.",
                    "tax_savings": round(savings, 2),
                    "annual_cost": round(sep_limit, 2),
                    "priority": "high",
                })

        # --- Strategy 7: Charitable Giving Bunching ---
        current_ded = tax_data.get("total_deductions") or 0
        from core.tax_math import STANDARD_DEDUCTION
        std_ded = STANDARD_DEDUCTION.get(status, 15000)
        if current_ded <= std_ded:
            # User is taking standard deduction. Bunching could help in alternating years
            bunch_amount = std_ded + 5000  # Bunch enough to exceed standard deduction
            modified = {**tax_data, "total_deductions": bunch_amount}
            result = self.math.run_reconciliation(modified)
            savings = baseline["total_tax_2025"] - result["total_tax_2025"]
            if savings > 0:
                recommendations.append({
                    "strategy": "Charitable Giving Bunching",
                    "description": f"You're using the standard deduction (${std_ded:,.0f}). Consider bunching 2 years of charitable donations into one year to exceed it and itemize, saving ${savings:,.2f} in that year.",
                    "tax_savings": round(savings, 2),
                    "annual_cost": round(bunch_amount - std_ded, 2),
                    "priority": "low",
                })

        # Sort by savings descending
        recommendations.sort(key=lambda x: x["tax_savings"], reverse=True)

        total_savings = sum(r["tax_savings"] for r in recommendations)

        return {
            "current_tax": baseline["total_tax_2025"],
            "current_balance": baseline["balance"],
            "current_type": baseline["type"],
            "recommendations": recommendations,
            "total_potential_savings": round(total_savings, 2),
        }

    async def analyze_with_ai_summary(self, tax_data: dict) -> Dict[str, Any]:
        """Run analysis and add an LLM-generated personalized summary."""
        result = self.analyze(tax_data)

        if not self.api_key or not result["recommendations"]:
            return result

        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self.api_key)

            recs_text = "\n".join(
                f"- {r['strategy']}: saves ${r['tax_savings']:,.2f} (costs ${r['annual_cost']:,.2f}/yr)"
                for r in result["recommendations"]
            )

            prompt = f"""You are a friendly tax advisor. The user's current tax situation:
- Filing status: {tax_data.get('filing_status', 'Single')}
- Total tax: ${result['current_tax']:,.2f}
- {'Refund' if result['current_type'] == 'refund' else 'Owes'}: ${abs(result['current_balance']):,.2f}

Here are the optimization strategies we identified:
{recs_text}

Write a 3-4 sentence personalized summary. Be encouraging and specific about the top 2-3 actions. Mention dollar amounts. Do NOT give legal advice or say "consult a tax professional"."""

            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            result["ai_summary"] = response.choices[0].message.content.strip()
        except Exception:
            result["ai_summary"] = None

        return result
