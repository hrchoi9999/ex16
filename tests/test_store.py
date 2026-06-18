from datetime import datetime, timedelta

from personal_assistant.database import ScheduleStore
from personal_assistant.models import ScheduleEvent


def test_add_list_update_delete_event(tmp_path) -> None:
    store = ScheduleStore(tmp_path / "assistant.db")
    start_at = datetime.now() + timedelta(days=1)
    event = store.add_event(
        ScheduleEvent(
            id=None,
            title="회의",
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            importance=4,
        )
    )

    assert event.id is not None
    assert store.list_events()[0].title == "회의"

    updated = store.update_event(event.id, title="변경된 회의")
    assert updated is not None
    assert updated.title == "변경된 회의"

    store.delete_event(event.id)
    assert store.list_events(include_past=True) == []


def test_upsert_google_event_updates_existing_event(tmp_path) -> None:
    store = ScheduleStore(tmp_path / "assistant.db")
    start_at = datetime.now() + timedelta(days=1)
    first = store.upsert_google_event(
        ScheduleEvent(
            id=None,
            title="Google 일정",
            start_at=start_at,
            end_at=start_at + timedelta(hours=1),
            google_event_id="google-1",
        )
    )

    second = store.upsert_google_event(
        ScheduleEvent(
            id=None,
            title="변경된 Google 일정",
            start_at=start_at + timedelta(hours=2),
            end_at=start_at + timedelta(hours=3),
            google_event_id="google-1",
        )
    )

    events = store.list_events(include_past=True)
    assert first.id == second.id
    assert len(events) == 1
    assert events[0].title == "변경된 Google 일정"
