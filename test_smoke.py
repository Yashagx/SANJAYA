import urllib.request
import json

register_url = "http://localhost:8100/auth/register"
login_url = "http://localhost:8100/auth/login"

headers = {"Content-Type": "application/json"}

# Register
try:
    req = urllib.request.Request(register_url, json.dumps({"username":"yash","email":"ya8009672@gmail.com","password":"Test1234!","mfa_enabled":True}).encode(), headers)
    with urllib.request.urlopen(req) as response:
        print("Register:", response.read().decode())
except urllib.error.HTTPError as e:
    print("Register failed:", e.code, e.read().decode())

# Login
try:
    req = urllib.request.Request(login_url, json.dumps({"username":"yash","password":"Test1234!"}).encode(), headers)
    with urllib.request.urlopen(req) as response:
        info = json.loads(response.read().decode())
        print("Login OK:", list(info.keys()))
        if "access_token" in info:
            print("Access Token present")
except urllib.error.HTTPError as e:
    print("Login failed:", e.code, e.read().decode())
