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
- **UI tests** drive Chrome in **headless** mode through the login → create item → delete item flow.
- UI tests are **flow-only** (no explicit `assert` statements). We rely on **explicit waits**; if elements are missing or not clickable in time, Selenium raises and the test fails.

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

> **Note:** No explicit assertions. The scenario **passes** if it completes without Selenium exceptions/timeouts.

---

## Strategy — How We Test

**API**
- `pytest` + `requests`
- Auth via **API Key (client_credentials)** generated **per server** in Web Vault → *Settings → Security → Keys*
- Validate HTTP 200 + minimal schema/keys

**UI**
- `pytest` + **Selenium** (Chrome headless via WebDriverManager)
- Robust CSS/XPath locators + **explicit waits** (`presence_of_element_located`, `element_to_be_clickable`)
- Overlay/backdrop handling (Angular CDK) and scroll-into-view/JS-click fallbacks
- Ephemeral data: create then delete the test item in the same run

**Architecture note (justification):** Vaultwarden is Bitwarden‑compatible. Password grant requires client‑side KDF hashing (PBKDF2/Argon2id) after `/api/accounts/prelogin`. Using **API Key** keeps API automation simple while UI still exercises real login.

---

## Success Criteria

- ✅ API access token is obtained via API Key
- ✅ All targeted endpoints return **200 OK**
- ✅ `/api/version` returns a plausible, non-empty string
- ✅ `/api/accounts/profile` + `/api/ciphers` contain expected keys/shape
- ✅ UI scenario (login → create → delete) finishes **without Selenium exceptions**
- ✅ Two consecutive runs pass on a clean environment

---

## Environments

### Local (primary, recommended)

**Vaultwarden (Docker):**
```bash
docker rm -f vaultwarden 2>/dev/null
docker run -d --name vaultwarden   -p 3000:80   -v vw-data:/data   -e SIGNUPS_ALLOWED=false   vaultwarden/server:latest
```

**Runner:** Python 3.12 venv; Chrome headless (WebDriverManager).

### EC2 (optional)

- Same container flags (`-p 3000:80`, `-v vw-data:/data`)
- Access Web Vault via SSH tunnel:
  ```bash
  ssh -i <key.pem> -N -L 3000:localhost:3000 ubuntu@<EC2-IP>
  ```
- **Important:** API keys are **per server** — generate a separate key on EC2.

---

## Test Data

- **API Key (per server)** — from Web Vault → *Settings → Security → Keys → View API key*
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

> Do **not** commit secrets. Keep them in env vars or a local `.env` that is git‑ignored.

---

## How to Run

```bash
# 1) Environment
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt || pip install pytest requests selenium webdriver-manager

# 2) Start Vaultwarden (see Environments section), then export API key envs
export VAULTWARDEN_URL=http://localhost:3000
export CLIENT_ID="user.xxxxx"
export CLIENT_SECRET="yyyyy"

# 3) Run API suite
pytest tests/api -v

# 4) Run UI suite (headless; flow-only)
pytest tests/ui -v
```

**Handy tips**
```bash
# If Chrome gets stuck:
pkill -f chrome || true
rm -f ~/.config/google-chrome/Singleton* 2>/dev/null || true

# Fresh local data (DANGER: deletes vault data)
docker rm -f vaultwarden && docker volume rm vw-data
```

---

## Reporting & Artifacts

Default: console output + exit code via `pytest -v`.

CI‑friendly (optional):
```bash
pytest -v   --junitxml=reports/junit.xml   --html=reports/report.html --self-contained-html
```
Keep `docker logs -f vaultwarden` visible during runs for quick triage.

---

## Risks & Notes

- API keys are **rotatable** and **unique per server** — ensure the correct key for each environment
- UI selectors may change across Vaultwarden releases; overlay handling reduces flakiness
- If password grant becomes necessary, implement `/api/accounts/prelogin` + client‑side KDF hashing

---

### Suggested `.gitignore` (snippet)

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
.env
.env.*

# Test outputs
.pytest_cache/
reports/
screenshots/
*.log

# IDE/OS
.vscode/
.idea/
.DS_Store
Thumbs.db
```

---

### Quick .env (git‑ignored)
```bash
VAULTWARDEN_URL=http://localhost:3000
CLIENT_ID=user.xxxxx
CLIENT_SECRET=yyyyy
```
Load with:
```bash
set -a; source .env; set +a
```
