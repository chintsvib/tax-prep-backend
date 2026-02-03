from typing import List, Dict, Any

class InsightAgent:
    def run(self, last_year: Dict[str, Any], this_year: Dict[str, Any]) -> List[Dict[str, str]]:
        insights = []

        # --- 1. None-Safe Variable Initialization ---
        # We ensure all numeric fields default to 0 to prevent TypeError: '>' not supported
        last_se_tax = last_year.get('self_employment_tax') or 0
        this_est_payments = this_year.get('estimated_tax_payments') or 0
        last_est_payments = last_year.get('estimated_tax_payments') or 0
        last_qbi = last_year.get('qbi_deduction') or 0
        last_sch2 = last_year.get('schedule_2_total') or 0
        last_sch3 = last_year.get('schedule_3_total') or 0
        
        last_w2_withholding = last_year.get('w2_withholding') or 0
        this_w2_withholding = this_year.get('w2_withholding') or 0

        # --- 2. Self-Employment & Penalty Risk Logic ---
        # Flag if the user is self-employed but underpaying estimated taxes
        if last_se_tax > 0:
            if this_est_payments < last_est_payments:
                insights.append({
                    "type": "warning", 
                    "title": "Estimated Payment Gap", 
                    "text": "You paid SE tax last year, but your quarterly estimated payments have dropped. You might face an underpayment penalty."
                })

        # --- 3. QBI (Qualified Business Income) Insight ---
        # Explains the 20% deduction benefit found on Line 13
        if last_qbi > 0:
            qbi_impact = last_qbi * 0.20 # Rough estimate of tax savings
            insights.append({
                "type": "info", 
                "title": "QBI Benefit", 
                "text": f"Last year, your Qualified Business Income deduction saved you roughly ${qbi_impact:,.0f} in taxes. Ensure your business structure remains the same to keep this."
            })

        # --- 4. Schedule 2 (Additional Taxes) Alert ---
        # Alerts user to niche taxes like AMT or SE Tax
        if last_sch2 > 500:
            insights.append({
                "type": "info", 
                "title": "Additional Taxes", 
                "text": "You had significant 'Additional Taxes' on Schedule 2 last year. These are often related to self-employment or specialized tax scenarios."
            })

        # --- 5. Schedule 3 (Credits) Context ---
        # Contextualizes the $600+ credits you saw in your extraction
        if last_sch3 > 0:
            insights.append({
                "type": "info",
                "title": "Tax Credits Detected",
                "text": f"You claimed ${last_sch3:,.0f} in Schedule 3 credits last year (e.g., Foreign Tax or Energy credits). Make sure to check for these again for 2025."
            })

        # --- 6. Withholding Trend Analysis ---
        if this_w2_withholding < (last_w2_withholding * 0.9):
            insights.append({
                "type": "warning",
                "title": "Withholding Drop",
                "text": "Your current W-2 withholding is lower than last year. This could lead to a lower refund or a tax bill if your income stayed the same."
            })

        # --- 7. Fallback Message ---
        if not insights:
            insights.append({
                "type": "success", 
                "title": "Stable Profile", 
                "text": "Your tax profile appears consistent with last year's return. No major red flags detected."
            })
            
        return insights