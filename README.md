# SmartCampusHub

SmartCampusHub is a centralized college campus management web application designed to streamline campus events, student registrations, hackathon team formations, announcements, and user management.

## Technology Stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python FastAPI
- **Database:** PostgreSQL
- **Database Driver:** Psycopg 3

## Team Responsibilities

- **Person 1:** Database design and PostgreSQL setup.
- **Person 2:** Authentication, user management, and announcements.
- **Person 3:** Events, registrations, and hackathon teams.
- **Person 4:** Frontend development and integration.

## Database Foundation (Person 1)

- **Schema & Reset:** [`database/schema.sql`](database/schema.sql) | [`database/reset_schema.sql`](database/reset_schema.sql)
- **Seed & Reset:** [`database/seed.sql`](database/seed.sql) | [`database/reset_seed.sql`](database/reset_seed.sql)
- **Shared Connection Utility:** [`backend/app/db.py`](backend/app/db.py)
- **ER Diagram:** [`docs/er_diagram/ER_Diagram.png`](docs/er_diagram/ER_Diagram.png)
- **Setup & Integration Guide:** [`docs/setup_guide.md`](docs/setup_guide.md)
- **Database Tests:** [`tests/test_database.py`](tests/test_database.py) | [`tests/test_schema.py`](tests/test_schema.py)
