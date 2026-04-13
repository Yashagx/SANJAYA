import requests

payload = {"text":"Assess vessel MV Chennai Star at Khor Fakkan, Hormuz transit in 48 hours to Rotterdam urgently"}
res = requests.post("http://16.112.128.251:8000/nlpredict", json=payload)
print(res.status_code)
print(res.text)
