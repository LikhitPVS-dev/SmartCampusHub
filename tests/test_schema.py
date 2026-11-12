"""
tests/test_schema.py
Person 1 â€“ Database Foundation | SmartCampusHub College Portal

Tests:
  - All six tables exist.
  - Every column has the correct name and data type.
  - Primary keys exist on the correct columns.
  - Foreign-key relationships are present.
  - UNIQUE constraints are enforced.
  - CHECK constraints reject invalid values.
  - DEFAULT values are applied.
  - Trigger: team leader auto-added to team_members.
  - Trigger: team leader cannot be directly removed from team_members.

Requirements:
  - schema.sql applied to the target database (seed.sql NOT required).
  - Run:  pytest tests/test_schema.py -v
"""

import pytest
import psycopg

from backend.app.db import init_db_pool, close_db_pool, get_db_cursor, get_db_connection


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def db_pool():
    init_db_pool(min_size=1, max_size=5)
    yield
    close_db_pool()


@pytest.fixture(scope="module")
def clean_schema():
    """
    Insert minimal valid rows needed for FK-dependent tests,
    then clean up after the whole module runs.
    Uses a stable test user and event that can be referenced by other tests.
    """
    # Minimal admin user
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES ('Test Admin', 'schema_test_admin@test.local',
                    'hash_placeholder', 'Admin')
            ON CONFLICT (email) DO NOTHING
            RETURNING user_id
        """)
        row = cur.fetchone()

    with get_db_cursor() as cur:
        cur.execute(
            "SELECT user_id FROM users WHERE email = 'schema_test_admin@test.local'"
        )
        admin_id = cur.fetchone()["user_id"]

    # Minimal student user
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES ('Test Student', 'schema_test_student@test.local',
                    'hash_placeholder', 'Student')
            ON CONFLICT (email) DO NOTHING
        """)

    with get_db_cursor() as cur:
        cur.execute(
            "SELECT user_id FROM users WHERE email = 'schema_test_student@test.local'"
        )
        student_id = cur.fetchone()["user_id"]

    # Minimal hackathon event
    with get_db_cursor() as cur:
        cur.execute("""
            INSERT INTO events (title, event_type, start_date, end_date,
                                registration_deadline, venue, organizer_id, status)
            VALUES ('Schema Test Hackathon', 'Hackathon',
                    NOW() + INTERVAL '10 days',
                    NOW() + INTERVAL '12 days',
                    NOW() + INTERVAL '5 days',
                    'Test Venue', %s, 'Upcoming')
            RETURNING event_id
        """, (admin_id,))
        event_id = cur.fetchone()["event_id"]

    yield {"admin_id": admin_id, "student_id": student_id, "event_id": event_id}

    # Teardown: remove in reverse FK order (hackathon_teams cascades to team_members)
    with get_db_cursor() as cur:
        cur.execute("DELETE FROM hackathon_teams WHERE hackathon_id = %s", (event_id,))
        cur.execute("DELETE FROM team_members   WHERE student_id IN (%s, %s)", (admin_id, student_id))
        cur.execute("DELETE FROM announcements  WHERE event_id = %s OR created_by IN (%s, %s)",
                    (event_id, admin_id, student_id))
        cur.execute("DELETE FROM registrations  WHERE student_id IN (%s, %s)", (admin_id, student_id))
        cur.execute("DELETE FROM events         WHERE event_id = %s", (event_id,))
        cur.execute("DELETE FROM users          WHERE user_id  IN (%s, %s)", (admin_id, student_id))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_tables() -> list[str]:
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
        """)
        return [r["table_name"] for r in cur.fetchall()]


def _get_columns(table: str) -> dict[str, dict]:
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT column_name,
                   data_type,
                   is_nullable,
                   column_default,
                   is_identity,
                   identity_generation
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
        """, (table,))
        return {r["column_name"]: r for r in cur.fetchall()}


# ---------------------------------------------------------------------------
# 1. Table existence
# ---------------------------------------------------------------------------

class TestTableExistence:

    REQUIRED_TABLES = {
        "users", "events", "registrations",
        "announcements", "hackathon_teams", "team_members"
    }

    def test_all_six_tables_exist(self):
        existing = set(_get_tables())
        missing = self.REQUIRED_TABLES - existing
        assert not missing, f"Missing tables: {missing}"

    def test_no_extra_unexpected_tables(self):
        existing = set(_get_tables())
        assert existing == self.REQUIRED_TABLES, (
            f"Schema must contain exactly the 6 agreed tables. "
            f"Extra: {existing - self.REQUIRED_TABLES}, "
            f"Missing: {self.REQUIRED_TABLES - existing}"
        )


