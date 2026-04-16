import urllib.request
import json
import uuid

BASE_URL = "http://localhost:8100/auth"
headers = {"Content-Type": "application/json"}

# Use a new user to avoid MFA lockout or refresh issues if testing multiple times
new_user = f"yash_{uuid.uuid4().hex[:4]}"

try:
    req = urllib.request.Request(f"{BASE_URL}/register", json.dumps({"username":new_user,"email":f"{new_user}@gmail.com","password":"Test1234!","mfa_enabled":True}).encode(), headers)
    urllib.request.urlopen(req)
except Exception as e:
    pass

try:
    req = urllib.request.Request(f"{BASE_URL}/login", json.dumps({"username":new_user,"password":"Test1234!"}).encode(), headers)
    with urllib.request.urlopen(req) as res:
        login_data = json.loads(res.read().decode())
        print("Login Data:", login_data)
        
        mfa_challenge_id = login_data.get("challenge_id")
        mfa_code = login_data.get("debug_otp")
        print(f"Got challenge_id={mfa_challenge_id}, otp={mfa_code}")
        
    if mfa_code:
        req2 = urllib.request.Request(f"{BASE_URL}/verify-mfa", json.dumps({"challenge_id":mfa_challenge_id,"otp":mfa_code}).encode(), headers)
        with urllib.request.urlopen(req2) as res2:
            verify_data = json.loads(res2.read().decode())
            print("Verify MFA:", verify_data)
            
            token = verify_data.get("access_token")
            redirect = verify_data.get("redirect_url")
            print("Token:", token[:10], "..., Redirect:", redirect)
            
            req3 = urllib.request.Request(f"{BASE_URL}/me")
            req3.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req3) as res3:
                me_data = json.loads(res3.read().decode())
                print("Me Data Redirect config verification inside DB / response:", me_data)
                
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode())
