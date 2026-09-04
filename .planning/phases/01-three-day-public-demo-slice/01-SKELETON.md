# Walking Skeleton — SavePoint

**Phase:** 1
**Generated:** 2026-09-04

## Capability Proven End-to-End

Una persona inicia sesión en la demo, abre un juego del catálogo local y guarda un estado que persiste en PostgreSQL y vuelve a mostrarse en la interfaz.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | Next.js 16 + TypeScript; Django 5.2 LTS + DRF | UI accesible/SSR y dominio relacional con auth madura |
| Data layer | PostgreSQL 18, Django ORM y migraciones | Ruta canónica local, CI y deployment |
| Auth | Sesión Django, cookie segura, CSRF, same-origin | Evita tokens propios y secretos en navegador |
| Deployment target | Docker Compose + PaaS Docker elegido por checkpoint | Misma imagen local/pública |
| Directory layout | `apps/web`, `apps/api`, `data`, `infra`, `e2e`, `docs` | Separa interfaz, dominio, corpus, operación y evidencia |

## Stack Touched in Phase 1

- [ ] Project scaffold (framework, build, lint, test runner)
- [ ] Routing — at least one real route
- [ ] Database — at least one real read AND one real write
- [ ] UI — at least one interactive element wired to the API
- [ ] Deployment — running on dev environment OR documented local full-stack run command

## Out of Scope (Deferred to Later Slices)

- Registro abierto, recuperación de contraseña y administración completa
- API de enriquecimiento en runtime y filtros avanzados
- Comentarios, listas, importación/exportación e inventario enriquecido
- Recomendadores de contenido, colaborativos e híbridos y panel de investigación

## Subsequent Slice Plan

- Phase 2: corpus gobernado y evaluación congelada
- Phase 3: colección completa y portabilidad
- Phase 4: descubrimiento y enriquecimiento
- Phase 5: harness y baselines
- Phase 6: contenido explicable
- Phase 7: colaborativo/híbrido
- Phase 8: panel, hardening y evidencia final
