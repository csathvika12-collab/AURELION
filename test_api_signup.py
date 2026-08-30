import requests
import json

url = "http://localhost:8000/api/auth/signup"
headers = {"Content-Type": "application/json"}
data = {
    "email": "api_test_user@example.com",
    "password": "securepassword",
    "full_name": "API Test User"
}

try:
    response = requests.post(url, json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
