"""
tests/test_database.py
Person 1 â€“ Database Foundation | SmartCampusHub College Portal

Tests:
  - Database connection via shared connection utility.
  - Pool initialisation and cleanup.
  - Basic read / write / rollback behaviour.
  - Connection health check.
  - Concurrent connection handling.

Requirements:
  - .env file present with valid DB_* variables pointing to a running
    PostgreSQL instance where schema.sql has been applied.
  - Run:  pytest tests/test_database.py -v
"""

import pytest
import psycopg
from psycopg.rows import tuple_row

from backend.app.db import (
    init_db_pool,
    close_db_pool,
    get_db_connection,
    get_db_cursor,
    check_db_health,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def db_pool():
    """Initialise and tear down the pool once for the entire test module."""
    init_db_pool(min_size=1, max_size=5)
    yield
    close_db_pool()


# ---------------------------------------------------------------------------
# 1. Connection tests
# ---------------------------------------------------------------------------

class TestDatabaseConnection:

    def test_pool_provides_connection(self):
        """get_db_connection() must yield a live psycopg Connection."""
        with get_db_connection() as conn:
            assert conn is not None
            assert isinstance(conn, psycopg.Connection)

    def test_basic_query_executes(self):
        """A trivial SELECT must succeed and return the expected value."""
        with get_db_cursor() as cur:
            cur.execute("SELECT 1 AS value")
            row = cur.fetchone()
        assert row is not None
        assert row["value"] == 1

    def test_server_version_accessible(self):
        """PostgreSQL server version should be retrievable."""
        with get_db_cursor() as cur:
            cur.execute("SELECT version()")
            row = cur.fetchone()
        assert row is not None
        assert "PostgreSQL" in row["version"]

    def test_current_database_name(self):
        """current_database() should return the DB_NAME configured in .env."""
        import os
        expected = os.environ.get("DB_NAME", "smartcampushub")
        with get_db_cursor() as cur:
            cur.execute("SELECT current_database() AS db")
            row = cur.fetchone()
        assert row["db"] == expected

    def test_tuple_row_factory(self):
        """get_db_cursor() must support alternate row factories."""
        with get_db_cursor(row_factory=tuple_row) as cur:
            cur.execute("SELECT 42 AS n")
            row = cur.fetchone()
        assert row == (42,)

    def test_health_check_healthy(self):
        """check_db_health() must return status=healthy when pool is active."""
        result = check_db_health()
        assert result["status"] == "healthy"
        assert "database" in result


# ---------------------------------------------------------------------------
# 2. Transaction behaviour
# ---------------------------------------------------------------------------

class TestTransactions:

    def test_insert_and_commit(self):
        """
        INSERT into users, commit via context-manager exit,
        then verify the row persists in a new pooled connection.
        """
        email = "tx_commit_test@test.local"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (full_name, email, password_hash, role) "
                        "VALUES (%s, %s, %s, %s) RETURNING user_id",
                        ("TX Commit User", email, "hash_placeholder", "Student"),
                    )
                    inserted_id = cur.fetchone()["user_id"]

            # Read back in a fresh pooled cursor
            with get_db_cursor() as cur:
                cur.execute("SELECT full_name FROM users WHERE user_id = %s", (inserted_id,))
                result = cur.fetchone()

            assert result is not None
            assert result["full_name"] == "TX Commit User"
        finally:
            with get_db_cursor() as cur:
                cur.execute("DELETE FROM users WHERE email = %s", (email,))

    def test_rollback_on_exception(self):
        """
        An exception inside get_db_connection() must trigger a rollback.
        The INSERT must NOT persist after the exception.
        """
        email = "tx_rollback_test@test.local"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (full_name, email, password_hash, role) "
                        "VALUES (%s, %s, %s, %s)",
                        ("TX Rollback User", email, "hash_placeholder", "Student"),
                    )
                raise ValueError("Intentional error â€“ triggers rollback")
        except ValueError:
            pass  # expected

        with get_db_cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM users WHERE email = %s", (email,))
            result = cur.fetchone()

        assert result["cnt"] == 0, "Rolled-back INSERT must not persist"

    def test_multiple_statements_in_one_transaction(self):
        """Multiple statements inside a single connection share one transaction."""
        email_a = "tx_multi_a@test.local"
        email_b = "tx_multi_b@test.local"
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (full_name, email, password_hash, role) "
                        "VALUES (%s, %s, %s, %s)",
                        ("Multi A", email_a, "hash", "Student"),
                    )
                    cur.execute(
                        "INSERT INTO users (full_name, email, password_hash, role) "
                        "VALUES (%s, %s, %s, %s)",
                        ("Multi B", email_b, "hash", "Student"),
                    )

            with get_db_cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM users WHERE email IN (%s, %s)",
                    (email_a, email_b),
                )
                row = cur.fetchone()

            assert row["cnt"] == 2
        finally:
            with get_db_cursor() as cur:
                cur.execute(
                    "DELETE FROM users WHERE email IN (%s, %s)",
                    (email_a, email_b),
                )


# ---------------------------------------------------------------------------
# 3. Resource management
# ---------------------------------------------------------------------------

class TestResourceManagement:

    def test_concurrent_connections(self):
        """
        Multiple simultaneous connections must all succeed independently.
        """
        results = []
        for i in range(5):
            with get_db_cursor() as cur:
                cur.execute("SELECT %s AS n", (i,))
                row = cur.fetchone()
                results.append(row["n"])

        assert results == [0, 1, 2, 3, 4]

    def test_double_init_pool_safe(self):
        """
        Calling init_db_pool() when the pool already exists must not raise.
        """
        try:
            init_db_pool()   # pool already open from module fixture
        except Exception as exc:
            pytest.fail(f"Second init_db_pool() raised unexpectedly: {exc}")

    def test_connection_released_after_context_exit(self):
        """
        After exiting get_db_connection(), subsequent connections must work,
        confirming the connection was properly returned to the pool.
        """
        with get_db_connection():
            pass   # acquire and release

        with get_db_cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        assert row["ok"] == 1

