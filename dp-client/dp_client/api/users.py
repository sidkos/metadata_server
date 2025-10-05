from __future__ import annotations

from typing import Any, Dict, Union


class UsersAPI:
    """Users endpoints wrapper using generated metadata_client api module.

    Implements a generalized approach to load and validate all user endpoints
    at initialization time to avoid per-call checks and asserts.
    """

    # Mapping of logical names to attributes provided by metadata_client.api.users
    _ENDPOINT_ATTRS: Dict[str, str] = {
        "create": "users_create",
        "list": "users_list",
        "retrieve": "users_retrieve",
        "update": "users_update",
        "partial_update": "users_partial_update",
        "destroy": "users_destroy",
    }

    def __init__(self, client: Any) -> None:
        """Initialize the UsersAPI wrapper.

        Args:
            client: An instance of the generated metadata_client Client or
                AuthenticatedClient that will be used to perform HTTP requests.

        Raises:
            RuntimeError: If the metadata_client package or required modules
                cannot be imported, or if any of the expected endpoints are
                missing from metadata_client.api.users.
        """
        try:
            from metadata_client.api import users as _users_api
            from metadata_client.models import User as _User
        except Exception as exc:
            raise RuntimeError(
                "metadata-client is required but not installed or failed to import. "
                f"Original error: {exc}. Install it or run: pip install -r dp-client/requirements.txt"
            ) from exc

        self._client = client
        self._User = _User

        # Load all endpoints dynamically
        self._ep: Dict[str, Any] = {
            key: getattr(_users_api, attr_name, None) for key, attr_name in self._ENDPOINT_ATTRS.items()
        }

        # Validate presence of ALL endpoints (include all options)
        missing = [self._ENDPOINT_ATTRS[k] for k, v in self._ep.items() if v is None]
        if missing:
            raise RuntimeError(
                "metadata_client.api.users is missing required endpoints: "
                + ", ".join(missing)
                + ". Regenerate the client from the updated API spec."
            )

    def create_user(self, user: Union[Any, dict]):
        """Create a user via POST /api/users/.

        Args:
            user: Either a metadata_client.models.User instance or a dict that
                can be converted to one via User.from_dict.

        Returns:
            The detailed response object from the generated client containing
            status_code, content, headers, and parsed payload.
        """
        body = self._User.from_dict(user) if isinstance(user, dict) else user
        return self._ep["create"].sync_detailed(client=self._client, body=body)

    def get_user(self, user_id: str):
        """Retrieve a user by ID via GET /api/users/{id}/.

        Args:
            user_id: The primary key of the user to retrieve.

        Returns:
            The detailed response object from the generated client.
        """
        return self._ep["retrieve"].sync_detailed(client=self._client, id=user_id)

    def list_users(self):
        """List all users via GET /api/users/.

        Returns:
            The detailed response object from the generated client.
        """
        return self._ep["list"].sync_detailed(client=self._client)

    def update_user(self, user_id: str, body: Union[Any, dict]):
        """Update a user via PUT /api/users/{id}/.

        Args:
            user_id: The primary key of the user to update.
            body: Either a metadata_client.models.User (or compatible dict) with
                fields to fully update. "id" must not be included by server rules.

        Returns:
            The detailed response object from the generated client.
        """
        body_obj = self._User.from_dict(body) if isinstance(body, dict) else body
        return self._ep["update"].sync_detailed(client=self._client, id=user_id, body=body_obj)

    def partial_update_user(self, user_id: str, body: dict):
        """Partially update a user via PATCH /api/users/{id}/.

        Args:
            user_id: The primary key of the user to update.
            body: A partial JSON dictionary of fields to update. Must not
                include "id" (server enforces immutability).

        Returns:
            The detailed response object from the generated client.
        """
        # PATCH accepts a partial dict
        return self._ep["partial_update"].sync_detailed(client=self._client, id=user_id, body=body)

    def delete_user(self, user_id: str):
        """Delete a user via DELETE /api/users/{id}/.

        Args:
            user_id: The primary key of the user to delete.

        Returns:
            The detailed response object from the generated client.
        """
        return self._ep["destroy"].sync_detailed(client=self._client, id=user_id)
