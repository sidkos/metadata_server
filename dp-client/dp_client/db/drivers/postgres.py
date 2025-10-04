from __future__ import annotations

from typing import Any, Optional, Tuple

try:
    import psycopg2
except Exception as exc:  # pragma: no cover
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

    def _conn(self):
        return psycopg2.connect(**self._conn_params)

    def fetch_one(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[tuple]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchone()

    def fetch_value(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Any]:
        row = self.fetch_one(query, params)
        return row[0] if row is not None and len(row) > 0 else None

    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> int:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                # psycopg2 rowcount: number of rows affected by last command
                affected = cur.rowcount
                conn.commit()
                return int(affected)
