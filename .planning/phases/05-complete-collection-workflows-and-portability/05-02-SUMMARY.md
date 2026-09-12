---
phase: 05-complete-collection-workflows-and-portability
plan: 02
subsystem: api
tags: [django, drf, postgresql, comments, custom-lists, optimistic-concurrency, privacy]

requires:
  - phase: 05-complete-collection-workflows-and-portability
    provides: "05-01: AccountProfile/FavoriteSlot, owner-scoped profile/favorites endpoints, build_public_profile privacy gating"
provides:
  - "GameComment (LIB-03/D-04/D-05): one comment per user/work (UniqueConstraint), owner-only CRUD via /api/library/comments/<id>/, a by-work listing endpoint at /api/library/entries/<work_id>/comments/ that resolves public/private server-side"
  - "CustomList/CustomListItem (LIB-04/D-06/D-07): manual ordered lists of a user's own collected works, membership re-checked against LibraryEntry, with UniqueConstraint(list, work) and UniqueConstraint(list, position)"
  - "Optimistic-concurrency reorder endpoint (/api/library/lists/<list_id>/reorder/): mandatory expected_version, select_for_update()-serialized, HTTP 409 on stale version without mutation, two-phase temp-then-final position write inside one transaction"
  - "build_public_profile() extended with a public comments/lists aggregate, each item gated by its own visibility field independent of collection_visibility/favorites_visibility"
  - "New PostgreSQL migration 0003_phase5_comments_lists.py (GameComment, CustomList, CustomListItem tables and constraints), shared by this plan's whole scope per 05-PATTERNS.md's explicit migration-sharing note"
affects: [05-03-copy-metadata, 05-04-export-and-portability-reconciliation, apps/web game-detail comments UI, apps/web collection/lists UI]

actuals:
  tokens: 18600
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Two-phase position write for atomic reorder: write all items to unique temporary positions well outside the final 1..N range first, then assign the final consecutive range, so the intermediate state never collides with UniqueConstraint(list, position) inside the same transaction"
    - "Optimistic concurrency via a persisted version counter: select_for_update() the parent row, compare version before touching any child row, raise a typed exception (StaleListVersion) mapped to HTTP 409 by the view -- never caught and retried silently"
    - "Independent per-item visibility, not derived from profile-level toggles: GameComment.visibility and CustomList.visibility are each their own public/private field, resolved before serialization, exactly like AccountProfile's collection_visibility/favorites_visibility but never coupled to them"
    - "Two-tier serialization for the same entity: serialize_comment/serialize_list (owner-facing, includes id/version/visibility) vs serialize_profile_comment/serialize_profile_list (minimal allowlist for the public-profile aggregate, no id/version/visibility)"

key-files:
  created:
    - apps/api/library/migrations/0003_phase5_comments_lists.py
    - apps/api/library/tests/test_comments.py
    - apps/api/library/tests/test_lists.py
  modified:
    - apps/api/library/models.py
    - apps/api/library/serializers.py
    - apps/api/library/services.py
    - apps/api/library/views.py
    - apps/api/library/urls.py
    - apps/api/library/tests/test_schema.py
    - apps/api/accounts/serializers.py
    - apps/api/accounts/tests/test_public_profile.py

key-decisions:
  - "CustomList is the primary name for the new library aggregate (assumption-delta: promote), not an alias of any prior entity -- no earlier representation of manual game lists existed to preserve, per the plan's explicit instruction."
  - "Reorder takes the list's complete current CustomListItem id set (not work ids) as the ordering payload -- items already exist per work, and using item ids keeps the endpoint agnostic to any future case where a list could reference the same work through more than one item row."
  - "Comment/list visibility is deliberately never derived from AccountProfile.collection_visibility/favorites_visibility -- each carries its own independent public/private field, resolved before serialization, matching D-05's explicit resolution of Open Question 2 in 05-RESEARCH.md."
  - "The by-work comments listing endpoint (GET /api/library/entries/<work_id>/comments/) is public (AllowAny) and shows public comments plus the caller's own comment; the by-id endpoint (/api/library/comments/<comment_id>/) is owner-only for all methods including GET, so a non-owner's read/edit/delete attempt is indistinguishable from a nonexistent comment."
  - "Owner-scoped list/comment CRUD and the public-profile aggregate use two different serializer functions for the same model (serialize_* vs serialize_profile_*) rather than one function with a conditional shape, so the public allowlist can never accidentally include an owner-only key added later to the owner-facing DTO."

