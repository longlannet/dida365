#!/usr/bin/env python3
"""Print the Dida365 OAuth authorization URL."""
from urllib.parse import urlencode
from config_utils import load_oauth_config

AUTH_URL = "https://dida365.com/oauth/authorize"
SCOPE = "tasks:read tasks:write"

cfg = load_oauth_config()
query = urlencode({
    "client_id": cfg["client_id"],
    "redirect_uri": cfg["redirect_uri"],
    "response_type": "code",
    "scope": SCOPE,
})
print(f"{AUTH_URL}?{query}")
