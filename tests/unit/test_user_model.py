import os
from http import HTTPStatus

import pytest
import requests
from metadata_client import AuthenticatedClient, Client
from metadata_client.api.health import health_retrieve
from metadata_client.api.users import (
    users_create,
    users_list,
    users_retrieve,
)
from metadata_client.models import User

from src.tools import generate_israeli_id, generate_random_phone_number


@pytest.fixture
def base_url() -> str:
    return os.environ.get(
        "API_BASE_URL",
        f"http://{os.environ.get('METADATA_HOST', 'localhost')}:{os.environ.get('METADATA_PORT', '8000')}",
    )


@pytest.fixture
def anon_client(base_url: str):
    # Unauthenticated client to verify public endpoints (e.g., health)
    return Client(base_url=base_url)


@pytest.fixture
def client(base_url: str):
    # Prefer an already-provided token if present
    token = os.environ.get("API_TOKEN")
    if not token:
        # Otherwise, obtain a token from the API using test credentials
        username = os.environ.get("TEST_USERNAME")
        password = os.environ.get("TEST_PASSWORD")
        if not username or not password:
            raise RuntimeError(
                "TEST_USERNAME/TEST_PASSWORD or API_TOKEN must be set for authenticated tests"
            )
        resp = requests.post(
            f"{base_url}/api/token/",
            json={"username": username, "password": password},
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json()["access"]

    return AuthenticatedClient(base_url=base_url, token=token, prefix="Bearer")


def test_health_check(anon_client):
    response = health_retrieve.sync_detailed(client=anon_client)
    assert response.status_code == 200
    assert response.status_code == HTTPStatus.OK


def test_create_user_valid(client):
    user = User(
        id=generate_israeli_id(), name="Test User", phone=generate_random_phone_number(), address="Test Street 1"
    )
    response = users_create.sync_detailed(client=client, body=user)
    assert response.status_code == HTTPStatus.CREATED
    assert response.parsed.id == user.id
    assert response.parsed.name == user.name


def test_create_user_invalid_id(client):
    user = User(id="123789456", name="Test User", phone=generate_random_phone_number(), address="Test Street 1")
    response = users_create.sync_detailed(client=client, body=user)
    assert response.status_code == 400
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.parsed is None


def test_create_user_invalid_phone(client):
    user = User(id=generate_israeli_id(), name="Test User", phone="0501234567", address="Test Street 1")
    response = users_create.sync_detailed(client=client, body=user)
    assert response.status_code == 400
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.parsed is None


def test_retrieve_user(client):
    user = User(
        id=generate_israeli_id(), name="Test User", phone=generate_random_phone_number(), address="Test Street 1"
    )
    create_resp = users_create.sync_detailed(client=client, body=user)
    assert create_resp.status_code == HTTPStatus.CREATED
    response = users_retrieve.sync_detailed(client=client, id=user.id)
    assert response.status_code == HTTPStatus.OK
    assert response.parsed.id == user.id
    assert response.parsed.name == user.name


def test_list_users(client):
    users_data = [
        User(id=generate_israeli_id(), name="Test User", phone=generate_random_phone_number(), address="Street 1"),
        User(id=generate_israeli_id(), name="Test User", phone=generate_random_phone_number(), address="Street 2"),
    ]
    for user in users_data:
        resp = users_create.sync_detailed(client=client, body=user)
        assert resp.status_code == HTTPStatus.CREATED
    list_resp = users_list.sync_detailed(client=client)
    assert list_resp.status_code == HTTPStatus.OK
    returned_ids = {u.id for u in list_resp.parsed}
    for user in users_data:
        assert user.id in returned_ids
