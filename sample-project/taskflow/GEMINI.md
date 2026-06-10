# TaskFlow — Gemini CLI Context

## Project Overview
TaskFlow is a REST API for managing personal tasks. Built with FastAPI + SQLite.
Run it with: `uvicorn main:app --reload`
Docs at: http://localhost:8000/docs

## Key Files
- `main.py` — FastAPI app, middleware, router registration
- `models.py` — SQLAlchemy models: User, Task, Tag (many-to-many via task_tags)
- `schemas.py` — Pydantic v2 schemas for request/response validation
- `auth.py` — JWT authentication: hash_password, verify_password, get_current_user
- `database.py` — SQLAlchemy engine, SessionLocal, get_db() dependency
- `routers/users.py` — POST /users/register, POST /users/login
- `routers/tasks.py` — CRUD for /tasks/ (requires auth)
- `routers/tags.py` — CRUD for /tags/ (requires auth)

## API Endpoints
```
POST   /users/register      Create account {email, username, password}
POST   /users/login         Get JWT token (form: username, password)
GET    /tasks/              List tasks (query: completed, priority, tag)
POST   /tasks/              Create task {title, description, priority, due_date, tag_ids}
GET    /tasks/{id}          Get single task
PATCH  /tasks/{id}          Update task fields
DELETE /tasks/{id}          Delete task
GET    /tags/               List all tags
POST   /tags/               Create tag {name, color}
DELETE /tags/{id}           Delete tag
GET    /health              Health check
```

## Authentication
All /tasks/ and /tags/ routes require: `Authorization: Bearer <token>`
Get a token from POST /users/login with form-encoded username+password.

## Database
SQLite file: `taskflow.db` in project root (created automatically on first run).
Reset: delete `taskflow.db` and restart the server.

## Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Start server (auto-reload on file changes)
uvicorn main:app --reload

# Run tests
pytest tests/ -v

# Quick API test (after starting server)
curl http://localhost:8000/health
```

## Common Tasks for Gemini CLI
- "Explain how the JWT authentication flow works in this project"
- "Add a due_date filter to GET /tasks/"
- "Write a test for the tag filtering feature"
- "Find all places where we query the database directly"
- "What would break if I changed Task.priority from a string to an enum?"
