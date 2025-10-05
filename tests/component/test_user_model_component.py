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

    # Cleanup: delete via API and validate DB removal
    del_resp = client.delete_user(payload["id"])  # 204 expected
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.PGDBClient.get_user_by_id(payload["id"]) is None


def test_create_user_invalid_id_component(client: DPClient, require_db):
    payload = {
        "id": "123789456",  # invalid checksum
        "name": "Test User",
        "phone": generate_random_phone_number(),
        "address": "Test Street 1",
    }
    response = client.create_user(payload)
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

    # Cleanup: delete and verify DB removal
    del_resp = client.delete_user(payload["id"])  # 204 expected
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.PGDBClient.get_user_by_id(payload["id"]) is None


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

    # Cleanup: delete all created users via API and validate DB removal
    for u in users_data:
        del_resp = client.delete_user(u["id"])  # 204 expected
        assert del_resp.status_code == HTTPStatus.NO_CONTENT
        assert client.PGDBClient.get_user_by_id(u["id"]) is None


# ---- Parametrized update/patch and delete with DB validations ----


def _new_user_payload() -> dict:
    return {
        "id": generate_israeli_id(),
        "name": "Comp A",
        "phone": generate_random_phone_number(),
        "address": "Addr A",
    }


PATCH_CASES_COMPONENT = [
    pytest.param(lambda: {"address": "Comp St 99"}, True, id="component:patch-address:ok"),
    pytest.param(lambda: {"name": "Comp Renamed"}, True, id="component:patch-name:ok"),
    pytest.param(lambda: {"phone": generate_random_phone_number()}, True, id="component:patch-phone:ok"),
    pytest.param(lambda: {"phone": "0501234567"}, False, id="component:patch-phone:bad-format"),
    pytest.param(lambda: {"id": generate_israeli_id()}, False, id="component:patch-id:forbidden"),
]


@pytest.mark.usefixtures("require_db")
@pytest.mark.parametrize("payload_builder,expect_ok", PATCH_CASES_COMPONENT)
def test_component_users_partial_update_parametrized(client: DPClient, created_user_ids, payload_builder, expect_ok):
    payload = _new_user_payload()
    created_user_ids.append(payload["id"])  # ensure cleanup

    create_resp = client.create_user(payload)
    assert create_resp.status_code == HTTPStatus.CREATED

    patch_body = payload_builder()
    resp = client.partial_update_user(payload["id"], patch_body)

    if expect_ok:
        assert resp.status_code == HTTPStatus.OK
        for k, v in patch_body.items():
            if k == "id":
                continue
            assert getattr(resp.parsed, k) == v
        # DB verify
        db = client.PGDBClient.get_user_by_id(payload["id"])
        for k, v in patch_body.items():
            if k != "id":
                assert db[k] == v
    else:
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.parsed is None
        # DB should remain unchanged
        db = client.PGDBClient.get_user_by_id(payload["id"])
        assert db is not None

    # Cleanup: delete via API and validate DB removal
    del_resp = client.delete_user(payload["id"])  # 204 expected
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.PGDBClient.get_user_by_id(payload["id"]) is None


PUT_CASES_COMPONENT = [
    pytest.param(
        lambda: {"name": "Comp B", "phone": generate_random_phone_number(), "address": "Addr B"},
        True,
        id="component:put-no-id:ok",
    ),
    pytest.param(
        lambda: {
            "id": generate_israeli_id(),
            "name": "Comp C",
            "phone": generate_random_phone_number(),
            "address": "Addr C",
        },
        False,
        id="component:put-with-id:forbidden",
    ),
    pytest.param(
        lambda: {"name": "Comp D", "phone": "0501234567", "address": "Addr D"},
        False,
        id="component:put-invalid-phone:bad-format",
    ),
]


@pytest.mark.usefixtures("require_db")
@pytest.mark.parametrize("payload_builder,expect_ok", PUT_CASES_COMPONENT)
def test_component_users_update_put_parametrized(client: DPClient, created_user_ids, payload_builder, expect_ok):
    payload = _new_user_payload()
    created_user_ids.append(payload["id"])  # ensure cleanup

    create_resp = client.create_user(payload)
    assert create_resp.status_code == HTTPStatus.CREATED

    put_body = payload_builder()
    resp = client.update_user(payload["id"], put_body)

    if expect_ok:
        assert resp.status_code == HTTPStatus.OK
        assert resp.parsed.id == payload["id"]
        for k, v in put_body.items():
            if k == "id":
                continue
            assert getattr(resp.parsed, k) == v
        # DB verify
        db = client.PGDBClient.get_user_by_id(payload["id"])
        for k, v in put_body.items():
            if k != "id":
                assert db[k] == v
    else:
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.parsed is None

    # Cleanup: delete via API and validate DB removal
    del_resp = client.delete_user(payload["id"])  # 204 expected
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.PGDBClient.get_user_by_id(payload["id"]) is None
