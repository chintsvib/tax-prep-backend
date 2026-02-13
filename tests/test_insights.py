from agents.optimization_agent import OptimizationAgent
from core.tax_math import TaxMath


def test_optimization_w2_employee():
    """A W-2 employee should get 401k, IRA, HSA recommendations."""
    agent = OptimizationAgent(math_engine=TaxMath())
    result = agent.analyze({
        "filing_status": "Single",
        "wages": 75000,
        "schedule_1_income": 0,
        "w2_withholding": 12000,
        "schedule_3_total": 0,
        "total_deductions": 15000,
    })
    strategies = [r["strategy"] for r in result["recommendations"]]
    assert "Max Out 401(k)" in strategies
    assert "Traditional IRA Contribution" in strategies
    assert "HSA Contribution" in strategies
    # Every recommendation should have positive savings
    for rec in result["recommendations"]:
        assert rec["tax_savings"] >= 0
    assert result["total_potential_savings"] > 0


def test_optimization_self_employed():
    """A self-employed person should get SEP-IRA recommendation."""
    agent = OptimizationAgent(math_engine=TaxMath())
    result = agent.analyze({
        "filing_status": "Single",
        "wages": 0,
        "schedule_1_income": 80000,
        "w2_withholding": 0,
        "schedule_3_total": 0,
        "total_deductions": 15000,
    })
    strategies = [r["strategy"] for r in result["recommendations"]]
    assert "SEP-IRA Contribution" in strategies


def test_optimization_owing_taxes():
    """Someone owing taxes should get a withholding adjustment recommendation."""
    agent = OptimizationAgent(math_engine=TaxMath())
    result = agent.analyze({
        "filing_status": "Single",
        "wages": 100000,
        "schedule_1_income": 0,
        "w2_withholding": 5000,  # Very low withholding
        "schedule_3_total": 0,
        "total_deductions": 15000,
    })
    strategies = [r["strategy"] for r in result["recommendations"]]
    assert "Increase W-4 Withholding" in strategies
    assert result["current_type"] == "owe"


def test_optimization_filing_status():
    """Single filer should see Head of Household option."""
    agent = OptimizationAgent(math_engine=TaxMath())
    result = agent.analyze({
        "filing_status": "Single",
        "wages": 60000,
        "schedule_1_income": 0,
        "w2_withholding": 10000,
        "schedule_3_total": 0,
        "total_deductions": 15000,
    })
    strategies = [r["strategy"] for r in result["recommendations"]]
    assert "File as Head of household" in strategies


def test_optimization_sorted_by_savings():
    """Recommendations should be sorted by tax_savings descending."""
    agent = OptimizationAgent(math_engine=TaxMath())
    result = agent.analyze({
        "filing_status": "Single",
        "wages": 100000,
        "schedule_1_income": 20000,
        "w2_withholding": 15000,
        "schedule_3_total": 0,
    })
    savings = [r["tax_savings"] for r in result["recommendations"]]
    assert savings == sorted(savings, reverse=True)


def test_optimization_endpoint(client, auth_header):
    """Test the /insights/optimize API endpoint."""
    resp = client.post("/insights/optimize", json={
        "filing_status": "Single",
        "wages": 75000,
        "w2_withholding": 12000,
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_tax"] > 0
    assert len(data["recommendations"]) > 0
    assert data["total_potential_savings"] > 0
