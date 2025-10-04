from __future__ import annotations

from typing import Any


class HealthAPI:
    """Health endpoints wrapper using generated metadata_client api module."""

    def __init__(self, client: Any) -> None:
        try:
            from metadata_client.api.health import health_retrieve as _health_retrieve  # noqa: WPS433
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "metadata-client is required but not installed or failed to import. "
                f"Original error: {exc}. Install it or run: pip install -r dp-client/requirements.txt"
            ) from exc
        self._client = client
        self._health_retrieve = _health_retrieve

    def health_check(self):
        return self._health_retrieve.sync_detailed(client=self._client)
