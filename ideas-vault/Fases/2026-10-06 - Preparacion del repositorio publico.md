# 2026-10-06 - Preparación del repositorio público

Estado: en curso. Criterio del autor: en GitHub solo lo que permite que la web funcione, el TFG y los mockups. **Todo se conserva en local**; lo que sale de GitHub se deja de versionar (`git rm --cached` + `.gitignore`), nunca se borra del disco.

## Decisiones tomadas, carpeta por carpeta

| Carpeta o fichero | Decisión | Commit |
|---|---|---|
| `e2e/artifacts/` | Sale de GitHub (capturas que regeneran las pruebas). Se mantienen los specs y `fixtures/hostile.json`, que leen dos tests de la API. | 05a7948 |
| `thesis/` y `TFG/` | La memoria pasa a vivir en `TFG/` con la versión exportada de Prism. En `TFG/` solo queda lo que debe verse en GitHub. | e1d6fbf |
| `.claude/`, `.codex/`, `.agents/`, `.github/{gsd-core,skills,agents,scripts,hooks,...}` | Salen de GitHub (instalación local de GSD, 2.955 ficheros). En `.github/` se quedan `workflows/` y `dependabot.yml`. El método se enlaza desde el README (GSD 1.12.0). | este cambio |
| `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` | Salen de GitHub y siguen en local. Su contenido general se fusiona en `CONVENTIONS.md`, que pasa a ser el documento único (idioma ahora en §2, issues en §5). | este cambio |
| `CONTRIBUTING.md`, `ONBOARDING.md` | `CONTRIBUTING.md` rehecho en español y sin referencias internas; `ONBOARDING.md` (plantilla sin rellenar) sale de GitHub. | este cambio |
| `scripts/` | Salen `thesis-figures/`, los `verify-*`, `generate-phase-07-evidence` y los tres de traducción de sinopsis. Se quedan `public-corpus/`, `acquire_catalogue.py` y `mobile-audit/`. Pasarelas de CI y copias de seguridad: pendientes de decisión. | este cambio |
| `.planning/` | Se queda en GitHub como evidencia del método. Salen la caché de investigación, el estado de máquina de GSD (`state.json`, `config.json`, `estimation-calibration.json`, `WINDOWS.md`), `codebase/` y `onboarding/`. Las 6 maquetas HTML de la fase 01.1 pasan a `design/mockups/4-maquetas-html-fase-01-1/`. Pendiente: normalizar rutas locales en los `PLAN.md`. | este cambio |
| Copias de seguridad | Sale todo salvo `backup-postgres.ps1`. Backup manual de la base local creado el 2026-10-06 fuera del repositorio (631 MB, 331.000 obras, 433 usuarios), comprobado con su manifiesto. | este cambio |
| `docs/` | Se quedan `adr/` (9), `methodology/` (11, por ahora completa y pendiente de revisión) y 10 de `verification/` (los que exigen el arranque, el CI o el registro de evidencia, más `igdb-api-probe` e `igdb-catalogue-freeze`). Salen `deployment/` (con `public-demo.md`) y 49 informes de `verification/` que no son de fase; siguen en local. Los 22 documentos `phase-*` vuelven a publicarse agrupados en `verification/phase-NN/` (manual, launch gate, operaciones, firma, resultados); enlaces relativos y rutas del registro de evidencia actualizados, la foto congelada `phase-01-signoff.2026-09-05T10-45.md` solo se mueve. Referencias a lo retirado anotadas como «no incluido en el repositorio público». Pins del registro de evidencia refrescados (`check-secrets.ps1`, `uv.lock`, `deployed-smoke.spec.ts`) y `check-evidence` vuelve a pasar. | este cambio |
| `docs/methodology/` | Se queda `protocol.json`, `recommendation-algorithms.md` y tres documentos generales reescritos: `agent-method.md` (fusiona el método y los controles con agentes), `ai-use-disclosure.md` y `evaluation-protocol.md` (fusiona el protocolo y la adenda v15). Salen `agent-ledger.jsonl`, `academic-reference-register.md`, los dos `phase-07-*` y los dos documentos fusionados (siguen en local). `scripts/check-evidence.ps1` sale con el registro, porque sin él falla. `docs/deployment/backup-recovery.md` vuelve a publicarse, adaptado a lo que se publica (solo `backup-postgres.ps1`). | este cambio |
| `apps/api/*.json` | De 28 se quedan 8: los 4 que fijan los tests de Postgres (`corpus-*`, `feature-vector-cache-2026.09.2`), el artefacto v15 que carga el panel de investigación y los de v12, v13 (inválida) y v14. Salen 20 (4 ejecuciones fallidas, comprobaciones previas, cachés `fs-v5`..`fs-v9`, PopScore, población candidata, facetas); siguen en local. | este cambio |
| `design/` | En GitHub solo `design/README.md` y los 5 renders de los lienzos de Claude Design (`web`, `ideas`, `ideas-v2`, `inicio`, `identity`), sin subcarpetas. Todo lo demás (`design/mockups/`: lienzos originales, primera pasada de capturas, maquetas HTML de la fase 01.1, logos «Cristal» y `design/brand/`) sigue en local y está ignorado. | este cambio |
| `data/` | Se quedan `raw/`, `manifests/`, `demo/` (los lee `import_catalogue` y `seed_demo`; los tests fijan sus hashes) y `localization/summaries-es.json` (1.898 sinopsis traducidas con Claude a partir de IGDB; el arranque falla sin él). Salen `summaries-es.work.jsonl`, `provenance.json`, `curated.json` y el `HANDOFF`. Se añade al README una sección «Datos y atribuciones» (Wikidata CC0, Wikimedia, IGDB y la traducción como obra derivada). | este cambio |
| CI (`quality-gates.yml`) | Se mantienen las pasarelas de CI. Estaba en rojo desde e8b6d25 porque `check-dependencies` aprobaba Next 16.3.4 y el catálogo de pnpm ya tenía 16.3.8; corregido en 1fd8f35 con un anexo de legitimidad. En verde desde entonces. | 1fd8f35 |

