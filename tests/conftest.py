from __future__ import annotations

import os
from pathlib import Path

import pytest

try:
    # Enable local hostname fallback for Postgres unless explicitly disabled
    # This lets component tests run locally when POSTGRES_HOST (e.g., 'db') isn't resolvable.
    os.environ.setdefault("POSTGRES_ALLOW_LOCAL_FALLBACK", "true")

    # Load environment variables from repository .env so tests and CI have required config
    from dotenv import load_dotenv

    _repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=_repo_root / ".env", override=False)
except Exception:
    # If python-dotenv is not available, silently continue; CI should provide envs
    pass


@pytest.fixture
def base_url() -> str:
    """Resolve API base URL from environment with sensible defaults.

    Prefers API_BASE_URL; otherwise builds from METADATA_HOST and METADATA_PORT.
    """
    return os.environ.get(
        "API_BASE_URL",
        f"http://{os.environ.get('METADATA_HOST', 'localhost')}:{os.environ.get('METADATA_PORT', '8000')}",
    )


@pytest.fixture
def auth_token(base_url: str) -> str:
    """Get an access token for authenticated API tests.

    Uses API_TOKEN if set; otherwise performs username/password login against /api/token/.
    """
    token = os.environ.get("API_TOKEN")
    if token:
        return token

    import requests  # imported here to avoid hard dependency if not needed

    username = os.environ.get("TEST_USERNAME")
    password = os.environ.get("TEST_PASSWORD")
    if not username or not password:
        raise RuntimeError("TEST_USERNAME/TEST_PASSWORD or API_TOKEN must be set for authenticated tests")

    resp = requests.post(
        f"{base_url}/api/token/",
        json={"username": username, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access"]
