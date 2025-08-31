import requests
import json

# Base API URL and credentials (replace with actual admin credentials)
BASE_URL = "https://re-cluster1.ps-redislabs.org:9443/v1"
AUTH = ("admin@yourcompany.com", "yourpassword")

# Disable SSL verification for self-signed certs (not recommended for production)
requests.packages.urllib3.disable_warnings()

# 1. Create a new database
db_payload = {
    "name": "exercise2-db",
    "memory_size": 2 * 1024**3,  # 2 GB
    "type": "redis"
}
print("Creating database...")
db_resp = requests.post(f"{BASE_URL}/bdbs", auth=AUTH, json=db_payload, headers={"Content-Type": "application/json"}, verify=False)
db_resp.raise_for_status()
db = db_resp.json()
db_id = db["uid"]
print(f"Created database: {db['name']} (UID {db_id})")

# 2. Create three new users
users = [
    {"email": "john.doe@example.com", "password": "Passw0rd!1", "name": "John Doe", "role": "db_viewer"},
    {"email": "mike.smith@example.com", "password": "Passw0rd!2", "name": "Mike Smith", "role": "db_member"},
    {"email": "cary.johnson@example.com", "password": "Passw0rd!3", "name": "Cary Johnson", "role": "admin"}
]
print("\nCreating users...")
for u in users:
    res = requests.post(f"{BASE_URL}/users", auth=AUTH, json=u, headers={"Content-Type": "application/json"}, verify=False)
    res.raise_for_status()
    print(f"  Created user: {u['name']} ({u['role']})")

# 3. List and display all users
print("\nListing all users...")
list_resp = requests.get(f"{BASE_URL}/users", auth=AUTH, headers={"Accept": "application/json"}, verify=False)
list_resp.raise_for_status()
for u in list_resp.json():
    print(f"- Name: {u['name']}, Role: {u['role']}, Email: {u['email']}")

# 4. Delete the created database
print(f"\nDeleting database UID {db_id}...")
del_resp = requests.delete(f"{BASE_URL}/bdbs/{db_id}", auth=AUTH, verify=False)
del_resp.raise_for_status()
print("Database deleted.")
