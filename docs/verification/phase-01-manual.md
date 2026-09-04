# Phase 1 manual verification protocol

This protocol complements automated pytest, Vitest, Playwright, and axe checks. It is versioned so that a thesis reviewer can reproduce the same human observations. Never paste passwords, cookies, DSNs, API keys, or environment dumps into this document or screenshots.

## Automated coverage (Plan 01-10, `e2e/a11y.spec.ts`)

The following sections of this checklist are now exercised automatically, at commit `97d438e` and later: 26 tests, all green -- axe (critical/serious = 0) across homepage/login/catalogue/one game detail/sources, ES and EN, at 375x812 and 1280x800; the full keyboard-only journey (skip link → login → search → detail → status → collection → profile → sign-out); no horizontal overflow at 375px; `prefers-reduced-motion` renders without error. This is agent-generated automated evidence, not a human confirmation -- per Sign-off below, it does not by itself close the **Reflow at 400% zoom** or **Basic screen-reader pass** sections, which require an actual human at a real zoom level / with a real screen reader. Those two sections' checkboxes remain unchecked pending that human session; do not check them from automated output.



## Evidence header

Record one row for every verification session.

| UTC date | Git commit | Environment/URL | Browser and version | OS | Reviewer | Result |
|---|---|---|---|---|---|---|
| _pending_ | _pending_ | local or public URL, without credentials | _pending_ | _pending_ | _pending_ | PASS / FAIL |

For failures, record only the page, observable behavior, expected behavior, and a non-sensitive screenshot reference. Link the fixing commit and repeat the entire affected section.

## Preconditions

- Use the immutable local catalogue and synthetic demo users only.
- Verify Spanish and English independently; switching locale must preserve route and form input.
- Exercise homepage, login, catalogue, one game detail, collection, public profile, and sources/methodology.
- Open developer tools only to inspect DOM/network field names. Redact cookies and authorization-related headers from all evidence.
- Confirm external-provider access can be disabled without losing the catalogue journey.

## Keyboard-only journey

- [ ] The skip link is first, is visible on focus, and moves focus to `main`.
- [ ] Tab order follows reading order; every focus indicator is visible and unclipped.
- [ ] Homepage → login → catalogue is achievable without a pointer.
- [ ] Search submits with Enter, moves focus to the result heading, and announces the count once.
- [ ] Mobile menu reports its expanded state, closes with Escape, and returns focus to its trigger.
- [ ] Status can be saved using native keyboard interaction; success is announced once.
- [ ] A 3.5/5 rating can be selected and saved without relying on colour or star shape.
- [ ] Two distinct copies can be added; format, platform, and edition remain understandable.
- [ ] Collection and public profile are reachable and sign-out is an explicit action.
- [ ] Failed form submissions preserve safe user input and focus a linked error summary.
- [ ] No primary action or information is available only on hover.

## Reflow at 320 CSS pixels

Set the viewport to 320 CSS pixels wide at 100% zoom, then visit every required page in ES and EN.

- [ ] There is no horizontal page scrolling.
- [ ] Navigation, forms, buttons, cards, provenance, and copy rows remain fully reachable.
- [ ] Controls retain a usable 44×44 CSS pixel target or a documented inline exception.
- [ ] Titles, translated labels, source names, URLs, and error messages wrap without clipping.
- [ ] Cover frames retain a 3:4 ratio without shifting adjacent content.
- [ ] DOM order and visual order match; no mobile-only information replaces desktop content.

## Reflow at 400% zoom

Use a desktop viewport of at least 1280×800, set browser zoom to 400%, and repeat the required pages in ES and EN.

- [ ] Content reflows to one dimension without horizontal page scrolling.
- [ ] Focused controls are not hidden by sticky elements, dialogs, or viewport edges.
- [ ] Form errors, live regions, menus, and modal content remain perceivable and operable.
- [ ] Text is not truncated, overlapped, or replaced with icons.

## Basic screen-reader pass

Use NVDA with Firefox/Chrome on Windows or VoiceOver with Safari on macOS. Record the combination in the evidence header.

- [ ] Page title, language, one `h1`, landmarks, and navigation purpose are announced.
- [ ] Links and buttons have specific localized names; icons and duplicate cover images do not repeat noise.
- [ ] Form labels, required state, descriptions, errors, selected status, and numeric rating are announced.
- [ ] Loading, result counts, and mutation outcomes are announced once without reading the whole grid.
- [ ] Public-profile unavailable state does not reveal whether a private account exists.
- [ ] Sources/provenance are understandable and external link destinations are evident.

## Hostile fixture and privacy review

Use `e2e/fixtures/hostile.json`; it contains only synthetic identifiers and hostile strings.

- [ ] Every `untrustedText` value renders as inert text; no element, event handler, style, or script is created.
- [ ] Every `untrustedUrls` value is rejected; no navigation, redirect, server fetch, or link is produced.
- [ ] Owner A can access only A-owned copy data; visitor B cannot infer or mutate it by changing an identifier.
- [ ] The deliberately incorrect dataset hash blocks import and reports no raw record content.
- [ ] Public-profile DOM, HTML/RSC payloads, accessibility tree, and network responses contain no email, owned-copy detail, internal ID, note, purchase field, cookie, or credential.
- [ ] Browser bundles, source maps, container history, logs, screenshots, and generated reports contain no infrastructure secret or provider key.

## Visual and motion observations

- [ ] Token colors meet the required contrast and do not convey status alone.
- [ ] Reduced-motion preference removes all non-essential transition motion.
- [ ] Missing/unlicensed covers use the first-party placeholder and preserve attribution boundaries.
- [ ] Spanish and English have no raw translation keys, mixed-language states, or clipping under approximately 30% text expansion.

## Sign-off

The session passes only when all applicable boxes are checked, automated checks for the same commit are green, and every failure has been corrected and re-tested. The reviewer signs with name/initials and UTC date; agent-generated observations must be labelled as automated proposals until a human confirms them.

