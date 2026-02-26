import os
from fastapi import APIRouter, Depends, HTTPException
from core.tax_math import TaxMath
from core.schemas import (
    OptimizationRequest, OptimizationResponse, Recommendation,
    RefundExplainerRequest, RefundExplainerResponse, RefundChangeDriver,
)
from core.auth import get_current_user
from core.models import User
from agents.optimization_agent import OptimizationAgent
from agents.refund_explainer_agent import RefundExplainerAgent

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


@router.post("/explain-refund-change", response_model=RefundExplainerResponse)
async def explain_refund_change(
    req: RefundExplainerRequest,
):
    """Explain WHY the user's refund/owed amount changed between two tax years."""
    if not req.prior_data or not req.current_data:
        raise HTTPException(
            status_code=400,
            detail="Provide prior_data and current_data",
        )
    prior = req.prior_data
    current = req.current_data

    agent = RefundExplainerAgent(math_engine=math_engine, api_key=API_KEY)
    result = await agent.explain_with_ai_summary(prior, current)

    return RefundExplainerResponse(
        prior_year=result["prior_year"],
        current_year=result["current_year"],
        prior_balance=result["prior_balance"],
        prior_balance_type=result["prior_balance_type"],
        current_balance=result["current_balance"],
        current_balance_type=result["current_balance_type"],
        total_change=result["total_change"],
        total_change_direction=result["total_change_direction"],
        drivers=[RefundChangeDriver(**d) for d in result["drivers"]],
        ai_summary=result.get("ai_summary"),
    )
