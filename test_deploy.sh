#!/bin/bash
set -e

echo "=== Test 1: Hormuz Crisis (CRITICAL) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"MV-CHENNAI-STAR","origin":"Khor Fakkan","destination":"Rotterdam","days_real":8,"days_scheduled":3,"benefit_per_order":-50,"sales_per_customer":500,"discount_rate":0.05,"profit_ratio":-0.1,"quantity":8400,"category_id":73,"shipping_mode_encoded":0,"month":2,"hs_code":"8471"}' | python3 -m json.tool
echo ""

echo "=== Test 2: Chennai-Singapore (MEDIUM) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"MV-INDIA-EXPRESS","origin":"Chennai","destination":"Singapore","days_real":4,"days_scheduled":3,"benefit_per_order":120,"sales_per_customer":800,"discount_rate":0.05,"profit_ratio":0.15,"quantity":500,"category_id":45,"shipping_mode_encoded":1,"month":4,"hs_code":"6204"}' | python3 -m json.tool
echo ""

echo "=== Test 3: Mumbai-Dubai (LOW) ==="
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"vessel_id":"MV-GUJARAT-STAR","origin":"Mumbai","destination":"Dubai","days_real":3,"days_scheduled":3,"benefit_per_order":200,"sales_per_customer":1200,"discount_rate":0.02,"profit_ratio":0.2,"quantity":1200,"category_id":30,"shipping_mode_encoded":2,"month":6,"hs_code":"7308"}' | python3 -m json.tool
echo ""

echo "=== DB Records ==="
PGPASSWORD='Sanjaya2026!' psql -U sanjaya_user -d sanjaya_db -c "SELECT id, vessel_id, origin, destination, risk_score, risk_level FROM risk_assessments ORDER BY id DESC;"

echo "=== Stats Endpoint ==="
curl -s http://localhost:8000/stats | python3 -m json.tool

echo "=== History Endpoint ==="
curl -s http://localhost:8000/history | python3 -m json.tool

echo "=== Health Check ==="
curl -s http://localhost:8000/health | python3 -m json.tool

echo "=== ALL TESTS COMPLETE ==="
