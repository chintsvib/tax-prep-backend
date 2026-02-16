"""
Load synthetic 1040 data into the backend via API.

Usage:
  python tests/load_test_data.py                          # local (localhost:8000)
  python tests/load_test_data.py https://your-railway.app  # production
"""

import sys
import requests
from synthetic_1040_data import SCENARIOS

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

# Create a test user (or login if exists)
EMAIL = "testuser@taxprep.dev"
PASSWORD = "TestPass123!"

print(f"Target: {BASE_URL}")
print(f"User:   {EMAIL}\n")

# Try signup, then login
resp = requests.post(f"{BASE_URL}/auth/signup", json={
    "email": EMAIL, "password": PASSWORD, "full_name": "Test User"
})
if resp.status_code == 200:
    token = resp.json()["access_token"]
    print("Created new test user")
else:
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": EMAIL, "password": PASSWORD
    })
    resp.raise_for_status()
    token = resp.json()["access_token"]
    print("Logged in as existing test user")

headers = {"Authorization": f"Bearer {token}"}

# Load each scenario
for i, scenario in enumerate(SCENARIOS, 1):
    name = scenario.pop("name")
    payload = scenario
    resp = requests.post(f"{BASE_URL}/tax-records", json=payload, headers=headers)
    if resp.status_code == 200:
        rid = resp.json()["id"]
        status = "REFUND" if payload["refund_amount"] > 0 else "OWES"
        amount = payload["refund_amount"] or payload["owed_amount"]
        print(f"  [{i}/8] {name}")
        print(f"         -> Record #{rid} | {payload['filing_status']} | {status} ${amount:,.0f}")
    else:
        print(f"  [{i}/8] FAILED: {name}")
        print(f"         -> {resp.status_code}: {resp.text[:200]}")
    scenario["name"] = name  # restore

print(f"\nDone! Loaded {len(SCENARIOS)} test records.")
print(f"Login with {EMAIL} / {PASSWORD} to view them.")
