from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from .models import ScheduleEvent


class ScheduleStore:
    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    start_at TEXT NOT NULL,
                    end_at TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    importance INTEGER NOT NULL DEFAULT 3,
                    google_event_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def add_event(self, event: ScheduleEvent) -> ScheduleEvent:
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO events (
                    title, start_at, end_at, description, location,
                    importance, google_event_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.title,
                    event.start_at.isoformat(timespec="seconds"),
                    event.end_at.isoformat(timespec="seconds"),
                    event.description,
                    event.location,
                    event.importance,
                    event.google_event_id,
                    now,
                    now,
                ),
            )
            event.id = int(cursor.lastrowid)
            return event

    def upsert_google_event(self, event: ScheduleEvent) -> ScheduleEvent:
        if not event.google_event_id:
            return self.add_event(event)

        existing = self.get_event_by_google_id(event.google_event_id)
        if existing is None:
            return self.add_event(event)

        updated = self.update_event(
            int(existing.id),
            title=event.title,
            start_at=event.start_at,
            end_at=event.end_at,
            description=event.description,
            location=event.location,
            importance=event.importance,
            google_event_id=event.google_event_id,
        )
        return updated if updated is not None else event

    def list_events(self, include_past: bool = False) -> list[ScheduleEvent]:
        query = "SELECT * FROM events"
        params: tuple[str, ...] = ()
        if not include_past:
            query += " WHERE end_at >= ?"
            params = (datetime.now().isoformat(timespec="seconds"),)
        query += " ORDER BY start_at ASC"

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_event(row) for row in rows]

    def update_event(self, event_id: int, **updates: object) -> ScheduleEvent | None:
        allowed = {"title", "start_at", "end_at", "description", "location", "importance", "google_event_id"}
        filtered = {key: value for key, value in updates.items() if key in allowed and value is not None}
        if not filtered:
            return self.get_event(event_id)

        assignments: list[str] = []
        values: list[object] = []
        for key, value in filtered.items():
            assignments.append(f"{key} = ?")
            if isinstance(value, datetime):
                values.append(value.isoformat(timespec="seconds"))
            else:
                values.append(value)
        assignments.append("updated_at = ?")
        values.append(datetime.now().isoformat(timespec="seconds"))
        values.append(event_id)

        with self._connect() as connection:
            connection.execute(
                f"UPDATE events SET {', '.join(assignments)} WHERE id = ?",
                tuple(values),
            )
        return self.get_event(event_id)

    def delete_event(self, event_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM events WHERE id = ?", (event_id,))

    def get_event(self, event_id: int) -> ScheduleEvent | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return self._row_to_event(row) if row else None

    def get_event_by_google_id(self, google_event_id: str) -> ScheduleEvent | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM events WHERE google_event_id = ?",
                (google_event_id,),
            ).fetchone()
        return self._row_to_event(row) if row else None

    def upcoming_important(self, hours: int = 24) -> list[ScheduleEvent]:
        now = datetime.now()
        until = now + timedelta(hours=hours)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM events
                WHERE start_at BETWEEN ? AND ?
                   OR (importance >= 4 AND end_at >= ?)
                ORDER BY importance DESC, start_at ASC
                """,
                (
                    now.isoformat(timespec="seconds"),
                    until.isoformat(timespec="seconds"),
                    now.isoformat(timespec="seconds"),
                ),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> ScheduleEvent:
        return ScheduleEvent(
            id=int(row["id"]),
            title=str(row["title"]),
            start_at=datetime.fromisoformat(str(row["start_at"])),
            end_at=datetime.fromisoformat(str(row["end_at"])),
            description=str(row["description"]),
            location=str(row["location"]),
            importance=int(row["importance"]),
            google_event_id=row["google_event_id"],
        )


def seed_sample_events(store: ScheduleStore, events: Iterable[ScheduleEvent]) -> None:
    if store.list_events(include_past=True):
        return
    for event in events:
        store.add_event(event)
