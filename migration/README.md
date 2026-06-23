# Streamlit to FastAPI + React Migration

## Goal

Move AI Scheduler from a Streamlit monolith to a maintainable web-service structure.

## Folder Strategy

- `legacy_streamlit/`: current working Streamlit app, preserved for reference and fallback.
- `personal_assistant/`: shared Python domain modules, reused by both Streamlit and FastAPI.
- `backend/`: new FastAPI API layer.
- `frontend/`: new React PC web UI.

## Migration Order

1. Keep Streamlit running through root `app.py` compatibility entrypoint.
2. Add FastAPI health and schedule read APIs.
3. Build React three-panel PC shell.
4. Connect React calendar read-only data.
5. Add event create/update/delete.
6. Add Google Calendar import/sync.
7. Add interest-site collection and deadline registration.
8. Add AI chat command router.
9. Retire Streamlit once React reaches feature parity.

## Sprint 1 Result

- Streamlit remains available through `http://localhost:8501`.
- FastAPI exposes schedule data through `GET /events/range`.
- React PC preview runs on `http://localhost:5173`.
- The React month calendar reads real SQLite-backed schedule data through FastAPI.
- Date selection updates the right detail panel without Streamlit reruns.
- Current React scope is read-only; create/update/delete, Google sync, site collection, and AI chat migration remain in later sprints.
