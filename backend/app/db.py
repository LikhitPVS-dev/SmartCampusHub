"""
backend/app/db.py
Person 1 – Database Foundation | SmartCampusHub College Portal

Provides a reusable Psycopg 3 connection pool and context managers for
Person 2 (auth, users, announcements) and Person 3 (events, registrations, teams).

REQUIRED ENVIRONMENT VARIABLES  (place in backend/.env — see backend/.env.example)
    DB_HOST      – PostgreSQL server host   (default: localhost)
    DB_PORT      – PostgreSQL port          (default: 5432)
    DB_NAME      – Database name            (default: smartcampushub)
    DB_USER      – Database user            (default: postgres)
    DB_PASSWORD  – Database password        (required)

QUICK-START FOR PERSON 2 AND PERSON 3
-------------------------------------
1. Wire the pool into backend/app/main.py:

    from contextlib import asynccontextmanager
    from fastapi import FastAPI
    from backend.app.db import init_db_pool, close_db_pool

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db_pool()
        yield
        close_db_pool()

    app = FastAPI(lifespan=lifespan)

2. Single-cursor queries (returns dict rows by default):

    from backend.app.db import get_db_cursor

    with get_db_cursor() as cur:
        cur.execute(
            "SELECT user_id, full_name, email, role, department "
            "FROM users WHERE user_id = %s",
            (user_id,),
        )
        user = cur.fetchone()

3. Multi-statement transactions:

    from backend.app.db import get_db_connection

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT max_participants FROM events WHERE event_id = %s FOR UPDATE", (event_id,))
            ...
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import psycopg
from dotenv import load_dotenv
from psycopg.rows import RowFactory, dict_row
from psycopg_pool import ConnectionPool

# Load backend/.env first (matches backend/.env.example), then fallback to root .env
_BACKEND_ENV = Path(__file__).resolve().parent.parent / ".env"
_ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_BACKEND_ENV)
load_dotenv(_ROOT_ENV)

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None


def _build_conninfo() -> str:
    """Assemble a libpq connection string from environment variables."""
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "smartcampushub")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASSWORD", "")

    missing = [
        k for k, v in {"DB_NAME": name, "DB_USER": user, "DB_PASSWORD": password}.items() if not v
    ]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Check backend/.env."
        )

    return f"host={host} port={port} dbname={name} user={user} password={password}"


def init_db_pool(min_size: int = 1, max_size: int = 10) -> None:
    """Open the Psycopg 3 connection pool. Call once during FastAPI startup."""
    global _pool
    if _pool is not None:
        logger.warning("init_db_pool() called but pool already exists – skipping.")
        return

    conninfo = _build_conninfo()
    _pool = ConnectionPool(
        conninfo=conninfo,
        min_size=min_size,
        max_size=max_size,
        kwargs={"row_factory": dict_row},
        open=True,
    )
    logger.info(
        "Database pool initialised (min=%d, max=%d, db=%s).",
        min_size,
        max_size,
        os.environ.get("DB_NAME", "smartcampushub"),
    )


def close_db_pool() -> None:
    """Close the Psycopg 3 connection pool. Call once during FastAPI shutdown."""
    global _pool
    if _pool is None:
        return
    _pool.close()
    _pool = None
    logger.info("Database pool closed.")


def _get_pool() -> ConnectionPool:
    """Return the active pool, raising a clear error if uninitialised."""
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialised. "
            "Call init_db_pool() before using database connections "
            "(typically in your FastAPI lifespan handler)."
        )
    return _pool


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """
    Yield a live database connection from the pool.
    Commits on clean exit; rolls back on exception; returns connection to pool.
    """
    pool = _get_pool()
    with pool.connection() as conn:
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()


@contextmanager
def get_db_cursor(
    row_factory: RowFactory = dict_row,
) -> Generator[psycopg.Cursor, None, None]:
    """
    Yield a database cursor inside a managed connection and transaction.
    Defaults to dict_row so rows behave as dicts (row["column_name"]).
    """
    with get_db_connection() as conn:
        with conn.cursor(row_factory=row_factory) as cur:
            yield cur


def check_db_health() -> dict:
    """Return a health-status dict for FastAPI /health checks."""
    db_name = os.environ.get("DB_NAME", "smartcampushub")
    try:
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            result = cur.fetchone()
        if result and result.get("ok") == 1:
            return {"status": "healthy", "database": db_name}
        return {"status": "unhealthy", "error": "Unexpected query result"}
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        return {"status": "unhealthy", "error": str(exc)}
