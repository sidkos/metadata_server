from __future__ import annotations

from typing import Any, Optional, Tuple, cast

from psycopg2.extensions import connection as PGConnection

try:
    import psycopg2
except Exception as exc:
    raise RuntimeError(
        "psycopg2-binary is required for Postgres driver. Install it via dp-client dependencies."
    ) from exc


class PostgresDriver:
    """Simple PostgreSQL driver using psycopg2. No Django coupling.

    Connection parameters must be provided explicitly by the caller (no hardcoded defaults).
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
    ) -> None:
        self._conn_params = dict(host=host, port=port, dbname=dbname, user=user, password=password)

    def _conn(self) -> PGConnection:
        return psycopg2.connect(**self._conn_params)

    def fetch_one(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[tuple[Any, ...]]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                row = cast(Optional[tuple[Any, ...]], cur.fetchone())
                return row

    def fetch_value(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[int]:
        row = self.fetch_one(query, params)
        if row is None or len(row) == 0:
            return None
        try:
            return int(row[0])
        except (TypeError, ValueError):
            return None

    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                affected = cur.rowcount
                conn.commit()
                return int(affected)
