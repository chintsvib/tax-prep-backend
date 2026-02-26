from agents.refund_explainer_agent import RefundExplainerAgent
from core.tax_math import TaxMath


PRIOR_YEAR = {
    "tax_year": 2023,
    "filing_status": "Single",
    "dependents_count": 0,
    "wages": 70000,
    "schedule_1_income": 0,
    "w2_withholding": 11000,
    "schedule_3_total": 0,
    "total_deductions": None,
    "deduction_type": "Standard",
    "self_employment_tax": 0,
    "qbi_deduction": 0,
    "schedule_2_total": 0,
    "estimated_tax_payments": 0,
    "other_income": 0,
    "child_tax_credit": 0,
    "taxable_interest": 0,
    "ordinary_dividends": 0,
    "capital_gain_or_loss": 0,
    "withholding_1099": 0,
}

CURRENT_YEAR = {
    **PRIOR_YEAR,
    "tax_year": 2024,
    "wages": 85000,
    "w2_withholding": 14000,
}


# --- Unit tests (agent-level, no DB) ---

def test_explain_basic_wage_increase():
    agent = RefundExplainerAgent(math_engine=TaxMath())
    result = agent.explain(PRIOR_YEAR, CURRENT_YEAR)

    assert result["prior_year"] == 2023
    assert result["current_year"] == 2024
    assert isinstance(result["drivers"], list)
    assert len(result["drivers"]) >= 2

    fields = [d["field"] for d in result["drivers"]]
    assert "wages" in fields
    assert "w2_withholding" in fields

    wages_driver = next(d for d in result["drivers"] if d["field"] == "wages")
    assert wages_driver["direction"] == "decreased_refund"
    assert wages_driver["impact_on_balance"] < 0

    wh_driver = next(d for d in result["drivers"] if d["field"] == "w2_withholding")
    assert wh_driver["direction"] == "increased_refund"
    assert wh_driver["impact_on_balance"] > 0


def test_explain_no_change():
    agent = RefundExplainerAgent(math_engine=TaxMath())
    result = agent.explain(PRIOR_YEAR, PRIOR_YEAR)
    assert result["drivers"] == []
    assert result["total_change"] == 0.0


def test_explain_filing_status_change():
    agent = RefundExplainerAgent(math_engine=TaxMath())
    current = {**PRIOR_YEAR, "tax_year": 2024, "filing_status": "Married filing jointly"}
    result = agent.explain(PRIOR_YEAR, current)

    fields = [d["field"] for d in result["drivers"]]
    assert "filing_status" in fields
    fs_driver = next(d for d in result["drivers"] if d["field"] == "filing_status")
    assert fs_driver["direction"] == "increased_refund"


def test_explain_added_dependents():
    agent = RefundExplainerAgent(math_engine=TaxMath())
    current = {**PRIOR_YEAR, "tax_year": 2024, "dependents_count": 1}
    result = agent.explain(PRIOR_YEAR, current)

    fields = [d["field"] for d in result["drivers"]]
    assert "dependents_count" in fields
    dep_driver = next(d for d in result["drivers"] if d["field"] == "dependents_count")
    assert dep_driver["direction"] == "increased_refund"


def test_explain_drivers_sorted_by_impact():
    agent = RefundExplainerAgent(math_engine=TaxMath())
    current = {
        **PRIOR_YEAR,
        "tax_year": 2024,
        "wages": 120000,
        "w2_withholding": 20000,
        "schedule_1_income": 5000,
    }
    result = agent.explain(PRIOR_YEAR, current)
    impacts = [abs(d["impact_on_balance"]) for d in result["drivers"]]
    assert impacts == sorted(impacts, reverse=True)


def test_explain_total_change_matches():
    agent = RefundExplainerAgent(math_engine=TaxMath())
    result = agent.explain(PRIOR_YEAR, CURRENT_YEAR)
    expected = round(result["current_balance"] - result["prior_balance"], 2)
    assert result["total_change"] == expected


def test_explain_drivers_sum_close_to_total():
    agent = RefundExplainerAgent(math_engine=TaxMath())
    result = agent.explain(PRIOR_YEAR, CURRENT_YEAR)
    driver_sum = sum(d["impact_on_balance"] for d in result["drivers"])
    assert abs(driver_sum - result["total_change"]) < 1.0


def test_explain_each_driver_has_explanation():
    agent = RefundExplainerAgent(math_engine=TaxMath())
    result = agent.explain(PRIOR_YEAR, CURRENT_YEAR)
    for driver in result["drivers"]:
        assert len(driver["explanation"]) > 20
        assert "$" in driver["explanation"]


# --- Integration tests (endpoint-level, with DB) ---

def _create_record(client, auth_header, overrides=None):
    data = {**PRIOR_YEAR}
    data.pop("tax_year", None)
    data["tax_year"] = 2023
    if overrides:
        data.update(overrides)
    resp = client.post("/tax-records", json=data, headers=auth_header)
    assert resp.status_code == 200
    return resp.json()["id"]


def test_endpoint_by_record_ids(client, auth_header):
    prior_id = _create_record(client, auth_header, {"tax_year": 2023, "wages": 70000})
    current_id = _create_record(client, auth_header, {"tax_year": 2024, "wages": 85000, "w2_withholding": 14000})

    resp = client.post("/insights/explain-refund-change", json={
        "prior_record_id": prior_id,
        "current_record_id": current_id,
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["prior_year"] == 2023
    assert data["current_year"] == 2024
    assert len(data["drivers"]) > 0
    assert "total_change" in data


def test_endpoint_by_tax_years(client, auth_header):
    _create_record(client, auth_header, {"tax_year": 2023, "wages": 70000})
    _create_record(client, auth_header, {"tax_year": 2024, "wages": 85000, "w2_withholding": 14000})

    resp = client.post("/insights/explain-refund-change", json={
        "prior_year": 2023,
        "current_year": 2024,
    }, headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.json()["drivers"]) > 0


def test_endpoint_by_raw_data(client, auth_header):
    resp = client.post("/insights/explain-refund-change", json={
        "prior_data": PRIOR_YEAR,
        "current_data": CURRENT_YEAR,
    }, headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.json()["drivers"]) > 0


def test_endpoint_missing_record_404(client, auth_header):
    resp = client.post("/insights/explain-refund-change", json={
        "prior_record_id": 9999,
        "current_record_id": 9998,
    }, headers=auth_header)
    assert resp.status_code == 404


def test_endpoint_missing_year_404(client, auth_header):
    resp = client.post("/insights/explain-refund-change", json={
        "prior_year": 2020,
        "current_year": 2021,
    }, headers=auth_header)
    assert resp.status_code == 404


def test_endpoint_no_params_400(client, auth_header):
    resp = client.post("/insights/explain-refund-change", json={}, headers=auth_header)
    assert resp.status_code == 400


def test_endpoint_user_isolation(client, auth_header):
    prior_id = _create_record(client, auth_header, {"tax_year": 2023})

    resp = client.post("/auth/signup", json={
        "email": "userb@example.com", "password": "pass"
    })
    header_b = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp = client.post("/insights/explain-refund-change", json={
        "prior_record_id": prior_id,
        "current_record_id": prior_id,
    }, headers=header_b)
    assert resp.status_code == 404
