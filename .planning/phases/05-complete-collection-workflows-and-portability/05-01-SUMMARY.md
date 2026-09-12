---
phase: 05-complete-collection-workflows-and-portability
plan: 01
subsystem: auth
tags: [django, drf, postgresql, session-auth, csrf, privacy, favorites, profile]

requires:
  - phase: 01-three-day-public-demo-slice
    provides: "Django session auth, hashed passwords, CSRF-protected login/register/logout, hand-built public-profile allowlist"
  - phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
    provides: "LibraryEntry/GameWork as the collection-membership boundary favorites must check against"
provides:
  - "AccountProfile (bio, avatar_url, collection_visibility, favorites_visibility) one-to-one with User, migrated to PostgreSQL"
  - "FavoriteSlot (user, slot 1..5, work) with per-user slot/work uniqueness and a slot-range CheckConstraint"
  - "GET/PATCH /api/accounts/me/profile/ -- owner-scoped, alias-immutable profile editing"
  - "GET/PUT /api/accounts/me/favorites/ -- atomic full-replace of the five-slot favorites shelf, owner-scoped"
  - "build_public_profile() extended with independent collection_visibility/favorites_visibility gating, owner-always-sees-own-data, and a stable five-slot public favorites projection"
affects: [05-02-comments-and-lists, 05-03-copy-metadata, 05-04-export-and-portability-reconciliation, apps/web profile/collection UI]

actuals:
  tokens: 13300
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - "Validate-before-touching-the-database in services.update_profile/replace_favorites so a rejected payload never leaves a stray default row or partial mutation behind"
    - "Owner-derived authorization: every new service function takes `user` explicitly from `request.user`, never from the payload (IDOR boundary), matching library.services"
    - "Public projection privacy resolved before serialization: build_public_profile(user, viewer=...) decides collection/favorites visibility first, then builds the allowlisted dict -- owner always sees their own data, everyone else gets the privacy-resolved (never absent) shape"

key-files:
  created:
    - apps/api/accounts/migrations/0003_phase5_profile.py
    - apps/api/accounts/services.py
    - apps/api/accounts/tests/test_profile.py
    - apps/api/accounts/tests/test_schema.py
  modified:
    - apps/api/accounts/models.py
    - apps/api/accounts/serializers.py
    - apps/api/accounts/views.py
    - apps/api/accounts/urls.py
    - apps/api/accounts/tests/test_public_profile.py

key-decisions:
  - "Bio and avatar_url are always part of the public profile projection (no privacy toggle of their own), matching D-01's scope -- only collection_visibility and favorites_visibility gate data, per D-02/D-03."
  - "An account with no AccountProfile row yet (never edited) defaults to public for both collection and favorites, preserving Phase 1's pre-privacy-toggle behavior for every account that predates this migration."
  - "The public profile endpoint (GET /api/accounts/profiles/<alias>/) is the single surface for privacy resolution: the owner visiting their own alias while authenticated always sees their own full activity/favorites regardless of visibility; every other caller (anonymous or a different account) gets the privacy-resolved, stable-shaped projection (empty activity / five-null favorites when private)."
  - "Favorites are a full-replace resource (PUT), not incremental add/remove endpoints -- the submitted set is authoritative in one transaction, matching library.services.save_library_configuration's established pattern."
  - "Favorite/collection membership is re-validated in the service layer against the requesting user's own LibraryEntry rows before any delete/create, closing the specific IDOR shape where a work already owned by a different user could otherwise be favorited by someone who never added it to their own collection."

patterns-established:
  - "Validate-then-mutate service functions: services.py never wraps validation and the get_or_create/select_for_update inside the same atomic block when a validation failure must leave zero trace -- validation always runs before the transaction opens."
  - "viewer-aware public projections: any future privacy-gated public endpoint should follow build_public_profile's viewer= keyword pattern (default None = fully anonymous) rather than adding a second, parallel 'owner view' endpoint."

