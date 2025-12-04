import httpx
import time

BASE_URL = "http://127.0.0.1:8000/api"

def print_result(test_name, success, details=""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} - {test_name}")
    if details:
        print(f"   Details: {details}")

def run_tests():
    print("Starting Registration Role Verification...\n")
    
    suffix = int(time.time())
    
    # 1. Register as Admin
    print("--- 1. Register as Admin ---")
    admin_data = {
        "username": f"reg_admin_{suffix}",
        "email": f"reg_admin_{suffix}@example.com",
        "firstname": "Reg",
        "lastname": "Admin",
        "password": "password123",
        "user_role": "admin"
    }
    
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        resp = client.post("/auth/register", json=admin_data)
        if resp.status_code != 201:
            print(f"Registration failed: {resp.text}")
            return
            
        user = resp.json()["user"]
        success = user["user_role"] == "admin"
        print_result("Register with Admin Role", success, f"Role: {user['user_role']}")
        
        # 2. Register as User (Default)
        print("\n--- 2. Register as User (Explicit) ---")
        user_data = {
            "username": f"reg_user_{suffix}",
            "email": f"reg_user_{suffix}@example.com",
            "firstname": "Reg",
            "lastname": "User",
            "password": "password123",
            "user_role": "user"
        }
        
        resp = client.post("/auth/register", json=user_data)
        if resp.status_code != 201:
            print(f"Registration failed: {resp.text}")
            return
            
        user = resp.json()["user"]
        success = user["user_role"] == "user"
        print_result("Register with User Role", success, f"Role: {user['user_role']}")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"Error running tests: {e}")