# ---------------------------------------------------------------------------
# 2. Column definitions
# ---------------------------------------------------------------------------

class TestColumnDefinitions:

    def test_users_columns(self):
        cols = _get_columns("users")
        assert set(cols.keys()) == {
            "user_id", "full_name", "email", "password_hash", "role", "department"
        }
        assert cols["user_id"]["data_type"]           == "integer"
        assert cols["user_id"]["is_identity"]         == "YES"
        assert cols["user_id"]["identity_generation"] == "ALWAYS"
        assert cols["full_name"]["data_type"]         == "character varying"
        assert cols["email"]["data_type"]             == "character varying"
        assert cols["password_hash"]["data_type"]     == "text"
        assert cols["role"]["data_type"]              == "character varying"
        assert cols["department"]["data_type"]        == "character varying"
        assert cols["user_id"]["is_nullable"]         == "NO"
        assert cols["full_name"]["is_nullable"]       == "NO"
        assert cols["email"]["is_nullable"]           == "NO"
        assert cols["password_hash"]["is_nullable"]   == "NO"
        assert cols["role"]["is_nullable"]            == "NO"
        assert cols["department"]["is_nullable"]      == "YES"

    def test_events_columns(self):
        cols = _get_columns("events")
        required = [
            "event_id", "title", "description", "event_type", "start_date",
            "end_date", "registration_deadline", "venue", "organizer_id",
            "status", "max_participants"
        ]
        assert set(cols.keys()) == set(required)
        assert cols["event_id"]["data_type"]              == "integer"
        assert cols["event_id"]["is_identity"]            == "YES"
        assert cols["event_id"]["identity_generation"]    == "ALWAYS"
        assert cols["start_date"]["data_type"]            == "timestamp with time zone"
        assert cols["end_date"]["data_type"]              == "timestamp with time zone"
        assert cols["registration_deadline"]["data_type"] == "timestamp with time zone"
        assert cols["organizer_id"]["data_type"]          == "integer"
        assert cols["max_participants"]["data_type"]      == "integer"
        assert cols["max_participants"]["is_nullable"]    == "YES"
        assert cols["description"]["is_nullable"]         == "YES"

    def test_registrations_columns(self):
        cols = _get_columns("registrations")
        assert set(cols.keys()) == {
            "registration_id", "student_id", "event_id",
            "registration_date", "status"
        }
        assert cols["registration_id"]["data_type"]           == "integer"
        assert cols["registration_id"]["is_identity"]         == "YES"
        assert cols["registration_id"]["identity_generation"] == "ALWAYS"
        assert cols["student_id"]["data_type"]                == "integer"
        assert cols["event_id"]["data_type"]                  == "integer"
        assert cols["registration_date"]["data_type"]         == "timestamp with time zone"
        assert cols["registration_date"]["column_default"]    is not None

    def test_announcements_columns(self):
        cols = _get_columns("announcements")
        assert set(cols.keys()) == {
            "announcement_id", "title", "content",
            "published_at", "created_by", "event_id"
        }
        assert cols["announcement_id"]["data_type"]           == "integer"
        assert cols["announcement_id"]["is_identity"]         == "YES"
        assert cols["announcement_id"]["identity_generation"] == "ALWAYS"
        assert cols["published_at"]["data_type"]              == "timestamp with time zone"
        assert cols["published_at"]["column_default"]         is not None
        assert cols["created_by"]["data_type"]                == "integer"
        assert cols["event_id"]["data_type"]                  == "integer"
        assert cols["event_id"]["is_nullable"]                == "YES"

    def test_hackathon_teams_columns(self):
        cols = _get_columns("hackathon_teams")
        assert set(cols.keys()) == {
            "team_id", "team_name", "hackathon_id", "team_leader_id"
        }
        assert cols["team_id"]["data_type"]           == "integer"
        assert cols["team_id"]["is_identity"]         == "YES"
        assert cols["team_id"]["identity_generation"] == "ALWAYS"
        assert cols["hackathon_id"]["data_type"]      == "integer"
        assert cols["team_leader_id"]["data_type"]    == "integer"

    def test_team_members_columns(self):
        cols = _get_columns("team_members")
        assert set(cols.keys()) == {"team_id", "student_id"}
        assert cols["team_id"]["data_type"]    == "integer"
        assert cols["team_id"]["is_identity"]  == "NO"
        assert cols["student_id"]["data_type"] == "integer"
        assert cols["student_id"]["is_identity"] == "NO"


