import os
from fastapi import FastAPI, UploadFile, File
from agents.extraction_agent import ExtractionAgent
from agents.insight_agent import InsightAgent
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
from core.schemas import TaxYearData
from agents.drafting_agent import DraftingAgent
from core.tax_math import TaxMath

app = FastAPI()

math_engine = TaxMath()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development; narrow this down for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents (API Key from Environment Variable)
API_KEY = os.getenv("OPENAI_API_KEY")
extractor = ExtractionAgent(api_key=API_KEY)
insighter = InsightAgent()

class AnalysisPayload(BaseModel):
    last_year: dict
    this_year: dict

@app.post("/extract")
async def extract_tax_data(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    data = await extractor.run(pdf_bytes)
    return {"status": "success", "data": data}

from core.tax_math import calculate_2025_estimate

@app.post("/analyze")
async def analyze_and_calculate(payload: AnalysisPayload):
    # 1. Run the Math Agent first
    math_results = calculate_2025_estimate(payload.this_year)
    
    # 2. Run the Insight Agent
    insights = insighter.run(payload.last_year, payload.this_year)
    
    # 3. Add a dynamic 'Math-based' insight
    if math_results['refund_or_owe'] < 0:
        math_results['status'] = "OWE"
        insights.append({
            "type": "warning",
            "title": "Payment Shortfall",
            "text": f"Based on your changes, you may owe ${abs(math_results['refund_or_owe']):,.2f}. Consider adjusting your withholding now."
        })
    else:
        math_results['status'] = "REFUND"
    
    return {
        "status": "success",
        "calculation": math_results,
        "insights": insights
    }

@app.post("/generate-draft")
async def generate_draft(data: TaxYearData):
    drafter = DraftingAgent("data/f1040_template.pdf")
    output_filename = "tax_draft_2025.pdf"
    
    drafter.generate(data.dict(), output_filename)
    
    return FileResponse(
        output_filename, 
        media_type="application/pdf", 
        filename="Your_Tax_Assistant_Draft.pdf"
    )


@app.post("/api/v1/reconcile")
async def reconcile_taxes(request: ReconciliationRequest):
    try:
        # 1. Convert Pydantic model to dictionary
        input_data = request.model_dump()
        
        # 2. Run the math logic
        results = math_engine.run_reconciliation(input_data)
        
        # 3. Return the payload to Lovable
        return {
            "status": "success",
            "calculation": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))