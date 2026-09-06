"""Tests for the demo account bootstrap commands.

Covers both the singular Phase 1 `bootstrap_demo_account` (Plan 01-15 Task 1,
AUTH-01/SEC-02) and the plural `bootstrap_demo_accounts` (Plan 01.1-04,
AUTH-02) that drives N clearly-labelled simulated accounts from an
environment-only seed contract.
"""

from __future__ import annotations

import json
import threading
from io import StringIO

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command, CommandError
from django.db import connections

from accounts.management.commands.bootstrap_demo_accounts import LEGACY_ANCHOR_KEY
from accounts.models import (
    DEMO_ACCOUNT_ANCHOR_ID,
    SIMULATED_ACCOUNT_MARKER,
    DemoAccountAnchor,
    DemoAccountIdentity,
    demo_identity_anchor_id,
)

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


# ---------------------------------------------------------------------------
# Plural bootstrap_demo_accounts (Plan 01.1-04, AUTH-02)
# ---------------------------------------------------------------------------

SIM_ONE_KEY = "sim-one"
SIM_TWO_KEY = "sim-two"
SIM_ONE_USERNAME = "canary-sim-one-do-not-leak"
SIM_TWO_USERNAME = "canary-sim-two-do-not-leak"
SIM_ONE_PASSWORD = "Canary-Sim-One-Value-Secret-3!"  # noqa: S105 - test fixture
SIM_TWO_PASSWORD = "Canary-Sim-Two-Value-Secret-8!"  # noqa: S105 - test fixture


def _two_account_contract() -> str:
    return json.dumps(
        [
            {
                "key": SIM_ONE_KEY,
                "username": SIM_ONE_USERNAME,
                "password": SIM_ONE_PASSWORD,
                "label": "Simulated account one",
            },
            {"key": SIM_TWO_KEY, "username": SIM_TWO_USERNAME, "password": SIM_TWO_PASSWORD},
        ]
    )


def _run_bootstrap_accounts(monkeypatch: pytest.MonkeyPatch, contract: str) -> tuple[str, str]:
    monkeypatch.setenv("DEMO_ACCOUNTS", contract)
    out, err = StringIO(), StringIO()
    call_command("bootstrap_demo_accounts", stdout=out, stderr=err)
    return out.getvalue(), err.getvalue()


@pytest.mark.django_db
def test_accounts_missing_env_aborts_before_any_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEMO_ACCOUNTS", raising=False)

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_accounts")

    assert User.objects.count() == 0
    assert DemoAccountIdentity.objects.count() == 0


