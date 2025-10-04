from __future__ import annotations

import os
import socket
from typing import Iterable, Optional, cast

from .drivers.postgres import PostgresDriver


class PGDBClient:
    """PostgreSQL Database client using a dedicated driver (no Django dependencies).

    Reads connection parameters from arguments or environment variables (no hardcoded defaults):
      - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    """

    def __init__(
        self,
        *,
        host: Optional[str] = None,
        port: Optional[int] = None,
        dbname: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        table: str = "metadata_manager_user",
    ) -> None:
        # Allow explicit args to override env; otherwise read from env without fallback defaults
        env_host = os.environ.get("POSTGRES_HOST")
        env_port = os.environ.get("POSTGRES_PORT")
        env_db = os.environ.get("POSTGRES_DB")
        env_user = os.environ.get("POSTGRES_USER")
        env_password = os.environ.get("POSTGRES_PASSWORD")

        final_host = host or env_host
        final_port = port if port is not None else (int(env_port) if env_port else None)
        final_db = dbname or env_db
        final_user = user or env_user
        final_password = password or env_password

        missing = []
        if not final_host:
            missing.append("POSTGRES_HOST or host")
        if final_port is None:
            missing.append("POSTGRES_PORT or port")
        if not final_db:
            missing.append("POSTGRES_DB or dbname")
        if not final_user:
            missing.append("POSTGRES_USER or user")
        if not final_password:
            missing.append("POSTGRES_PASSWORD or password")

        if missing:
            raise RuntimeError(
                "PGDBClient configuration missing: "
                + ", ".join(missing)
                + ". Provide env vars in .env or pass parameters explicitly."
            )

        # Optional DNS resolution fallback for local runs outside Docker networks.
        # If POSTGRES_HOST is not resolvable and POSTGRES_ALLOW_LOCAL_FALLBACK is truthy,
        # transparently switch to localhost. This preserves env-driven config with no hardcoded defaults
        # unless explicitly opted-in by the environment.
        allow_fallback = os.environ.get("POSTGRES_ALLOW_LOCAL_FALLBACK", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        # At this point, required parameters are present; narrow Optional types for type-checker
        final_host_str = cast(str, final_host)
        final_port_int = cast(int, final_port)
        final_db_str = cast(str, final_db)
        final_user_str = cast(str, final_user)
        final_password_str = cast(str, final_password)

        resolved_host: str = final_host_str
        try:
            # Try to resolve the host name; if it fails, consider fallback.
            socket.gethostbyname(final_host_str)
        except Exception:
            if allow_fallback:
                resolved_host = "localhost"

        self._driver = PostgresDriver(
            host=resolved_host,
            port=final_port_int,
            dbname=final_db_str,
            user=final_user_str,
            password=final_password_str,
        )
        self._table = table

    def get_user_by_id(self, user_id: str):
        row = self._driver.fetch_one(
            f"SELECT id, name, phone, address FROM {self._table} WHERE id = %s",
            (user_id,),
        )
        if not row:
            return None
        return {"id": row[0], "name": row[1], "phone": row[2], "address": row[3]}

    def users_exist(self, user_ids: Iterable[str]) -> bool:
        ids = list(user_ids)
        if not ids:
            return True
        count = self._driver.fetch_value(
            f"SELECT COUNT(*) FROM {self._table} WHERE id = ANY(%s)",
            (ids,),
        )
        return int(count or 0) == len(ids)

    def delete_users_by_ids(self, user_ids: Iterable[str]) -> int:
        ids = list(user_ids)
        if not ids:
            return 0
        return self._driver.execute(
            f"DELETE FROM {self._table} WHERE id = ANY(%s)",
            (ids,),
        )
