class InsightAgent:
    def run(self, last_year: dict, this_year: dict):
        insights = []

        # 1. Self-Employment (SE) Tax Surprise
        # If SE tax existed last year, check if estimated payments are keeping up
        if last_year.get('self_employment_tax', 0) > 0:
            if this_year.get('estimated_tax_payments', 0) < last_year.get('estimated_tax_payments', 0):
                insights.append({
                    "type": "warning",
                    "title": "Estimated Payment Gap",
                    "text": "You paid SE tax last year, but your quarterly estimated payments have dropped. You might face an underpayment penalty."
                })

        # 2. The QBI "Invisible" Deduction
        # If QBI was high last year, explain its impact
        if last_year.get('qbi_deduction', 0) > 0:
            qbi_impact = last_year['qbi_deduction'] * 0.20 # Rough tax savings
            insights.append({
                "type": "info",
                "title": "QBI Benefit",
                "text": f"Last year, your Qualified Business Income deduction saved you roughly ${qbi_impact:,.0f} in taxes. Ensure your business structure remains the same to keep this."
            })

        # 3. Withholding Mix (W-2 vs 1099)
        # 1099s rarely have withholding, so this is a key "Ask" for the user
        if last_year.get('withholding_1099', 0) > 0 and this_year.get('withholding_1099', 0) == 0:
             insights.append({
                "type": "action",
                "title": "1099 Withholding Check",
                "text": "You had tax withheld from 1099s last year. If your clients aren't withholding this year, you need to increase your quarterly payments."
            })

        # 4. Schedule 2/3 Complexity
        if last_year.get('schedule_2_total', 0) > 500:
            insights.append({
                "type": "info",
                "title": "Additional Taxes",
                "text": "You have significant 'Additional Taxes' (Schedule 2). This often includes SE tax or Alternative Minimum Tax."
            })

        if not insights:
            insights.append({
                "type": "success",
                "title": "Stable Profile",
                "text": "Your tax profile appears consistent with last year's simple return."
            })
            
        return insights