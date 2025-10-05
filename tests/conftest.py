from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, cast

import pytest
import requests
from metadata_client import AuthenticatedClient as _AuthenticatedClient
from metadata_client import Client as _Client
from metadata_client.models import User

from src.tools import generate_israeli_id, generate_random_phone_number

# Ensure in-repo dp-client package is importable before site-packages version
_repo_root = Path(__file__).resolve().parents[1]
_dp_pkg_path = str(_repo_root / "dp-client")
if _dp_pkg_path not in sys.path:
    sys.path.insert(0, _dp_pkg_path)

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


@pytest.fixture(scope="session", autouse=True)
def base_url() -> str:
    """Resolve API base URL from environment with sensible defaults.

    Prefers API_BASE_URL; otherwise builds from METADATA_HOST and METADATA_PORT.

    Returns:
        str: A non-empty base URL string. Always truthy; falls back to http://localhost:8000.
    """
    return os.environ.get(
        "API_BASE_URL",
        f"http://{os.environ.get('METADATA_HOST', 'localhost')}:{os.environ.get('METADATA_PORT', '8000')}",
    )


@pytest.fixture(scope="session", autouse=True)
def auth_token(base_url: str) -> str:
    """Get an access token for authenticated API tests.

    Uses API_TOKEN if set; otherwise performs username/password login against /api/token/.
    """
    token = os.environ.get("API_TOKEN")
    if token:
        return token

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
    data = cast(dict[str, Any], resp.json())
    return cast(str, data["access"])


try:
    AuthenticatedClient: Any = _AuthenticatedClient
    Client: Any = _Client
except Exception:
    AuthenticatedClient = None
    Client = None


@pytest.fixture(scope="session", autouse=True)
def non_authenticated_client(base_url: str) -> _Client:
    """Unauthenticated generated API client (metadata_client.Client).

    Args:
        base_url: Base URL for the API under test.

    Returns:
        metadata_client.Client instance.
    """
    return _Client(base_url=base_url)


@pytest.fixture(scope="session", autouse=True)
def client(base_url: str, auth_token: str) -> _AuthenticatedClient:
    """Authenticated generated API client (metadata_client.AuthenticatedClient).

    Args:
        base_url: Base URL for the API under test.
        auth_token: Access token for Authorization header.

    Returns:
        metadata_client.AuthenticatedClient instance.
    """
    return _AuthenticatedClient(base_url=base_url, token=auth_token, prefix="Bearer")


@pytest.fixture(scope="function")
def new_user() -> User:
    """Build a fresh valid User payload for tests.

    Returns:
        User: A new User instance with randomized, valid fields.
    """
    return User(
        id=generate_israeli_id(),
        name="User A",
        phone=generate_random_phone_number(),
        address="Addr A",
    )
