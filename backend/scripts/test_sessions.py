import requests

URL = "http://localhost:8000/api/v1/auth/login"
payload = {"email": "user@example.com", "password": "password"}  # pragma: allowlist secret # nosec

for i in range(6):
    r = requests.post(URL, json=payload, timeout=10)
    print(f"Login {i + 1}: {r.status_code}")

print("Now check Redis:")
print('redis-cli KEYS "session:USER_ID:*"')
