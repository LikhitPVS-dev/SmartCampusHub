-- =============================================================================
-- SmartCampusHub – College Portal
-- File:    database/reset_schema.sql
-- Owner:   Person 1 – Database Foundation
-- Target:  PostgreSQL 14+
--
-- DESTRUCTIVE RESET SCRIPT (Development Only)
-- Drops all triggers, trigger functions, and all six tables using CASCADE.
-- WARNING: Running this script permanently destroys all data in the database.
--
-- After running this, re-initialize with:
--   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql
-- =============================================================================

DROP TRIGGER  IF EXISTS trg_prevent_leader_removal  ON team_members;
DROP TRIGGER  IF EXISTS trg_team_leader_membership  ON hackathon_teams;
DROP FUNCTION IF EXISTS fn_prevent_leader_removal();
DROP FUNCTION IF EXISTS fn_enforce_team_leader_membership();

DROP TABLE IF EXISTS team_members    CASCADE;
DROP TABLE IF EXISTS hackathon_teams CASCADE;
DROP TABLE IF EXISTS announcements   CASCADE;
DROP TABLE IF EXISTS registrations   CASCADE;
DROP TABLE IF EXISTS events          CASCADE;
DROP TABLE IF EXISTS users           CASCADE;

