# AI Scheduler Frontend

React + Vite frontend scaffold for the migration from Streamlit.

## Run

```powershell
cd C:\AI_Agent\ex16\frontend
npm.cmd install
npm.cmd run dev
```

The first migration target is the PC three-panel layout: left navigation, center calendar, and right task/AI panel.

## Sprint 1 Scope

- Reads events from `http://localhost:8000/events/range`.
- Renders the PC month calendar in a three-panel layout.
- Shows selected date details in the right panel.
- Uses `VITE_API_BASE_URL` when a different backend URL is needed.

## Sprint 2 Scope

- Creates local events from the selected date detail panel.
- Edits existing events through the same right-panel form.
- Deletes events from the selected date detail cards.
- Refreshes the month calendar after each create/update/delete operation.
