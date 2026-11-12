-- =============================================================================
-- SmartCampusHub – College Portal
-- File:    database/schema.sql
-- Owner:   Person 1 – Database Foundation
-- Target:  PostgreSQL 14+
--
-- Creates all six tables in dependency-aware order on a clean database.
-- Includes primary keys, foreign keys, unique constraints, check constraints,
-- default values, triggers (team-leader membership rule), and indexes.
--
-- NOTE: This script is NOT idempotent; it assumes a clean database without
-- existing portal tables. To wipe and recreate an existing dev database,
-- run database/reset_schema.sql first (destroys all existing data).
--
-- How to run:
--   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql
-- =============================================================================


-- =============================================================================
-- TABLE 1: users
-- All portal users: Students, Faculty, Admins.
--
-- Integration notes for Person 2 and Person 3:
--   - Passwords are stored ONLY as hashes. Never insert or return plaintext.
--   - Role values are case-sensitive: 'Student', 'Faculty', 'Admin'.
--   - FKs pointing here from other tables do NOT enforce the role field.
--     Always validate the role in application logic before acting on it.
-- =============================================================================
CREATE TABLE users (
    user_id       INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name     VARCHAR(150) NOT NULL,
    email         VARCHAR(255) NOT NULL,
    password_hash TEXT         NOT NULL,
    role          VARCHAR(20)  NOT NULL,
    department    VARCHAR(100),                    -- NULL is allowed (e.g. Admin may have no dept)

    CONSTRAINT uq_users_email  UNIQUE (email),
    CONSTRAINT chk_users_role  CHECK  (role IN ('Student', 'Faculty', 'Admin'))
);


-- =============================================================================
-- TABLE 2: events
-- College events and hackathons created by Faculty or Admin.
--
-- Integration notes for Person 3 (event owner):
--   - Hackathon records must use event_type = 'Hackathon' (exact string).
--   - NULL max_participants means unlimited capacity.
--   - Never store a registration count column here; query registrations instead.
--   - Capacity and deadline enforcement belong in Person 3's application layer.
--   - The FK to users(organizer_id) does NOT guarantee organizer is Faculty/Admin.
--     Validate the role in Person 3's business logic.
-- =============================================================================
CREATE TABLE events (
    event_id              INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title                 VARCHAR(200) NOT NULL,
    description           TEXT,
    event_type            VARCHAR(50)  NOT NULL,
    start_date            TIMESTAMPTZ  NOT NULL,
    end_date              TIMESTAMPTZ  NOT NULL,
    registration_deadline TIMESTAMPTZ  NOT NULL,
    venue                 VARCHAR(255) NOT NULL,
    organizer_id          INTEGER      NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    status                VARCHAR(20)  NOT NULL,
    max_participants      INTEGER,

    CONSTRAINT chk_events_status          CHECK (status IN ('Upcoming', 'Ongoing', 'Completed', 'Cancelled')),
    CONSTRAINT chk_events_max_participants CHECK (max_participants IS NULL OR max_participants > 0),
    CONSTRAINT chk_events_dates           CHECK (end_date >= start_date),
    CONSTRAINT chk_events_reg_deadline    CHECK (registration_deadline <= start_date)
);


-- =============================================================================
-- TABLE 3: registrations
-- Student sign-ups for events.
--
-- Integration notes for Person 3 (registration owner):
--   - UNIQUE(student_id, event_id) prevents duplicate rows.
--   - For re-registration: UPDATE the existing row's status to 'Registered'
--     instead of INSERTing a new row (the UNIQUE constraint will block INSERT).
--   - Cancelled registrations are RETAINED; never DELETE them.
--   - Capacity check: COUNT(*) WHERE event_id = %s AND status = 'Registered'
--     Use SELECT ... FOR UPDATE on the events row for safe concurrent checks.
--   - The FK to users(student_id) does NOT guarantee role = 'Student'.
--     Validate in application logic before allowing registration.
-- =============================================================================
CREATE TABLE registrations (
    registration_id   INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id        INTEGER      NOT NULL REFERENCES users(user_id)   ON DELETE RESTRICT,
    event_id          INTEGER      NOT NULL REFERENCES events(event_id) ON DELETE RESTRICT,
    registration_date TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status            VARCHAR(20)  NOT NULL,

    CONSTRAINT uq_registrations_student_event UNIQUE (student_id, event_id),
    CONSTRAINT chk_registrations_status       CHECK  (status IN ('Registered', 'Cancelled'))
);


-- =============================================================================
-- TABLE 4: announcements
-- College-wide and event-linked announcements created by Faculty or Admin.
--
-- Integration notes for Person 2 (announcement owner):
--   - event_id is nullable. NULL means a general (non-event-specific) announcement.
--   - ON DELETE SET NULL: if the linked event is deleted, the announcement
--     survives and event_id becomes NULL.
--   - The FK to users(created_by) does NOT guarantee role = 'Faculty'/'Admin'.
--     Validate authorization in Person 2's business logic.
-- =============================================================================
CREATE TABLE announcements (
    announcement_id INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    content         TEXT         NOT NULL,
    published_at    TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER      NOT NULL REFERENCES users(user_id)   ON DELETE RESTRICT,
    event_id        INTEGER               REFERENCES events(event_id) ON DELETE SET NULL
    -- ON DELETE SET NULL is intentional: announcement outlives its linked event.
);


