"""Tests for the demo account bootstrap command (Plan 01-15 Task 1, AUTH-01/SEC-02)."""

from __future__ import annotations

import threading
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError
from django.db import connections

from accounts.models import DEMO_ACCOUNT_ANCHOR_ID, DemoAccountAnchor

User = get_user_model()

CANARY_USERNAME = "canary-demo-user-do-not-leak"
CANARY_PASSWORD = "Canary-Secret-Value-Do-Not-Leak-9!"  # noqa: S105 - test fixture, not a real credential


def _run_bootstrap(monkeypatch: pytest.MonkeyPatch, username: str, password: str) -> tuple[str, str]:
    monkeypatch.setenv("DEMO_USERNAME", username)
    monkeypatch.setenv("DEMO_PASSWORD", password)
    out, err = StringIO(), StringIO()
    call_command("bootstrap_demo_account", stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


@pytest.mark.django_db
def test_missing_env_vars_aborts_before_any_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEMO_USERNAME", raising=False)
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_account")

    assert User.objects.count() == 0
    assert DemoAccountAnchor.objects.count() == 0


@pytest.mark.django_db
def test_missing_password_only_aborts_before_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_USERNAME", CANARY_USERNAME)
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_account")

    assert User.objects.count() == 0


@pytest.mark.django_db
def test_creates_account_on_first_run(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap(monkeypatch, CANARY_USERNAME, CANARY_PASSWORD)

    assert User.objects.count() == 1
    anchor = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID)
    user = anchor.user
    assert user.username == CANARY_USERNAME
    assert user.check_password(CANARY_PASSWORD)


@pytest.mark.django_db
def test_idempotent_rerun_preserves_anchor_and_user(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap(monkeypatch, CANARY_USERNAME, CANARY_PASSWORD)
    first_anchor = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID)
    first_user_pk = first_anchor.user.pk

    _run_bootstrap(monkeypatch, CANARY_USERNAME, CANARY_PASSWORD)

    assert User.objects.count() == 1
    second_anchor = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID)
    assert second_anchor.user.pk == first_user_pk
    assert second_anchor.id == first_anchor.id


@pytest.mark.django_db
def test_rotation_changes_password_and_invalidates_old(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap(monkeypatch, CANARY_USERNAME, CANARY_PASSWORD)
    new_password = "Rotated-Canary-Value-Also-Secret-7!"  # noqa: S105

    _run_bootstrap(monkeypatch, CANARY_USERNAME, new_password)

    user = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID).user
    user.refresh_from_db()
    assert user.check_password(new_password)
    assert not user.check_password(CANARY_PASSWORD)


@pytest.mark.django_db
def test_username_rotation_renames_same_account(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap(monkeypatch, CANARY_USERNAME, CANARY_PASSWORD)
    first_user_pk = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID).user.pk

    new_username = "canary-demo-user-renamed"
    _run_bootstrap(monkeypatch, new_username, CANARY_PASSWORD)

    assert User.objects.count() == 1
    anchor = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID)
    assert anchor.user.pk == first_user_pk
    assert anchor.user.username == new_username


@pytest.mark.django_db
def test_username_collision_with_unrelated_account_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    User.objects.create_user(username="already-taken", password="Some-Other-Password-1!")

    monkeypatch.setenv("DEMO_USERNAME", "already-taken")
    monkeypatch.setenv("DEMO_PASSWORD", CANARY_PASSWORD)

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_account")

    assert DemoAccountAnchor.objects.count() == 0


@pytest.mark.django_db
def test_weak_password_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_USERNAME", CANARY_USERNAME)
    monkeypatch.setenv("DEMO_PASSWORD", "1234")  # noqa: S105 - deliberately weak fixture

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_account")

    assert User.objects.count() == 0


@pytest.mark.django_db
def test_stdout_and_stderr_never_contain_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    out, err = _run_bootstrap(monkeypatch, CANARY_USERNAME, CANARY_PASSWORD)

    combined = out + err
    assert CANARY_USERNAME not in combined
    assert CANARY_PASSWORD not in combined

    user = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID).user
    assert user.password not in combined  # the stored hash must not leak either


@pytest.mark.django_db
def test_failed_run_error_output_never_contains_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_USERNAME", CANARY_USERNAME)
    monkeypatch.setenv("DEMO_PASSWORD", "1234")  # noqa: S105

    err = StringIO()
    with pytest.raises(CommandError) as exc_info:
        call_command("bootstrap_demo_account", stderr=err)

    assert CANARY_USERNAME not in str(exc_info.value)
    assert "1234" not in str(exc_info.value)


@pytest.mark.django_db(transaction=True)
def test_concurrent_bootstrap_creates_exactly_one_account(monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    os.environ["DEMO_USERNAME"] = CANARY_USERNAME
    os.environ["DEMO_PASSWORD"] = CANARY_PASSWORD
    errors: list[BaseException] = []

    def _worker() -> None:
        try:
            call_command("bootstrap_demo_account")
        except BaseException as exc:  # noqa: BLE001 - captured for the assertion below
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=_worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    del os.environ["DEMO_USERNAME"]
    del os.environ["DEMO_PASSWORD"]

    assert not errors, f"concurrent bootstrap raised: {errors}"
    assert User.objects.count() == 1
    assert DemoAccountAnchor.objects.count() == 1
