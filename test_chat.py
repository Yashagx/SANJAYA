import json, subprocess, sys

r = subprocess.run([
    'curl', '-s', '-X', 'POST', 'http://localhost:8000/chat',
    '-H', 'Content-Type: application/json',
    '-d', json.dumps({'message': 'What are the riskiest routes in my uploaded company data?'})
], capture_output=True, text=True)

d = json.loads(r.stdout)
print('BRAHMA:', str(d.get('response', ''))[:300])
