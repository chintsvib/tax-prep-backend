import requests
import json

# The local URL for your FastAPI server
URL = "http://127.0.0.1:8000/api/v1/reconcile"

# Sample data for a self-employed user
test_payload = {
    "filing_status": "Single",
    "wages": 50000.0,
    "schedule_1_income": 20000.0,  # This should trigger SE tax calculation
    "w2_withholding": 8000.0,
    "schedule_3_total": 500.0,
    "total_deductions": 15000.0    # 2025 Standard Deduction
}

def run_test():
    print(f"🚀 Sending test request to {URL}...\n")
    try:
        response = requests.post(URL, json=test_payload)
        
        if response.status_code == 200:
            print("✅ Success!")
            data = response.json()["calculation"]
            
            # Print the key results
            print(f"--- Results ---")
            print(f"AGI: ${data['agi_2025']:,.2f}")
            print(f"Total Tax: ${data['total_tax_2025']:,.2f}")
            print(f"Result: {data['type'].upper()} of ${abs(data['balance']):,.2f}")
            print(f"---------------\n")
        else:
            print(f"❌ Failed! Status Code: {response.status_code}")
            print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the server. Is FastAPI running on port 8000?")

if __name__ == "__main__":
    run_test()