-- =============================================================================
-- TABLE 5: hackathon_teams
-- Teams participating in hackathon events.
--
-- Integration notes for Person 3 (team owner):
--   - hackathon_id must reference an event with event_type = 'Hackathon'.
--     The FK does NOT enforce event_type; validate in application logic.
--   - team_leader_id must reference a user with role = 'Student'.
--     The FK does NOT enforce the role; validate in application logic.
--   - The trigger trg_team_leader_membership (below) automatically inserts
--     the team leader as a team_members row on INSERT or leader UPDATE.
--   - Team name must be unique within a given hackathon.
-- =============================================================================
CREATE TABLE hackathon_teams (
    team_id        INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    team_name      VARCHAR(100) NOT NULL,
    hackathon_id   INTEGER      NOT NULL REFERENCES events(event_id) ON DELETE RESTRICT,
    team_leader_id INTEGER      NOT NULL REFERENCES users(user_id)   ON DELETE RESTRICT,

    CONSTRAINT uq_hackathon_team_name UNIQUE (hackathon_id, team_name)
);


-- =============================================================================
-- TABLE 6: team_members
-- Students belonging to hackathon teams.
-- Composite PK (team_id, student_id) prevents duplicate membership.
--
-- Integration notes for Person 3 (team-member owner):
--   - The FK to users(student_id) does NOT guarantee role = 'Student'.
--     Validate in application logic before adding a member.
--   - Deleting a hackathon_teams row cascades to remove its team_members rows.
--   - The trigger trg_prevent_leader_removal (below) blocks removal of the
--     team leader. Reassign the leader first, then remove the old leader if needed.
--
-- OPEN TEAM DECISION:
--   Whether a student may join multiple teams in the same hackathon is
--   currently UNDECIDED. By default, this schema allows it.
--   If the team later decides to restrict students to one team per hackathon,
--   an additional database trigger or application-level check will be required
--   (PostgreSQL does not allow subqueries inside index expressions).
-- =============================================================================
CREATE TABLE team_members (
    team_id    INTEGER NOT NULL REFERENCES hackathon_teams(team_id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(user_id)           ON DELETE RESTRICT,

    CONSTRAINT pk_team_members PRIMARY KEY (team_id, student_id)
);


-- =============================================================================
-- TRIGGER FUNCTIONS
-- Rule: Team leader must always be a member of their own team.
-- This is enforced at the database layer so the rule holds regardless of
-- which backend module inserts a team (Person 2, Person 3, or any future code).
-- =============================================================================

-- Function 1: Auto-insert the leader into team_members after team creation or
--             leader reassignment.
CREATE OR REPLACE FUNCTION fn_enforce_team_leader_membership()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO team_members (team_id, student_id)
    VALUES (NEW.team_id, NEW.team_leader_id)
    ON CONFLICT DO NOTHING;   -- leader already a member: no-op
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_team_leader_membership
AFTER INSERT OR UPDATE OF team_leader_id ON hackathon_teams
FOR EACH ROW EXECUTE FUNCTION fn_enforce_team_leader_membership();


-- Function 2: Block direct removal of the team leader from team_members.
--             Person 3 must reassign the leader first.
CREATE OR REPLACE FUNCTION fn_prevent_leader_removal()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM hackathon_teams
        WHERE team_id = OLD.team_id
          AND team_leader_id = OLD.student_id
    ) THEN
        RAISE EXCEPTION
            'Cannot remove user_id=% from team_members for team_id=% '
            'because they are the current team leader. '
            'Update hackathon_teams.team_leader_id first.',
            OLD.student_id, OLD.team_id;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_leader_removal
BEFORE DELETE ON team_members
FOR EACH ROW EXECUTE FUNCTION fn_prevent_leader_removal();


-- =============================================================================
-- INDEXES
-- PostgreSQL does NOT automatically index foreign-key columns.
-- All FK columns and common filter/sort columns are indexed explicitly.
-- =============================================================================

-- users  (email already indexed by UNIQUE constraint)

-- events
CREATE INDEX idx_events_organizer_id  ON events(organizer_id);
CREATE INDEX idx_events_status        ON events(status);
CREATE INDEX idx_events_start_date    ON events(start_date);
CREATE INDEX idx_events_event_type    ON events(event_type);

-- registrations
CREATE INDEX idx_reg_student_id       ON registrations(student_id);
CREATE INDEX idx_reg_event_id         ON registrations(event_id);
CREATE INDEX idx_reg_event_status     ON registrations(event_id, status); -- fast capacity check

-- announcements
CREATE INDEX idx_ann_created_by       ON announcements(created_by);
CREATE INDEX idx_ann_event_id         ON announcements(event_id);
CREATE INDEX idx_ann_published_at     ON announcements(published_at DESC);

-- hackathon_teams
CREATE INDEX idx_ht_hackathon_id      ON hackathon_teams(hackathon_id);
CREATE INDEX idx_ht_team_leader_id    ON hackathon_teams(team_leader_id);

-- team_members
CREATE INDEX idx_tm_student_id        ON team_members(student_id);
-- team_id is already the leading column of the composite PK index
