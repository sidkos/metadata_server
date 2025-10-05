from http import HTTPStatus
from typing import Callable, Dict, List

import pytest
from dp_client import DPClient

from src.tools import generate_israeli_id, generate_random_phone_number


def test_health_check_component(non_authenticated_client: DPClient) -> None:
    """Test health endpoint responds with 200 OK.
    1. Build non-authenticated client
    2. Call GET /api/health/
    3. Assert HTTP 200
    """
    response = non_authenticated_client.health_check()
    assert response.status_code == HTTPStatus.OK


def test_create_user_valid_component(client: DPClient, created_user_ids: List[str], require_db: None) -> None:
    """Test creating a valid user and DB persistence + cleanup.
    1. Create a user via API
    2. Verify response body and DB state
    3. Delete user via API and verify DB removal
    """
    payload: Dict[str, object] = {
        "id": generate_israeli_id(),
        "name": "Test User",
        "phone": generate_random_phone_number(),
        "address": "Test Street 1",
    }
    created_user_ids.append(str(payload["id"]))

    response = client.create_user(payload)
    assert response.status_code == HTTPStatus.CREATED
    assert response.parsed is not None
    assert response.parsed.id == payload["id"]
    assert response.parsed.name == payload["name"]

    db_user = client.PGDBClient.get_user_by_id(str(payload["id"]))
    assert db_user is not None, "User should exist in DB after creation"
    assert db_user["name"] == payload["name"]
    assert db_user["phone"] == payload["phone"]
    assert db_user["address"] == payload["address"]

    del_resp = client.delete_user(str(payload["id"]))
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.PGDBClient.get_user_by_id(str(payload["id"])) is None


def test_create_user_invalid_id_component(client: DPClient, require_db: None) -> None:
    """Test creating a user with invalid ID fails and no DB insert occurs.
    1. Build invalid payload with bad ID
    2. Call POST /api/users/
    3. Assert 400 and no DB record exists
    """
    payload: Dict[str, object] = {
        "id": "123789456",
        "name": "Test User",
        "phone": generate_random_phone_number(),
        "address": "Test Street 1",
    }
    response = client.create_user(payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.parsed is None

    assert client.PGDBClient.get_user_by_id(str(payload["id"])) is None


def test_create_user_invalid_phone_component(client: DPClient, require_db: None) -> None:
    """Test creating a user with invalid phone fails and no DB insert occurs.
    1. Build invalid payload with bad phone
    2. Call POST /api/users/
    3. Assert 400 and no DB record exists
    """
    payload: Dict[str, object] = {
        "id": generate_israeli_id(),
        "name": "Test User",
        "phone": "0501234567",
        "address": "Test Street 1",
    }
    response = client.create_user(payload)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.parsed is None

    assert client.PGDBClient.get_user_by_id(str(payload["id"])) is None


def test_retrieve_user_component(client: DPClient, created_user_ids: List[str], require_db: None) -> None:
    """Test retrieving a user reflects created data and cleanup works.
    1. Create a user via API
    2. Retrieve user via API and verify fields
    3. Delete user and verify DB cleanup
    """
    payload: Dict[str, object] = {
        "id": generate_israeli_id(),
        "name": "Test User",
        "phone": generate_random_phone_number(),
        "address": "Test Street 1",
    }
    created_user_ids.append(str(payload["id"]))

    create_resp = client.create_user(payload)
    assert create_resp.status_code == HTTPStatus.CREATED

    assert client.PGDBClient.users_exist([str(payload["id"])])

    response = client.get_user(str(payload["id"]))
    assert response.status_code == HTTPStatus.OK
    assert response.parsed is not None
    assert response.parsed.id == payload["id"]
    assert response.parsed.name == payload["name"]

    del_resp = client.delete_user(str(payload["id"]))
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.PGDBClient.get_user_by_id(str(payload["id"])) is None


def test_list_users_component(client: DPClient, created_user_ids: List[str], require_db: None) -> None:
    """Test listing users contains created users and cleanup works.
    1. Create two users via API
    2. List users and verify IDs included
    3. Delete users and verify DB cleanup
    """
    users_data: List[Dict[str, object]] = [
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
        created_user_ids.append(str(u["id"]))
        resp = client.create_user(u)
        assert resp.status_code == HTTPStatus.CREATED

    ids = [str(u["id"]) for u in users_data]
    assert client.PGDBClient.users_exist(ids)

    list_resp = client.list_users()
    assert list_resp.status_code == HTTPStatus.OK
    assert list_resp.parsed is not None
    returned_ids_api = {u.id for u in list_resp.parsed}
    for u in users_data:
        assert u["id"] in returned_ids_api

    for u in users_data:
        del_resp = client.delete_user(str(u["id"]))
        assert del_resp.status_code == HTTPStatus.NO_CONTENT
        assert client.PGDBClient.get_user_by_id(str(u["id"])) is None


def _new_user_payload() -> dict[str, object]:
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
def test_component_users_partial_update_parametrized(
    client: DPClient,
    created_user_ids: List[str],
    payload_builder: Callable[[], Dict[str, object]],
    expect_ok: bool,
) -> None:
    """Test PATCH variants (parametrized) and DB validation + cleanup.
    1. Create user via API
    2. PATCH with parametrized body and assert success or failure
    3. Verify DB state accordingly and delete user
    """
    payload = _new_user_payload()
    created_user_ids.append(str(payload["id"]))

    create_resp = client.create_user(payload)
    assert create_resp.status_code == HTTPStatus.CREATED

    patch_body = payload_builder()
    resp = client.partial_update_user(str(payload["id"]), patch_body)

    if expect_ok:
        assert resp.status_code == HTTPStatus.OK
        assert resp.parsed is not None
        for k, v in patch_body.items():
            if k == "id":
                continue
            assert getattr(resp.parsed, k) == v
        db = client.PGDBClient.get_user_by_id(str(payload["id"]))
        assert db is not None
        for k, v in patch_body.items():
            if k != "id":
                assert db[k] == v
    else:
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.parsed is None
        db = client.PGDBClient.get_user_by_id(str(payload["id"]))
        assert db is not None

    del_resp = client.delete_user(str(payload["id"]))
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.PGDBClient.get_user_by_id(str(payload["id"])) is None


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
def test_component_users_update_put_parametrized(
    client: DPClient,
    created_user_ids: List[str],
    payload_builder: Callable[[], Dict[str, object]],
    expect_ok: bool,
) -> None:
    """Test PUT variants (parametrized) with strict id and DB validation.
    1. Create user via API
    2. PUT with parametrized body and assert success or failure
    3. Verify DB state accordingly and delete user
    """
    payload = _new_user_payload()
    created_user_ids.append(str(payload["id"]))

    create_resp = client.create_user(payload)
    assert create_resp.status_code == HTTPStatus.CREATED

    put_body = payload_builder()
    resp = client.update_user(str(payload["id"]), put_body)

    if expect_ok:
        assert resp.status_code == HTTPStatus.OK
        assert resp.parsed is not None
        assert resp.parsed.id == payload["id"]
        for k, v in put_body.items():
            if k == "id":
                continue
            assert getattr(resp.parsed, k) == v
        db = client.PGDBClient.get_user_by_id(str(payload["id"]))
        assert db is not None
        for k, v in put_body.items():
            if k != "id":
                assert db[k] == v
    else:
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.parsed is None

    del_resp = client.delete_user(str(payload["id"]))
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    assert client.PGDBClient.get_user_by_id(str(payload["id"])) is None
