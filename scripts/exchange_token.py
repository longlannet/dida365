#!/usr/bin/env python3
"""Exchange an OAuth code for a Dida365 token.

Writes config/token.json with 0600 permissions.
"""
import argparse
import requests
from config_utils import DEFAULT_BASE_URL, TOKEN_FILE, load_oauth_config, save_json_private

TOKEN_URL = "https://dida365.com/oauth/token"
SCOPE = "tasks:read tasks:write"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("code", help="OAuth code from the redirect URL")
    args = parser.parse_args()

    cfg = load_oauth_config()
    # Official docs describe OAuth2 token exchange with Basic Auth for
    # client_id/client_secret. Keep a body-credential fallback for older local
    # setups that used that form before this skill was cleaned up.
    payload = {
        "code": args.code,
        "grant_type": "authorization_code",
        "scope": SCOPE,
        "redirect_uri": cfg["redirect_uri"],
    }
    resp = requests.post(
        TOKEN_URL,
        data=payload,
        auth=(cfg["client_id"], cfg["client_secret"]),
        timeout=30,
    )
    if resp.status_code >= 400:
        fallback_payload = {
            **payload,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
        }
        resp = requests.post(TOKEN_URL, data=fallback_payload, timeout=30)
    if resp.status_code >= 400:
        raise SystemExit(f"Token exchange failed [{resp.status_code}]: {resp.text}")

    token_data = resp.json()
    api_config = {
        "access_token": token_data["access_token"],
        "token_type": token_data.get("token_type", "bearer"),
        "scope": token_data.get("scope", SCOPE),
        "base_url": DEFAULT_BASE_URL,
    }
    save_json_private(TOKEN_FILE, api_config)
    print(f"✅ Token saved to {TOKEN_FILE}")


if __name__ == "__main__":
    main()
