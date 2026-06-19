from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

from .models import AppUser, ExternalScheduleCandidate, ScheduleEvent


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
                    source TEXT NOT NULL DEFAULT 'local',
                    source_url TEXT NOT NULL DEFAULT '',
                    sync_status TEXT NOT NULL DEFAULT 'local',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._ensure_event_columns(connection)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL DEFAULT '',
                    provider TEXT NOT NULL DEFAULT 'google',
                    linked_at TEXT NOT NULL,
                    auto_sync INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS external_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    recruitment_period TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT '모집중',
                    collected_at TEXT NOT NULL,
                    selected INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    @staticmethod
    def _ensure_event_columns(connection: sqlite3.Connection) -> None:
        existing = {row["name"] for row in connection.execute("PRAGMA table_info(events)").fetchall()}
        additions = {
            "source": "TEXT NOT NULL DEFAULT 'local'",
            "source_url": "TEXT NOT NULL DEFAULT ''",
            "sync_status": "TEXT NOT NULL DEFAULT 'local'",
        }
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE events ADD COLUMN {name} {definition}")

    def add_event(self, event: ScheduleEvent) -> ScheduleEvent:
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO events (
                    title, start_at, end_at, description, location,
                    importance, google_event_id, source, source_url,
                    sync_status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.title,
                    event.start_at.isoformat(timespec="seconds"),
                    event.end_at.isoformat(timespec="seconds"),
                    event.description,
                    event.location,
                    event.importance,
                    event.google_event_id,
                    event.source,
                    event.source_url,
                    event.sync_status,
                    now,
                    now,
                ),
            )
            event.id = int(cursor.lastrowid)
            return event

    def upsert_google_event(self, event: ScheduleEvent) -> ScheduleEvent:
        event.source = "google_calendar"
        event.sync_status = "synced"
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
            source=event.source,
            source_url=event.source_url,
            sync_status=event.sync_status,
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
        allowed = {
            "title",
            "start_at",
            "end_at",
            "description",
            "location",
            "importance",
            "google_event_id",
            "source",
            "source_url",
            "sync_status",
        }
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
            connection.execute(f"UPDATE events SET {', '.join(assignments)} WHERE id = ?", tuple(values))
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
            row = connection.execute("SELECT * FROM events WHERE google_event_id = ?", (google_event_id,)).fetchone()
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

    def register_user(self, email: str, display_name: str = "", provider: str = "google") -> AppUser:
        now = datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO users (email, display_name, provider, linked_at, auto_sync)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(email) DO UPDATE SET
                    display_name = excluded.display_name,
                    provider = excluded.provider,
                    linked_at = excluded.linked_at,
                    auto_sync = 1
                """,
                (email.strip(), display_name.strip(), provider, now),
            )
            row = connection.execute("SELECT * FROM users WHERE email = ?", (email.strip(),)).fetchone()
        return self._row_to_user(row)

    def get_active_user(self) -> AppUser | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM users ORDER BY linked_at DESC LIMIT 1").fetchone()
        return self._row_to_user(row) if row else None

    def upsert_candidate(self, candidate: ExternalScheduleCandidate) -> ExternalScheduleCandidate:
        now = candidate.collected_at or datetime.now().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO external_candidates (
                    source, category, title, recruitment_period, url, status, collected_at, selected
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    source = excluded.source,
                    category = excluded.category,
                    title = excluded.title,
                    recruitment_period = excluded.recruitment_period,
                    status = excluded.status,
                    collected_at = excluded.collected_at
                """,
                (
                    candidate.source,
                    candidate.category,
                    candidate.title,
                    candidate.recruitment_period,
                    candidate.url,
                    candidate.status,
                    now,
                    int(candidate.selected),
                ),
            )
            row = connection.execute("SELECT * FROM external_candidates WHERE url = ?", (candidate.url,)).fetchone()
        return self._row_to_candidate(row)

    def list_candidates(self, only_open: bool = True) -> list[ExternalScheduleCandidate]:
        query = "SELECT * FROM external_candidates"
        params: tuple[str, ...] = ()
        if only_open:
            query += " WHERE status = ?"
            params = ("모집중",)
        query += " ORDER BY collected_at DESC, source ASC"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_candidate(row) for row in rows]

    def delete_candidates_by_sources(self, sources: tuple[str, ...]) -> None:
        if not sources:
            return
        placeholders = ",".join("?" for _ in sources)
        with self._connect() as connection:
            connection.execute(f"DELETE FROM external_candidates WHERE source IN ({placeholders})", sources)

    def mark_candidate_selected(self, candidate_id: int) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE external_candidates SET selected = 1 WHERE id = ?", (candidate_id,))

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
            source=str(row["source"]),
            source_url=str(row["source_url"]),
            sync_status=str(row["sync_status"]),
        )

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> AppUser:
        return AppUser(
            id=int(row["id"]),
            email=str(row["email"]),
            display_name=str(row["display_name"]),
            provider=str(row["provider"]),
            linked_at=str(row["linked_at"]),
            auto_sync=bool(row["auto_sync"]),
        )

    @staticmethod
    def _row_to_candidate(row: sqlite3.Row) -> ExternalScheduleCandidate:
        return ExternalScheduleCandidate(
            id=int(row["id"]),
            source=str(row["source"]),
            category=str(row["category"]),
            title=str(row["title"]),
            recruitment_period=str(row["recruitment_period"]),
            url=str(row["url"]),
            status=str(row["status"]),
            collected_at=str(row["collected_at"]),
            selected=bool(row["selected"]),
        )


def seed_sample_events(store: ScheduleStore, events: Iterable[ScheduleEvent]) -> None:
    if store.list_events(include_past=True):
        return
    for event in events:
        store.add_event(event)
