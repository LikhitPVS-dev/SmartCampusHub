-- =============================================================================
-- SmartCampusHub – College Portal
-- File:    database/seed.sql
-- Owner:   Person 1 – Database Foundation
-- Purpose: Realistic fictional sample data for local development and testing.
--
-- Run AFTER schema.sql on an empty database:
--   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/seed.sql
--
-- To wipe existing data before re-seeding, run database/reset_seed.sql first.
--
-- Password note:
--   All seed users share the password: College@123
--   The hash below is bcrypt(cost=12) of that string.
--   These are development-only accounts. Never use them in production.
-- =============================================================================


-- =============================================================================
-- USERS  (3 Admin · 3 Faculty · 9 Students)
-- All seed passwords = "College@123"
-- Hash = $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2
-- =============================================================================
INSERT INTO users (full_name, email, password_hash, role, department) VALUES

-- Admins
('Admin One',       'admin1@campus.edu',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Admin',   NULL),
('Admin Two',       'admin2@campus.edu',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Admin',   NULL),
('Admin Three',     'admin3@campus.edu',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Admin',   NULL),

-- Faculty
('Dr. Priya Sharma',    'priya.sharma@campus.edu',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Faculty', 'Computer Science'),
('Prof. Rahul Mehta',   'rahul.mehta@campus.edu',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Faculty', 'Electronics'),
('Dr. Anitha Nair',     'anitha.nair@campus.edu',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Faculty', 'Mathematics'),

-- Students
('Arjun Patel',         'arjun.patel@student.edu',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Computer Science'),
('Sneha Reddy',         'sneha.reddy@student.edu',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Computer Science'),
('Kiran Kumar',         'kiran.kumar@student.edu',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Electronics'),
('Meera Pillai',        'meera.pillai@student.edu',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Mathematics'),
('Rohit Singh',         'rohit.singh@student.edu',   '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Computer Science'),
('Divya Krishnamurthy', 'divya.k@student.edu',       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Electronics'),
('Sai Teja Reddy',      'sai.teja@student.edu',      '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Computer Science'),
('Lakshmi Devi',        'lakshmi.devi@student.edu',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Mathematics'),
('Nikhil Verma',        'nikhil.verma@student.edu',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGLP9X5K/Yq1Lz6PqJqaH2V6tS2', 'Student', 'Electronics');

-- IDs after insert:
--  1 = Admin One        | 2 = Admin Two       | 3 = Admin Three
--  4 = Dr. Priya Sharma | 5 = Prof. Rahul Mehta | 6 = Dr. Anitha Nair
--  7 = Arjun Patel      | 8 = Sneha Reddy     | 9 = Kiran Kumar
-- 10 = Meera Pillai    | 11 = Rohit Singh     | 12 = Divya K
-- 13 = Sai Teja Reddy  | 14 = Lakshmi Devi   | 15 = Nikhil Verma


-- =============================================================================
-- EVENTS  (mix of types and statuses)
-- organizer_id references Faculty or Admin users (IDs 1–6)
-- =============================================================================
INSERT INTO events (title, description, event_type, start_date, end_date,
                    registration_deadline, venue, organizer_id, status, max_participants)
VALUES

-- 1. Upcoming general seminar (unlimited capacity)
('Tech Horizons Seminar 2026',
 'An annual seminar covering emerging technology trends.',
 'Seminar',
 '2026-12-15 09:00:00+05:30',
 '2026-12-15 17:00:00+05:30',
 '2026-12-10 23:59:00+05:30',
 'Main Auditorium, Block A',
 4, 'Upcoming', NULL),

-- 2. Upcoming workshop (limited capacity)
('Python for Data Science Workshop',
 'Hands-on workshop covering NumPy, Pandas and Matplotlib.',
 'Workshop',
 '2026-12-20 10:00:00+05:30',
 '2026-12-20 16:00:00+05:30',
 '2026-12-17 23:59:00+05:30',
 'Computer Lab 3, Block B',
 4, 'Upcoming', 30),

-- 3. Ongoing hackathon (limited capacity)
('SmartCampus Hackathon 2026',
 'Build innovative solutions for real campus problems. Teams of 2–4.',
 'Hackathon',
 '2026-11-11 08:00:00+05:30',
 '2026-11-13 20:00:00+05:30',
 '2026-11-08 23:59:00+05:30',
 'Innovation Hub, Block C',
 5, 'Ongoing', 60),

-- 4. Completed event (historical)
('Annual Cultural Fest 2024',
 'Music, dance and art performances by college students.',
 'Cultural',
 '2024-11-10 10:00:00+05:30',
 '2024-11-11 22:00:00+05:30',
 '2024-11-05 23:59:00+05:30',
 'Open Air Theatre',
 1, 'Completed', 200),

-- 5. Cancelled event (historical)
('Mathematics Olympiad',
 'Inter-college mathematics competition. Cancelled due to scheduling conflict.',
 'Competition',
 '2025-01-30 09:00:00+05:30',
 '2025-01-30 17:00:00+05:30',
 '2025-01-25 23:59:00+05:30',
 'Exam Hall 1',
 6, 'Cancelled', 50),

-- 6. Upcoming hackathon (for a second team scenario)
('AI Innovation Hackathon',
 'Create AI-driven applications to solve societal challenges.',
 'Hackathon',
 '2027-01-10 08:00:00+05:30',
 '2027-01-12 20:00:00+05:30',
 '2027-01-05 23:59:00+05:30',
 'Innovation Hub, Block C',
 5, 'Upcoming', 80);

-- IDs after insert:
--  1 = Tech Horizons Seminar 2026
--  2 = Python Data Science Workshop
--  3 = SmartCampus Hackathon 2026  (Ongoing, Hackathon)
--  4 = Annual Cultural Fest 2024   (Completed)
--  5 = Mathematics Olympiad        (Cancelled)
--  6 = AI Innovation Hackathon     (Upcoming, Hackathon)


-- =============================================================================
-- REGISTRATIONS
-- Only Student users (IDs 7–15) may register.
-- =============================================================================
INSERT INTO registrations (student_id, event_id, registration_date, status) VALUES

-- Tech Horizons Seminar (event 1 – upcoming, deadline 2026-12-10)
(7,  1, '2026-11-15 10:00:00+05:30', 'Registered'),
(8,  1, '2026-11-16 11:30:00+05:30', 'Registered'),
(9,  1, '2026-11-17 09:15:00+05:30', 'Registered'),
(10, 1, '2026-11-18 14:00:00+05:30', 'Cancelled'),   -- cancelled registration, retained

-- Python Workshop (event 2 – upcoming, deadline 2026-12-17)
(7,  2, '2026-11-20 10:00:00+05:30', 'Registered'),
(11, 2, '2026-11-21 12:00:00+05:30', 'Registered'),
(12, 2, '2026-11-22 15:00:00+05:30', 'Registered'),

-- SmartCampus Hackathon 2026 (event 3 – ongoing, deadline 2026-11-08)
(7,  3, '2026-11-01 09:00:00+05:30', 'Registered'),
(8,  3, '2026-11-01 09:30:00+05:30', 'Registered'),
(9,  3, '2026-11-02 10:00:00+05:30', 'Registered'),
(10, 3, '2026-11-02 11:00:00+05:30', 'Registered'),
(11, 3, '2026-11-03 13:00:00+05:30', 'Registered'),
(12, 3, '2026-11-04 14:00:00+05:30', 'Registered'),

-- Cultural Fest (event 4 – completed, historical)
(13, 4, '2024-11-01 10:00:00+05:30', 'Registered'),
(14, 4, '2024-11-02 11:00:00+05:30', 'Registered'),
(15, 4, '2024-11-03 12:00:00+05:30', 'Cancelled'),   -- cancelled but retained

-- AI Innovation Hackathon (event 6 – upcoming, deadline 2027-01-05)
(13, 6, '2026-11-25 10:00:00+05:30', 'Registered'),
(14, 6, '2026-11-25 11:00:00+05:30', 'Registered'),
(15, 6, '2026-11-26 09:00:00+05:30', 'Registered');


-- =============================================================================
-- ANNOUNCEMENTS  (general + event-linked)
-- Only Faculty/Admin may create (IDs 1–6).
-- =============================================================================
INSERT INTO announcements (title, content, published_at, created_by, event_id) VALUES

-- General announcements (event_id = NULL)
('Welcome to Fall Semester 2026',
 'The portal is now live for Fall Semester 2026. Please update your profile and check upcoming events.',
 '2026-11-01 09:00:00+05:30', 1, NULL),

('Campus Maintenance Notice',
 'Block B labs will be unavailable on 18-Nov-2026 from 08:00 to 12:00 for scheduled maintenance.',
 '2026-11-05 10:00:00+05:30', 2, NULL),

('Library Extended Hours',
 'The main library will remain open until 22:00 during the examination preparation period.',
 '2026-11-08 08:30:00+05:30', 3, NULL),

-- Event-linked announcements
('Tech Horizons Seminar – Registration Open',
 'Registration for the Tech Horizons Seminar 2026 is now open. Register before 10 Dec 2026.',
 '2026-11-10 10:00:00+05:30', 4, 1),

('Python Workshop – Prerequisites',
 'Participants for the Python Data Science Workshop should have basic Python knowledge. Bring your own laptop.',
 '2026-11-12 11:00:00+05:30', 4, 2),

('SmartCampus Hackathon – Now Underway!',
 'The SmartCampus Hackathon 2026 has officially begun. Teams must submit their projects by 13 Nov at 18:00.',
 '2026-11-11 08:30:00+05:30', 5, 3),

('Mathematics Olympiad – Cancelled',
 'We regret to announce that the Mathematics Olympiad scheduled for 30 Jan 2025 has been cancelled. Apologies for the inconvenience.',
 '2025-01-22 09:00:00+05:30', 6, 5);


-- =============================================================================
-- HACKATHON TEAMS
-- hackathon_id must reference an event with event_type = 'Hackathon'.
-- team_leader_id must be a Student.
-- The trigger trg_team_leader_membership will auto-insert the leader
-- into team_members immediately after each INSERT here.
-- =============================================================================
INSERT INTO hackathon_teams (team_name, hackathon_id, team_leader_id) VALUES

-- SmartCampus Hackathon 2025 (event_id = 3)
('ByteBuilders',  3, 7),   -- Arjun leads
('CircuitSages',  3, 9),   -- Kiran leads

-- AI Innovation Hackathon (event_id = 6)
('NeuralNinjas',  6, 13),  -- Sai Teja leads
('DataDynamos',   6, 14);  -- Lakshmi leads

-- IDs after insert: 1 = ByteBuilders, 2 = CircuitSages,
--                   3 = NeuralNinjas,  4 = DataDynamos
-- Note: team leaders (7, 9, 13, 14) are automatically in team_members via trigger.


-- =============================================================================
-- TEAM MEMBERS
-- Leader rows already exist via trigger; only add non-leader members here.
-- student_id must be a Student user (IDs 7–15).
-- =============================================================================
INSERT INTO team_members (team_id, student_id) VALUES

-- ByteBuilders (team 1, leader = Arjun 7, already inserted by trigger)
(1, 8),   -- Sneha
(1, 11),  -- Rohit

-- CircuitSages (team 2, leader = Kiran 9, already inserted by trigger)
(2, 12),  -- Divya
(2, 10),  -- Meera

-- NeuralNinjas (team 3, leader = Sai Teja 13, already inserted by trigger)
(3, 15),  -- Nikhil

-- DataDynamos (team 4, leader = Lakshmi 14, already inserted by trigger)
(4, 15);  -- Nikhil (also in DataDynamos – allowed by current default schema)
           -- Remove this row if the team decides one-team-per-hackathon.
