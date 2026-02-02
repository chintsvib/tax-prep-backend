def calculate_2025_estimate(data: dict):
    """
    Simplified 2025 Federal Tax Calculator
    """
    filing_status = data.get("filing_status", "Single")
    taxable_income = data.get("taxable_income", 0.0)
    withholding = data.get("w2_withholding", 0.0) + data.get("withholding_1099", 0.0)
    est_payments = data.get("estimated_tax_payments", 0.0)
    total_paid = withholding + est_payments

    # 2025 Simplified Brackets (Married Filing Jointly vs Single)
    if filing_status == "Married filing jointly":
        # Simplified effective tax rate logic for MVP
        if taxable_income <= 23650: tax = taxable_income * 0.10
        elif taxable_income <= 96050: tax = 2365 + (taxable_income - 23650) * 0.12
        else: tax = 11053 + (taxable_income - 96050) * 0.22
    else:
        if taxable_income <= 11925: tax = taxable_income * 0.10
        elif taxable_income <= 48475: tax = 1192 + (taxable_income - 11925) * 0.12
        else: tax = 5578 + (taxable_income - 48475) * 0.22

    # Add Self-Employment Tax (Approx 15.3% on 92.35% of SE income)
    se_tax = data.get("self_employment_tax", 0.0)
    total_tax_liability = tax + se_tax
    
    # Final Result
    diff = total_paid - total_tax_liability
    
    return {
        "estimated_total_tax": round(total_tax_liability, 2),
        "total_payments": round(total_paid, 2),
        "refund_or_owe": round(diff, 2)
    }