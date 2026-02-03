import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Internal Imports
from agents.extraction_agent import ExtractionAgent
from agents.insight_agent import InsightAgent
from agents.drafting_agent import DraftingAgent
from core.tax_math import TaxMath
from core.schemas import TaxYearData, ReconciliationRequest

load_dotenv()

app = FastAPI()

# 1. Initialize Engines Once
math_engine = TaxMath()
API_KEY = os.getenv("OPENAI_API_KEY")
extractor = ExtractionAgent(api_key=API_KEY)
insighter = InsightAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalysisPayload(BaseModel):
    last_year: dict
    this_year: dict

# --- ENDPOINTS ---

@app.post("/extract")
async def extract_tax_data(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    data = await extractor.run(pdf_bytes)
    return {"status": "success", "data": data}

@app.post("/analyze")
async def analyze_and_calculate(payload: AnalysisPayload):
    # Use model_dump if these are Pydantic models, or leave as dict
    math_results = math_engine.run_reconciliation(payload.this_year)
    insights = insighter.run(payload.last_year, payload.this_year)
    
    # Corrected key access: Use 'balance' from our tax_math.py logic
    balance = math_results.get('balance', 0)
    
    if balance < 0:
        math_results['status'] = "OWE"
        insights.append({
            "type": "warning",
            "title": "Payment Shortfall",
            "text": f"Based on your changes, you may owe ${abs(balance):,.2f}. Consider adjusting your withholding now."
        })
    else:
        math_results['status'] = "REFUND"
    
    return {
        "status": "success",
        "calculation": math_results,
        "insights": insights
    }

@app.post("/api/v1/reconcile")
async def reconcile_taxes(request: ReconciliationRequest):
    try:
        # request.model_dump() handles the Pydantic to Dict conversion
        results = math_engine.run_reconciliation(request.model_dump())
        return {
            "status": "success",
            "calculation": results # This is the key test_api.py is looking for
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-draft")
async def generate_draft(data: TaxYearData):
    drafter = DraftingAgent("data/f1040_template.pdf")
    output_filename = "tax_draft_2025.pdf"
    drafter.generate(data.model_dump(), output_filename)
    
    return FileResponse(
        output_filename, 
        media_type="application/pdf", 
        filename="Your_Tax_Assistant_Draft.pdf"
    )