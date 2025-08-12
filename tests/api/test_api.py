import requests
import uuid

VAULTWARDEN_URL = "http://localhost:3000"
CLIENT_ID = "user.eefb6ad6-05e4-4c1a-b3a9-06bf642ca497"
CLIENT_SECRET = "SQoIWxFcuojXfiXnVmpSnot9uebYvn"
ORG_ID = "MidTermProject"

def get_access_token():
    data = {
        "grant_type": "client_credentials",
        "scope": "api",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "deviceIdentifier": str(uuid.uuid4()),  # Required device identifier
        "deviceType": "1",  # CLI client type
        "deviceName": "Python API Client"
    }

    response = requests.post(f"{VAULTWARDEN_URL}/identity/connect/token", headers={
        "Content-Type": "application/x-www-form-urlencoded"
    }, data=data)
    response.raise_for_status()
    return response.json()["access_token"]


def make_api_request(endpoint):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{VAULTWARDEN_URL}/api{endpoint}", headers=headers)
    response.raise_for_status()
    return response.json()


############ TESTING API ENDPOINTS ############

# Health Checks
def test_health_alive():
    r = requests.get("http://localhost:3000/alive")
    assert r.status_code == 200
# API Alive Check
def test_health_api_alive():
    r = requests.get(f"{VAULTWARDEN_URL}/api/alive")
    assert r.status_code == 200
    
# Version Check
def test_version():
    r = requests.get(f"{VAULTWARDEN_URL}/api/version", timeout=5)
    assert r.status_code == 200

    ver = None
    data = r.json()
    if isinstance(data, dict):
        ver = data.get("version") or data.get("serverVersion")
    elif isinstance(data, str):
        ver = data.strip().strip('"')

    if not ver:
        ver = (r.text or "").strip().strip('"')

    assert ver, f"Could not parse version from response: {r.text}"
    assert any(ch.isdigit() for ch in ver), f"Version doesn't look right: {ver}"
    
# Account Profile
def test_account_profile():
    data = make_api_request("/accounts/profile")
    assert isinstance(data, dict), f"Expected JSON object, got {type(data).__name__}"
    assert "email" in data, "Profile response missing 'email'"
    assert "id" in data, "Profile response missing 'id'"
    assert "name" in data or "userName" in data, "Profile missing a name field"

# List Ciphers
def test_list_ciphers():
    data = make_api_request("/ciphers") 
    assert isinstance(data, dict), "Expected JSON object from /ciphers"
    assert "data" in data, "Missing 'data' key in /ciphers response"
    assert isinstance(data["data"], list), "'data' is not a list"