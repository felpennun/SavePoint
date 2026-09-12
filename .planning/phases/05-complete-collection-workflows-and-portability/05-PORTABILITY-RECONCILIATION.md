---
phase: "05"
plan: "04"
status: complete
created: "2026-09-13"
---

# Fase 5 — Reconciliación de portabilidad y perfil (PROF-01/PORT-01..04)

**Propósito:** cerrar explícitamente la divergencia detectada en `05-RESEARCH.md`
("Pitfall 1: dejar que el requisito antiguo mande sobre el contexto") entre el
wording histórico de `REQUIREMENTS.md`/`ROADMAP.md` y las decisiones bloqueadas
de `05-CONTEXT.md` (D-01, D-08, D-09). Este documento es la fuente única de
verdad sobre qué quedó implementado en la Fase 5 y qué permanece diferido, para
que ningún ejecutor futuro reintroduzca alcance no autorizado (JSON, importación,
alias editable) "para completar el roadmap".

## Matriz de decisión

| Requisito | Decisión bloqueada | Estado en Fase 5 | Evidencia |
|---|---|---|---|
| **PROF-01** | **D-01**: el alias público coincide con `User.username` y no es editable; solo biografía y avatar HTTPS son datos editables del perfil. | Satisfecho tal como quedó redactado en `REQUIREMENTS.md` ("User can edit their biography and optional HTTPS avatar while the login alias remains immutable") — el wording ya no exige edición de alias. | `apps/api/accounts/services.py::update_profile`, `apps/api/accounts/tests/test_profile.py::test_profile_update_payload_cannot_change_username` (Plan 05-01). |
| **PORT-01** | **D-08**: la portabilidad de esta fase se limita a exportación CSV; el contenido exportado corresponde a los datos visibles en la aplicación. | Satisfecho **únicamente en su parte CSV versionada**. El wording vigente de `REQUIREMENTS.md`/`ROADMAP.md` ya excluye JSON explícitamente ("JSON is not part of the Phase 5 closure"), por lo que no queda parcial respecto a su propio texto — pero sigue siendo una satisfacción parcial del enunciado histórico más amplio del roadmap original (colección+ratings+listas como CSV **y** JSON). No se implementa JSON en esta fase ni como código "preparatorio". | `apps/api/library/export.py`, `apps/api/library/tests/test_export.py` (Plan 05-04, Tarea 1). |
| **PORT-02** | **D-09**: JSON e importación con vista previa quedan fuera de la implementación actual; deben señalarse como pendientes con reconciliación explícita del roadmap. | **pending**, asignado explícitamente a **Phase 7**. Ningún endpoint, parser ni test de feature de importación se crea en `apps/api/library` durante la Fase 5. | `.planning/ROADMAP.md` (sección "Portability carry-over" de la Fase 7); `.planning/REQUIREMENTS.md` (traceability table: `PORT-02 | Phase 7 | Pending`). |
| **PORT-03** | **D-09**: los resultados por fila, errores y conflictos deterministas de importación quedan fuera de la implementación actual. | **pending**, asignado explícitamente a **Phase 7**. Sin endpoints, parsers ni tests de feature de importación en `apps/api/library`. | `.planning/ROADMAP.md` (sección "Portability carry-over" de la Fase 7); `.planning/REQUIREMENTS.md` (traceability table: `PORT-03 | Phase 7 | Pending`). |
| **PORT-04** | Derivado de D-08: las celdas CSV neutralizan fórmulas de hoja de cálculo potencialmente maliciosas. | Satisfecho: cada celda pasa por `neutralize_spreadsheet_formula()` antes de `csv.writer`, de forma idempotente. | `apps/api/library/export.py::neutralize_spreadsheet_formula`, `apps/api/library/tests/test_export.py::test_hostile_store_and_comment_values_are_neutralized_in_the_export`. |

## Decisión adicional: `CustomList` es el agregado primario, no un alias

`CustomList`/`CustomListItem` (Plan 05-02) son la representación canónica y
única de "lista personalizada de juegos" en el backend de SavePoint. No existe
ninguna entidad previa de la que `CustomList` sea un alias o una migración de
nombre: antes de la Fase 5 no había ningún modelo de listas manuales de juegos
en el repositorio (`apps/api/library/models.py` solo tenía `LibraryEntry` y
`OwnedCopy`). Esta es una decisión de **promoción** (nueva entidad), confirmada
en `05-02-SUMMARY.md` ("`CustomList` is the primary name for the new library
aggregate (assumption-delta: promote), not an alias of any prior entity").
Cualquier trabajo futuro sobre listas (Fase 6/7, importación futura de listas
bajo PORT-02/03) debe extender `CustomList`/`CustomListItem`, no crear una
segunda representación paralela.

## Frontera de alcance verificada para esta reconciliación

- `apps/api/library/export.py` es de solo lectura: construye filas desde
  campos nombrados (`FavoriteSlot`, `LibraryEntry`, `OwnedCopy`, `GameComment`,
  `CustomListItem`), nunca desde `values()` amplio ni `__dict__`.
- No existe ningún archivo cuyo nombre contenga `import` o `parser` bajo
  `apps/api/library`, y no hay rutas, clases ni parsers de importación
  registrados en `apps/api/library/urls.py` o `apps/api/library/views.py`.
- Los importadores de catálogo que sí existen en el repositorio (por ejemplo,
  los comandos de gobierno del corpus IGDB en `apps/api/catalogue/management/`)
  están fuera del ámbito de esta reconciliación: importan datos de catálogo
  gobernado, no colecciones/listas de usuario, y no se reclasifican aquí como
  parte de PORT-02/PORT-03.

## Cierre

Con esta reconciliación:

- `PROF-01` permanece cerrado según el wording vigente (Plan 05-01).
- `PORT-01` queda cerrado en su alcance CSV-only vigente; JSON no forma parte
  del cierre de la Fase 5.
- `PORT-02` y `PORT-03` permanecen `pending`, asignados a `Phase 7`, sin
  endpoints ni tests de feature en esta fase.
- `PORT-04` queda cerrado con evidencia de neutralización idempotente.
- `CustomList` queda documentado como el agregado primario y único de listas
  personalizadas.

Ningún requisito se declara completo por encima de lo que su propia evidencia
automatizada demuestra.
