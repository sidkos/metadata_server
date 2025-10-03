import os
import pytest
from metadata_client.models import User
from metadata_client import Client
from metadata_client.api.users import (
    users_create,
    users_list,
    users_retrieve,
    users_ids_retrieve,
)


@pytest.fixture
def client():
    base_url = os.environ.get("API_BASE_URL", f"http://{os.environ["METADATA_HOST"]}:{os.environ["METADATA_PORT"]}")
    return Client(base_url=base_url)


@pytest.mark.usefixtures("db")
def test_create_user_valid(client):
    user = User(id='123456782', name='Test User', phone='+972501234567', address='Test Street 1')
    response = users_create(client=client, json_body=user)
    assert response.id == user.id
    assert response.name == user.name


@pytest.mark.usefixtures("db")
def test_create_user_invalid_id(client):
    user = User(id='123456789', name='Test User', phone='+972501234567', address='Test Street 1')
    with pytest.raises(Exception):
        users_create(client=client, json_body=user)


@pytest.mark.usefixtures("db")
def test_create_user_invalid_phone(client):
    user = User(id='123456782', name='Test User', phone='0501234567', address='Test Street 1')
    with pytest.raises(Exception):
        users_create(client=client, json_body=user)


@pytest.mark.usefixtures("db")
def test_retrieve_user(client):
    user = User(id='123456782', name='Test User', phone='+972501234567', address='Test Street 1')
    users_create(client=client, json_body=user)
    retrieved = users_retrieve(client=client, id=user.id)
    assert retrieved.id == user.id
    assert retrieved.name == user.name


@pytest.mark.usefixtures("db")
def test_list_users(client):
    users_data = [
        User(id='123456782', name='User One', phone='+972501234567', address='Street 1'),
        User(id='234567892', name='User Two', phone='+972501234568', address='Street 2')
    ]
    for user in users_data:
        users_create(client=client, json_body=user)
    user_list = users_list(client=client)
    returned_ids = {u.id for u in user_list}
    for user in users_data:
        assert user.id in returned_ids


@pytest.mark.usefixtures("db")
def test_list_user_ids(client):
    users_data = [
        User(id='123456782', name='User One', phone='+972501234567', address='Street 1'),
        User(id='234567892', name='User Two', phone='+972501234568', address='Street 2')
    ]
    for user in users_data:
        users_create(client=client, json_body=user)
    ids = users_ids_retrieve(client=client)
    for user in users_data:
        assert user.id in ids
