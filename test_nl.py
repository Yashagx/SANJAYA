import json, subprocess, sys

r = subprocess.run([
    'curl', '-s', '-X', 'POST', 'http://localhost:8000/nlpredict',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({'text': 'Assess vessel MV Chennai Star at Khor Fakkan planning Hormuz transit in 48 hours to Rotterdam urgently'})
], capture_output=True, text=True)

d = json.loads(r.stdout)
ba = d.get('bedrock_analysis', {})
print('RS:', d.get('risk_score'), d.get('risk_level'))
print('Confidence:', ba.get('confidence_score'), '%')
print('Verdict:', str(ba.get('brahma_verdict', ''))[:100])
print('Comp steps:', len(ba.get('computation_steps', [])))
print('Scenarios:')
for s in ba.get('alternative_scenarios', []):
    name = s.get('name', '?')
    rs = s.get('calculated_rs', '?')
    print(f'  {name}: RS={rs}')
print('Agent insights:', len(ba.get('agent_insights', [])))
