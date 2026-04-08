# Secure API Learning Session - Compressed History

**Date:** March 6, 2026  
**Learner:** Data Engineer (3y Python, PySpark/Databricks, basic bash)  
**Goal:** Build FastAPI with JWT authentication + database GET endpoints

---

## Session Summary

### Phase 1: Project Setup & SQLite Database

**Objective:** Create project structure and set up SQLite database.

**Key Decisions:**
- Used SQLite for local development (file-based, zero setup)
- Organized project: `secure-api/{auth, database, routes}`
- Used `uv` package manager (modern, faster than pip)

**Dependencies (requirements.txt):**
```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib==1.7.4
bcrypt==3.2.2
sqlalchemy==2.0.23
```

**Critical Fix:** Downgraded `bcrypt` to 3.2.2 (from 4.1.1) due to passlib compatibility issue with `__about__.__version__` attribute.

**Commands:**
```bash
mkdir -p secure-api/{auth,database,routes}
cd secure-api
uv sync
uv run python database/seed.py
uv run sqlite3 secure_api.db "SELECT * FROM users;"
```

---

### Phase 2: Database Architecture (`database/db.py`)

**Components Breakdown:**

| Component | Purpose | Usage |
|-----------|---------|-------|
| `DATABASE_URL` | SQLite connection string | Points to `./secure_api.db` |
| `engine` | Connection pool | Manages all DB connections; `check_same_thread=False` for async |
| `SessionLocal` | Session factory | Creates fresh session per request; handles transactions |
| `Base` | ORM registry | Parent class for all models; tracks table definitions |
| `User` class | ORM model | Maps Python objects ↔ database rows |

**How `Base` Works:**
- `Base = declarative_base()` creates a registry of all ORM models
- When you define `class User(Base)`, SQLAlchemy registers it
- `Base.metadata.create_all(engine)` generates SQL `CREATE TABLE` from registered models
- **Idempotent:** Safe to call multiple times (skips existing tables)

**Base Usage Across Project:**
1. **main.py:** `Base.metadata.create_all(bind=engine)` → initializes tables on startup
2. **seed.py:** `Base.metadata.create_all()` → ensures tables exist before seeding
3. **routes/api.py:** `db.query(User)` → queries using User model
4. **auth/security.py:** `db.query(User)` → validates login credentials

---

### Phase 3: Database Seeding (`database/seed.py`)

**Purpose:** Add test data for development/testing.

**Key Concepts:**
- **Schema vs. Data:** `main.py` creates empty table structure; `seed.py` populates it
- **Password Hashing:** Uses `passlib.CryptContext` with bcrypt (never store plain text)
- **Bcrypt 72-byte limit:** Passwords longer than 72 bytes are truncated by bcrypt itself

**Workflow:**
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()
user = User(username="testuser", hashed_password=pwd_context.hash("password123"), email="test@example.com")
db.add(user)
db.commit()
db.close()
```

**Run Once:** `uv run python database/seed.py`

---

### Phase 4: Project Structure & Initialization

**main.py Pattern:**
```python
from fastapi import FastAPI
from database.db import Base, engine

Base.metadata.create_all(bind=engine)  # Initialize tables
app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Run:** `uv run python main.py` → Server starts on `http://localhost:8000`

---

## Key Learning Points

### Why This Architecture?
1. **Separation of Concerns:** DB schema, initialization, routes, auth are separate modules
2. **Scalability:** Swap SQLite → PostgreSQL by changing one line (`DATABASE_URL`)
3. **Testability:** Mock `SessionLocal` in tests without touching real DB
4. **Transferability:** Pattern works across FastAPI, Flask, Django, etc.

### Dependency Management with `uv`
- **Version pinning** prevents compatibility issues (e.g., bcrypt 4.1.1 broke passlib)
- **`uv sync`** ensures reproducible environments
- **`uv run`** executes scripts in project's virtual environment

### SQLAlchemy ORM Benefits
- **No raw SQL:** Define tables as Python classes
- **Type safety:** Column types enforced at Python level
- **Injection prevention:** Parameterized queries built-in
- **Lazy loading:** Queries execute only when needed

---

## Current Project State

**Files Created:**
- ✅ `database/db.py` - SQLAlchemy engine, SessionLocal, User model
- ✅ `database/seed.py` - Test data population
- ✅ `main.py` - FastAPI app initialization
- ✅ `secure_api.db` - SQLite database file (auto-created)
- ✅ `requirements.txt` - Dependencies

**Database Status:**
- ✅ `users` table created with columns: `id`, `username`, `hashed_password`, `email`
- ✅ Sample users seeded (testuser, admin)
- ✅ Passwords hashed with bcrypt

**Next Phase:** Build authentication module (`auth/security.py`)
- JWT token generation & validation
- Protected endpoints
- Login endpoint

---

## Debugging Notes

**Issue:** `AttributeError: module 'bcrypt' has no attribute '__about__'`
- **Root Cause:** passlib 1.7.4 incompatible with bcrypt 4.x
- **Solution:** Downgrade bcrypt to 3.2.2
- **Lesson:** Always pin transitive dependencies; use `pip-audit` for security updates

**Issue:** `ValueError: password cannot be longer than 72 bytes`
- **Root Cause:** Bcrypt cipher block size limit (Blowfish algorithm)
- **Solution:** Don't manually truncate; bcrypt handles it
- **Lesson:** Understand cryptographic constraints, not just syntax

---

## Commands Reference

```bash
# Setup
uv sync                                    # Install dependencies
uv run python database/seed.py             # Seed test data
uv run python main.py                      # Start API server

# Inspection
uv run sqlite3 secure_api.db               # Open SQLite CLI
  > SELECT * FROM users;                   # View users
  > .schema users                          # View table structure
  > .exit                                  # Exit

# Testing
curl http://localhost:8000/health          # Test health endpoint
```

---

## Next Steps (Not Yet Implemented)

1. **auth/security.py** - JWT token creation & validation
2. **routes/api.py** - Protected GET endpoint for database queries
3. **Login endpoint** - Exchange credentials for JWT token
4. **Dependency injection** - FastAPI's `Depends()` for auth guards

---

## Learner Reflection Questions

1. Why is `Base.metadata.create_all()` idempotent? (Hint: check SQLAlchemy source)
2. What happens if you call `seed.py` twice? Why?
3. How would you modify `db.py` to use PostgreSQL instead of SQLite?
4. Why separate `seed.py` from `main.py` instead of combining them?

---

**Status:** Ready for authentication module implementation  
**Estimated Next Session:** 30-45 minutes for JWT + protected endpoints