patterns-established:
  - "Version-gated reorder: any future reorderable owner-scoped collection should follow CustomList.version's pattern (expected_version required at the serializer level, select_for_update() + version compare before any child mutation, StaleListVersion -> HTTP 409) rather than trusting client-submitted order without a concurrency token."
  - "Per-entity visibility rather than profile-level visibility inheritance: new user-generated content types (future ratings-with-text, reviews, etc.) should carry their own visibility field resolved independently, not be gated through AccountProfile's toggles."

requirements-completed: [LIB-03, LIB-04, PRIV-01]

coverage:
  - id: D1
    description: "Exactly one comment per user/work; the author has full CRUD over it; a second creation attempt for the same work returns 409 without duplicating or mutating the existing row."
    requirement: "LIB-03"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_comments.py::test_owner_can_create_read_edit_and_delete_their_own_comment"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_comments.py::test_second_comment_for_the_same_work_returns_conflict_without_duplicating"
        status: pass
    human_judgment: false
  - id: D2
    description: "A work outside the caller's own collection is rejected without mutation; a non-owner cannot read, edit, or delete another user's comment via the by-id endpoint; unauthenticated creation is rejected."
    requirement: "LIB-03"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_comments.py::test_work_outside_collection_is_rejected_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_comments.py::test_user_b_cannot_read_edit_or_delete_user_a_comment"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_comments.py::test_unauthenticated_create_is_rejected"
        status: pass
    human_judgment: false
  - id: D3
    description: "The author always retains access to their own private comment via the by-work listing; third parties (anonymous or another user) only ever receive public comments; hostile comment text is returned as inert text, never executed or stripped."
    requirement: "LIB-03, PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_comments.py::test_author_sees_own_private_comment_via_the_by_work_listing"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_comments.py::test_third_parties_only_receive_public_comments"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_comments.py::test_hostile_comment_text_is_returned_as_inert_text"
        status: pass
    human_judgment: false
  - id: D4
    description: "Custom lists are owner CRUD; every item must already belong to the owner's own LibraryEntry collection; the same work cannot be added to a list twice."
    requirement: "LIB-04"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_owner_can_create_edit_and_delete_a_list"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_adding_an_uncollected_work_is_rejected_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_adding_the_same_work_twice_is_rejected"
        status: pass
    human_judgment: false
  - id: D5
    description: "Reorder requires expected_version and the exact current item-id set; assigns consecutive 1..N positions; the new order and version survive a reload."
    requirement: "LIB-04"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_reorder_assigns_consecutive_positions_stable_after_reload"
        status: pass
    human_judgment: false
  - id: D6
    description: "A reorder without expected_version is rejected with 400 before any mutation; a stale expected_version returns 409 with the previous order and version completely unchanged; a matching version processes under select_for_update() and returns the new version and persisted order."
    requirement: "LIB-04"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_reorder_without_expected_version_is_rejected_without_mutation"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_stale_expected_version_returns_conflict_without_changes"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_matching_version_reorders_and_returns_new_version"
        status: pass
    human_judgment: false
  - id: D7
    description: "Two concurrent reorders against the same list serialize via select_for_update(): exactly one succeeds, the other loses the race against the now-stale version, and the final item positions are never duplicated or gapped."
    requirement: "LIB-04"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_concurrent_reorders_serialize_without_duplicate_or_gapped_positions"
        status: pass
    human_judgment: false
  - id: D8
    description: "An exception raised mid-reorder (mismatched item-id set) leaves the previous positions and version completely intact; a non-owner cannot read, edit, delete, add-item-to, or reorder another user's list; the public-list projection exposes only name/items(work_slug/work_title/position), never id/version/visibility."
    requirement: "LIB-04, PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_exception_during_reorder_leaves_previous_order_intact"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_user_b_cannot_access_user_a_private_list_resources"
        status: pass
      - kind: integration
        ref: "apps/api/library/tests/test_lists.py::test_public_list_projection_only_exposes_allowlisted_fields"
        status: pass
    human_judgment: false
  - id: D9
    description: "PostgreSQL actually contains the migration chain, tables, and constraints (UniqueConstraint per user/work comment, per list/work and list/position item, both CheckConstraint visibility enums) with protective/cascade FK semantics; no pending migrations after makemigrations --check --dry-run."
    requirement: "LIB-03, LIB-04"
    verification:
      - kind: integration
        ref: "apps/api/library/tests/test_schema.py (10 new tests covering GameComment/CustomList/CustomListItem)"
        status: pass
      - kind: unit
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py migrate --noinput"
        status: pass
      - kind: unit
        ref: "docker compose -f infra/compose.yaml run --rm api python apps/api/manage.py makemigrations --check --dry-run"
        status: pass
    human_judgment: false
  - id: D10
    description: "build_public_profile()'s comments/lists aggregate is gated by each item's own visibility field (never collection_visibility/favorites_visibility); the owner sees all of their own regardless of visibility; third parties see only the public subset; the response never leaks a forbidden key (id, visibility, version, and the pre-existing denylist)."
    requirement: "PRIV-01"
    verification:
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_public_profile_includes_only_public_comments_for_third_parties"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_owner_sees_all_own_comments_regardless_of_visibility"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_public_profile_includes_only_public_lists_for_third_parties"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_owner_sees_all_own_lists_regardless_of_visibility"
        status: pass
      - kind: integration
        ref: "apps/api/accounts/tests/test_public_profile.py::test_public_list_projection_has_no_forbidden_keys"
        status: pass
    human_judgment: false
  - id: D11
    description: "No regression anywhere in the backend: the full apps/api suite passes after every task."
    verification:
      - kind: integration
        ref: "docker compose -f infra/compose.yaml run --rm api pytest apps/api -q"
        status: pass
    human_judgment: false
  - id: D12
    description: "The Playwright collection-workflows E2E journey (comment CRUD, list CRUD/reorder, privacy) is the web session's responsibility per this plan's <handoff> and has not been run from this backend-only plan."
    verification: []
    human_judgment: true
    rationale: "This plan's <verification>/<handoff> explicitly assign e2e/collection-workflows.spec.ts to the other (web) session; this backend-only plan cannot run or fake that browser evidence."

