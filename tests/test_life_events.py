SAMPLE_DATA = {
    "filing_status": "Single",
    "wages": 75000,
    "schedule_1_income": 0,
    "w2_withholding": 12000,
    "schedule_3_total": 0,
    "total_deductions": 15000,
}


def test_list_life_events(client):
    resp = client.get("/life-events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) >= 7
    keys = [e["key"] for e in events]
    assert "got_married" in keys
    assert "maxed_401k" in keys


def test_apply_got_married(client, auth_header):
    resp = client.post("/life-events/apply", json={
        "event_key": "got_married",
        "base_data": SAMPLE_DATA,
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["event"] == "Got Married"
    # MFJ should reduce tax (wider brackets + higher standard deduction)
    assert data["after"]["total_tax_2025"] <= data["before"]["total_tax_2025"]


def test_apply_maxed_401k(client, auth_header):
    resp = client.post("/life-events/apply", json={
        "event_key": "maxed_401k",
        "base_data": SAMPLE_DATA,
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    # 401k reduces taxable income, so tax should go down
    assert data["after"]["total_tax_2025"] < data["before"]["total_tax_2025"]
    assert data["diff"]["total_tax_2025"] < 0


def test_apply_started_side_hustle(client, auth_header):
    resp = client.post("/life-events/apply", json={
        "event_key": "started_side_hustle",
        "base_data": SAMPLE_DATA,
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    # Side hustle adds income, so tax should go up
    assert data["after"]["total_tax_2025"] > data["before"]["total_tax_2025"]


def test_apply_had_baby(client, auth_header):
    resp = client.post("/life-events/apply", json={
        "event_key": "had_baby",
        "base_data": SAMPLE_DATA,
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    # Child tax credit reduces balance owed / increases refund
    assert data["after"]["balance"] > data["before"]["balance"]


def test_apply_with_custom_values(client, auth_header):
    resp = client.post("/life-events/apply", json={
        "event_key": "started_side_hustle",
        "base_data": SAMPLE_DATA,
        "custom_values": {"schedule_1_income": 50000},
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    # Custom override should use $50k not the default $10k
    assert data["after"]["agi_2025"] > data["before"]["agi_2025"] + 20000


def test_apply_from_scenario(client, auth_header):
    # Create a scenario first
    create_resp = client.post("/scenarios", json={
        "name": "Base",
        **SAMPLE_DATA,
    }, headers=auth_header)
    sid = create_resp.json()["id"]

    resp = client.post("/life-events/apply", json={
        "event_key": "maxed_401k",
        "base_scenario_id": sid,
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["diff"]["total_tax_2025"] < 0


def test_apply_unknown_event(client, auth_header):
    resp = client.post("/life-events/apply", json={
        "event_key": "won_lottery",
        "base_data": SAMPLE_DATA,
    }, headers=auth_header)
    assert resp.status_code == 404
