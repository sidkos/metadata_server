from __future__ import annotations

from typing import Any


class HealthAPI:
    """Health endpoints wrapper using generated metadata_client api module."""

    def __init__(self, client: Any) -> None:
        """Initialize the HealthAPI wrapper.

        Args:
            client: An instance of the generated metadata_client Client or
                AuthenticatedClient used to perform HTTP requests.

        Raises:
            RuntimeError: If the generated health endpoint cannot be imported.
        """
        try:
            from metadata_client.api.health import health_retrieve as _health_retrieve
        except Exception as exc:
            raise RuntimeError(
                "Metadata-client is required but not installed or failed to import. "
                f"Original error: {exc}. Install it or run: pip install -r dp-client/requirements.txt"
            ) from exc
        self._client = client
        self._health_retrieve = _health_retrieve

    def health_check(self):
        """Call GET /api/health/ and return the detailed response.

        Returns:
            The detailed response object from the generated client.
        """
        return self._health_retrieve.sync_detailed(client=self._client)
