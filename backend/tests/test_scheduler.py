import threading
import time

from app.ingestion import scheduler


def test_scheduler_backs_off_when_another_run_holds_the_lock(monkeypatch):
    calls = []
    monkeypatch.setattr(scheduler, "STARTUP_DELAY_SECONDS", 0)
    monkeypatch.setattr(scheduler, "_seconds_until_due", lambda: 0)
    monkeypatch.setattr(scheduler, "run_ingestion", lambda: calls.append(1))

    scheduler._stop.clear()
    thread = threading.Thread(target=scheduler._loop)
    thread.start()
    time.sleep(0.3)
    scheduler.stop()
    thread.join(timeout=2)

    assert not thread.is_alive()
    assert len(calls) == 1