# ---------------------------------------------------------------------------
# 3. Primary keys
# ---------------------------------------------------------------------------

class TestPrimaryKeys:

    def _get_pk_columns(self, table: str) -> list[str]:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema    = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_schema    = 'public'
                  AND tc.table_name      = %s
                ORDER BY kcu.ordinal_position
            """, (table,))
            return [r["column_name"] for r in cur.fetchall()]

    def test_users_pk(self):
        assert self._get_pk_columns("users") == ["user_id"]

    def test_events_pk(self):
        assert self._get_pk_columns("events") == ["event_id"]

    def test_registrations_pk(self):
        assert self._get_pk_columns("registrations") == ["registration_id"]

    def test_announcements_pk(self):
        assert self._get_pk_columns("announcements") == ["announcement_id"]

    def test_hackathon_teams_pk(self):
        assert self._get_pk_columns("hackathon_teams") == ["team_id"]

    def test_team_members_composite_pk(self):
        pk_cols = self._get_pk_columns("team_members")
        assert set(pk_cols) == {"team_id", "student_id"}
        assert len(pk_cols) == 2


# ---------------------------------------------------------------------------
# 4. Foreign keys
# ---------------------------------------------------------------------------

class TestForeignKeys:

    def _get_fks(self, table: str) -> list[dict]:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT
                    kcu.column_name         AS column_name,
                    ccu.table_name          AS foreign_table,
                    ccu.column_name         AS foreign_column,
                    rc.delete_rule          AS on_delete
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema    = kcu.table_schema
                JOIN information_schema.referential_constraints rc
                  ON tc.constraint_name = rc.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                  ON rc.unique_constraint_name = ccu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema    = 'public'
                  AND tc.table_name      = %s
            """, (table,))
            return cur.fetchall()

    def _fk_map(self, table: str) -> dict[str, dict]:
        return {r["column_name"]: r for r in self._get_fks(table)}

    def test_events_fk_organizer(self):
        fks = self._fk_map("events")
        assert "organizer_id" in fks
        assert fks["organizer_id"]["foreign_table"]  == "users"
        assert fks["organizer_id"]["foreign_column"] == "user_id"
        assert fks["organizer_id"]["on_delete"]      == "RESTRICT"

    def test_registrations_fk_student(self):
        fks = self._fk_map("registrations")
        assert "student_id" in fks
        assert fks["student_id"]["foreign_table"]  == "users"
        assert fks["student_id"]["foreign_column"] == "user_id"
        assert fks["student_id"]["on_delete"]      == "RESTRICT"

    def test_registrations_fk_event(self):
        fks = self._fk_map("registrations")
        assert "event_id" in fks
        assert fks["event_id"]["foreign_table"]  == "events"
        assert fks["event_id"]["foreign_column"] == "event_id"
        assert fks["event_id"]["on_delete"]      == "RESTRICT"

    def test_announcements_fk_created_by(self):
        fks = self._fk_map("announcements")
        assert "created_by" in fks
        assert fks["created_by"]["foreign_table"]  == "users"
        assert fks["created_by"]["on_delete"]      == "RESTRICT"

    def test_announcements_fk_event_set_null(self):
        fks = self._fk_map("announcements")
        assert "event_id" in fks
        assert fks["event_id"]["foreign_table"]  == "events"
        assert fks["event_id"]["on_delete"]      == "SET NULL"

    def test_hackathon_teams_fk_hackathon(self):
        fks = self._fk_map("hackathon_teams")
        assert "hackathon_id" in fks
        assert fks["hackathon_id"]["foreign_table"]  == "events"
        assert fks["hackathon_id"]["on_delete"]      == "RESTRICT"

    def test_hackathon_teams_fk_leader(self):
        fks = self._fk_map("hackathon_teams")
        assert "team_leader_id" in fks
        assert fks["team_leader_id"]["foreign_table"]  == "users"
        assert fks["team_leader_id"]["on_delete"]      == "RESTRICT"

    def test_team_members_fk_team(self):
        fks = self._fk_map("team_members")
        assert "team_id" in fks
        assert fks["team_id"]["foreign_table"]  == "hackathon_teams"
        assert fks["team_id"]["on_delete"]      == "CASCADE"

    def test_team_members_fk_student(self):
        fks = self._fk_map("team_members")
        assert "student_id" in fks
        assert fks["student_id"]["foreign_table"]  == "users"
        assert fks["student_id"]["on_delete"]      == "RESTRICT"


