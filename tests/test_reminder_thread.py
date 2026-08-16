"""The background reminder loop survives a database error.

check_reminders() runs in a daemon thread for the life of the process and is
the only thing that sends task-deadline emails. It had its `try` outside the
`with app.app_context()`, so an exception unwound the context before the handler
ran and the `db.session.rollback()` in that handler raised RuntimeError: Working
outside of application context. That escaped the except, broke the `while True`,
and killed the thread -- silently, since the exception surfaced only on the
thread's own stderr. From the first database hiccup onward the app looked
healthy and never sent another reminder.

These tests drive one iteration of the loop by making sleep() end it, and none
of them request a fixture that pushes an app context -- the bug is only visible
when there is no ambient context to fall back on, which is exactly the
background thread's situation.
"""

import pytest

import app as app_module


class LoopEnded(Exception):
    """Raised from a patched sleep() to stop the otherwise infinite loop."""


@pytest.fixture
def one_iteration(monkeypatch):
    """Make check_reminders run exactly one pass, then raise LoopEnded."""
    calls = {"sleeps": 0}

    def fake_sleep(seconds):
        calls["sleeps"] += 1
        raise LoopEnded()

    monkeypatch.setattr(app_module.time_module, "sleep", fake_sleep)
    return calls


def test_a_database_error_is_swallowed_and_the_loop_continues(app, one_iteration,
                                                              monkeypatch):
    """The failure mode that killed the thread.

    If the rollback runs outside the app context this raises RuntimeError
    instead of reaching sleep(), and the loop is over for good.
    """
    def boom(*args, **kwargs):
        raise RuntimeError("database is on fire")

    monkeypatch.setattr(app_module.db.session, "query", boom)

    with pytest.raises(LoopEnded):
        app_module.check_reminders()

    assert one_iteration["sleeps"] == 1, (
        "the loop never reached its sleep, so it did not survive the error"
    )


def test_the_error_is_logged_rather_than_silent(app, one_iteration, monkeypatch,
                                                caplog):
    def boom(*args, **kwargs):
        raise RuntimeError("database is on fire")

    monkeypatch.setattr(app_module.db.session, "query", boom)

    with caplog.at_level("ERROR"):
        with pytest.raises(LoopEnded):
            app_module.check_reminders()

    assert any("database is on fire" in r.getMessage() for r in caplog.records), (
        "a failing reminder sweep must leave something in the log"
    )


def test_a_clean_sweep_also_reaches_the_sleep(app, database, one_iteration):
    """The happy path still completes an iteration with real tables present."""
    with pytest.raises(LoopEnded):
        app_module.check_reminders()

    assert one_iteration["sleeps"] == 1


def test_due_tasks_are_emailed_and_marked(app, database, one_iteration,
                                          monkeypatch):
    """The loop's actual job, which nothing covered either."""
    from datetime import datetime, timedelta
    from models import db, Wedding, Task

    sent = []
    monkeypatch.setattr(app_module, "send_reminder_email",
                        lambda **kwargs: sent.append(kwargs) or True)

    with app.app_context():
        wedding = Wedding(couple_names="Reminder Couple",
                          wedding_date=datetime.utcnow() + timedelta(days=60),
                          email="couple@example.com")
        db.session.add(wedding)
        db.session.flush()
        due = Task(wedding_id=wedding.id, title="Due soon",
                   due_date=datetime.utcnow() + timedelta(days=1))
        later = Task(wedding_id=wedding.id, title="Not yet",
                     due_date=datetime.utcnow() + timedelta(days=30))
        done = Task(wedding_id=wedding.id, title="Already done",
                    due_date=datetime.utcnow() + timedelta(days=1),
                    completed=True)
        db.session.add_all([due, later, done])
        db.session.commit()
        due_id = due.id

    with pytest.raises(LoopEnded):
        app_module.check_reminders()

    titles = [k["task_title"] for k in sent]
    assert titles == ["Due soon"], (
        f"expected only the imminent, incomplete task to be emailed, got {titles}"
    )

    with app.app_context():
        assert Task.query.get(due_id).reminder_sent is True, (
            "the task was not marked, so it will be emailed again every hour"
        )
