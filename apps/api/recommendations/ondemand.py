"""Run the recommendation queue worker on demand instead of polling.

The local stack runs one long-lived ``process_recommendation_jobs --loop``
container per algorithm, which asks the database for work every few seconds.
That is fine against a local PostgreSQL but keeps a serverless database such
as Neon awake around the clock. In the public deployment the API therefore
starts a short-lived worker process whenever a refresh is queued; the worker
drains the queue and exits, so the database is only queried when somebody acts.

* ``RECOMMENDATION_ONDEMAND_WORKER=1`` switches the launcher on (render-start.sh
  sets it). Without it nothing is ever started, which is what the local stack,
  the tests and the offline evaluation rely on.
* A file lock guarantees a single worker at a time. The launcher takes the lock
  itself and hands it to the process it starts (the descriptor is inherited and
  named in ``RECOMMENDATION_WORKER_LOCK_FD``), so there is no gap between the
  decision to start a worker and the worker owning the lock. A launcher that
  finds the lock taken does nothing (the running worker looks at the queue
  again before it finishes), and a worker started by hand that cannot take the
  lock gives up.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

try:  # POSIX only; on other systems the launcher stays disabled
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

ENABLE_ENV = "RECOMMENDATION_ONDEMAND_WORKER"
INHERITED_LOCK_ENV = "RECOMMENDATION_WORKER_LOCK_FD"
LOCK_PATH = Path(tempfile.gettempdir()) / "savepoint-recommendation-worker.lock"
API_ROOT = Path(__file__).resolve().parents[1]
# Views that notice a stuck refresh may ask for a worker again, but not more
# often than this (starting a worker costs a Django start-up).
MIN_RETRY_INTERVAL_SECONDS = 30.0
# How long a worker waits for another one to finish before giving up.
LOCK_WAIT_SECONDS = 20.0
# Pause before the last look at the queue, to catch a job queued just now.
FINAL_RECHECK_SECONDS = 2.0

_launch_guard = threading.Lock()
_last_launch = 0.0


def enabled() -> bool:
    return fcntl is not None and os.environ.get(ENABLE_ENV) == "1"


def request_worker(*, rate_limited: bool = False) -> bool:
    """Start a worker unless one is running; return whether one was started."""

    global _last_launch
    if not enabled():
        return False
    with _launch_guard:
        now = time.monotonic()
        if rate_limited and now - _last_launch < MIN_RETRY_INTERVAL_SECONDS:
            return False
        handle = open(LOCK_PATH, "a+")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return False
        try:
            process = subprocess.Popen(  # noqa: S603
                [sys.executable, "manage.py", "process_recommendation_jobs", "--ondemand"],
                cwd=API_ROOT,
                env={**os.environ, INHERITED_LOCK_ENV: str(handle.fileno())},
                pass_fds=(handle.fileno(),),
                start_new_session=True,
            )
        except OSError:
            logger.exception("could not start the on-demand recommendation worker")
            fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()
            return False
        _last_launch = now
        # Closing this descriptor does not release the lock: the child holds a
        # copy of the same open file description until it exits.
        handle.close()
    # Reap the child when it exits so no zombie is left behind.
    threading.Thread(target=process.wait, daemon=True).start()
    return True


@contextmanager
def _exclusive_lock(timeout: float):
    inherited = os.environ.pop(INHERITED_LOCK_ENV, None)
    if inherited is not None:
        # Started by request_worker(): the lock is already held through the
        # inherited descriptor.
        handle = os.fdopen(int(inherited), "a+")
        try:
            yield True
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)
            handle.close()
        return
    handle = open(LOCK_PATH, "a+")
    deadline = time.monotonic() + timeout
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError:
                if time.monotonic() >= deadline:
                    break
                time.sleep(0.5)
        yield acquired
    finally:
        if acquired:
            fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()


def drain_exclusive(
    process_one_job: Callable[[], bool],
    *,
    lock_wait: float = LOCK_WAIT_SECONDS,
    final_recheck: float = FINAL_RECHECK_SECONDS,
) -> int | None:
    """Process jobs until the queue is empty while holding the worker lock.

    Returns the number of jobs processed, or ``None`` when another worker held
    the lock for the whole wait (that worker will pick the new job up).
    """

    if fcntl is None:  # pragma: no cover
        return None
    processed = 0
    with _exclusive_lock(lock_wait) as acquired:
        if not acquired:
            return None
        while True:
            while process_one_job():
                processed += 1
            # A job queued while the last one was being published would
            # otherwise wait for the next trigger: look once more.
            time.sleep(final_recheck)
            if not process_one_job():
                break
            processed += 1
    return processed
