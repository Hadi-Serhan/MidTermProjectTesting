# tests/common/envtools.py
import os

import requests
from dotenv import find_dotenv, load_dotenv

# Load .env once for all tests
load_dotenv(find_dotenv(), override=False)


def pick_url() -> str:
    """Resolve VAULTWARDEN_URL from env/.env, or probe common ports."""
    # 1) Most explicit wins
    url = os.getenv("VAULTWARDEN_URL")
    if url:
        return url

    # 2) Profile-based (your .env already has VW_PROFILE/local/aws blocks)
    prof = os.getenv("VW_PROFILE", "").lower()
    if prof == "aws":
        url = os.getenv("AWS_VAULTWARDEN_URL")
        if url:
            return url
    if prof == "local":
        url = os.getenv("LOCAL_VAULTWARDEN_URL")
        if url:
            return url

    # 3) Probe candidates (alive)
    candidates = [
        os.getenv("LOCAL_VAULTWARDEN_URL"),
        os.getenv("AWS_VAULTWARDEN_URL"),
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:33000",
    ]
    for u in [c for c in candidates if c]:
        try:
            r = requests.get(f"{u}/alive", timeout=0.7)
            if r.status_code == 200:
                return u
        except Exception:
            pass

    # Last resort
    return "http://localhost:3000"


def headless_default() -> bool:
    """Headless on CI/servers; visible on local desktops unless overridden."""
    val = os.getenv("HEADLESS")
    if val is not None:
        return val.lower() in ("1", "true", "yes")

    # Auto: if CI or no DISPLAY -> headless
    if os.getenv("GITHUB_ACTIONS") or os.getenv("CI") or not os.getenv("DISPLAY"):
        return True
    return False


def resolve_api_credentials():
    """Return (url, client_id, client_secret) using the same rules."""
    url = pick_url()

    # Explicit standard names take precedence
    cid = os.getenv("CLIENT_ID")
    csec = os.getenv("CLIENT_SECRET")
    if cid and csec:
        return url, cid, csec

    prof = os.getenv("VW_PROFILE", "").lower()
    if prof == "aws":
        return url, os.getenv("AWS_CLIENT_ID"), os.getenv("AWS_CLIENT_SECRET")
    if prof == "local":
        return url, os.getenv("LOCAL_CLIENT_ID"), os.getenv("LOCAL_CLIENT_SECRET")

    # Fallback: infer from chosen url
    if "8000" in url or "33000" in url:
        return url, os.getenv("AWS_CLIENT_ID"), os.getenv("AWS_CLIENT_SECRET")
    else:
        return url, os.getenv("LOCAL_CLIENT_ID"), os.getenv("LOCAL_CLIENT_SECRET")