# ---------------------------------------------------------------------------
# 5. UNIQUE constraints
# ---------------------------------------------------------------------------

class TestUniqueConstraints:

    def _has_unique(self, table: str, columns: list[str]) -> bool:
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT tc.constraint_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema    = kcu.table_schema
                WHERE tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY')
                  AND tc.table_schema = 'public'
                  AND tc.table_name   = %s
                GROUP BY tc.constraint_name
                HAVING array_agg(kcu.column_name::text ORDER BY kcu.ordinal_position)
                       = %s::text[]
            """, (table, columns))
            return cur.fetchone() is not None

    def test_users_email_unique(self):
        assert self._has_unique("users", ["email"])

    def test_registrations_student_event_unique(self):
        assert self._has_unique("registrations", ["student_id", "event_id"])

    def test_hackathon_teams_name_unique_per_hackathon(self):
        assert self._has_unique("hackathon_teams", ["hackathon_id", "team_name"])

    def test_team_members_composite_pk_is_unique(self):
        # The composite PK implicitly enforces uniqueness
        assert self._has_unique("team_members", ["team_id", "student_id"])


# ---------------------------------------------------------------------------
# 6. CHECK constraints
# ---------------------------------------------------------------------------

class TestCheckConstraints:

    def test_users_role_check(self):
        """Invalid role must be rejected."""
        with pytest.raises(psycopg.errors.CheckViolation):
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO users (full_name, email, password_hash, role)
                    VALUES ('Bad Role', 'badrole@test.local', 'hash', 'Manager')
                """)

    def test_events_status_check(self, clean_schema):
        """Invalid event status must be rejected."""
        admin_id = clean_schema["admin_id"]

        with pytest.raises(psycopg.errors.CheckViolation):
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO events (title, event_type, start_date, end_date,
                                        registration_deadline, venue, organizer_id, status)
                    VALUES ('Bad Status', 'Seminar',
                            NOW() + INTERVAL '5 days',
                            NOW() + INTERVAL '6 days',
                            NOW() + INTERVAL '2 days',
                            'Hall A', %s, 'Draft')
                """, (admin_id,))

    def test_events_max_participants_check(self, clean_schema):
        """max_participants = 0 must be rejected (must be > 0 when provided)."""
        admin_id = clean_schema["admin_id"]

        with pytest.raises(psycopg.errors.CheckViolation):
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO events (title, event_type, start_date, end_date,
                                        registration_deadline, venue, organizer_id,
                                        status, max_participants)
                    VALUES ('Zero Capacity', 'Seminar',
                            NOW() + INTERVAL '5 days',
                            NOW() + INTERVAL '6 days',
                            NOW() + INTERVAL '2 days',
                            'Hall A', %s, 'Upcoming', 0)
                """, (admin_id,))

    def test_events_date_order_check(self, clean_schema):
        """end_date < start_date must be rejected."""
        admin_id = clean_schema["admin_id"]

        with pytest.raises(psycopg.errors.CheckViolation):
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO events (title, event_type, start_date, end_date,
                                        registration_deadline, venue, organizer_id, status)
                    VALUES ('Bad Dates', 'Seminar',
                            NOW() + INTERVAL '6 days',
                            NOW() + INTERVAL '5 days',
                            NOW() + INTERVAL '2 days',
                            'Hall A', %s, 'Upcoming')
                """, (admin_id,))

    def test_registrations_status_check(self, clean_schema):
        """Invalid registration status must be rejected."""
        student_id = clean_schema["student_id"]
        event_id = clean_schema["event_id"]

        with pytest.raises(psycopg.errors.CheckViolation):
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO registrations (student_id, event_id, status)
                    VALUES (%s, %s, 'Pending')
                """, (student_id, event_id))


# ---------------------------------------------------------------------------
# 7. UNIQUE constraint enforcement (via real INSERTs)
# ---------------------------------------------------------------------------

