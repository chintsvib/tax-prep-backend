from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.database import get_session
from core.models import User, Scenario
from core.auth import get_current_user
from core.tax_math import TaxMath
from core.schemas import (
    ScenarioCreate, ScenarioResponse, ScenarioCompareResponse,
    WhatIfRequest, WhatIfResponse,
)

router = APIRouter(prefix="/scenarios", tags=["scenarios"])
math_engine = TaxMath()


def _scenario_to_tax_data(s) -> dict:
    return {
        "filing_status": s.filing_status,
        "wages": s.wages,
        "schedule_1_income": s.schedule_1_income,
        "w2_withholding": s.w2_withholding,
        "schedule_3_total": s.schedule_3_total,
        "total_deductions": s.total_deductions,
    }


def _calc_and_fill(scenario: Scenario) -> Scenario:
    result = math_engine.run_reconciliation(_scenario_to_tax_data(scenario))
    scenario.agi = result["agi_2025"]
    scenario.taxable_income = result["taxable_income_2025"]
    scenario.total_tax = result["total_tax_2025"]
    scenario.balance = result["balance"]
    scenario.balance_type = result["type"]
    return scenario


@router.post("", response_model=ScenarioResponse)
def create_scenario(
    req: ScenarioCreate,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    scenario = Scenario(
        user_id=user.id,
        name=req.name,
        description=req.description,
        base_record_id=req.base_record_id,
        filing_status=req.filing_status,
        wages=req.wages,
        schedule_1_income=req.schedule_1_income,
        w2_withholding=req.w2_withholding,
        schedule_3_total=req.schedule_3_total,
        total_deductions=req.total_deductions,
    )
    _calc_and_fill(scenario)
    session.add(scenario)
    session.commit()
    session.refresh(scenario)
    return scenario


@router.get("", response_model=list[ScenarioResponse])
def list_scenarios(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    scenarios = session.exec(
        select(Scenario).where(Scenario.user_id == user.id)
    ).all()
    return scenarios


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(
    scenario_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    scenario = session.get(Scenario, scenario_id)
    if not scenario or scenario.user_id != user.id:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.delete("/{scenario_id}")
def delete_scenario(
    scenario_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    scenario = session.get(Scenario, scenario_id)
    if not scenario or scenario.user_id != user.id:
        raise HTTPException(status_code=404, detail="Scenario not found")
    session.delete(scenario)
    session.commit()
    return {"status": "deleted"}


@router.post("/compare", response_model=ScenarioCompareResponse)
def compare_scenarios(
    scenario_a_id: int,
    scenario_b_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    a = session.get(Scenario, scenario_a_id)
    b = session.get(Scenario, scenario_b_id)
    if not a or a.user_id != user.id or not b or b.user_id != user.id:
        raise HTTPException(status_code=404, detail="Scenario not found")

    diff = {
        "wages": round((b.wages or 0) - (a.wages or 0), 2),
        "agi": round((b.agi or 0) - (a.agi or 0), 2),
        "total_tax": round((b.total_tax or 0) - (a.total_tax or 0), 2),
        "balance": round((b.balance or 0) - (a.balance or 0), 2),
    }
    return ScenarioCompareResponse(
        scenario_a=ScenarioResponse.model_validate(a, from_attributes=True),
        scenario_b=ScenarioResponse.model_validate(b, from_attributes=True),
        diff=diff,
    )


@router.post("/what-if", response_model=WhatIfResponse)
def what_if(
    req: WhatIfRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Build baseline data
    if req.base_scenario_id:
        scenario = session.get(Scenario, req.base_scenario_id)
        if not scenario or scenario.user_id != user.id:
            raise HTTPException(status_code=404, detail="Base scenario not found")
        base_data = _scenario_to_tax_data(scenario)
    else:
        base_data = {
            "filing_status": "Single",
            "wages": 0.0,
            "schedule_1_income": 0.0,
            "w2_withholding": 0.0,
            "schedule_3_total": 0.0,
            "total_deductions": None,
        }

    baseline = math_engine.run_reconciliation(base_data)

    # Apply overrides
    modified_data = {**base_data, **req.overrides}
    modified = math_engine.run_reconciliation(modified_data)

    diff = {
        key: round(modified.get(key, 0) - baseline.get(key, 0), 2)
        for key in baseline
        if isinstance(baseline.get(key), (int, float))
    }

    return WhatIfResponse(baseline=baseline, modified=modified, diff=diff)
