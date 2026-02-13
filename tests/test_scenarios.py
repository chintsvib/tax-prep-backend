SAMPLE_DATA = {
    "name": "Base 2025",
    "filing_status": "Single",
    "wages": 75000,
    "schedule_1_income": 0,
    "w2_withholding": 12000,
    "schedule_3_total": 0,
    "total_deductions": 15000,
}


def test_create_scenario(client, auth_header):
    resp = client.post("/scenarios", json=SAMPLE_DATA, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Base 2025"
    assert data["agi"] > 0
    assert data["total_tax"] > 0
    assert data["balance_type"] in ("refund", "owe")


def test_list_scenarios(client, auth_header):
    client.post("/scenarios", json=SAMPLE_DATA, headers=auth_header)
    client.post("/scenarios", json={**SAMPLE_DATA, "name": "Scenario B"}, headers=auth_header)
    resp = client.get("/scenarios", headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_scenario(client, auth_header):
    create_resp = client.post("/scenarios", json=SAMPLE_DATA, headers=auth_header)
    sid = create_resp.json()["id"]
    resp = client.get(f"/scenarios/{sid}", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["id"] == sid


def test_delete_scenario(client, auth_header):
    create_resp = client.post("/scenarios", json=SAMPLE_DATA, headers=auth_header)
    sid = create_resp.json()["id"]
    resp = client.delete(f"/scenarios/{sid}", headers=auth_header)
    assert resp.status_code == 200
    # Verify it's gone
    resp = client.get(f"/scenarios/{sid}", headers=auth_header)
    assert resp.status_code == 404


def test_compare_scenarios(client, auth_header):
    r1 = client.post("/scenarios", json=SAMPLE_DATA, headers=auth_header)
    r2 = client.post("/scenarios", json={
        **SAMPLE_DATA, "name": "Higher Wages", "wages": 100000
    }, headers=auth_header)
    id_a = r1.json()["id"]
    id_b = r2.json()["id"]

    resp = client.post(
        f"/scenarios/compare?scenario_a_id={id_a}&scenario_b_id={id_b}",
        headers=auth_header,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["diff"]["wages"] == 25000
    assert data["diff"]["total_tax"] > 0  # Higher wages = more tax


def test_what_if_from_scenario(client, auth_header):
    create_resp = client.post("/scenarios", json=SAMPLE_DATA, headers=auth_header)
    sid = create_resp.json()["id"]

    resp = client.post("/scenarios/what-if", json={
        "base_scenario_id": sid,
        "overrides": {"wages": 100000},
    }, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["modified"]["total_tax_2025"] > data["baseline"]["total_tax_2025"]
    assert data["diff"]["total_tax_2025"] > 0


def test_what_if_no_base(client, auth_header):
    resp = client.post("/scenarios/what-if", json={
        "overrides": {"wages": 50000, "w2_withholding": 8000},
    }, headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["modified"]["agi_2025"] > 0


def test_scenario_isolation(client, auth_header):
    """User A's scenarios are not visible to User B."""
    client.post("/scenarios", json=SAMPLE_DATA, headers=auth_header)

    # Create User B
    resp = client.post("/auth/signup", json={
        "email": "userb@example.com", "password": "pass"
    })
    token_b = resp.json()["access_token"]
    header_b = {"Authorization": f"Bearer {token_b}"}

    resp = client.get("/scenarios", headers=header_b)
    assert resp.status_code == 200
    assert len(resp.json()) == 0
