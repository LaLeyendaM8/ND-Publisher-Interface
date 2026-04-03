from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings


def has_database() -> bool:
    return bool(get_settings().database_url)


def require_database_url() -> str:
    database_url = get_settings().database_url
    if not database_url:
        raise RuntimeError("DATABASE_URL fehlt in services/api/.env")
    return database_url


@contextmanager
def db_conn() -> Iterator[psycopg.Connection[Any]]:
    conn = psycopg.connect(require_database_url(), autocommit=True, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()
