import json, subprocess, sys

r = subprocess.run([
    'curl', '-s', '-X', 'POST', 'http://localhost:8000/upload/history',
    '-F', 'file=@/tmp/test_history.csv'
], capture_output=True, text=True)

d = json.loads(r.stdout)
a = d.get('analysis', {})
print('Status:', d.get('status'))
print('Summary:', str(a.get('dataset_summary', ''))[:100])
print('Records:', a.get('total_records'))
print('Delay rate:', a.get('delay_rate_percent'), '%')
print('Insights:', len(a.get('key_insights', [])))
print('Calibration:', a.get('risk_calibration', {}).get('calibration_confidence'))
