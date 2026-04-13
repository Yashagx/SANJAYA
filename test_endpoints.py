import requests

try:
    print("Testing EC2 Direct (/health)...")
    res1 = requests.get("http://16.112.128.251:8000/health", timeout=5)
    print("EC2 Direct:", res1.status_code, res1.text)
except Exception as e:
    print("EC2 Direct Error:", e)

try:
    print("Testing API Gateway (/health)...")
    res2 = requests.get("https://nxvg8lbkrh.execute-api.ap-south-2.amazonaws.com/prod/health", timeout=5)
    print("API GW:", res2.status_code, res2.text)
except Exception as e:
    print("API GW Error:", e)

payload = {"text": "Assess vessel MV Chennai Star at Khor Fakkan, Hormuz transit in 48 hours to Rotterdam urgently"}
try:
    print("Testing API GW POST (/nlpredict)...")
    res3 = requests.post("https://nxvg8lbkrh.execute-api.ap-south-2.amazonaws.com/prod/nlpredict", json=payload, timeout=15)
    print("API GW POST:", res3.status_code)
except Exception as e:
    print("API GW POST Error:", e)
