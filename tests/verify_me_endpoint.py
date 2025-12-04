import httpx
import time

BASE_URL = "http://127.0.0.1:8000/api/auth"

def run_test():
    print("Testing /me endpoint...")
    
    suffix = int(time.time())
    user_data = {
        "username": f"me_test_{suffix}",
        "email": f"me_test_{suffix}@example.com",
        "firstname": "Me",
        "lastname": "Test",
        "password": "password123"
    }

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Register
        print("Registering...")
        resp = client.post("/register", json=user_data)
        if resp.status_code != 201:
            print(f"Registration failed: {resp.text}")
            return

        # 2. Login
        print("Logging in...")
        resp = client.post("/login", json={"username": user_data["username"], "password": user_data["password"]})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        
        token = resp.json().get("access_token")
        print(f"Got token: {token[:10]}...")

        # 3. Get Me
        print("Calling /me...")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/me", headers=headers)
        
        if resp.status_code == 200:
            print("SUCCESS: /me returned 200")
            print(resp.json())
        else:
            print(f"FAILURE: /me returned {resp.status_code}")
            print(resp.text)

if __name__ == "__main__":
    run_test()
