from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING, Dict, Union

from metadata_client import AuthenticatedClient, Client
from metadata_client.types import Response

if TYPE_CHECKING:  # import only for type checkers; runtime uses lazy-loaded attributes
    from metadata_client.models import User as _User
    from metadata_client.models import UserUpdate as _UserUpdate

from typing import cast


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

    def __init__(self, client: Union[Client, AuthenticatedClient]) -> None:
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
            from metadata_client.models import PatchedUserUpdate as _PatchedUserUpdate
            from metadata_client.models import User as _User
            from metadata_client.models import UserUpdate as _UserUpdate
        except Exception as exc:
            raise RuntimeError(
                "metadata-client is required but not installed or failed to import. "
                f"Original error: {exc}. Install it or run: pip install -r dp-client/requirements.txt"
            ) from exc

        self._client = client
        self._User = _User
        self._UserUpdate = _UserUpdate
        self._PatchedUserUpdate = _PatchedUserUpdate

        # Load all endpoints by importing submodules explicitly since
        # metadata_client.api.users may not expose submodules as attributes.
        import importlib

        tmp_ep: Dict[str, ModuleType | None] = {}
        for key, attr_name in self._ENDPOINT_ATTRS.items():
            module_name = f"metadata_client.api.users.{attr_name}"
            try:
                mod = importlib.import_module(module_name)
            except Exception:
                mod = None
            tmp_ep[key] = mod

        # Validate presence of ALL endpoints (include all options)
        missing = [self._ENDPOINT_ATTRS[k] for k, v in tmp_ep.items() if v is None]
        if missing:
            raise RuntimeError(
                "metadata_client.api.users is missing required endpoints: "
                + ", ".join(missing)
                + ". Regenerate the client from the updated API spec."
            )

        self._ep: Dict[str, ModuleType] = cast(Dict[str, ModuleType], tmp_ep)

    def create_user(self, user: Union[_User, dict[str, object]]) -> Response[_User]:
        """Create a user via POST /api/users/.

        Args:
            user: Either a metadata_client.models.User instance or a dict that
                can be converted to one via User.from_dict.

        Returns:
            The detailed response object from the generated client containing
            status_code, content, headers, and parsed payload.
        """
        body = self._User.from_dict(user) if isinstance(user, dict) else user
        res: Response[_User] = self._ep["create"].sync_detailed(client=self._client, body=body)
        return res

    def get_user(self, user_id: str) -> Response[_User]:
        """Retrieve a user by ID via GET /api/users/{id}/.

        Args:
            user_id: The primary key of the user to retrieve.

        Returns:
            The detailed response object from the generated client.
        """
        res: Response[_User] = self._ep["retrieve"].sync_detailed(client=self._client, id=user_id)
        return res

    def list_users(self) -> Response[list[_User]]:
        """List all users via GET /api/users/.

        Returns:
            The detailed response object from the generated client.
        """
        res: Response[list[_User]] = self._ep["list"].sync_detailed(client=self._client)
        return res

    def update_user(self, user_id: str, body: Union[_UserUpdate, dict[str, object]]) -> Response[_User]:
        """Update a user via PUT /api/users/{id}/.

        Args:
            user_id: The primary key of the user to update.
            body: Either a metadata_client.models.UserUpdate instance or a dict
                that will be converted with UserUpdate.from_dict. If the dict
                omits an "id" field, this client will inject the path id to
                satisfy the generated model requirements. Attempting to change
                the id (mismatch between body and path) will result in 400 from
                the server.

        Returns:
            The detailed response object from the generated client.
        """
        if isinstance(body, dict):
            if "id" not in body:
                body = {**body, "id": user_id}
            body_obj = self._UserUpdate.from_dict(body)
        else:
            body_obj = body

        res: Response[_User] = self._ep["update"].sync_detailed(client=self._client, id=user_id, body=body_obj)
        return res

    def partial_update_user(self, user_id: str, body: dict[str, object]) -> Response[_User]:
        """Partially update a user via PATCH /api/users/{id}/.

        Args:
            user_id: The primary key of the user to update.
            body: A partial JSON dictionary of fields to update. Must not
                include "id" (server enforces immutability). Converted to
                PatchedUserUpdate model for the generated client.

        Returns:
            The detailed response object from the generated client.
        """
        m_body = self._PatchedUserUpdate.from_dict(body)
        res: Response[_User] = self._ep["partial_update"].sync_detailed(client=self._client, id=user_id, body=m_body)
        return res

    def delete_user(self, user_id: str) -> Response[None]:
        """Delete a user via DELETE /api/users/{id}/.

        Args:
            user_id: The primary key of the user to delete.

        Returns:
            The detailed response object from the generated client.
        """
        res: Response[None] = self._ep["destroy"].sync_detailed(client=self._client, id=user_id)
        return res