class TestUniqueEnforcement:

    def test_duplicate_email_rejected(self):
        """Two users with the same email must raise UniqueViolation."""
        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO users (full_name, email, password_hash, role)
                VALUES ('Dup User 1', 'dup_email_test@test.local', 'hash', 'Student')
                ON CONFLICT DO NOTHING
            """)

        with pytest.raises(psycopg.errors.UniqueViolation):
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO users (full_name, email, password_hash, role)
                    VALUES ('Dup User 2', 'dup_email_test@test.local', 'hash', 'Admin')
                """)

        # Clean up
        with get_db_cursor() as cur:
            cur.execute(
                "DELETE FROM users WHERE email = 'dup_email_test@test.local'"
            )

    def test_duplicate_registration_rejected(self, clean_schema):
        """Same student registering for the same event twice must raise UniqueViolation."""
        sid = clean_schema["student_id"]
        eid = clean_schema["event_id"]

        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO registrations (student_id, event_id, status)
                VALUES (%s, %s, 'Registered')
                ON CONFLICT DO NOTHING
            """, (sid, eid))

        with pytest.raises(psycopg.errors.UniqueViolation):
            with get_db_cursor() as cur:
                cur.execute("""
                    INSERT INTO registrations (student_id, event_id, status)
                    VALUES (%s, %s, 'Registered')
                """, (sid, eid))

        with get_db_cursor() as cur:
            cur.execute(
                "DELETE FROM registrations WHERE student_id = %s AND event_id = %s",
                (sid, eid)
            )


# ---------------------------------------------------------------------------
# 8. Trigger tests
# ---------------------------------------------------------------------------

class TestTriggers:

    def test_team_leader_auto_added_to_members(self, clean_schema):
        """
        Creating a hackathon team must automatically insert the leader
        into team_members (via trigger trg_team_leader_membership).
        """
        sid = clean_schema["student_id"]
        eid = clean_schema["event_id"]

        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO hackathon_teams (team_name, hackathon_id, team_leader_id)
                VALUES ('TriggerTestTeam', %s, %s)
                RETURNING team_id
            """, (eid, sid))
            team_id = cur.fetchone()["team_id"]

        with get_db_cursor() as cur:
            cur.execute("""
                SELECT 1 FROM team_members
                WHERE team_id = %s AND student_id = %s
            """, (team_id, sid))
            row = cur.fetchone()

        assert row is not None, "Leader was not auto-added to team_members by trigger"

        # Cleanup â€“ delete team first (cascades to team_members)
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM hackathon_teams WHERE team_id = %s", (team_id,))

    def test_leader_removal_blocked(self, clean_schema):
        """
        Directly removing the team leader from team_members must raise
        an exception (via trigger trg_prevent_leader_removal).
        """
        sid = clean_schema["student_id"]
        eid = clean_schema["event_id"]

        with get_db_cursor() as cur:
            cur.execute("""
                INSERT INTO hackathon_teams (team_name, hackathon_id, team_leader_id)
                VALUES ('LeaderRemovalTest', %s, %s)
                RETURNING team_id
            """, (eid, sid))
            team_id = cur.fetchone()["team_id"]

        with pytest.raises(psycopg.errors.RaiseException):
            with get_db_cursor() as cur:
                cur.execute("""
                    DELETE FROM team_members
                    WHERE team_id = %s AND student_id = %s
                """, (team_id, sid))

        # Cleanup â€“ delete team first (cascades to team_members)
        with get_db_cursor() as cur:
            cur.execute("DELETE FROM hackathon_teams WHERE team_id = %s", (team_id,))


# ---------------------------------------------------------------------------
# 9. Index verification
# ---------------------------------------------------------------------------

class TestIndexes:

    EXPECTED_INDEXES = {
        "idx_events_organizer_id",
        "idx_events_status",
        "idx_events_start_date",
        "idx_events_event_type",
        "idx_reg_student_id",
        "idx_reg_event_id",
        "idx_reg_event_status",
        "idx_ann_created_by",
        "idx_ann_event_id",
        "idx_ann_published_at",
        "idx_ht_hackathon_id",
        "idx_ht_team_leader_id",
        "idx_tm_student_id",
    }

    def test_all_expected_indexes_exist(self):
        with get_db_cursor() as cur:
            cur.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public'
            """)
            existing = {r["indexname"] for r in cur.fetchall()}

        missing = self.EXPECTED_INDEXES - existing
        assert not missing, f"Missing expected indexes: {missing}"

