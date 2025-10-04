from __future__ import annotations

from typing import Any, Optional


class MetaDataServerAPIClientFactory:
    """Factory to construct metadata_client Client/AuthenticatedClient consistently.

    Mirrors how unit/component tests construct the generated client.
    """

    def __init__(self) -> None:
        # Import lazily to keep dp-client importable even if metadata-client is missing
        try:
            from metadata_client import AuthenticatedClient as _AuthenticatedClient  # type: ignore
            from metadata_client import Client as _Client
        except Exception as exc:
            raise RuntimeError(
                "metadata-client is required but not installed or failed to import. "
                f"Original error: {exc}. Install it or run: pip install -r dp-client/requirements.txt"
            ) from exc
        self._AuthenticatedClient = _AuthenticatedClient
        self._Client = _Client

    def build(self, base_url: str, token: Optional[str] = None, prefix: str = "Bearer") -> Any:
        if token:
            return self._AuthenticatedClient(base_url=base_url, token=token, prefix=prefix)
        return self._Client(base_url=base_url)
