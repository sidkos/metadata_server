from http import HTTPStatus

import pytest
from metadata_client import AuthenticatedClient
from metadata_client.api.health import health_retrieve
from metadata_client.api.users import (
    users_create,
    users_destroy,
    users_partial_update,
    users_retrieve,
    users_update,
)
from metadata_client.models import User, UserUpdate, PatchedUserUpdate

from src.tools import generate_israeli_id, generate_random_phone_number


def test_health_check(non_authenticated_client):
    response = health_retrieve.sync_detailed(client=non_authenticated_client)
    assert response.status_code == HTTPStatus.OK


CREATE_CASES = [
    pytest.param(
        lambda: User(id=generate_israeli_id(), name="Ok", phone=generate_random_phone_number(), address="A"),
        True,
        id="create:ok",
    ),
    pytest.param(
        lambda: User(id="123789456", name="BadID", phone=generate_random_phone_number(), address="A"),
        False,
        id="create:bad-id",
    ),
    pytest.param(
        lambda: User(id=generate_israeli_id(), name="BadPhone", phone="0501234567", address="A"),
        False,
        id="create:bad-phone",
    ),
]


@pytest.mark.parametrize("user_builder,expect_ok", CREATE_CASES)
def test_users_create_parametrized(client, user_builder, expect_ok):
    user = user_builder()
    resp = users_create.sync_detailed(client=client, body=user)
    if expect_ok:
        assert resp.status_code == HTTPStatus.CREATED
        assert resp.parsed.id == user.id
        # Cleanup: delete via API and validate removal
        del_resp = users_destroy.sync_detailed(client=client, id=user.id)
        assert del_resp.status_code == HTTPStatus.NO_CONTENT
        get_resp = users_retrieve.sync_detailed(client=client, id=user.id)
        assert get_resp.status_code == HTTPStatus.NOT_FOUND
    else:
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.parsed is None


PATCH_CASES = [
    pytest.param(lambda: {"address": "New Street 1"}, True, id="patch-address:ok"),
    pytest.param(lambda: {"name": "Renamed"}, True, id="patch-name:ok"),
    pytest.param(lambda: {"phone": generate_random_phone_number()}, True, id="patch-phone:ok-valid"),
    pytest.param(lambda: {"phone": "0501234567"}, False, id="patch-phone:bad-format"),
    pytest.param(lambda: {"id": generate_israeli_id()}, False, id="patch-id:forbidden"),
]


@pytest.mark.parametrize("payload_builder,expect_ok", PATCH_CASES)
def test_users_partial_update_parametrized(client: AuthenticatedClient, payload_builder, expect_ok, new_user: User):
    user = new_user
    create_resp = users_create.sync_detailed(client=client, body=user)
    assert create_resp.status_code == HTTPStatus.CREATED

    patch_body = payload_builder()
    m_body = PatchedUserUpdate.from_dict(patch_body)
    resp = users_partial_update.sync_detailed(client=client, id=user.id, body=m_body)

    if expect_ok:
        assert resp.status_code == HTTPStatus.OK
        assert resp.parsed is not None
        for k, v in patch_body.items():
            if k == "id":
                continue
            assert getattr(resp.parsed, k) == v
        assert resp.parsed.id == user.id
    else:
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.parsed is None

    # Cleanup: delete the created user and validate deletion
    del_resp = users_destroy.sync_detailed(client=client, id=user.id)
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    get_resp = users_retrieve.sync_detailed(client=client, id=user.id)
    assert get_resp.status_code == HTTPStatus.NOT_FOUND


PUT_CASES = [
    pytest.param(
        # OK: client sends id equal to path (many generators require id in model)
        lambda cur_id: {"id": cur_id, "name": "User B", "phone": generate_random_phone_number(), "address": "Addr B"},
        True,
        id="put-with-same-id:ok",
    ),
    pytest.param(
        # Forbidden: client sends a different id attempting to change PK
        lambda cur_id: {
            "id": generate_israeli_id(),
            "name": "User B",
            "phone": generate_random_phone_number(),
            "address": "Addr B",
        },
        False,
        id="put-with-different-id:forbidden",
    ),
    pytest.param(
        # Invalid phone while keeping same id
        lambda cur_id: {"id": cur_id, "name": "User C", "phone": "0501234567", "address": "Addr C"},
        False,
        id="put-invalid-phone:bad-format",
    ),
]


@pytest.mark.parametrize("payload_builder,expect_ok", PUT_CASES)
def test_users_update_put_parametrized(client: AuthenticatedClient, payload_builder, expect_ok, new_user: User):
    user = new_user
    create_resp = users_create.sync_detailed(client=client, body=user)
    assert create_resp.status_code == HTTPStatus.CREATED

    put_body = payload_builder(user.id)
    m_body = UserUpdate.from_dict(put_body)
    resp = users_update.sync_detailed(client=client, id=user.id, body=m_body)

    if expect_ok:
        assert resp.status_code == HTTPStatus.OK
        assert resp.parsed is not None
        assert resp.parsed.id == user.id
        for k, v in put_body.items():
            if k == "id":
                continue
            assert getattr(resp.parsed, k) == v
    else:
        assert resp.status_code == HTTPStatus.BAD_REQUEST
        assert resp.parsed is None

    # Cleanup: delete the created user and validate deletion
    del_resp = users_destroy.sync_detailed(client=client, id=user.id)
    assert del_resp.status_code == HTTPStatus.NO_CONTENT
    get_resp = users_retrieve.sync_detailed(client=client, id=user.id)
    assert get_resp.status_code == HTTPStatus.NOT_FOUND
