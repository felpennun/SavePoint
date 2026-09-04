# Commit and issue-tracking policy

This project is a single-author academic thesis repository. This document fixes the commit message
format and how work is tracked so history stays legible for the tribunal and for anyone (human or
agent) resuming work later.

## Issue tracking

Work beyond a trivial fix is tracked as a GitHub Issue on
[felpennun/SavePoint](https://github.com/felpennun/SavePoint/issues), organised on the
[SavePoint project board](https://github.com/users/felpennun/projects/1) (Todo / In Progress / Done).

- `phase-01`, `phase-02`, ... label which GSD phase an issue belongs to.
- `deployment`, `bug`, `documentation`, `enhancement`, etc. label the kind of work.

## Commit message format

```
<type>(<scope>): <summary>

[optional body: why, not what]

[optional: Refs #<issue> | Closes #<issue>]
[optional: Co-Authored-By: <agent name> <noreply@anthropic.com>]
```

**Type** — one of the [Conventional Commits](https://www.conventionalcommits.org/) types actually used
in this repo's history: `feat`, `fix`, `docs`, `test`, `chore`, `build`, `refactor`.

**Scope** — the GSD plan ID when the commit closes out a plan (`01-11`, `01-12`), otherwise a short area
name (`api`, `web`, `deploy`). Keep using the plan-ID scope for GSD-driven commits — it already ties every
commit to its `.planning/phases/*/*-SUMMARY.md`.

**Summary** — imperative, lower case, no trailing period, states *why* the commit exists over *what*
changed line-by-line (the diff already shows that).

## Linking commits to issues

When a commit fully resolves a tracked issue, add a trailer line:

```
Closes #6
```

GitHub closes the issue automatically when that commit lands on `main`. For a commit that only makes
progress on an issue without resolving it, use `Refs #6` instead — this links the commit in the issue's
timeline without closing it.

Do not put the issue reference in the summary line; keep it as a trailer so the summary line stays a
clean, greppable description of the change on its own.

## What never goes in a commit message, issue, or PR body

- Connection strings, passwords, API keys, tokens, or cookies — not even redacted fragments or
  hostnames from a real provider (Neon, Render, Vercel). Use `scripts/check-secrets.ps1`'s canary
  patterns as a reference for what counts as secret-shaped.
- Screenshots or logs that were not first checked for the above.

## Attribution

Commits produced with AI-agent assistance end with a `Co-Authored-By:` trailer naming the agent, matching
the existing history. This is informational, not a policy toggle — it stays on unless explicitly
disabled for a session.