requirements-completed: [PROF-01, PRIV-01]

coverage:
  - id: D1
    description: "Real registration/login persists a PostgreSQL session and an irreversible password hash; identity survives a reload via a fresh session."
    requirement: "PROF-01"
    verification:
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_registration_leaves_a_real_postgresql_session_and_irreversible_hash"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_login_again_and_reload_preserves_identity_and_profile"
        status: pass
    human_judgment: false
  - id: D2
    description: "The login alias (User.username) cannot be changed through the profile endpoint; avatar_url is validated as HTTPS-only within a length limit."
    requirement: "PROF-01"
    verification:
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_profile_update_payload_cannot_change_username"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_non_https_avatar_url_is_rejected_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_oversized_avatar_url_is_rejected_without_mutation"
        status: pass
    human_judgment: false
  - id: D3
    description: "Anonymous callers and cross-account IDOR attempts (profile payload owner override, favorites tied to another user's LibraryEntry) are rejected without mutation; CSRF-less mutation on the new endpoint is rejected; duplicate case-insensitive registration stays uniform."
    requirement: "PROF-01, PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_anonymous_request_to_profile_endpoint_is_rejected"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_payload_owner_override_is_ignored_and_never_touches_another_account"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_favorite_payload_cannot_reference_another_users_work_ownership"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_profile_update_without_csrf_token_is_rejected"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_duplicate_registration_case_insensitive_returns_uniform_error"
        status: pass
    human_judgment: false
  - id: D4
    description: "Five favorite slots (1..5) full-replace, from the owner's own collection only: null gaps allowed, sixth slot/duplicate slot/duplicate work/non-owned work all rejected without mutation; replace is a full overwrite, not a merge."
    requirement: "PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_replacing_five_favorite_slots_from_owned_collection"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_favorite_slots_allow_null_gaps"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_slot_number_six_is_rejected_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_duplicate_slot_number_in_payload_is_rejected"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_duplicate_work_in_payload_is_rejected"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_work_outside_collection_is_rejected_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_profile.py::test_replace_is_a_full_overwrite_not_a_merge"
        status: pass
    human_judgment: false
  - id: D5
    description: "The four collection_visibility x favorites_visibility combinations are enforced independently for anonymous and user B (never friends-only), the owner always sees their own full data, and an account with no AccountProfile row yet defaults to public."
    requirement: "PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_privacy_combination_is_enforced_for_anonymous_and_user_b"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_owner_always_sees_their_own_data_regardless_of_visibility"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_default_profile_without_explicit_settings_is_public"
        status: pass
    human_judgment: false
  - id: D6
    description: "The public profile projection contains only allowlisted keys -- no email, password, internal IDs, copies, purchase, location, notes, or private rating -- across all privacy combinations."
    requirement: "PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_response_never_contains_private_fields_recursively"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_privacy_combination_is_enforced_for_anonymous_and_user_b"
        status: pass
    human_judgment: false
  - id: D7
    description: "PostgreSQL actually contains the expected migration chain, constraints (UNIQUE one-to-one, both visibility CheckConstraints, both FavoriteSlot UniqueConstraints, the slot-range CheckConstraint) and FK semantics; no pending migrations; demo fixtures stay a separate table from real-account profiles."
    requirement: "PROF-01, PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/accounts/tests/test_schema.py (8 tests)"
        status: pass
      - kind: unit
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py migrate --noinput"
        status: pass
      - kind: unit
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run"
        status: pass
    human_judgment: false
  - id: D8
    description: "No regression in the wider backend: full apps/api/accounts suite and the full apps/api backend suite pass after each task."
    verification:
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api -q"
        status: pass
    human_judgment: false
  - id: D9
    description: "The Playwright collection-workflows E2E journey and its axe/keyboard matrix (owned by the web session, not this plan) still need to run against these new endpoints before the phase itself can be signed off."
    verification: []
    human_judgment: true
    rationale: "This plan's <verification>/<handoff> explicitly assign e2e/collection-workflows.spec.ts and the accessibility matrix to the other (web) session; this backend-only plan cannot run or fake that browser evidence."

