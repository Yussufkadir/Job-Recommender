import requests
import time

API_BASE = "http://localhost:8000"

def test_auth_flow():
    email = f"test_{int(time.time())}@example.com"
    password = "Password123!"
    
    print(f"--- Testing Auth Flow for {email} ---")

    signup_url = f"{API_BASE}/auth/signup"
    signup_data = {"email": email, "password": password}
    print(f"POST {signup_url}")
    try:
        response = requests.post(signup_url, json=signup_data)
        print(f"Signup Status: {response.status_code}")
        print(f"Signup Body: {response.text}")
    except Exception as e:
        print(f"Signup failed: {e}")
        return

    if response.status_code != 200:
        print("Signup was not successful, skipping login test.")
        return

    login_url = f"{API_BASE}/auth/login"
    login_data = {"email": email, "password": password}
    print(f"\nPOST {login_url}")
    try:
        response = requests.post(login_url, json=login_data)
        print(f"Login Status: {response.status_code}")
        print(f"Login Body: {response.text}")
    except Exception as e:
        print(f"Login failed: {e}")

if __name__ == "__main__":
    test_auth_flow()
