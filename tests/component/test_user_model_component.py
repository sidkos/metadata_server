from http import HTTPStatus
from typing import Generator, List

import pytest
from dp_client import DPClient

from src.tools import generate_israeli_id, generate_random_phone_number

# Define a tuple of psycopg2-related exceptions if psycopg2 is available.
# This lets us catch specific DB connectivity/driver errors without a blanket Exception.
# Always keep a consistent, typed value to satisfy mypy.
PSYCOPG2_ERRORS: tuple[type[BaseException], ...] = tuple()
try:
    import psycopg2

    PSYCOPG2_ERRORS = (
        psycopg2.OperationalError,
        psycopg2.InterfaceError,
        psycopg2.Error,
    )
except Exception:  # psycopg2 not installed or failed to import in this context
    # Leave PSYCOPG2_ERRORS as an empty tuple of exception types
    pass


@pytest.fixture
def non_authenticated_client(base_url: str) -> DPClient:
    return DPClient(base_url=base_url)


@pytest.fixture
def client(base_url: str, auth_token: str) -> DPClient:
    return DPClient(base_url=base_url, token=auth_token, prefix="Bearer")


@pytest.fixture
def require_db(client: DPClient):
    """Skip tests that require direct DB access if the DB is not reachable.

    Tries a simple query via PGDBClient; on failure, skips the test.
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
    ids: List[str] = []
    # Pre-test cleanup (defensive): ensure none of these ids already exist (normally random, but be safe)
    if ids:
        try:
            client.PGDBClient.delete_users_by_ids(ids)
        except PSYCOPG2_ERRORS + (RuntimeError,):
            # DB not available/misconfigured; ignore cleanup in pre
            pass
    yield ids
    # Post-test cleanup: remove created users directly from DB since there is no DELETE API
    if ids:
        try:
            client.PGDBClient.delete_users_by_ids(ids)
        except PSYCOPG2_ERRORS + (RuntimeError,):
            # DB not available/misconfigured; ignore cleanup in post
            pass


def test_health_check_component(non_authenticated_client: DPClient):
    response = non_authenticated_client.health_check()
    assert response.status_code == 200
    assert response.status_code == HTTPStatus.OK


def test_create_user_valid_component(client: DPClient, created_user_ids, require_db):
    payload = {
        "id": generate_israeli_id(),
        "name": "Test User",
        "phone": generate_random_phone_number(),
        "address": "Test Street 1",
    }
    created_user_ids.append(payload["id"])

    response = client.create_user(payload)
    assert response.status_code == HTTPStatus.CREATED
    assert response.parsed.id == payload["id"]
    assert response.parsed.name == payload["name"]

    # Verify in DB via dp-client DB driver
    db_user = client.PGDBClient.get_user_by_id(payload["id"])
    assert db_user is not None, "User should exist in DB after creation"
    assert db_user["name"] == payload["name"]
    assert db_user["phone"] == payload["phone"]
    assert db_user["address"] == payload["address"]


def test_create_user_invalid_id_component(client: DPClient, require_db):
    payload = {
        "id": "123789456",  # invalid checksum
        "name": "Test User",
        "phone": generate_random_phone_number(),
        "address": "Test Street 1",
    }
    response = client.create_user(payload)
    assert response.status_code == 400
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.parsed is None

    # Verify not in DB
    assert client.PGDBClient.get_user_by_id(payload["id"]) is None


def test_create_user_invalid_phone_component(client: DPClient, require_db):
    payload = {
        "id": generate_israeli_id(),
        "name": "Test User",
        "phone": "0501234567",  # invalid format
        "address": "Test Street 1",
    }
    response = client.create_user(payload)
    assert response.status_code == 400
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.parsed is None

    # Verify not in DB
    assert client.PGDBClient.get_user_by_id(payload["id"]) is None


def test_retrieve_user_component(client: DPClient, created_user_ids, require_db):
    payload = {
        "id": generate_israeli_id(),
        "name": "Test User",
        "phone": generate_random_phone_number(),
        "address": "Test Street 1",
    }
    created_user_ids.append(payload["id"])

    create_resp = client.create_user(payload)
    assert create_resp.status_code == HTTPStatus.CREATED

    # Verify in DB first via dp-client
    assert client.PGDBClient.users_exist([payload["id"]])

    response = client.get_user(payload["id"])
    assert response.status_code == HTTPStatus.OK
    assert response.parsed.id == payload["id"]
    assert response.parsed.name == payload["name"]


def test_list_users_component(client: DPClient, created_user_ids, require_db):
    users_data = [
        {
            "id": generate_israeli_id(),
            "name": "Test User",
            "phone": generate_random_phone_number(),
            "address": "Street 1",
        },
        {
            "id": generate_israeli_id(),
            "name": "Test User",
            "phone": generate_random_phone_number(),
            "address": "Street 2",
        },
    ]
    for u in users_data:
        created_user_ids.append(u["id"])
        resp = client.create_user(u)
        assert resp.status_code == HTTPStatus.CREATED

    # DB cross-check: all created users present (via dp-client DB driver)
    ids = [u["id"] for u in users_data]
    assert client.PGDBClient.users_exist(ids)

    # API list still OK
    list_resp = client.list_users()
    assert list_resp.status_code == HTTPStatus.OK
    returned_ids_api = {u.id for u in list_resp.parsed}
    for u in users_data:
        assert u["id"] in returned_ids_api
