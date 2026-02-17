import requests  # type: ignore

URL = "http://localhost:8000/api/v1/auth/login"
<<<<<<< HEAD
payload = {
    "email": "user@example.com",
    "password": "password",  # pragma: allowlist secret
}  # nosec
=======
payload = {"email": "user@example.com", "password": "password"}  # pragma: allowlist secret # nosec
>>>>>>> 2b6c4e0f3e2bdec671123c59cab390bd0dde93d7

for i in range(6):
    r = requests.post(URL, json=payload, timeout=10)
    print(f"Login {i + 1}: {r.status_code}")

print("Now check Redis:")
print('redis-cli KEYS "session:USER_ID:*"')
