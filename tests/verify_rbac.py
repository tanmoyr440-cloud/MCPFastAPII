import httpx
import time
import sqlite3

BASE_URL = "http://127.0.0.1:8000/api"
DB_PATH = "ai_desk.db"

def print_result(test_name, success, details=""):
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status} - {test_name}")
    if details:
        print(f"   Details: {details}")

def make_admin(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE user SET user_role = 'admin' WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def run_tests():
    print("Starting RBAC Verification...\n")
    
    suffix = int(time.time())
    admin_data = {
        "username": f"admin_{suffix}",
        "email": f"admin_{suffix}@example.com",
        "firstname": "Admin",
        "lastname": "User",
        "password": "password123"
    }
    
    user_data = {
        "username": f"user_{suffix}",
        "email": f"user_{suffix}@example.com",
        "firstname": "Normal",
        "lastname": "User",
        "password": "password123"
    }

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        
        # 1. Register Users
        print("--- 1. Setup: Register Users ---")
        # Register Admin
        resp = client.post("/auth/register", json=admin_data)
        if resp.status_code != 201:
            print(f"Admin registration failed: {resp.text}")
            return
        admin_id = resp.json()["user"]["id"]
        
        # Register Normal User
        resp = client.post("/auth/register", json=user_data)
        if resp.status_code != 201:
            print(f"User registration failed: {resp.text}")
            return
        user_id = resp.json()["user"]["id"]
        
        # Promote Admin manually
        make_admin(admin_data["username"])
        print(f"Promoted {admin_data['username']} to admin")
        
        # Login Admin
        resp = client.post("/auth/login", json={"username": admin_data["username"], "password": admin_data["password"]})
        admin_token = resp.json().get("access_token")
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Login User
        resp = client.post("/auth/login", json={"username": user_data["username"], "password": user_data["password"]})
        user_token = resp.json().get("access_token")
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # 2. Test List Users
        print("\n--- 2. Test List Users ---")
        # User try list (Should Fail)
        resp = client.get("/users", headers=user_headers)
        success = resp.status_code == 403
        print_result("User Cannot List Users", success, f"Got {resp.status_code}" if not success else "")
        
        # Admin try list (Should Pass)
        resp = client.get("/users", headers=admin_headers)
        success = resp.status_code == 200
        print_result("Admin Can List Users", success, f"Got {resp.status_code}" if not success else "")
        
        # 3. Test Update User
        print("\n--- 3. Test Update User ---")
        # User try update self (Should Fail per strict requirement, or I implemented strict admin only)
        # My implementation restricts ALL updates to admin only.
        resp = client.put(f"/users/{user_id}", json={"firstname": "Hacked"}, headers=user_headers)
        success = resp.status_code == 403
        print_result("User Cannot Update Self", success, f"Got {resp.status_code}" if not success else "")
        
        # Admin try update user (Should Pass)
        resp = client.put(f"/users/{user_id}", json={"firstname": "AdminUpdated"}, headers=admin_headers)
        success = resp.status_code == 200
        print_result("Admin Can Update User", success, f"Got {resp.status_code}" if not success else "")
        
        # 4. Test Delete User
        print("\n--- 4. Test Delete User ---")
        # User try delete self (Should Fail)
        resp = client.delete(f"/users/{user_id}", headers=user_headers)
        success = resp.status_code == 403
        print_result("User Cannot Delete Self", success, f"Got {resp.status_code}" if not success else "")
        
        # Admin try delete user (Should Pass)
        resp = client.delete(f"/users/{user_id}", headers=admin_headers)
        success = resp.status_code == 204
        print_result("Admin Can Delete User", success, f"Got {resp.status_code}" if not success else "")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"Error running tests: {e}")
