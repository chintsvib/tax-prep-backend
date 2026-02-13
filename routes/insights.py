import os
from fastapi import APIRouter, Depends
from core.models import User
from core.auth import get_current_user
from core.tax_math import TaxMath
from core.schemas import OptimizationRequest, OptimizationResponse, Recommendation
from agents.optimization_agent import OptimizationAgent

router = APIRouter(prefix="/insights", tags=["insights"])

math_engine = TaxMath()
API_KEY = os.getenv("OPENAI_API_KEY")


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_taxes(
    req: OptimizationRequest,
    user: User = Depends(get_current_user),
):
    agent = OptimizationAgent(math_engine=math_engine, api_key=API_KEY)

    tax_data = req.model_dump()
    result = await agent.analyze_with_ai_summary(tax_data)

    return OptimizationResponse(
        current_tax=result["current_tax"],
        current_balance=result["current_balance"],
        current_type=result["current_type"],
        recommendations=[Recommendation(**r) for r in result["recommendations"]],
        total_potential_savings=result["total_potential_savings"],
        ai_summary=result.get("ai_summary"),
    )
