from __future__ import annotations

from typing import Any, Union


class UsersAPI:
    """Users endpoints wrapper using generated metadata_client api module."""

    def __init__(self, client: Any) -> None:
        try:
            from metadata_client.api.users import users_create as _users_create
            from metadata_client.api.users import users_list as _users_list
            from metadata_client.api.users import users_retrieve as _users_retrieve
            from metadata_client.models import User as _User
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "metadata-client is required but not installed or failed to import. "
                f"Original error: {exc}. Install it or run: pip install -r dp-client/requirements.txt"
            ) from exc
        self._client = client
        self._users_create = _users_create
        self._users_list = _users_list
        self._users_retrieve = _users_retrieve
        self._User = _User

    def create_user(self, user: Union[Any, dict]):
        body = self._User.from_dict(user) if isinstance(user, dict) else user
        return self._users_create.sync_detailed(client=self._client, body=body)

    def get_user(self, user_id: str):
        return self._users_retrieve.sync_detailed(client=self._client, id=user_id)

    def list_users(self):
        return self._users_list.sync_detailed(client=self._client)
