from __future__ import annotations

from typing import Optional, Union

from metadata_client import AuthenticatedClient, Client
from metadata_client.models import User as _User
from metadata_client.models import UserUpdate as _UserUpdate
from metadata_client.types import Response

from .api.health import HealthAPI
from .api.users import UsersAPI
from .clients.metadata import MetaDataServerAPIClientFactory
from .db.pg import PGDBClient


class DPClient:
    """High-level helper that composes separated concerns.

    Exposes:
      - self.MetaDataServerAPIClient: underlying generated client instance (Client or AuthenticatedClient)
      - self.UsersApi: operations around Users endpoints
      - self.HealthAPI: operations around Health endpoints
      - self.PGDBClient: optional DB helper for direct DB assertions/cleanup

    Backward compatibility: keeps thin wrapper methods (health_check, create_user, get_user, list_users).
    """

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        *,
        prefix: str = "Bearer",
        timeout: float = 10.0,
    ) -> None:
        """Initialize DPClient and its composed helpers.

        Args:
            base_url: Base URL of the metadata server (e.g., http://localhost:8000/api).
            token: Optional bearer token for authenticated requests.
            prefix: Authorization prefix (default: "Bearer").
            timeout: Default request timeout in seconds for higher-level operations.
        """
        self._client_factory = MetaDataServerAPIClientFactory()
        self.MetaDataServerAPIClient: Union[Client, AuthenticatedClient] = self._client_factory.build(
            base_url=base_url, token=token, prefix=prefix
        )
        self.UsersApi = UsersAPI(self.MetaDataServerAPIClient)
        self.HealthAPI = HealthAPI(self.MetaDataServerAPIClient)
        self.PGDBClient = PGDBClient()
        self._timeout = timeout

    def health_check(self) -> Response[dict[str, str]]:
        """Call the health check endpoint.

        Returns:
            The detailed response from the generated client for GET /api/health/.
        """
        return self.HealthAPI.health_check()

    def create_user(self, user: Union[_User, dict[str, object]]) -> Response[_User]:
        """Create a user.

        Args:
            user: User model instance or dict payload for user creation.

        Returns:
            The detailed response from the generated client.
        """
        return self.UsersApi.create_user(user)

    def get_user(self, user_id: str) -> Response[_User]:
        """Retrieve a user by ID.

        Args:
            user_id: Primary key of the user.

        Returns:
            The detailed response from the generated client.
        """
        return self.UsersApi.get_user(user_id)

    def list_users(self) -> Response[list[_User]]:
        """List all users.

        Returns:
            The detailed response from the generated client.
        """
        return self.UsersApi.list_users()

    # New endpoints wrappers
    def update_user(self, user_id: str, body: Union[_UserUpdate, dict[str, object]]) -> Response[_User]:
        """Update a user via PUT /api/users/{id}/.

        Args:
            user_id: Primary key of the user to update.
            body: User model instance or compatible dict with fields to update.

        Returns:
            The detailed response from the generated client.
        """
        # Delegate to UsersAPI which normalizes payload and types
        return self.UsersApi.update_user(user_id, body)

    def partial_update_user(self, user_id: str, body: dict[str, object]) -> Response[_User]:
        """Partially update a user via PATCH /api/users/{id}/.

        Args:
            user_id: Primary key of the user to update.
            body: Partial dict of fields to update (must not include "id").

        Returns:
            The detailed response from the generated client.
        """
        return self.UsersApi.partial_update_user(user_id, body)

    def delete_user(self, user_id: str) -> Response[None]:
        """Delete a user via DELETE /api/users/{id}/.

        Args:
            user_id: Primary key of the user to delete.

        Returns:
            The detailed response from the generated client.
        """
        return self.UsersApi.delete_user(user_id)
