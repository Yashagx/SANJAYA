import sys, json, requests

payload = {"text":"Assess vessel MV Chennai Star at Khor Fakkan, Hormuz transit in 48 hours to Rotterdam urgently"}
try:
    res = requests.post("http://16.112.128.251:8000/nlpredict", json=payload)
    d = res.json()
except Exception as e:
    print("API Error:", e)
    if 'res' in locals(): print(res.text)
    sys.exit(1)

ev=d.get('evidence',{})
ba=d.get('bedrock_analysis',{})
ae=d.get('agent_enrichment',{})
print('=== SANJAYA FULL VALIDATION ===')
print(f'RS: {d.get("risk_score")} | {d.get("risk_level")}')
print(f'Parsed: {d.get("parsed_payload",{}).get("origin")} -> {d.get("parsed_payload",{}).get("destination")}')
print()
print('VAYU evidence points:', len(ev.get('weather',{}).get('evidence_points',[])))
for ep in ev.get('weather',{}).get('evidence_points',[])[:2]:
    print(f'  - {ep.get("parameter", ep.get("metric", "?"))} : {ep.get("value","?")}')
print()
print('SANCHAR evidence points:', len(ev.get('geopolitics',{}).get('evidence_points',[])))
for ep in ev.get('geopolitics',{}).get('evidence_points',[])[:2]:
    print(f'  - {ep.get("headline","?")[:60]}')
print()
print('NIDHI evidence points:', len(ev.get('ml',{}).get('evidence_points',[])))
for ep in ev.get('ml',{}).get('evidence_points',[])[:2]:
    print(f'  - {ep.get("feature","?")} : SHAP={ep.get("shap_contribution","?")}')
print()
print('BRAHMA enrichment keys:', list(ae.keys()))
for agent, info in ae.items():
    print(f'  {agent}: {str(info.get("narrative",""))[:80]}')
print()
print('Bedrock confidence:', ba.get('confidence_score'),'%')
print('Computation steps:', len(ba.get('computation_steps',[])))
print('Scenarios:', [s.get('calculated_rs') for s in ba.get('alternative_scenarios',[])])
print('Verdict:', str(ba.get('brahma_verdict',''))[:100])
