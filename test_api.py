import os
import django
import json
import urllib.request
import urllib.error

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
user, created = User.objects.get_or_create(username='testuser123', email='test12345@example.com')
if created:
    user.set_password('testpassword123')
user.is_active = True
user.save()

BASE_URL = "http://127.0.0.1:8000/api"

def make_request(url, payload=None, headers=None):
    if headers is None:
        headers = {}
    headers['Content-Type'] = 'application/json'
    
    data = json.dumps(payload).encode('utf-8') if payload else None
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

# Login
login_data = {
    "username": "testuser123",
    "password": "testpassword123"
}
status, text = make_request(f"{BASE_URL}/login/", login_data)
print("Login Status:", status)
token = json.loads(text).get('access')

# Send Transfer
headers = {
    "Authorization": f"Bearer {token}"
}
payload = {
    "recipient_email": "zarkhman122@gmail.com",
    "subject": "Fund Receive",
    "token": "USDC",
    "amount": 50000,
    "message": "Kindly receive your amount"
}
status, text = make_request(f"{BASE_URL}/transfers/send/", payload, headers)
print("Transfer Status:", status)
print("Transfer Response:", text)
