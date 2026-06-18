# Local Deployment

## Current Local URL

- Streamlit app: http://localhost:8501
- Verified at: 2026-06-18 17:00:25 +09:00

## Run Command

```powershell
cd C:\AI_Agent\ex16
..\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless true
```

## Verification

- Local HTTP check: `200 OK`
- Codex right-side browser: opened at `http://localhost:8501`
- Test suite: `pytest` 3 passed
- Import check: `python -c "import app; print('app import ok')"`

## Visible Sections

- Top bar with `AI Scheduler`, search, date, notification, and profile.
- Left PC workspace panel with Week/Day/Month menu, integrations, and mini calendar.
- Center weekly calendar grid with hourly rows.
- Right AI work panel with `AI Smart Assistant`, smart task recommendations, and productivity score.
- Bottom interaction area with AI schedule input, manual registration, and event update/delete controls.
- Local SQLite DB: `data/personal_assistant_pc.db`