duration: 55min
completed: 2026-09-12
status: complete
---

# Phase 5 Plan 1: Identity/Profile/Favorites Summary

**Real Django-session registration/login with an owner-scoped, alias-immutable profile (bio + HTTPS avatar) and a five-slot favorites shelf, both gated by independent public/private visibility resolved server-side before any allowlisted projection is built.**

## Performance
- **Duration:** ~55min
- **Started:** 2026-09-12T20:30:00Z (approx, worktree spawn)
- **Completed:** 2026-09-12
- **Tasks:** 3/3 completed
- **Files modified:** 9 (4 created, 5 modified) under `apps/api/accounts/`

## Accomplishments
- Added `AccountProfile` (bio/avatar_url/collection_visibility/favorites_visibility) and `FavoriteSlot` (user/slot 1..5/work) models with a single PostgreSQL migration (`0003_phase5_profile.py`), generated via `makemigrations` inside Docker so its serialization exactly matches Django's own output (zero drift against `makemigrations --check --dry-run`).
- Built owner-scoped `GET/PATCH /api/accounts/me/profile/` (alias immutable, HTTPS-only avatar validation, visibility toggles) and `GET/PUT /api/accounts/me/favorites/` (atomic full-replace, collection-membership re-checked against the caller's own `LibraryEntry` rows).
- Extended `build_public_profile()` to independently gate `activity`/`summary` behind `collection_visibility` and a new `favorites` five-slot projection behind `favorites_visibility`, with the owner always seeing their own full data and a stable (never-absent) shape for everyone else.
- Verified the resulting PostgreSQL schema directly (`information_schema`, `pg_constraint`, model `_meta`) rather than trusting the ORM alone, and re-ran the full backend suite after every task (final: 554/554 passing).

## Task Commits
1. **Task 1 RED: failing tests for owner-scoped profile** - `ed04183` (test)
2. **Task 1 GREEN: owner-scoped GET/PATCH profile endpoint** - `9727d06` (feat)
3. **Task 2 RED: failing tests for five favorite slots and privacy combos** - `b52dab9` (test)
4. **Task 2 GREEN: five-slot favorites + public collection/favorites privacy** - `3b94321` (feat)
5. **Task 3: schema/regression lock against PostgreSQL** - `e102020` (test)

**Plan metadata:** commit pending (this SUMMARY + REQUIREMENTS.md, worktree mode)

## TDD Gate Compliance

Task 1 and Task 2 (both `tdd="true"`) each show a `test(05-01)` commit followed by a `feat(05-01)` commit, confirmed via `git log --oneline --grep`. Task 3 (`type="auto"`, no `tdd` attribute) is schema-verification-only and correctly has no `feat` commit -- no production code changed in that task, only a new PostgreSQL introspection test file.

## Files Created/Modified
- `apps/api/accounts/models.py` - `ProfileVisibility`, `AccountProfile`, `FavoriteSlot` (with `MIN_FAVORITE_SLOT`/`MAX_FAVORITE_SLOT`/`BIO_MAX_LENGTH`/`AVATAR_URL_MAX_LENGTH` constants and their `CheckConstraint`/`UniqueConstraint` pairs)
- `apps/api/accounts/migrations/0003_phase5_profile.py` - PostgreSQL schema for both new tables, depending on `accounts.0002_demo_accounts` and `catalogue.0018_merge_new_releases_and_curated_labels`
- `apps/api/accounts/services.py` (new) - `get_or_create_profile`, `update_profile`, `replace_favorites` -- validate-before-write, owner always from `request.user`
- `apps/api/accounts/serializers.py` - `AccountProfileSerializer`, `serialize_account_profile`, `FavoriteSlotInputSerializer`, `ReplaceFavoritesRequestSerializer`, `serialize_favorite_slots`, and `build_public_profile(user, *, viewer=None)` extended with privacy-gated `activity`/`summary`/`favorites` plus always-visible `bio`/`avatar_url`
- `apps/api/accounts/views.py` - `MyProfileView`, `MyFavoritesView`; `PublicProfileView.get` now passes `viewer=request.user`
- `apps/api/accounts/urls.py` - `me/profile/` and `me/favorites/` routes
- `apps/api/accounts/tests/test_profile.py` (new, 441 lines) - profile persistence/IDOR/CSRF/avatar/alias tests plus five-slot favorites CRUD/validation/IDOR tests
- `apps/api/accounts/tests/test_public_profile.py` - four privacy-combination tests, owner-always-sees test, no-profile-row-defaults-public test
- `apps/api/accounts/tests/test_schema.py` (new) - PostgreSQL introspection for the new migration's tables, constraints, and FK semantics

## Decisions Made
See `key-decisions` in frontmatter. The most consequential: bio/avatar are always part of the public projection (no privacy toggle of their own, matching D-01's scope), while `collection_visibility`/`favorites_visibility` are the only two independent privacy switches (D-02/D-03) -- and the owner viewing their own public-profile alias always sees their own full data regardless of those switches.

## Deviations from Plan

None - plan executed exactly as written. The migration file was generated via `docker compose run --rm api python manage.py makemigrations accounts --name phase5_profile` rather than hand-written, which is a mechanical detail (guarantees zero serialization drift against Django's own `makemigrations --check`), not a scope or behavior deviation from the plan's explicit instruction to create `0003_phase5_profile.py`.

## Issues Encountered

One self-caught bug during Task 1's GREEN step (Rule 1 -- auto-fixed inline, not a plan deviation): the initial `services.update_profile` ran `select_for_update().get_or_create()` and field validation inside the same `transaction.atomic()` block, so a validation failure (e.g. non-HTTPS avatar) rolled back the just-created default `AccountProfile` row along with the invalid write, leaving `AccountProfile.DoesNotExist` where a caller might expect a bare row with empty defaults. Fixed by validating all fields *before* opening the transaction, so a rejected update never touches the database at all. Caught by the RED tests themselves (`test_non_https_avatar_url_is_rejected_without_mutation` et al. initially failed with `DoesNotExist` instead of a clean `avatar_url==""` state) before the GREEN commit; test assertions were adjusted to check `.filter(...).exists()` rather than assuming a profile row always exists, matching the corrected (and more correct) behavior.

**Total deviations:** 0 plan deviations; 1 in-flight bug caught and fixed by the task's own TDD cycle before commit. **Impact:** none -- caught pre-commit, no follow-up needed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness

Ready for hand-off: `GET/PATCH /api/accounts/me/profile/`, `PUT /api/accounts/me/favorites/`, `GET /api/accounts/profiles/<alias>/`, and `GET /api/accounts/me/` are all stable, tested against real PostgreSQL, and unchanged in the parts of their contract (`LoginView`/`RegisterView`/`LogoutView`/`MeView`, `build_public_profile`'s existing `alias`/`activity`/`summary` keys, `SessionAuthentication`/CSRF/`ScopedRateThrottle`) the web session and `apps/api/recommendations/published.py` depend on.

Open for the rest of the phase: Plan 05-02 (comments and lists) and 05-03 (copy metadata) build on the same `AccountProfile`/ownership patterns established here. The Playwright `e2e/collection-workflows.spec.ts` journey and its accessibility matrix -- explicitly the web session's responsibility per this plan's `<handoff>` -- have not been run from this plan and remain a phase-level gate before sign-off (see coverage D9).

## Self-Check: PASSED

All 10 claimed files verified present on disk; all 5 task commit hashes (`ed04183`, `9727d06`, `b52dab9`, `3b94321`, `e102020`) verified present in `git log`.

---
*Phase: 05-complete-collection-workflows-and-portability*
*Completed: 2026-09-12*
