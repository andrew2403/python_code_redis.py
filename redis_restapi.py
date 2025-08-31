import requests
import json
import time

# Base API URL and credentials (replace with actual admin credentials)
BASE_URL = "https://re-cluster1.ps-redislabs.org:9443/v1"
AUTH = ("admin@rl.org", "JaDsJgL")

# Headers
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Disable SSL verification for self-signed certs (not for production use)
requests.packages.urllib3.disable_warnings()

# ----------------------------
# 1. Create a new database
# ----------------------------
db_payload = {
    "name": "exercise2-db",
    "memory_size": 2 * 1024**3,  # 2 GB
    "type": "redis"
}

print("📦 Creating database...")
db_resp = requests.post(f"{BASE_URL}/bdbs", auth=AUTH, json=db_payload, headers=headers, verify=False)
db_resp.raise_for_status()
db = db_resp.json()
db_id = db["uid"]
print(f"✅ Database created: {db['name']} (UID {db_id})")

# ----------------------------
# 2. Fetch valid roles (fallback-safe)
# ----------------------------
print("\n📥 Fetching valid roles...")
roles_api = f"{BASE_URL}/roles"
roles_resp = requests.get(roles_api, auth=AUTH, headers=headers, verify=False)

if roles_resp.status_code == 200:
    available_roles = [r["name"].lower() for r in roles_resp.json()]
    print(f"Available roles: {available_roles}")
else:
    print("⚠️ Could not fetch roles from API, using defaults...")
    available_roles = ["admin", "viewer", "cluster_member"]

# Role mapping: map requested labels to actual cluster roles
role_map = {
    "db_viewer": "viewer" if "viewer" in available_roles else available_roles[0],
    "db_member": "cluster_member" if "cluster_member" in available_roles else available_roles[0],
    "admin": "admin"
}

# ----------------------------
# 3. Create three new users
# ----------------------------
users = [
    {
        "email": "john.doe@example.com",
        "name": "John Doe",
        "role": role_map["db_viewer"],
        "auth_method": "regular",
        "password": "SuperStrongPass#2023!"
    },
    {
        "email": "mike.smith@example.com",
        "name": "Mike Smith",
        "role": role_map["db_member"],
        "auth_method": "regular",
        "password": "SuperStrongPass#2024!"
    },
    {
        "email": "cary.johnson@example.com",
        "name": "Cary Johnson",
        "role": role_map["admin"],
        "auth_method": "password",
        "password": "SuperStrongPass#2025!"
    }
]

print("\n👤 Creating users...")
user_api = f"{BASE_URL}/users"

# Fetch existing users first
existing_users_resp = requests.get(user_api, auth=AUTH, headers=headers, verify=False)
existing_users = []
if existing_users_resp.status_code == 200:
    try:
        data = existing_users_resp.json()
        if isinstance(data, dict) and "users" in data:
            existing_users = data["users"]
        elif isinstance(data, list):
            existing_users = data
    except ValueError:
        print("⚠️ Could not parse existing users JSON.")

existing_emails = {u.get("email") for u in existing_users if isinstance(u, dict)}

for u in users:
    if u["email"] in existing_emails:
        print(f"⏭️ Skipping {u['email']} (already exists)")
        continue

    res = requests.post(user_api, auth=AUTH, json=u, headers=headers, verify=False)
    if res.status_code != 200:
        print(f"❌ Error creating user {u['email']}: {res.status_code} {res.text}")
    else:
        print(f"✅ Created user: {u['name']} ({u['role']})")

# ----------------------------
# 4. List and display all users
# ----------------------------
print("\n📋 Listing all users...")
list_resp = requests.get(user_api, auth=AUTH, headers=headers, verify=False)
list_resp.raise_for_status()

try:
    users_data = list_resp.json()
    if isinstance(users_data, dict) and "users" in users_data:
        existing_users = users_data["users"]
    elif isinstance(users_data, list):
        existing_users = users_data
    else:
        existing_users = []
except ValueError:
    print("⚠️ Could not parse JSON, response was:", list_resp.text)
    existing_users = []

for u in existing_users:
    if isinstance(u, dict):
        print(f"- Name: {u.get('name')}, Role: {u.get('role')}, Email: {u.get('email')}")
    else:
        print(f"- {u}")

# ----------------------------
# 5. Delete the created database
# ----------------------------
status_url = f"{BASE_URL}/bdbs/{db_id}"
print(f"\n⌛ Waiting until database UID {db_id} is active before deletion...")
while True:
    status_resp = requests.get(status_url, auth=AUTH, headers=headers, verify=False)
    status_resp.raise_for_status()
    status = status_resp.json().get("status")
    print(f"   Current DB status = {status}")
    if status == "active":
        break
    time.sleep(5)

print(f"\n🗑️ Deleting database UID {db_id}...")
del_resp = requests.delete(status_url, auth=AUTH, verify=False)

if del_resp.status_code == 409:
    print("⚠️ Conflict deleting DB, retrying with force...")
    del_resp = requests.delete(f"{status_url}?force=true", auth=AUTH, verify=False)

del_resp.raise_for_status()
print("✅ Database deleted.")