## Release v1.0.0 y paquete de datos

- **Release** `v1.0.0` (commit 07a2e1a) con `savepoint-demo-data-v1.0.0.dump` (430 MB, SHA-256 `2549b8c3…fbd395`) y su `.sha256`. Es un volcado saneado de la base local: catálogo completo (190.479 obras gobernadas, 331.000 registros) y datos de recomendación del catálogo, más solo `demo_user1/2/3` (contraseña `demo_user123`). Se eliminaron los otros 430 usuarios y las sesiones y la auditoría; se hizo en una base temporal restaurada desde el backup, sin tocar la base local. `demo_user1` es una copia de la cuenta del autor.
- **Restauración:** `scripts/restore-demo-data.sh` y `.ps1` (comprueban el hash, recrean la base, restauran y arrancan). Probados desde un clon limpio de GitHub: 190.479 juegos, las cuatro cuentas entran y las recomendaciones de `demo_user1` salen listas.
- **Clon limpio sin paquete:** `publish_base_catalogue` hace visibles los 150 juegos de Wikidata (antes el catálogo salía vacío); solo en la cadena de arranque de `compose.yaml`.
- **Aviso legal:** el paquete redistribuye datos de IGDB con fines académicos y atribución, lo que se aparta de ADR-006 (no se redistribuye el dataset en bloque). Decisión del autor, recogida en el README y en las notas de la release.
- **Alerta Dependabot #6:** corregida (`source-map-js` 1.2.2). Las 8 PRs de Dependabot se cerraron y `dependabot.yml` ignora saltos de versión mayor.

## Decisiones sobre el historial y las contraseñas demo

- **Historial:** se mantiene completo, sin reescribir, por razones académicas (685 commits, líneas `Co-Authored-By` de IA, issues y PRs que cita la memoria). gitleaks no encuentra secretos reales: sus 948 avisos son falsos positivos (`seed_key` en dos manifiestos sintéticos que ya no se publican). Quedan en el historial el correo personal del autor en 136 commits (4 y 5 de septiembre), dos commits con un coautor «GPT-6» inexistente, zips antiguos de la memoria y otros ficheros retirados del árbol.
- **Contraseñas demo:** no se rotan ni se quitan. Irán en el README: son de cuentas de demostración sin información sensible, los profesores pueden acceder y el autor valorará ponerlo privado de nuevo cuando tenga nota.
- **Aviso:** `check-secrets.ps1` solo admite como marcador conocido `SavePoint-Demo-2026-Visit!`; si el README lista las otras dos contraseñas demo habrá que añadirlas a esa lista para que el CI pase.

## Pendiente

`docs/`, `.planning/`, `ideas-vault/`, `scripts/`, `apps/api/*.json`, `design/`, ver el informe local `.design-import/informe-repositorio-publico.md`. Antes de publicar: contraseñas demo, `LICENSE`, contenido derivado de IGDB, alerta Dependabot #6 y la decisión sobre el historial de Git.

## Fuentes

- `CONVENTIONS.md` (documento único de convenciones).
- [[2026-10-05 - Revision completa del TFG]]
