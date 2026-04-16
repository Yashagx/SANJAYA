import json
import time
import uuid
import requests

base = 'http://127.0.0.1:8100'
uid = uuid.uuid4().hex[:8]
username = f'user_{uid}'
email = f'{username}@example.com'
password = 'SecurePass123!'

print('REGISTER...')
r = requests.post(f'{base}/auth/register', json={
    'username': username,
    'email': email,
    'password': password,
    'role': 'user',
    'mfa_enabled': True,
}, timeout=20)
print('register status:', r.status_code)
print('register body:', r.text)
r.raise_for_status()

print('LOGIN...')
r = requests.post(f'{base}/auth/login', json={
    'username': username,
    'password': password,
}, timeout=20)
print('login status:', r.status_code)
print('login body:', r.text)
r.raise_for_status()
login_json = r.json()
if not login_json.get('mfa_required'):
    raise RuntimeError('Expected MFA pending response')
challenge_id = login_json['challenge_id']
otp = login_json.get('debug_otp')
if not otp:
    raise RuntimeError('DEBUG_OTP_IN_RESPONSE not enabled or OTP missing')

print('VERIFY MFA...')
r = requests.post(f'{base}/auth/verify-mfa', json={
    'challenge_id': challenge_id,
    'otp': otp,
}, timeout=20)
print('verify status:', r.status_code)
print('verify body:', r.text)
r.raise_for_status()
tokens = r.json()
access_token = tokens['access_token']
refresh_token = tokens['refresh_token']

print('ME...')
r = requests.get(
    f'{base}/auth/me',
    headers={'Authorization': f'Bearer {access_token}'},
    timeout=20,
)
print('me status:', r.status_code)
print('me body:', r.text)
r.raise_for_status()

print('REFRESH...')
r = requests.post(f'{base}/auth/refresh', json={'refresh_token': refresh_token}, timeout=20)
print('refresh status:', r.status_code)
print('refresh body:', r.text)
r.raise_for_status()

print('LOGOUT...')
r = requests.post(f'{base}/auth/logout', json={'refresh_token': refresh_token}, timeout=20)
print('logout status:', r.status_code)
print('logout body:', r.text)
r.raise_for_status()

print('SMOKE_TEST_OK')