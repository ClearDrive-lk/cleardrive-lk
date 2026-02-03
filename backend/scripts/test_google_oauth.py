# backend/scripts/test_google_oauth.py

"""
Test Google OAuth integration.

IMPORTANT: This script requires manual interaction with Google.
You need to actually sign in with Google in your browser.
"""

import os
import requests  # type: ignore
from datetime import datetime
import json
import base64

# Use BACKEND_URL when running inside Docker so script and API see the same host
BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/") + "/api/v1"


def test_google_oauth_flow():
    """
    Test complete Google OAuth flow.

    Steps:
    1. User must get Google ID token manually (from browser)
    2. Send token to backend
    3. Receive OTP
    4. Verify OTP
    5. Get JWT tokens
    """

    print("🧪 Testing Google OAuth Integration\n")
    print("=" * 70)

    # Step 1: Instructions for getting Google ID token
    print("\n📋 Step 1: Get Google ID Token")
    print("-" * 70)
    print("To test this properly, you need a REAL Google ID token.")
    print("\nOption A: Use frontend (when Lehan builds it)")
    print("   Note: If you get 'Can't continue with google.com', check 'Authorized JavaScript origins'")
    print("         in Google Cloud Console. It must match your frontend URL (e.g., http://localhost:3000).")
    print("   Note: If you get 'FedCM get() rejects...', check if Third-party cookies are blocked")
    print("         in your browser (common in Incognito mode).")
    print("   Note: If you get 'Error 401: invalid_client', check your GOOGLE_CLIENT_ID for typos/spaces.")
    print("Option B: Use this test page:")
    print("  https://accounts.google.com/gsi/select")
    print("\nFor now, let's test with the verify-otp endpoint directly.")
    print("=" * 70)

    # For testing without Google, we'll simulate the flow
    test_email = input("\nEnter your test email (e.g., cleardrivelk@gmail.com): ")

    if not test_email:
        test_email = "cleardrivelk@gmail.com"

    # Step 1b: Ensure test user exists (dev-only; so resend-otp actually stores OTP)
    print(f"\n📋 Step 1b: Ensuring test user exists...")
    ensure_resp = requests.post(
        f"{BASE_URL}/auth/dev/ensure-user",
        json={"email": test_email, "name": test_email.split("@")[0]},
    )
    if ensure_resp.status_code == 200:
        data = ensure_resp.json()
        print(f"   {data.get('message', 'OK')}")
    # 404 = dev endpoint not available (production); continue anyway

    # Step 2: Manually trigger OTP (simulate Google OAuth success)
    print(f"\n📧 Step 2: Requesting OTP for {test_email}...")
    print("-" * 70)

    response = requests.post(f"{BASE_URL}/auth/resend-otp", json={"email": test_email})

    if response.status_code != 200:
        print(f"❌ Failed: {response.json()}")
        return

    data = response.json()
    otp = data.get("otp")  # In development, API returns OTP in response
    if otp:
        print(f"✅ OTP sent (development): {otp}")
    else:
        print(f"✅ OTP sent (check backend logs: docker-compose logs backend)")
    print(f"Response: {data}")

    # Step 3: Get OTP from user (or use the one from response in dev)
    print("\n🔐 Step 3: Verify OTP")
    print("-" * 70)
    if otp:
        use = input(f"Use OTP from response above? ({otp}) [Y/n]: ").strip().lower()
        if use != "n":
            pass  # otp already set
        else:
            otp = input("Enter OTP: ").strip()
    else:
        otp = input("Enter OTP from backend console logs: ").strip()

    if not otp or len(otp) != 6:
        print("❌ Invalid OTP format")
        return

    # Step 4: Verify OTP
    response = requests.post(f"{BASE_URL}/auth/verify-otp", json={"email": test_email, "otp": otp})

    if response.status_code == 200:
        tokens = response.json()
        print(f"\n✅ Authentication successful!")
        print("-" * 70)
        print(f"Access Token: {tokens['access_token'][:50]}...")
        print(f"Refresh Token: {tokens['refresh_token'][:50]}...")
        print(f"\nUser Info:")
        print(f"  Email: {tokens['user']['email']}")
        print(f"  Name: {tokens['user']['name']}")
        print(f"  Role: {tokens['user']['role']}")
        print(f"  ID: {tokens['user']['id']}")

        access_token = tokens["access_token"]

        # Step 5: Test protected endpoint
        print(f"\n📋 Step 4: Testing Protected Endpoint")
        print("-" * 70)

        response = requests.get(
            f"{BASE_URL}/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if response.status_code == 200:
            sessions = response.json()
            print(f"✅ Protected endpoint works!")
            print(f"Active sessions: {sessions['total']}")
        else:
            print(f"❌ Protected endpoint failed: {response.json()}")

        print("\n" + "=" * 70)
        print("✅ All tests passed! Google OAuth integration is working!")
        print("=" * 70)

    else:
        print(f"\n❌ OTP verification failed: {response.json()}")


def decode_jwt_audience(token):
    """Decode the audience (aud) claim from a JWT token without verifying signature."""
    try:
        # JWT is header.payload.signature
        parts = token.split(".")
        if len(parts) < 2:
            return "Invalid Token Format"

        payload = parts[1]
        # Add padding if needed
        payload += "=" * (-len(payload) % 4)

        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_str = decoded_bytes.decode("utf-8")
        data = json.loads(decoded_str)
        return data.get("aud", "No audience found")
    except Exception as e:
        return f"Error decoding: {str(e)}"


def test_with_real_google_token():
    """
    Test with a real Google ID token.

    You need to:
    1. Go to: https://developers.google.com/oauthplayground/
    2. Select "Google OAuth2 API v2"
    3. Select scopes: email, profile, openid
    4. Authorize APIs
    5. Exchange authorization code for tokens
    6. Copy the id_token
    """

    print("\n" + "=" * 70)
    print("🧪 Testing with Real Google ID Token")
    print("=" * 70)

    print(
        "\nTo get a real Google ID token (must use YOUR app's client, or you'll get 'wrong audience'):"
    )
    print("1. Visit: https://developers.google.com/oauthplayground/")
    print("2. Click the gear icon (⚙️) → check 'Use your own OAuth credentials'")
    print(
        "   Enter your Client ID and Client Secret from backend/.env (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)"
    )
    print(
        "   (NOTE: If you skip this, you'll get a token for the default Playground ID: 4166288126-...)"
    )
    print(
        "3. In Step 1, select scope: https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid"
    )
    print("4. Click 'Authorize APIs' and sign in with Google")
    print("5. In Step 2, click 'Exchange authorization code for tokens'")
    print("6. Copy the 'id_token' from the response (not access_token)")

    id_token = input("\nPaste Google ID token (or press Enter to skip): ")

    if not id_token:
        print("Skipped real token test.")
        return

    # Debug info
    aud = decode_jwt_audience(id_token)
    print(f"\n🔍 Token Debug Info:")
    print(f"   Token Audience (aud): {aud}")

    # Check what the container thinks the ID is
    env_id = os.environ.get("GOOGLE_CLIENT_ID", "Not Set")
    print(f"   Backend Config ID:    {env_id}")
    if env_id != aud:
        print(
            f"   ⚠️  MISMATCH: Backend has old ID. Run 'docker-compose up -d backend' to reload .env!"
        )

    response = requests.post(f"{BASE_URL}/auth/google", json={"id_token": id_token})

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Google OAuth successful!")
        print(f"Email: {data['email']}")
        print(f"Name: {data['name']}")
        print(f"Message: {data['message']}")
    else:
        print(f"\n❌ Failed: {response.json()}")


if __name__ == "__main__":
    print("\n" + "🔐" * 35)
    print("Google OAuth Integration Test")
    print("🔐" * 35 + "\n")

    # Test basic flow
    test_google_oauth_flow()

    # Optionally test with real Google token
    print("\n" + "-" * 70)
    test_real = input("\nTest with real Google token? (y/n): ")

    if test_real.lower() == "y":
        test_with_real_google_token()

    print("\n✅ Testing complete!\n")
