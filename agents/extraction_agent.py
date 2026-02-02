import openai
import pdfplumber
import io
import json

class ExtractionAgent:
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)

    async def run(self, pdf_bytes: bytes):
        # 1. Physical Extraction
        raw_text = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages[:2]:  # Focus on first 2 pages of 1040
                raw_text += (page.extract_text() or "") + "\n"

        # 2. AI Structuring
        prompt = f"""
        Extract the following values from this IRS Form 1040 text. 
        Return ONLY a JSON object. If a value is missing, use 0.0.
        
        FIELDS TO EXTRACT:
            - filing_status
            - wages (Line 1z)
            - qbi_deduction (Line 13 - Qualified Business Income)
            - schedule_2_total (Line 17 - Total Additional Taxes)
            - schedule_3_total (Line 20 - Total Nonrefundable Credits)
            - other_income (Line 8 - Other income from Schedule 1)
            - self_employment_tax (Schedule 2, Line 4 or 1040 Line 23 - Other Taxes)
            - w2_withholding (Line 25a)
            - 1099_withholding (Line 25b)
            - estimated_tax_payments (Line 26 - Includes 2024 payments and 2023 carryover)
            - agi (Line 11)
            - taxable_income (Line 15)
            - total_tax (Line 24)
            - refund_amount (Line 34)
            - owed_amount (Line 37)

        TEXT:
        {raw_text}
        """

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a tax data parser."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)