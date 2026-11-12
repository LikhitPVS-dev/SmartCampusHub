# SmartCampusHub – Database Setup & Integration Guide

**Owner:** Person 1 (Database Foundation)  
**Target:** PostgreSQL 14+ · Python 3.11+ · FastAPI · Psycopg 3

---

## 1. Prerequisites

- PostgreSQL 14+ running locally or accessible over TCP.
- Python 3.11+ with dependencies installed:

```bash
pip install -r backend/requirements.txt
```

---

## 2. Database & Environment Setup

Create the PostgreSQL database (default name in `backend/.env.example` is `smartcampushub`):

```sql
CREATE DATABASE smartcampushub;
```

Create `backend/.env` from `backend/.env.example`:

```bash
cp backend/.env.example backend/.env
```

Fill in your credentials (never commit `.env`):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smartcampushub
DB_USER=postgres
DB_PASSWORD=your_password

SECRET_KEY=your_secret_key
```

---

## 3. Schema Initialization & Reset

Initialize all six tables, triggers, and indexes on a **clean** database:

```bash
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql
```

> **Note:** `database/schema.sql` is **not idempotent** and does not drop existing tables. To wipe and recreate an existing development database from scratch, run `database/reset_schema.sql` first (**destroys all data**):
> ```bash
> psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/reset_schema.sql
> psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql
> ```

---

## 4. Sample Data (`seed.sql`)

Load fictional development data into an empty database:

```bash
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/seed.sql
```

To wipe all rows and reset identity sequences before re-seeding in development:

```bash
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/reset_seed.sql
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/seed.sql
```

All seed users share the development password **`College@123`** (stored as bcrypt hash).

---

## 5. Shared Connection Utility (`backend/app/db.py`)

All backend routers (`backend/app/routers/*`) must import from `backend.app.db`.

### FastAPI Lifespan (`backend/app/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.db import init_db_pool, close_db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db_pool()
    yield
    close_db_pool()

app = FastAPI(lifespan=lifespan)
```

### Queries (`get_db_cursor`) & Multi-Statement Transactions (`get_db_connection`)

```python
from backend.app.db import get_db_cursor, get_db_connection, check_db_health

# Single-cursor query (returns dict rows by default)
with get_db_cursor() as cur:
    cur.execute("SELECT user_id, full_name, role FROM users WHERE email = %s", (email,))
    user = cur.fetchone()

# Multi-statement atomic transaction
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT max_participants FROM events WHERE event_id = %s FOR UPDATE", (event_id,))
        ...
```

- Clean exit from `get_db_cursor()` / `get_db_connection()` **commits** automatically.
- Any exception **rolls back** automatically and re-raises.
- Do not call `conn.commit()` or `conn.rollback()` manually inside `with` blocks.

---

## 6. Running Database & Schema Tests

```bash
python -m pytest tests/ -v
```

---

## 7. ER Diagram & Schema Rules

- ER Diagram: [`docs/er_diagram/ER_Diagram.png`](er_diagram/ER_Diagram.png)
- Six tables: `users`, `events`, `registrations`, `announcements`, `hackathon_teams`, `team_members`.
- Foreign keys do **not** enforce `users.role` or `events.event_type`; Persons 2 and 3 must validate roles (`Student`, `Faculty`, `Admin`) and `event_type = 'Hackathon'` in application logic.
- Trigger `trg_team_leader_membership` automatically inserts `team_leader_id` into `team_members`; `trg_prevent_leader_removal` blocks removing the active leader directly.
- **Open team decision:** Whether a student may join multiple teams in the same hackathon is currently undecided (allowed by default).

