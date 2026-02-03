import openai
import pdfplumber
import io
import json
import os
from typing import Dict, Any

class ExtractionAgent:
    def __init__(self, api_key: str = None):
        # Uses provided key or looks for OPENAI_API_KEY environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key not found. Please set OPENAI_API_KEY.")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def run(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """
        Orchestrates the extraction: PDF text parsing followed by LLM structuring.
        """
        # 1. Physical Text Extraction (Focus on Page 1 & 2 of the 1040)
        raw_text = ""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                # We extract the first 3 pages to catch any Schedule 1/2/3 summaries
                for page in pdf.pages[:3]:
                    text = page.extract_text()
                    if text:
                        raw_text += text + "\n--- PAGE BREAK ---\n"
        except Exception as e:
            return {"status": "error", "reason": "pdf_parsing_failed", "message": str(e)}

        if not raw_text.strip():
            return {"status": "error", "reason": "no_text_found", "message": "PDF appears to be a scan/image."}

        # 2. AI Structuring Prompt
        # This prompt is tuned to handle the conditional visibility requirements
        prompt = f"""
        Extract the following values from this IRS Form 1040 and its summaries.
        Return ONLY a JSON object. For missing numeric values, use 0.0 unless specified otherwise.

        FIELDS TO EXTRACT:
        - filing_status: (e.g., 'Single', 'Married filing jointly')
        - dependents_count: (Count of individuals in the Dependents table on Page 1)
        - wages: (Line 1z)
        - tax_exempt_interest: (Line 2a)
        - taxable_interest: (Line 2b)
        - ordinary_dividends: (Line 3b)
        - capital_gain_or_loss: (Line 7)
        - agi: (Line 11)
        - deduction_type: (Check Line 12. If the box 'Itemized deductions (from Schedule A)' is checked, return 'Itemized'. Otherwise, return 'Standard'.)
        - total_deductions: (The dollar amount on Line 12)
        - taxable_income: (Line 15)
        - total_tax: (Line 24)
        - refund_amount: (Line 34)
        - owed_amount: (Line 37)
        
        SPECIAL CATEGORIES (Return null if value is 0.0 or not present):
        - other_income: (Line 8)
        - other_income_description: (If Line 8 > 0, describe the source from Schedule 1, e.g., 'Gambling', 'State Refund')
        - qbi_deduction: (Line 13)
        - self_employment_tax: (Line 23 or Schedule 2, Line 4)
        - schedule_2_total: (Line 17)
        - schedule_3_total: (Line 20)
        
        PAYMENTS:
        - w2_withholding: (Line 25a)
        - withholding_1099: (Line 25b)
        - estimated_tax_payments: (Line 26)

        TEXT TO PARSE:
        {raw_text}
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o", # Recommended for high-accuracy extraction
                messages=[
                    {"role": "system", "content": "You are a professional Tax Data Extraction Agent. You provide high-accuracy JSON data from tax documents."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            extracted_data = json.loads(response.choices[0].message.content)
            
            # Post-processing: Ensure 'null' logic is strictly enforced for UI conditional rendering
            for field in ["self_employment_tax", "qbi_deduction", "schedule_2_total", "schedule_3_total"]:
                if extracted_data.get(field) == 0.0:
                    extracted_data[field] = None
            
            return extracted_data

        except Exception as e:
            return {"status": "error", "reason": "llm_extraction_failed", "message": str(e)}