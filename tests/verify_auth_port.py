import httpx
import time

BASE_URL = "http://127.0.0.1:8000/api/auth"

def print_result(test_name, success, details=""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} - {test_name}")
    if details:
        print(f"   Details: {details}")

def run_tests():
    print("Starting HackItWell Auth Verification...\n")
    
    suffix = int(time.time())
    user_data = {
        "username": f"port_user_{suffix}",
        "email": f"port_user_{suffix}@example.com",
        "password": "password123",
        "firstname": "Port",
        "lastname": "User"
    }

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        
        # 1. Register User
        print("--- 1. Registration ---")
        resp = client.post("/register", json=user_data)
        success = resp.status_code == 201
        print_result("Register User", success, f"Got {resp.status_code}: {resp.text}" if not success else "")
        
        if success:
            data = resp.json()
            print_result("Register Response Wrapped", "user" in data)
            print_result("No Token in Register", "access_token" not in data)
            if "user" in data:
                print_result("Register Firstname Correct", data["user"].get("firstname") == "Port")
        
        # 2. Login User
        print("\n--- 2. Login ---")
        resp = client.post("/login", json={"username": user_data["username"], "password": user_data["password"]})
        success = resp.status_code == 200
        print_result("Login User", success, f"Got {resp.status_code}: {resp.text}" if not success else "")
        token = resp.json().get("access_token") if success else None
        
        # 3. Verify /me Wrapper
        print("\n--- 3. Verify Response Wrapper ---")
        if token:
            resp = client.get("/me", headers={"Authorization": f"Bearer {token}"})
            success = resp.status_code == 200
            print_result("Get /me", success, f"Got {resp.status_code}" if not success else "")
            if success:
                data = resp.json()
                user_obj = data.get("user")
                print_result("Response Wrapped in 'user'", user_obj is not None)
                if user_obj:
                    print_result("Firstname Correct", user_obj.get("firstname") == "Port")
                    print_result("Locked Field Present", "locked" in user_obj)
        
        # 4. Account Locking
        print("\n--- 4. Account Locking ---")
        print("Attempting 5 failed logins...")
        for i in range(5):
            resp = client.post("/login", json={"username": user_data["username"], "password": "wrongpassword"})
            print_result(f"Failed Attempt {i+1}", resp.status_code == 401)
            
        # 6th attempt with CORRECT password should fail
        print("Attempting login with CORRECT password after locking...")
        resp = client.post("/login", json={"username": user_data["username"], "password": user_data["password"]})
        success = resp.status_code == 401 and "locked" in resp.text
        print_result("Locked User Cannot Login", success, f"Got {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"Error running tests: {e}")
