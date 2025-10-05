from __future__ import annotations

from typing import Generator, List

import pytest
from dp_client import DPClient

# psycopg2-related exception tuple to allow conditional DB cleanup handling
PSYCOPG2_ERRORS: tuple[type[BaseException], ...] = tuple()
try:
    import psycopg2

    PSYCOPG2_ERRORS = (
        psycopg2.OperationalError,
        psycopg2.InterfaceError,
        psycopg2.Error,
    )
except Exception:
    # psycopg2 not installed or otherwise unavailable in this environment
    pass


@pytest.fixture
def non_authenticated_client(base_url: str) -> DPClient:
    """Build a DPClient without authentication for public endpoints.

    Args:
        base_url: Base URL for the API under test.

    Returns:
        DPClient: Client configured without Authorization header.
    """
    return DPClient(base_url=base_url)


@pytest.fixture
def client(base_url: str, auth_token: str) -> DPClient:
    """Build an authenticated DPClient for protected endpoints.

    Args:
        base_url: Base URL for the API under test.
        auth_token: Bearer token to use for authenticated requests.

    Returns:
        DPClient: Client configured with Authorization header.
    """
    return DPClient(base_url=base_url, token=auth_token, prefix="Bearer")


@pytest.fixture
def require_db(client: DPClient) -> None:
    """Skip tests requiring DB access if the DB is not reachable.

    Tries a simple query via PGDBClient; on failure, skips the test.

    Args:
        client: Authenticated DPClient instance.

    Returns:
        None. This is a guard fixture that may skip the test.
    """
    try:
        # Trigger a DB connection with a harmless lookup
        client.PGDBClient.get_user_by_id("__nonexistent__")
    except Exception as exc:
        pytest.skip(
            "Database not available for component DB checks: "
            f"{exc}\n"
            "Hints: set POSTGRES_HOST to a reachable host (e.g., localhost), "
            "or export POSTGRES_ALLOW_LOCAL_FALLBACK=true to fall back to localhost when 'db' is not resolvable, "
            "or run `docker-compose up -d` so the service name 'db' is resolvable."
        )


@pytest.fixture(scope="function")
def created_user_ids(client: DPClient) -> Generator[List[str], None, None]:
    """Track user IDs created during a test and ensure cleanup.

    Args:
        client: Authenticated DPClient instance.

    Yields:
        A mutable list to which tests append created IDs for automatic cleanup.
    """
    ids: List[str] = []
    # Defensive pre-cleanup if list is pre-populated for any reason
    if ids:
        try:
            client.PGDBClient.delete_users_by_ids(ids)
        except PSYCOPG2_ERRORS + (RuntimeError,):
            # DB not available/misconfigured; ignore cleanup in pre
            pass

    try:
        yield ids
    finally:
        if ids:
            try:
                client.PGDBClient.delete_users_by_ids(ids)
            except PSYCOPG2_ERRORS + (RuntimeError,):
                # DB not available/misconfigured; ignore cleanup in post
                pass
