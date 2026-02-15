SAMPLE_RECORD = {
    "tax_year": 2024,
    "filing_status": "Single",
    "wages": 75000,
    "schedule_1_income": 0,
    "w2_withholding": 12000,
    "schedule_3_total": 500,
    "total_deductions": 15000,
    "self_employment_tax": 0,
    "qbi_deduction": 0,
    "schedule_2_total": 0,
    "estimated_tax_payments": 0,
    "other_income": 0,
}


def test_create_tax_record(client, auth_header):
    resp = client.post("/tax-records", json=SAMPLE_RECORD, headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tax_year"] == 2024
    assert data["wages"] == 75000
    assert data["source"] == "manual"


def test_list_tax_records(client, auth_header):
    client.post("/tax-records", json=SAMPLE_RECORD, headers=auth_header)
    client.post("/tax-records", json={**SAMPLE_RECORD, "tax_year": 2023}, headers=auth_header)

    resp = client.get("/tax-records", headers=auth_header)
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 2
    # Should be sorted by year descending
    assert records[0]["tax_year"] == 2024
    assert records[1]["tax_year"] == 2023


def test_get_tax_record(client, auth_header):
    create_resp = client.post("/tax-records", json=SAMPLE_RECORD, headers=auth_header)
    rid = create_resp.json()["id"]

    resp = client.get(f"/tax-records/{rid}", headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["id"] == rid


def test_update_tax_record(client, auth_header):
    create_resp = client.post("/tax-records", json=SAMPLE_RECORD, headers=auth_header)
    rid = create_resp.json()["id"]

    updated = {**SAMPLE_RECORD, "wages": 90000}
    resp = client.put(f"/tax-records/{rid}", json=updated, headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["wages"] == 90000


def test_tax_record_isolation(client, auth_header):
    """User A's records not visible to User B."""
    client.post("/tax-records", json=SAMPLE_RECORD, headers=auth_header)

    # Create User B
    resp = client.post("/auth/signup", json={
        "email": "userb@example.com", "password": "pass"
    })
    header_b = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp = client.get("/tax-records", headers=header_b)
    assert len(resp.json()) == 0


def test_upload_without_api_key(client, auth_header):
    """Upload should fail gracefully without OpenAI key."""
    import io
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake content")
    resp = client.post(
        "/tax-records/upload?tax_year=2024",
        files={"file": ("test.pdf", fake_pdf, "application/pdf")},
        headers=auth_header,
    )
    # Should fail gracefully (500 no API key, or 422 extraction error)
    assert resp.status_code in (422, 500)