duration: 70min
completed: 2026-09-12
status: complete
---

# Phase 5 Plan 2: Comments and Custom Lists Summary

**Per-work unique comments and manual ordered custom lists, with a version-gated optimistic-concurrency reorder endpoint and a public-profile aggregate that resolves each item's own visibility independently of the profile-level collection/favorites toggles.**

## Performance
- **Duration:** ~70min
- **Started:** 2026-09-12T20:40:00Z (approx, worktree spawn)
- **Completed:** 2026-09-12T21:40:38Z
- **Tasks:** 3/3 completed
- **Files modified:** 11 (3 created, 8 modified) across `apps/api/library/` and `apps/api/accounts/`

## Accomplishments
- Added `GameComment` (`UniqueConstraint(user, work)`, its own `public/private` visibility) with owner-only CRUD at `/api/library/comments/<id>/` and a public-plus-own listing endpoint at `/api/library/entries/<work_id>/comments/`.
- Added `CustomList`/`CustomListItem` (`UniqueConstraint(list, work)`, `UniqueConstraint(list, position)`) with owner CRUD, collection-membership re-validation against `LibraryEntry`, and an atomic optimistic-concurrency reorder endpoint (`expected_version` required, `select_for_update()`, two-phase temporary-then-final position write, HTTP 409 on stale version without mutation).
- Generated one PostgreSQL migration (`0003_phase5_comments_lists.py`) via `makemigrations` inside Docker (zero drift against `makemigrations --check --dry-run`) covering all three new tables and their constraints, per 05-PATTERNS.md's explicit note that this plan's schema stays one migration even though it spans two tasks.
- Extended `build_public_profile()` with a `comments`/`lists` aggregate gated by each item's own `visibility` field (never derived from `collection_visibility`/`favorites_visibility`), verified with a recursive forbidden-key scan extended to catch `visibility`/`version` leaking into the public projection.
- Verified the resulting PostgreSQL schema directly (`information_schema`, `pg_constraint`, model `_meta`) for all three new tables, and re-ran the full backend suite after every task (final: 588/588 passing).

