# API Coverage — IGDB v4 (+ conditional RAWG)

> Full coverage by default. Opt-outs are explicit, reasoned decisions.
> Esta fase reejecuta el importador IGDB con campos nuevos (rating de usuario,
> summary, alternative_names, franchises, involved_companies) y, condicionado a
> la cobertura medida en Wave 0, puede añadir RAWG como segunda fuente de rating.

| capability | decision | reason |
|---|---|---|
| IGDB `POST /v4/games` — extended fields (`rating`, `rating_count`, `total_rating_count`, `summary`, `alternative_names.name`, `franchises.name`, `collections.name`, `involved_companies.company.name`, `involved_companies.developer`) | INTEGRATE | D-05 (user rating), D-11 (franchise/developer features), UI-SPEC §3 (synopsis), Pattern 4 (alias backfill). Dot-expansion keeps one request per page. |
| IGDB `POST /v4/games/count` — eligible primary-work count | INTEGRATE | already used by `import_igdb_catalogue` for the resumable-run boundary; unchanged. |
| IGDB `POST /v4/platforms` — id/slug/name resolution for the D-01 allowlist | INTEGRATE | Pattern 1: PS5/Xbox Series ids are `[ASSUMED]`; a live probe resolves the ~40-platform allowlist before `govern_corpus` runs. |
| IGDB Popularity Primitives / `hypes` / player-peak signals (trending) | OPT-OUT | deferred to Phase 6 (CONTEXT.md Deferred Ideas — "Estante Tendencia"; D-24 keeps only `first_release_date`-based "Novedades"). |
| IGDB `aggregated_rating` / `aggregated_rating_count` (critic score) | OPT-OUT | D-05 explicitly prefers user ratings over critic ratings; critic fields are last-resort only and not snapshotted. |
| IGDB covers / images | OPT-OUT | already covered in Phase 01.1 (hotlinked `t_cover_big`, ADR-006); not re-decided here. Full cover coverage stays incremental (01.1 D-06). |
| RAWG `GET /api/games` — user `rating` + `ratings_count` for allowlist works | INTEGRATE (gated) | D-05: decided at the **Plan 02-02 Task 3** `blocking-human` checkpoint (see also 02-RESEARCH.md Open Question 1) with the measured IGDB governed-corpus user-rating coverage in hand. D-06 sets **no hard coverage floor**: the ~60% figure is a non-binding decision aid for the author, not an automatic gate. If not activated: OPT-OUT recorded in ADR-008 with the measured coverage figure as the rationale. |
| RAWG `metacritic` (critic score) | OPT-OUT | D-05: critic source, last resort only; not used even if RAWG is adopted. |
| RAWG data redistribution / bulk catalogue pull | OPT-OUT | rawg.io/tos_api: 20k requests/month hard cap + no-redistribution clause. Any RAWG use is a bounded top-N-by-`rating_count` enrichment over allowlist works only, never a full catalogue pass. |
