#!/usr/bin/env python3
import urllib.request
import json

payload = {
    "vessel_id": "MV-CHENNAI-STAR",
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
    "month": 2,
    "hs_code": "8471"
}

data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    "http://localhost:8000/predict",
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

resp = urllib.request.urlopen(req)
result = json.loads(resp.read().decode("utf-8"))

print("=" * 50)
print(f"VESSEL:      {result['vessel_id']}")
print(f"ROUTE:       {result['route']}")
print(f"RISK SCORE:  {result['risk_score']}")
print(f"RISK LEVEL:  {result['risk_level']}")
print(f"RECOMMEND:   {result['recommendation']}")
print("=" * 50)
print("BREAKDOWN:")
for k, v in result["breakdown"].items():
    print(f"  {k}: {v}")
print("=" * 50)
print("REROUTING OPTIONS:")
for opt in result["rerouting_options"]:
    print(f"  {opt['route']}")
    print(f"    On-time: {opt['on_time_probability']} | Cost: {opt['extra_cost']} | {opt['verdict']}")
print("=" * 50)
print("WEATHER EVIDENCE:", result["evidence"]["weather"])
print("GEO EVIDENCE:", result["evidence"]["geopolitics"]["top_headline"])