## Task Commits
1. **Task 1+2 RED: failing tests for comments and custom lists** - `f02cdf3` (test)
2. **Task 1+2 GREEN: GameComment/CustomList/CustomListItem models, services, endpoints, migration** - `a50f77b` (feat)
3. **Task 3: public profile allowlist extension + schema verification** - `b7ffdec` (feat)

**Plan metadata:** commit pending (this SUMMARY, worktree mode)

## TDD Gate Compliance

Task 1 (`type="tracer" tdd="true"`) and Task 2 (`type="auto" tdd="true"`) share the identical five production files (`models.py`, `serializers.py`, `services.py`, `views.py`, `urls.py`) and a single migration by design (05-PATTERNS.md's explicit "División intencionada" note: `0003_phase5_comments_lists.py` is one migration for this whole plan, not split per task). A first attempt to split `models.py` into a comment-only intermediate commit (keeping the full migration) was tried and **reverted after it broke `pytest-django`'s transactional test-database flush** -- Django's migration-state autodetector treats a model present in the migration history but absent from `models.py` as a pending `DeleteModel`, which desynchronizes the ORM's view of the schema from the actual PostgreSQL tables and breaks `flush` for `transaction=True` tests. Given that verified constraint, Task 1 and Task 2 are committed together as one `test(05-02)` commit (`test_comments.py` + `test_lists.py`) followed by one `feat(05-02)` commit (all five production files + the migration) -- the RED-before-GREEN commit order is preserved at the plan level, but not isolated per task. Both test files independently exercise and pass their own task's full behavior list. Task 3 (`type="auto"`, no `tdd` attribute) correctly has a single `feat` commit with no preceding `test` commit, since it extends existing test files rather than introducing new ones under RED/GREEN.

## Files Created/Modified
- `apps/api/library/models.py` - `ContentVisibility`, `GameComment` (`COMMENT_TEXT_MAX_LENGTH`), `CustomList` (`LIST_NAME_MAX_LENGTH`, `version`), `CustomListItem`
- `apps/api/library/migrations/0003_phase5_comments_lists.py` - PostgreSQL schema for all three new tables and their constraints, depending on `library.0002_rating_copies` and `catalogue.0018_merge_new_releases_and_curated_labels`
- `apps/api/library/serializers.py` - `CommentInputSerializer`, `serialize_comment`, `serialize_profile_comment`, `CustomListInputSerializer`, `AddListItemSerializer`, `ReorderListSerializer`, `serialize_list`, `serialize_profile_list`, `_escape_text`
- `apps/api/library/services.py` - `CommentAlreadyExists`, `StaleListVersion`, `list_visible_comments`, `create_comment`, `update_comment`, `delete_comment`, `create_list`, `update_list`, `add_list_item`, `reorder_list_items`
- `apps/api/library/views.py` - `WorkCommentsView`, `CommentDetailView`, `MyListsView`, `ListDetailView`, `ListItemsView`, `ListItemDetailView`, `ListReorderView`
- `apps/api/library/urls.py` - `entries/<work_id>/comments/`, `comments/<comment_id>/`, `lists/`, `lists/<list_id>/`, `lists/<list_id>/items/`, `lists/<list_id>/items/<item_id>/`, `lists/<list_id>/reorder/`
- `apps/api/library/tests/test_comments.py` (new, 207 lines) - unicity, ownership, privacy, hostile-text CRUD tests
- `apps/api/library/tests/test_lists.py` (new, 340 lines) - membership, duplicate rejection, reorder oracle (missing/stale/matching version), concurrency, exception-rollback, cross-user isolation, public-projection allowlist tests
- `apps/api/library/tests/test_schema.py` - 10 new PostgreSQL introspection tests for the three new tables
- `apps/api/accounts/serializers.py` - `_serialize_public_comments`, `_serialize_public_lists`, `build_public_profile()` extended with `comments`/`lists` keys
- `apps/api/accounts/tests/test_public_profile.py` - extended `FORBIDDEN_KEYS`, five new tests for the comments/lists aggregate privacy

## Decisions Made
See `key-decisions` in frontmatter. The most consequential: `CustomList` is a genuinely new aggregate (promote, not alias); comment/list visibility is independent of `AccountProfile`'s two toggles; and the reorder payload uses item ids (not work ids) as the ordering key.

## Deviations from Plan

**1. [Process] Task 1 and Task 2 committed together instead of as two separate RED/GREEN pairs**
- **Found during:** preparing per-task commits after both tasks' code and tests were verified green
- **Issue:** Task 1 (comments) and Task 2 (lists) extend the identical five production files, and this plan's single migration covers both tasks' schema by explicit design (05-PATTERNS.md). An attempt to isolate Task 1's models.py to comment-only content (keeping the full migration) produced a genuine bug: Django's autodetector saw `CustomList`/`CustomListItem` as removed models relative to the migration history, and `pytest-django`'s `transaction=True` test teardown (`flush`) failed against the resulting inconsistent schema state.
- **Fix:** Restored the full combined state for all five files and the migration; committed one `test(05-02)` commit (both test files) followed by one `feat(05-02)` commit (all production code), preserving RED-before-GREEN ordering at the plan level.
- **Files affected:** `apps/api/library/{models,serializers,services,views,urls}.py`, the migration
- **Verification:** Full backend suite (588/588) passes at every commit boundary actually pushed to history; the broken intermediate split was verified-then-reverted before any commit was made from it.
- **Commit:** `f02cdf3`, `a50f77b`

**Total deviations:** 1 process deviation (commit granularity), 0 code bugs shipped. **Impact:** none on runtime correctness -- both task's full behavior lists are independently exercised and passing; only the git history's per-task isolation is coarser than the plan's nominal per-task tdd cycle.

## Issues Encountered

None beyond the process deviation above, which was caught and resolved before any commit was made from the broken intermediate state.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness

Ready for hand-off: `GET/POST /api/library/entries/<work_id>/comments/`, `GET/PATCH/DELETE /api/library/comments/<comment_id>/`, `GET/POST /api/library/lists/`, `GET/PATCH/DELETE /api/library/lists/<list_id>/`, `POST /api/library/lists/<list_id>/items/`, `DELETE /api/library/lists/<list_id>/items/<item_id>/`, and `POST /api/library/lists/<list_id>/reorder/` are all stable, tested against real PostgreSQL, and additive to the existing contract (`05-01`'s profile/favorites endpoints and Phase 1-4's auth/library/recommendation endpoints are unchanged).

Open for the rest of the phase: Plan 05-03 (copy metadata) builds on the same `OwnedCopy`/ownership patterns and depends on this plan's migration (`library.0003_phase5_comments_lists`) for its own `0004_phase5_copy_metadata.py`. The Playwright `e2e/collection-workflows.spec.ts` journey and its accessibility matrix -- explicitly the web session's responsibility per this plan's `<handoff>` -- have not been run from this plan and remain a phase-level gate before sign-off (see coverage D12).

## Self-Check: PASSED

All 11 claimed files verified present on disk; all 3 task commit hashes (`f02cdf3`, `a50f77b`, `b7ffdec`) verified present in `git log`.

---
*Phase: 05-complete-collection-workflows-and-portability*
*Completed: 2026-09-12*
