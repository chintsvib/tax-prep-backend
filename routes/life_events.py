from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from core.database import get_session
from core.models import User, Scenario
from core.auth import get_current_user
from core.tax_math import TaxMath
from core.schemas import LifeEventPreset, LifeEventApplyRequest, LifeEventApplyResponse

router = APIRouter(prefix="/life-events", tags=["life-events"])
math_engine = TaxMath()

# --- Life Event Presets ---
LIFE_EVENTS = {
    "got_married": {
        "name": "Got Married",
        "description": "Switch to Married Filing Jointly for a higher standard deduction and wider brackets",
        "fields_affected": ["filing_status"],
        "overrides": {"filing_status": "Married filing jointly"},
    },
    "had_baby": {
        "name": "Had a Baby",
        "description": "Add a $2,200 Child Tax Credit for a new dependent (2025 amount)",
        "fields_affected": ["dependents_count"],
        "adjustments": {"dependents_count_add": 1},
    },
    "started_side_hustle": {
        "name": "Started a Side Hustle",
        "description": "Add self-employment income ($10,000 default, adjust to your actual amount)",
        "fields_affected": ["schedule_1_income"],
        "overrides": {"schedule_1_income": 10000},
    },
    "bought_home": {
        "name": "Bought a Home",
        "description": "Switch to itemized deductions with mortgage interest + property tax (~$25,000)",
        "fields_affected": ["total_deductions"],
        "overrides": {"total_deductions": 25000},
    },
    "maxed_401k": {
        "name": "Maxed Out 401(k)",
        "description": "Reduce wages by $23,500 (2025 contribution limit) for pre-tax 401(k)",
        "fields_affected": ["wages"],
        "adjustments": {"wages_subtract": 23500},
    },
    "contributed_ira": {
        "name": "Traditional IRA Contribution",
        "description": "Deduct up to $7,000 (2025 limit) for a Traditional IRA contribution",
        "fields_affected": ["wages"],
        "adjustments": {"wages_subtract": 7000},
    },
    "contributed_hsa": {
        "name": "HSA Contribution",
        "description": "Deduct up to $4,300 (2025 individual limit) for an HSA contribution",
        "fields_affected": ["wages"],
        "adjustments": {"wages_subtract": 4300},
    },
    "lost_job": {
        "name": "Lost Job / Reduced Income",
        "description": "Reduce wages by 50% to simulate mid-year job loss",
        "fields_affected": ["wages", "w2_withholding"],
        "adjustments": {"wages_multiply": 0.5, "w2_withholding_multiply": 0.5},
    },
}


@router.get("", response_model=list[LifeEventPreset])
def list_life_events():
    return [
        LifeEventPreset(
            key=key,
            name=ev["name"],
            description=ev["description"],
            fields_affected=ev["fields_affected"],
        )
        for key, ev in LIFE_EVENTS.items()
    ]


@router.post("/apply", response_model=LifeEventApplyResponse)
def apply_life_event(
    req: LifeEventApplyRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    event = LIFE_EVENTS.get(req.event_key)
    if not event:
        raise HTTPException(status_code=404, detail=f"Life event '{req.event_key}' not found")

    # Build base data from scenario or provided data
    if req.base_scenario_id:
        scenario = session.get(Scenario, req.base_scenario_id)
        if not scenario or scenario.user_id != user.id:
            raise HTTPException(status_code=404, detail="Base scenario not found")
        base_data = {
            "filing_status": scenario.filing_status,
            "wages": scenario.wages,
            "schedule_1_income": scenario.schedule_1_income,
            "w2_withholding": scenario.w2_withholding,
            "schedule_3_total": scenario.schedule_3_total,
            "total_deductions": scenario.total_deductions,
        }
    elif req.base_data:
        base_data = req.base_data
    else:
        raise HTTPException(status_code=400, detail="Provide base_scenario_id or base_data")

    before = math_engine.run_reconciliation(base_data)

    # Apply event overrides and adjustments
    modified_data = {**base_data}

    # Direct overrides
    if "overrides" in event:
        for key, value in event["overrides"].items():
            modified_data[key] = value

    # Calculated adjustments
    if "adjustments" in event:
        for adj_key, adj_value in event["adjustments"].items():
            if adj_key.endswith("_subtract"):
                field = adj_key.replace("_subtract", "")
                modified_data[field] = max(0, (modified_data.get(field) or 0) - adj_value)
            elif adj_key.endswith("_add"):
                field = adj_key.replace("_add", "")
                modified_data[field] = (modified_data.get(field) or 0) + adj_value
            elif adj_key.endswith("_multiply"):
                field = adj_key.replace("_multiply", "")
                modified_data[field] = (modified_data.get(field) or 0) * adj_value

    # Allow user custom overrides on top
    if req.custom_values:
        modified_data.update(req.custom_values)

    after = math_engine.run_reconciliation(modified_data)

    diff = {
        key: round(after.get(key, 0) - before.get(key, 0), 2)
        for key in before
        if isinstance(before.get(key), (int, float))
    }

    return LifeEventApplyResponse(
        event=event["name"],
        before=before,
        after=after,
        diff=diff,
    )
