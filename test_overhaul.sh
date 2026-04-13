#!/bin/bash
set -e

echo "══════════════════════════════════════════════════"
echo "  SANJAYA v2.0 — OVERHAUL VALIDATION SUITE"
echo "══════════════════════════════════════════════════"
echo ""

echo "=== TEST 1: Hormuz Crisis (MUST be CRITICAL ≥85) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"MV-CHENNAI-STAR","origin":"Khor Fakkan","destination":"Rotterdam","days_real":8,"days_scheduled":3,"benefit_per_order":-50,"sales_per_customer":500,"discount_rate":0.05,"profit_ratio":-0.1,"quantity":8400,"category_id":73,"shipping_mode_encoded":0,"month":2,"hs_code":"8471","transport_mode":"sea","departure_date":"2026-04-20"}' | python3 -m json.tool
echo ""
echo "---"

echo "=== TEST 2: Mumbai-Dubai June sea (should be MEDIUM range) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"MV-GUJARAT","origin":"Mumbai","destination":"Dubai","days_real":3,"days_scheduled":3,"benefit_per_order":200,"sales_per_customer":1200,"discount_rate":0.02,"profit_ratio":0.2,"quantity":1200,"category_id":30,"shipping_mode_encoded":2,"month":6,"hs_code":"7308","transport_mode":"sea","departure_date":"2026-06-15"}' | python3 -m json.tool
echo ""
echo "---"

echo "=== TEST 3: Chennai-Singapore Aug monsoon (MEDIUM range) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"MV-INDIA-EX","origin":"Chennai","destination":"Singapore","days_real":4,"days_scheduled":3,"benefit_per_order":120,"sales_per_customer":800,"discount_rate":0.05,"profit_ratio":0.15,"quantity":500,"category_id":45,"shipping_mode_encoded":1,"month":8,"hs_code":"6204","transport_mode":"sea","departure_date":"2026-08-10"}' | python3 -m json.tool
echo ""
echo "---"

echo "=== TEST 4: Road Delhi-Mumbai July monsoon (MEDIUM-HIGH) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"TRUCK-DL-001","origin":"Delhi","destination":"Mumbai","days_real":4,"days_scheduled":2,"benefit_per_order":80,"sales_per_customer":400,"discount_rate":0.08,"profit_ratio":0.12,"quantity":200,"category_id":20,"shipping_mode_encoded":0,"month":7,"hs_code":"4011","transport_mode":"road","departure_date":"2026-07-15"}' | python3 -m json.tool
echo ""
echo "---"

echo "=== TEST 5: Air Delhi-Dubai Jan winter fog (MEDIUM) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"AI-CARGO-001","origin":"Delhi","destination":"Dubai","days_real":2,"days_scheduled":1,"benefit_per_order":500,"sales_per_customer":2000,"discount_rate":0.03,"profit_ratio":0.25,"quantity":50,"category_id":85,"shipping_mode_encoded":3,"month":1,"hs_code":"8542","transport_mode":"air","departure_date":"2026-01-10"}' | python3 -m json.tool
echo ""
echo "---"

echo "=== TEST 6: Shanghai-LA Dec peak season (MEDIUM-HIGH) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"MV-PACIFIC","origin":"Shanghai","destination":"Los Angeles","days_real":6,"days_scheduled":5,"benefit_per_order":80,"sales_per_customer":600,"discount_rate":0.05,"profit_ratio":0.1,"quantity":3000,"category_id":60,"shipping_mode_encoded":0,"month":12,"hs_code":"8542","transport_mode":"sea","departure_date":"2026-12-01"}' | python3 -m json.tool
echo ""

echo "══════════════════════════════════════════════════"
echo "  SUMMARY — Extract key results"
echo "══════════════════════════════════════════════════"

