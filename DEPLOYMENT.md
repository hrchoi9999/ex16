# Local Deployment

## Current Local URL

- Streamlit app: http://localhost:8501
- Verified at: 2026-06-18 17:18:05 +09:00

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
  - `월` 보기 선택 시 월간 캘린더로 전환됨.
  - `일` 보기 선택 시 하루 단위 일정 화면으로 전환됨.
  - `다음` 버튼 클릭 시 현재 보기 모드를 유지한 채 기준 날짜만 이동함.
  - `Google Calendar 가져오기` 버튼은 API 설정이 없을 때 설정 안내 메시지를 표시하고 앱 오류를 내지 않음.

## Visible Sections

- Top bar with `AI Scheduler`, search, date, notification, and profile.
- Functional control bar with previous/today/next, day/week/month selector, base date picker, and Google Calendar import.
- Left PC workspace panel with active Week/Day/Month indicator, integrations, and mini calendar.
- Center calendar workspace with day, week, and month layouts.
- Right AI work panel with `AI Smart Assistant`, smart task recommendations, and productivity score.
- Bottom interaction area with AI schedule input, manual registration, and event update/delete controls.
- Local SQLite DB: `data/personal_assistant_pc.db`

## Google Calendar Setup

Set these values in `.env` to enable real Google Calendar import and sync:

```env
GOOGLE_SERVICE_ACCOUNT_FILE=C:\path\to\service-account.json
GOOGLE_CALENDAR_ID=primary
APP_TIMEZONE=Asia/Seoul
```

The target Google Calendar must grant access to the service account email, or API calls will fail with a permission error.
