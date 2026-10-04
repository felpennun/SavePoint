"""The recommendation worker is started on demand, never polled for."""

from __future__ import annotations

import fcntl

import pytest

from recommendations import ondemand


@pytest.fixture(autouse=True)
def _lock_path(tmp_path, monkeypatch):  # noqa: ANN001
    monkeypatch.setattr(ondemand, "LOCK_PATH", tmp_path / "worker.lock")
    monkeypatch.setattr(ondemand, "_last_launch", 0.0)


@pytest.fixture
def popen_calls(monkeypatch):  # noqa: ANN001
    calls: list[list[str]] = []

    class FakeProcess:
        def wait(self) -> int:
            return 0

    def fake_popen(args, **kwargs):  # noqa: ANN001, ANN003
        calls.append(list(args))
        assert kwargs["start_new_session"] is True
        # the launcher hands its lock to the child through an inherited descriptor
        fd = int(kwargs["env"][ondemand.INHERITED_LOCK_ENV])
        assert kwargs["pass_fds"] == (fd,)
        return FakeProcess()

    monkeypatch.setattr(ondemand.subprocess, "Popen", fake_popen)
    return calls


def test_nothing_is_started_unless_the_launcher_is_enabled(monkeypatch, popen_calls) -> None:  # noqa: ANN001
    monkeypatch.delenv(ondemand.ENABLE_ENV, raising=False)
    assert ondemand.request_worker() is False
    assert popen_calls == []


def test_a_worker_is_started_when_enabled_and_none_is_running(monkeypatch, popen_calls) -> None:  # noqa: ANN001
    monkeypatch.setenv(ondemand.ENABLE_ENV, "1")
    assert ondemand.request_worker() is True
    assert len(popen_calls) == 1
    assert popen_calls[0][-2:] == ["process_recommendation_jobs", "--ondemand"]


def test_no_second_worker_is_started_while_one_holds_the_lock(monkeypatch, popen_calls) -> None:  # noqa: ANN001
    monkeypatch.setenv(ondemand.ENABLE_ENV, "1")
    with open(ondemand.LOCK_PATH, "a+") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX)
        assert ondemand.request_worker() is False
    assert popen_calls == []
    assert ondemand.request_worker() is True


def test_retries_from_a_view_are_rate_limited(monkeypatch, popen_calls) -> None:  # noqa: ANN001
    monkeypatch.setenv(ondemand.ENABLE_ENV, "1")
    assert ondemand.request_worker(rate_limited=True) is True
    assert ondemand.request_worker(rate_limited=True) is False
    # a queued refresh is never rate limited: it must always get its worker
    assert ondemand.request_worker() is True
    assert len(popen_calls) == 2


def test_the_started_worker_inherits_the_lock_instead_of_taking_it(monkeypatch) -> None:  # noqa: ANN001
    import os

    with open(ondemand.LOCK_PATH, "a+") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX)
        inherited = os.dup(holder.fileno())
        monkeypatch.setenv(ondemand.INHERITED_LOCK_ENV, str(inherited))
        # the lock is held by the launcher's descriptor: the worker must not
        # wait for it, it owns it
        assert ondemand.drain_exclusive(lambda: False, lock_wait=0.2, final_recheck=0) == 0


def test_drain_processes_until_the_queue_is_empty() -> None:
    queue = [True, True, True]  # three jobs, then empty (also at the final look)

    def process_one() -> bool:
        return queue.pop(0) if queue else False

    assert ondemand.drain_exclusive(process_one, final_recheck=0) == 3


def test_drain_picks_up_a_job_queued_during_the_final_look() -> None:
    answers = iter([True, False, True, False, False])  # job, empty, late job, empty, empty

    assert ondemand.drain_exclusive(lambda: next(answers, False), final_recheck=0) == 2


def test_drain_gives_up_when_another_worker_keeps_the_lock() -> None:
    with open(ondemand.LOCK_PATH, "a+") as holder:
        fcntl.flock(holder, fcntl.LOCK_EX)
        assert ondemand.drain_exclusive(lambda: True, lock_wait=0.2, final_recheck=0) is None


@pytest.mark.django_db
def test_queueing_a_refresh_asks_for_a_worker(
    django_user_model, monkeypatch, django_capture_on_commit_callbacks  # noqa: ANN001
) -> None:
    from recommendations import jobs
    from recommendations.models import RecommendationState

    requested: list[bool] = []
    monkeypatch.setattr(jobs, "request_worker", lambda: requested.append(True))
    user = django_user_model.objects.create_user(username="ondemand-user", password="Zq7!vNm-Strong-Pass-4418")
    RecommendationState.objects.create(user=user, collection_revision=1)
    with django_capture_on_commit_callbacks(execute=True):
        jobs.enqueue_latest_refresh(user.id)
    assert requested == [True]
