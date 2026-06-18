# Local Deployment

## Current Local URL

- Streamlit app: http://localhost:8501
- Verified at: 2026-06-18 17:29:40 +09:00

## Run Command

```powershell
cd C:\AI_Agent\ex16
..\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless true
```

## Verification

- Local HTTP check: `200 OK`
- Codex right-side browser: opened at `http://localhost:8501`
- Test suite: `pytest` 4 passed
- Import check: `python -c "import app; print('app import ok')"`
- Browser interaction checks:
  - Streamlit default header/toolbar is hidden and `Deploy` is not visible.
  - Main workspace starts at the top of the page.
  - Top day/week/month selector was removed.
  - Left panel `월 보기` link switches to month calendar and becomes active.
  - Bottom `캘린더 작업` area contains previous/today/next, base date, Google Calendar import, and search.

## Visible Sections

- Left PC workspace panel with `AI Scheduler`, day/week/month navigation links, integrations, and mini calendar.
- Center calendar workspace with day, week, and month layouts.
- Right AI work panel with `AI Smart Assistant`, smart task recommendations, and productivity score.
- Bottom task area with calendar controls, AI schedule input, manual registration, search, and event update/delete controls.
- Local SQLite DB: `data/personal_assistant_pc.db`

## Google Calendar Setup

Set these values in `.env` to enable real Google Calendar import and sync:

```env
GOOGLE_SERVICE_ACCOUNT_FILE=C:\path\to\service-account.json
GOOGLE_CALENDAR_ID=primary
APP_TIMEZONE=Asia/Seoul
```

The target Google Calendar must grant access to the service account email, or API calls will fail with a permission error.
