import httpx
import time

BASE_URL = "http://127.0.0.1:8000/api"

def print_result(test_name, success, details=""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} - {test_name}")
    if details:
        print(f"   Details: {details}")

def run_tests():
    print("Starting User Management Verification...\n")
    
    suffix = int(time.time())
    user_data = {
        "username": f"user_mgmt_{suffix}",
        "email": f"user_mgmt_{suffix}@example.com",
        "firstname": "Test",
        "lastname": "User",
        "password": "password123"
    }

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        
        # 1. Register User
        print("--- 1. Setup: Register & Login ---")
        resp = client.post("/auth/register", json=user_data)
        if resp.status_code != 201:
            print(f"Registration failed: {resp.text}")
            return
        
        user_id = resp.json()["user"]["id"]
        print(f"Registered user ID: {user_id}")

        # Login
        resp = client.post("/auth/login", json={"username": user_data["username"], "password": user_data["password"]})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            return
        
        token = resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. List Users
        print("\n--- 2. List Users ---")
        resp = client.get("/users", headers=headers)
        success = resp.status_code == 200 and isinstance(resp.json(), list)
        print_result("List Users", success, f"Got {resp.status_code}" if not success else f"Count: {len(resp.json())}")
        
        # 3. Get User Details
        print("\n--- 3. Get User Details ---")
        resp = client.get(f"/users/{user_id}", headers=headers)
        success = resp.status_code == 200 and resp.json()["user"]["id"] == user_id
        print_result("Get User by ID", success, f"Got {resp.status_code}" if not success else "")
        
        # 4. Update User
        print("\n--- 4. Update User ---")
        update_data = {"firstname": "Updated", "lastname": "Name"}
        resp = client.put(f"/users/{user_id}", json=update_data, headers=headers)
        success = resp.status_code == 200
        print_result("Update User", success, f"Got {resp.status_code}" if not success else "")
        if success:
            data = resp.json()["user"]
            print_result("Firstname Updated", data["firstname"] == "Updated")
            print_result("Lastname Updated", data["lastname"] == "Name")
            
        # 5. Delete User
        print("\n--- 5. Delete User ---")
        resp = client.delete(f"/users/{user_id}", headers=headers)
        success = resp.status_code == 204
        print_result("Delete User", success, f"Got {resp.status_code}" if not success else "")
        
        # Verify Deletion
        resp = client.get(f"/users/{user_id}", headers=headers)
        success = resp.status_code == 404
        print_result("Verify User Deleted", success, f"Got {resp.status_code}" if not success else "")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"Error running tests: {e}")
