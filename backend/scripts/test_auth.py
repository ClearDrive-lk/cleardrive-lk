# backend/scripts/test_auth.py

"""
Test authentication flow in development mode.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_auth_flow():
    """Test the complete auth flow."""
    
    print("🧪 Testing Authentication Flow\n")
    
    # Step 1: Simulate Google OAuth (skip for now, use direct OTP)
    print("Step 1: Skipping Google OAuth (need real credentials)")
    
    # For testing, let's create a user directly and generate OTP
    # In production, this would come from Google OAuth
    
    test_email = "yasindu.20232969@iit.ac.lk"
    
    # Step 2: Request OTP resend (this will generate OTP for existing user)
    print(f"Step 2: Requesting OTP for {test_email}...")
    
    response = requests.post(
        f"{BASE_URL}/auth/resend-otp",
        json={"email": test_email}
    )
    
    print(f"Response: {response.status_code}")
    print(f"Body: {response.json()}\n")
    
    # Check console logs for OTP (only in development)
    otp = input("Enter OTP from console logs: ")
    
    # Step 3: Verify OTP
    print(f"Step 3: Verifying OTP...")
    
    response = requests.post(
        f"{BASE_URL}/auth/verify-otp",
        json={
            "email": test_email,
            "otp": otp
        }
    )
    
    if response.status_code == 200:
        tokens = response.json()
        print(f"✅ Authentication successful!")
        print(f"Access Token: {tokens['access_token'][:50]}...")
        print(f"Refresh Token: {tokens['refresh_token'][:50]}...")
        print(f"User: {tokens['user']}\n")
        
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
        
        # Step 4: Test protected endpoint (get sessions)
        print("Step 4: Testing protected endpoint (Get Sessions)...")
        
        response = requests.get(
            f"{BASE_URL}/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            sessions = response.json()
            print(f"✅ Sessions retrieved: {sessions['total']} active sessions\n")
        else:
            print(f"❌ Failed to get sessions: {response.json()}\n")
        
        # Step 5: Test token refresh
        print("Step 5: Testing token refresh...")
        
        response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        if response.status_code == 200:
            new_tokens = response.json()
            print(f"✅ Tokens refreshed successfully!")
            print(f"New Access Token: {new_tokens['access_token'][:50]}...\n")
        else:
            print(f"❌ Token refresh failed: {response.json()}\n")
        
        # Step 6: Test logout
        print("Step 6: Testing logout...")
        
        response = requests.post(
            f"{BASE_URL}/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code == 200:
            print(f"✅ Logged out successfully!\n")
        else:
            print(f"❌ Logout failed: {response.json()}\n")
    
    else:
        print(f"❌ OTP verification failed: {response.json()}\n")


if __name__ == "__main__":
    test_auth_flow()