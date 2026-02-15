import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Internal Imports
from agents.insight_agent import InsightAgent
from agents.drafting_agent import DraftingAgent
from core.tax_math import TaxMath
from core.schemas import TaxYearData, ReconciliationRequest
from core.database import create_db
from routes.auth import router as auth_router
from routes.scenarios import router as scenarios_router
from routes.insights import router as insights_router
from routes.life_events import router as life_events_router

load_dotenv()


@asynccontextmanager
async def lifespan(app):
    create_db()
    yield


app = FastAPI(title="Tax Prep Assistant", version="2.0.0", lifespan=lifespan)

# 1. Initialize Engines Once
math_engine = TaxMath()
API_KEY = os.getenv("OPENAI_API_KEY")
insighter = InsightAgent()

# Lazy-init extraction agent (requires OpenAI key)
extractor = None
if API_KEY:
    from agents.extraction_agent import ExtractionAgent
    extractor = ExtractionAgent(api_key=API_KEY)

# 2. CORS — allow all origins (lock down in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include Routers
app.include_router(auth_router)
app.include_router(scenarios_router)
app.include_router(insights_router)
app.include_router(life_events_router)


# --- HEALTH CHECK ---

@app.get("/health")
def health():
    return {"status": "ok"}


class AnalysisPayload(BaseModel):
    last_year: dict
    this_year: dict

# --- ORIGINAL ENDPOINTS (preserved) ---

@app.post("/extract")
async def extract_tax_data(file: UploadFile = File(...)):
    if not extractor:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    pdf_bytes = await file.read()
    data = await extractor.run(pdf_bytes)
    return {"status": "success", "data": data}

@app.post("/analyze")
async def analyze_and_calculate(payload: AnalysisPayload):
    math_results = math_engine.run_reconciliation(payload.this_year)
    insights = insighter.run(payload.last_year, payload.this_year)

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
        results = math_engine.run_reconciliation(request.model_dump())
        return {
            "status": "success",
            "calculation": results
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