echo ""
echo "TEST1 Hormuz:"
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"vessel_id":"MV-CHENNAI-STAR","origin":"Khor Fakkan","destination":"Rotterdam","days_real":8,"days_scheduled":3,"benefit_per_order":-50,"sales_per_customer":500,"discount_rate":0.05,"profit_ratio":-0.1,"quantity":8400,"category_id":73,"shipping_mode_encoded":0,"month":2,"hs_code":"8471","transport_mode":"sea","departure_date":"2026-04-20"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  RS={d[\"risk_score\"]} | {d[\"risk_level\"]} | Mode={d[\"transport_mode\"]} | Season={d.get(\"season\",\"?\")} | Overrides={d.get(\"rule_overrides\",[])}')"

echo "TEST2 Mumbai-Dubai:"
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"vessel_id":"MV-GUJARAT","origin":"Mumbai","destination":"Dubai","days_real":3,"days_scheduled":3,"benefit_per_order":200,"sales_per_customer":1200,"discount_rate":0.02,"profit_ratio":0.2,"quantity":1200,"category_id":30,"shipping_mode_encoded":2,"month":6,"hs_code":"7308","transport_mode":"sea","departure_date":"2026-06-15"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  RS={d[\"risk_score\"]} | {d[\"risk_level\"]} | Mode={d[\"transport_mode\"]} | Season={d.get(\"season\",\"?\")} | Overrides={d.get(\"rule_overrides\",[])}')"

echo "TEST3 Chennai-Singapore:"
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"vessel_id":"MV-INDIA-EX","origin":"Chennai","destination":"Singapore","days_real":4,"days_scheduled":3,"benefit_per_order":120,"sales_per_customer":800,"discount_rate":0.05,"profit_ratio":0.15,"quantity":500,"category_id":45,"shipping_mode_encoded":1,"month":8,"hs_code":"6204","transport_mode":"sea","departure_date":"2026-08-10"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  RS={d[\"risk_score\"]} | {d[\"risk_level\"]} | Mode={d[\"transport_mode\"]} | Season={d.get(\"season\",\"?\")} | Overrides={d.get(\"rule_overrides\",[])}')"

echo "TEST4 Road Delhi-Mumbai:"
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"vessel_id":"TRUCK-DL-001","origin":"Delhi","destination":"Mumbai","days_real":4,"days_scheduled":2,"benefit_per_order":80,"sales_per_customer":400,"discount_rate":0.08,"profit_ratio":0.12,"quantity":200,"category_id":20,"shipping_mode_encoded":0,"month":7,"hs_code":"4011","transport_mode":"road","departure_date":"2026-07-15"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  RS={d[\"risk_score\"]} | {d[\"risk_level\"]} | Mode={d[\"transport_mode\"]} | Season={d.get(\"season\",\"?\")} | Overrides={d.get(\"rule_overrides\",[])}')"

echo "TEST5 Air Delhi-Dubai:"
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"vessel_id":"AI-CARGO-001","origin":"Delhi","destination":"Dubai","days_real":2,"days_scheduled":1,"benefit_per_order":500,"sales_per_customer":2000,"discount_rate":0.03,"profit_ratio":0.25,"quantity":50,"category_id":85,"shipping_mode_encoded":3,"month":1,"hs_code":"8542","transport_mode":"air","departure_date":"2026-01-10"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  RS={d[\"risk_score\"]} | {d[\"risk_level\"]} | Mode={d[\"transport_mode\"]} | Season={d.get(\"season\",\"?\")} | Overrides={d.get(\"rule_overrides\",[])}')"

echo "TEST6 Shanghai-LA:"
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"vessel_id":"MV-PACIFIC","origin":"Shanghai","destination":"Los Angeles","days_real":6,"days_scheduled":5,"benefit_per_order":80,"sales_per_customer":600,"discount_rate":0.05,"profit_ratio":0.1,"quantity":3000,"category_id":60,"shipping_mode_encoded":0,"month":12,"hs_code":"8542","transport_mode":"sea","departure_date":"2026-12-01"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  RS={d[\"risk_score\"]} | {d[\"risk_level\"]} | Mode={d[\"transport_mode\"]} | Season={d.get(\"season\",\"?\")} | Overrides={d.get(\"rule_overrides\",[])}')"

echo ""
echo "=== ALL 6 TESTS COMPLETE ==="
