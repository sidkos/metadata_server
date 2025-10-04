from __future__ import annotations

from typing import Any, Optional, Union

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
        self._client_factory = MetaDataServerAPIClientFactory()
        self.MetaDataServerAPIClient: Any = self._client_factory.build(base_url=base_url, token=token, prefix=prefix)
        self.UsersApi = UsersAPI(self.MetaDataServerAPIClient)
        self.HealthAPI = HealthAPI(self.MetaDataServerAPIClient)
        self.PGDBClient = PGDBClient()
        self._timeout = timeout

    def health_check(self):
        return self.HealthAPI.health_check()

    def create_user(self, user: Union[Any, dict[str, Any]]):
        return self.UsersApi.create_user(user)

    def get_user(self, user_id: str):
        return self.UsersApi.get_user(user_id)

    def list_users(self):
        return self.UsersApi.list_users()