@pytest.mark.django_db
def test_accounts_malformed_json_aborts_before_any_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_ACCOUNTS", "not-json{[")

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_accounts")

    assert User.objects.count() == 0
    assert DemoAccountIdentity.objects.count() == 0


@pytest.mark.django_db
def test_accounts_empty_array_aborts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEMO_ACCOUNTS", "[]")

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_accounts")

    assert User.objects.count() == 0


@pytest.mark.django_db
def test_creates_multiple_independent_simulated_accounts(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap_accounts(monkeypatch, _two_account_contract())

    assert User.objects.count() == 2
    assert DemoAccountIdentity.objects.count() == 2

    for key, username, password in (
        (SIM_ONE_KEY, SIM_ONE_USERNAME, SIM_ONE_PASSWORD),
        (SIM_TWO_KEY, SIM_TWO_USERNAME, SIM_TWO_PASSWORD),
    ):
        identity = DemoAccountIdentity.objects.get(seed_key=key)
        assert identity.is_simulated is True
        assert identity.marker == SIMULATED_ACCOUNT_MARKER
        assert identity.display_label  # non-empty, human-facing
        assert identity.user.username == username
        assert identity.user.check_password(password)
        assert identity.id == demo_identity_anchor_id(key)


@pytest.mark.django_db
def test_seeded_accounts_sign_in_independently(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap_accounts(monkeypatch, _two_account_contract())

    assert authenticate(username=SIM_ONE_USERNAME, password=SIM_ONE_PASSWORD) is not None
    assert authenticate(username=SIM_TWO_USERNAME, password=SIM_TWO_PASSWORD) is not None
    # Credentials are not interchangeable between the two simulated accounts.
    assert authenticate(username=SIM_ONE_USERNAME, password=SIM_TWO_PASSWORD) is None


@pytest.mark.django_db
def test_rerun_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap_accounts(monkeypatch, _two_account_contract())
    first = {i.seed_key: (i.id, i.user_id) for i in DemoAccountIdentity.objects.all()}

    _run_bootstrap_accounts(monkeypatch, _two_account_contract())
    second = {i.seed_key: (i.id, i.user_id) for i in DemoAccountIdentity.objects.all()}

    assert User.objects.count() == 2
    assert first == second


@pytest.mark.django_db
def test_password_rotation_updates_same_row(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap_accounts(monkeypatch, _two_account_contract())
    identity_before = DemoAccountIdentity.objects.get(seed_key=SIM_ONE_KEY)

    rotated_password = "Rotated-Sim-One-Value-Secret-5!"  # noqa: S105
    rotated_contract = json.dumps(
        [
            {"key": SIM_ONE_KEY, "username": SIM_ONE_USERNAME, "password": rotated_password},
            {"key": SIM_TWO_KEY, "username": SIM_TWO_USERNAME, "password": SIM_TWO_PASSWORD},
        ]
    )
    _run_bootstrap_accounts(monkeypatch, rotated_contract)

    identity_after = DemoAccountIdentity.objects.get(seed_key=SIM_ONE_KEY)
    assert identity_after.id == identity_before.id
    assert identity_after.user_id == identity_before.user_id
    identity_after.user.refresh_from_db()
    assert identity_after.user.check_password(rotated_password)
    assert not identity_after.user.check_password(SIM_ONE_PASSWORD)


@pytest.mark.django_db
def test_username_rotation_renames_same_account(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap_accounts(monkeypatch, _two_account_contract())
    original_user_pk = DemoAccountIdentity.objects.get(seed_key=SIM_ONE_KEY).user_id

    renamed = "canary-sim-one-renamed"
    renamed_contract = json.dumps(
        [
            {"key": SIM_ONE_KEY, "username": renamed, "password": SIM_ONE_PASSWORD},
            {"key": SIM_TWO_KEY, "username": SIM_TWO_USERNAME, "password": SIM_TWO_PASSWORD},
        ]
    )
    _run_bootstrap_accounts(monkeypatch, renamed_contract)

    assert User.objects.count() == 2
    identity = DemoAccountIdentity.objects.get(seed_key=SIM_ONE_KEY)
    assert identity.user_id == original_user_pk
    assert identity.user.username == renamed


@pytest.mark.django_db
def test_duplicate_key_in_contract_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = json.dumps(
        [
            {"key": SIM_ONE_KEY, "username": SIM_ONE_USERNAME, "password": SIM_ONE_PASSWORD},
            {"key": SIM_ONE_KEY, "username": SIM_TWO_USERNAME, "password": SIM_TWO_PASSWORD},
        ]
    )
    monkeypatch.setenv("DEMO_ACCOUNTS", contract)

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_accounts")

    assert User.objects.count() == 0
    assert DemoAccountIdentity.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_alias_in_contract_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = json.dumps(
        [
            {"key": SIM_ONE_KEY, "username": SIM_ONE_USERNAME, "password": SIM_ONE_PASSWORD},
            {"key": SIM_TWO_KEY, "username": SIM_ONE_USERNAME, "password": SIM_TWO_PASSWORD},
        ]
    )
    monkeypatch.setenv("DEMO_ACCOUNTS", contract)

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_accounts")

    assert User.objects.count() == 0
    assert DemoAccountIdentity.objects.count() == 0


@pytest.mark.django_db
def test_alias_collision_with_unrelated_account_fails_closed_no_partial_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    User.objects.create_user(username=SIM_TWO_USERNAME, password="Unrelated-Account-Pass-1!")

    monkeypatch.setenv("DEMO_ACCOUNTS", _two_account_contract())

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_accounts")

    # sim-one is processed first; its creation must be rolled back when sim-two collides.
    assert User.objects.count() == 1
    assert DemoAccountIdentity.objects.count() == 0


# --- SC3: switching from the singular to the plural command must not abort on
#     the primary demo account that the singular command already created. -----

LEGACY_USERNAME = "canary-legacy-primary-do-not-leak"
LEGACY_PASSWORD_NEW = "Canary-Legacy-Primary-Value-7!"  # noqa: S105 - test fixture


def _contract_with_legacy(legacy_username: str, legacy_password: str) -> str:
    return json.dumps(
        [
            {"key": LEGACY_ANCHOR_KEY, "username": legacy_username, "password": legacy_password},
            {"key": SIM_ONE_KEY, "username": SIM_ONE_USERNAME, "password": SIM_ONE_PASSWORD},
            {"key": SIM_TWO_KEY, "username": SIM_TWO_USERNAME, "password": SIM_TWO_PASSWORD},
        ]
    )


@pytest.mark.django_db
def test_plural_run_after_singular_reuses_the_primary_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A prior singular run leaves the primary user + anchor + identity. The
    plural command must recognise it by seed_key and rotate it in place, not
    create a duplicate."""
    _run_bootstrap(monkeypatch, LEGACY_USERNAME, CANARY_PASSWORD)
    primary_pk = DemoAccountIdentity.objects.get(seed_key=LEGACY_ANCHOR_KEY).user_id

    _run_bootstrap_accounts(
        monkeypatch, _contract_with_legacy(LEGACY_USERNAME, LEGACY_PASSWORD_NEW)
    )

    assert User.objects.count() == 3
    assert DemoAccountIdentity.objects.get(seed_key=LEGACY_ANCHOR_KEY).user_id == primary_pk
    assert authenticate(username=LEGACY_USERNAME, password=LEGACY_PASSWORD_NEW) is not None
    assert authenticate(username=SIM_ONE_USERNAME, password=SIM_ONE_PASSWORD) is not None
    assert authenticate(username=SIM_TWO_USERNAME, password=SIM_TWO_PASSWORD) is not None
    anchor = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID)
    assert anchor.user_id == primary_pk


@pytest.mark.django_db
def test_plural_adopts_a_legacy_primary_user_that_has_no_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The real switch-over case: the primary user + its DemoAccountAnchor
    exist (from the singular path or an interrupted migration) but no
    DemoAccountIdentity does yet. The legacy entry must adopt it, not abort
    with SeedContractError."""
    legacy_user = User.objects.create_user(
        username=LEGACY_USERNAME, password="Old-Legacy-Primary-Pass-1!"
    )
    DemoAccountAnchor.objects.create(id=DEMO_ACCOUNT_ANCHOR_ID, user=legacy_user)

    _run_bootstrap_accounts(
        monkeypatch, _contract_with_legacy(LEGACY_USERNAME, LEGACY_PASSWORD_NEW)
    )

    identity = DemoAccountIdentity.objects.get(seed_key=LEGACY_ANCHOR_KEY)
    assert identity.user_id == legacy_user.pk  # adopted, not recreated
    assert identity.is_simulated is True
    assert User.objects.count() == 3
    assert authenticate(username=LEGACY_USERNAME, password=LEGACY_PASSWORD_NEW) is not None
    assert authenticate(username=SIM_ONE_USERNAME, password=SIM_ONE_PASSWORD) is not None
    assert authenticate(username=SIM_TWO_USERNAME, password=SIM_TWO_PASSWORD) is not None
    assert DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID).user_id == legacy_user.pk


@pytest.mark.django_db
def test_legacy_entry_still_rejects_a_genuinely_unrelated_username_collision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Adoption is scoped to the account behind DEMO_ACCOUNT_ANCHOR_ID. If the
    legacy entry's username is already taken by some other, unrelated user,
    that is still a fail-closed SeedContractError with no partial mutation."""
    legacy_user = User.objects.create_user(
        username=LEGACY_USERNAME, password="Old-Legacy-Primary-Pass-1!"
    )
    DemoAccountAnchor.objects.create(id=DEMO_ACCOUNT_ANCHOR_ID, user=legacy_user)
    other = User.objects.create_user(username="someone-elses-name", password="Unrelated-2!")

    monkeypatch.setenv("DEMO_ACCOUNTS", _contract_with_legacy("someone-elses-name", LEGACY_PASSWORD_NEW))

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_accounts")

    other.refresh_from_db()
    assert other.check_password("Unrelated-2!")
    assert not DemoAccountIdentity.objects.filter(seed_key=LEGACY_ANCHOR_KEY).exists()
    legacy_user.refresh_from_db()
    assert legacy_user.username == LEGACY_USERNAME  # untouched


@pytest.mark.django_db
def test_weak_password_rejected_before_any_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = json.dumps(
        [
            {"key": SIM_ONE_KEY, "username": SIM_ONE_USERNAME, "password": SIM_ONE_PASSWORD},
            {"key": SIM_TWO_KEY, "username": SIM_TWO_USERNAME, "password": "1234"},
        ]
    )
    monkeypatch.setenv("DEMO_ACCOUNTS", contract)

    with pytest.raises(CommandError):
        call_command("bootstrap_demo_accounts")

    assert User.objects.count() == 0
    assert DemoAccountIdentity.objects.count() == 0


@pytest.mark.django_db
def test_output_never_contains_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    out, err = _run_bootstrap_accounts(monkeypatch, _two_account_contract())
    combined = out + err

    for secret in (
        SIM_ONE_USERNAME,
        SIM_TWO_USERNAME,
        SIM_ONE_PASSWORD,
        SIM_TWO_PASSWORD,
    ):
        assert secret not in combined

    for identity in DemoAccountIdentity.objects.all():
        assert identity.user.password not in combined  # stored hash must not leak


@pytest.mark.django_db
def test_failed_run_output_never_contains_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = json.dumps(
        [{"key": SIM_ONE_KEY, "username": SIM_ONE_USERNAME, "password": "1234"}]
    )
    monkeypatch.setenv("DEMO_ACCOUNTS", contract)

    err = StringIO()
    with pytest.raises(CommandError) as exc_info:
        call_command("bootstrap_demo_accounts", stderr=err)

    assert SIM_ONE_USERNAME not in (str(exc_info.value) + err.getvalue())
    assert "1234" not in str(exc_info.value)


@pytest.mark.django_db
def test_public_display_marker_is_credential_free(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap_accounts(monkeypatch, _two_account_contract())

    for identity in DemoAccountIdentity.objects.all():
        displayable = f"{identity.marker} {identity.display_label} {identity.seed_key}"
        for secret in (SIM_ONE_PASSWORD, SIM_TWO_PASSWORD, identity.user.password):
            assert secret not in displayable
        assert identity.is_simulated is True


@pytest.mark.django_db
def test_anchor_reference_is_deterministic_from_key() -> None:
    assert demo_identity_anchor_id(SIM_ONE_KEY) == demo_identity_anchor_id(SIM_ONE_KEY)
    assert demo_identity_anchor_id(SIM_ONE_KEY) != demo_identity_anchor_id(SIM_TWO_KEY)


@pytest.mark.django_db
def test_singular_command_still_works_and_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_bootstrap(monkeypatch, CANARY_USERNAME, CANARY_PASSWORD)

    # Legacy anchor still maintained for seed_demo compatibility.
    anchor = DemoAccountAnchor.objects.get(id=DEMO_ACCOUNT_ANCHOR_ID)
    assert anchor.user.username == CANARY_USERNAME
    assert User.objects.count() == 1
    # And the account is now also tracked as a simulated identity.
    assert DemoAccountIdentity.objects.filter(user=anchor.user, is_simulated=True).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_bootstrap_accounts_creates_exactly_one_set() -> None:
    import os

    os.environ["DEMO_ACCOUNTS"] = _two_account_contract()
    errors: list[BaseException] = []

    def _worker() -> None:
        try:
            call_command("bootstrap_demo_accounts")
        except BaseException as exc:  # noqa: BLE001 - captured for the assertion below
            errors.append(exc)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=_worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    del os.environ["DEMO_ACCOUNTS"]

    assert not errors, f"concurrent bootstrap raised: {errors}"
    assert User.objects.count() == 2
    assert DemoAccountIdentity.objects.count() == 2
