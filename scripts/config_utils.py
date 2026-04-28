#!/usr/bin/env python3
"""Shared config helpers for the Dida365 skill.

Secrets are intentionally loaded from environment variables or local config files;
never hard-code tokens/client secrets in scripts.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"
TOKEN_FILE = CONFIG_DIR / "token.json"
OAUTH_CONFIG_FILE = CONFIG_DIR / "oauth.json"
ENV_FILE = CONFIG_DIR / ".env"
DEFAULT_BASE_URL = "https://api.dida365.com/open/v1"
DEFAULT_REDIRECT_URI = "http://localhost:8080/"


def _load_dotenv(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_oauth_config() -> dict:
    _load_dotenv()
    data = _read_json(OAUTH_CONFIG_FILE)
    client_id = os.getenv("DIDA_CLIENT_ID") or data.get("client_id") or data.get("CLIENT_ID")
    client_secret = os.getenv("DIDA_CLIENT_SECRET") or data.get("client_secret") or data.get("CLIENT_SECRET")
    redirect_uri = os.getenv("DIDA_REDIRECT_URI") or data.get("redirect_uri") or DEFAULT_REDIRECT_URI
    if not client_id or not client_secret:
        raise SystemExit(
            "Missing Dida365 OAuth config. Set DIDA_CLIENT_ID/DIDA_CLIENT_SECRET "
            "or create config/oauth.json with client_id/client_secret."
        )
    return {"client_id": client_id, "client_secret": client_secret, "redirect_uri": redirect_uri}


def load_api_config() -> dict:
    _load_dotenv()
    data = _read_json(TOKEN_FILE)
    access_token = os.getenv("DIDA_ACCESS_TOKEN") or data.get("access_token")
    base_url = os.getenv("DIDA_BASE_URL") or data.get("base_url") or DEFAULT_BASE_URL
    if not access_token:
        raise SystemExit(
            f"Missing Dida365 access token. Put it in {TOKEN_FILE} or set DIDA_ACCESS_TOKEN."
        )
    return {"access_token": access_token, "base_url": base_url.rstrip("/")}


def save_json_private(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.chmod(tmp, 0o600)
    tmp.replace(path)
    os.chmod(path, 0o600)
