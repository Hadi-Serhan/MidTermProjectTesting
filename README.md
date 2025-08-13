# MidTermProjectTesting — Test Plan & Runbook

> **Vaultwarden (Bitwarden-compatible) UI & API automated tests.**  
> Goal: verify basic availability, authenticated API behavior, and a stable end‑to‑end UI flow.

---

## 🧭 Table of Contents
- [Overview](#overview)
- [Scope — What We Test](#scope--what-we-test)
- [Strategy — How We Test](#strategy--how-we-test)
- [Success Criteria](#success-criteria)
- [Environments](#environments)
- [Test Data](#test-data)
- [How to Run](#how-to-run)
- [Reporting & Artifacts](#reporting--artifacts)
- [Risks & Notes](#risks--notes)

---

## Overview

This project contains **automated API and UI tests** for a self‑hosted Vaultwarden instance.

- **API tests** exercise public/health and authenticated endpoints using **API Key (client_credentials)** auth.
- **UI tests** drive Chrome through the login → create item → delete item flow.

---

## Scope — What We Test

### API

| Area | Endpoint | Expectation |
|---|---|---|
| Health | `GET /alive` | `200 OK` |
| Health | `GET /api/alive` | `200 OK` |
| Version | `GET /api/version` | `200 OK`; non-empty version-like string |
| Identity (auth) | `GET /api/accounts/profile` | `200 OK`; includes `email`, `id`, and a name field |
| Vault (auth) | `GET /api/ciphers` | `200 OK`; JSON object with `data` list |

### UI (flow-only)

1. Login (email → **Continue** → master password → dashboard)
2. Create a **Login** item (Name, Username, Password, URI)
3. Open item options (⋮) and **delete** the item
4. Dismiss any modals/overlays cleanly


---

## Strategy — How We Test

**API**
- `pytest` + `requests`
- Auth via **API Key (client_credentials)** generated in Web Vault → *Settings → Security → Keys*
- Validate HTTP 200 + minimal schema/keys

**UI**
- `pytest` + **Selenium** (Chrome via WebDriverManager)
- Robust CSS/XPath locators + **explicit waits** (`presence_of_element_located`, `element_to_be_clickable`)
- Overlay/backdrop handling
- Ephemeral data: create then delete the test item in the same run

**Architecture note:** Vaultwarden is Bitwarden‑compatible. Password grant requires client‑side KDF hashing (PBKDF2/Argon2id) after `/api/accounts/prelogin`. Using **API Key** keeps API automation simple while UI still exercises real login.

---

## Success Criteria

- ✅ API access token is obtained via API Key
- ✅ All targeted endpoints return **200 OK**
- ✅ `/api/version` returns a plausible, non-empty string
- ✅ `/api/accounts/profile` + `/api/ciphers` contain expected keys/shape
- ✅ UI scenario (login → create → delete) finishes **without Selenium exceptions**

---

## Environments

### Local (primary, recommended)

**Vaultwarden (Docker):**
```bash
docker rm -f vaultwarden 2>/dev/null
docker run -d --name vaultwarden   -p 3000:80   -v vw-data:/data   -e SIGNUPS_ALLOWED=false   vaultwarden/server:latest
```

**Runner:** Python 3.12 venv; Chrome (WebDriverManager).


---

## Test Data

- **API Key** — from Web Vault → *Settings → Security → Keys → View API key*
  ```bash
  export VAULTWARDEN_URL=http://localhost:3000
  export CLIENT_ID="user.xxxxx"
  export CLIENT_SECRET="yyyyy"
  ```

- **UI User** — dedicated test account (create once while `SIGNUPS_ALLOWED=true`, then set to `false`)

- **Item template (UI):**
  - Name: `Test Login Item <timestamp>`
  - Username: `testuser`
  - Password: `testpassword`
  - URI: `https://example.com`


---

## How to Run

```bash
# 1) Environment
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt || pip install pytest requests selenium webdriver-manager

# 2) Start Vaultwarden, then export API key envs
export VAULTWARDEN_URL=http://localhost:3000
export CLIENT_ID="user.xxxxx"
export CLIENT_SECRET="yyyyy"

# 3) Run API suite
pytest tests/api -v

# 4) Run UI suite 
pytest tests/ui -v
```


---

## Risks & Notes

- API keys are **rotatable** and **unique per server** — ensure the correct key for each environment

---

