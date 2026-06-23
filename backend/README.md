# AI Scheduler Backend

FastAPI backend scaffold for the Streamlit-to-React migration.

## Run

```powershell
cd C:\AI_Agent\ex16
C:\AI_Agent\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

## Current Endpoints

- `GET /health`
- `GET /events`
- `GET /events/today`

The backend reuses the existing `personal_assistant` domain modules and SQLite database.
