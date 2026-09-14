---
quick_id: 260914-gdk
slug: sync-obsidian-vault-and-close-completed-
description: Synchronize the Obsidian vault with the repository and close only completed GitHub issues.
mode: quick-full
must_haves:
  truths:
    - Obsidian notes describe the repository's final Phase 7 state without stale completion claims.
    - Completed GitHub issues are closed with evidence, while unresolved operational and CI work remains open.
    - The remaining E2E rating assertion is idempotent for repeated runs.
  artifacts:
    - path: ideas-vault/Fases/Fase 7 - Panel de investigacion y hardening.md
      provides: Canonical Phase 7 vault note and associations.
    - path: e2e/demo-journey.spec.ts
      provides: Idempotent repeated-run rating flow.
  key_links:
    - from: ideas-vault/Fases/Fase 7 - Task 1 07-05 verificacion parcial 2026-09-14.md
      to: .planning/phases/07-research-panel-hardening-and-evidence-freeze/07-05-SUMMARY.md
      via: Historical partial note points to final closure.
    - from: GitHub issues 43, 51, 53
      to: repository evidence
      via: Close comments cite integrated code and passing tests.
---

## Task 1: Reconcile the Obsidian Phase 7 notes

- files: `ideas-vault/00 - Indice.md`, `ideas-vault/Fases/Fase 7 - Panel de investigacion y hardening.md`, `ideas-vault/Fases/Fase 7 - Panel y hardening.md`, `ideas-vault/Fases/Fase 7 - Task 1 07-05 verificacion parcial 2026-09-14.md`
- action: Keep one canonical Phase 7 note linked from the index and maps, update its final evidence links, mark the older duplicate as superseded, and make the partial verification note explicitly historical with a link to the final summary.
- verify: Search the vault for Phase 7 links and stale claims; all canonical associations resolve to current planning and verification artifacts.
- done: No Phase 7 note presents Tasks 2/3 as pending or competes with the canonical note.

## Task 2: Resolve the completed E2E issue and close only justified issues

- files: `e2e/demo-journey.spec.ts`, `.planning/quick/260914-gdk-sync-obsidian-vault-and-close-completed-/260914-gdk-SUMMARY.md`
- action: Make the repeated-run rating interaction conditional on `aria-pressed`, verify the focused E2E/test contract, then close #43, #51, and #53 with evidence. Leave #31 and #54 open because CI/protection and long-session connection capacity remain unresolved.
- verify: Run the focused available tests/checks, query GitHub issue states, and confirm the worktree has no unintended code changes.
- done: Issues #43, #51, and #53 are closed; #31 and #54 remain open with accurate scope.
