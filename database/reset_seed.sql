-- =============================================================================
-- SmartCampusHub – College Portal
-- File:    database/reset_seed.sql
-- Owner:   Person 1 – Database Foundation
-- Target:  PostgreSQL 14+
--
-- DESTRUCTIVE DATA RESET SCRIPT (Development Only)
-- Truncates all six tables and resets identity sequences to 1.
-- WARNING: Running this script permanently deletes all rows in all tables.
--
-- After running this, reload sample data with:
--   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/seed.sql
-- =============================================================================

TRUNCATE team_members, hackathon_teams, announcements,
         registrations, events, users
    RESTART IDENTITY CASCADE;

