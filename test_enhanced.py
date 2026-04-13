import json, subprocess, sys

payload = {
    "vessel_id": "MV-TEST",
    "origin": "Khor Fakkan",
    "destination": "Rotterdam",
    "days_real": 8,
    "days_scheduled": 3,
    "benefit_per_order": -50,
    "sales_per_customer": 500,
    "discount_rate": 0.05,
    "profit_ratio": -0.1,
    "quantity": 8400,
    "category_id": 73,
    "shipping_mode_encoded": 0,
    "month": 4,
    "hs_code": "8471",
    "transport_mode": "sea",
    "departure_date": "2026-04-20"
}

r = subprocess.run([
    'curl', '-s', '-X', 'POST', 'http://localhost:8000/predict/enhanced',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps(payload)
], capture_output=True, text=True)

d = json.loads(r.stdout)
ba = d.get('bedrock_analysis', {})
chi = ba.get('company_history_impact', {})
print('RS:', d.get('risk_score'), d.get('risk_level'))
print('Company history used:', chi.get('used'))
print('Adjustment:', chi.get('adjustment_applied'))
print('Explanation:', str(chi.get('explanation', ''))[:100])
print('Computation steps:', len(ba.get('computation_steps', [])))
