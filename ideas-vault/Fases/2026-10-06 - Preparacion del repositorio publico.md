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
| `design/` | En GitHub solo `mockups/rendered-claude-design/` (5 renders de los lienzos) y `mockups/4-maquetas-html-fase-01-1/` (6 maquetas HTML). Salen `design/brand/` (con su zip), `mockups/3-logos-y-banners/` (dirección «Cristal» descartada y duplicada), `mockups/1-lienzos-claude-design/` y `mockups/2-renders-nocturne-preview/`; siguen en local. | este cambio |
| CI (`quality-gates.yml`) | Se mantienen las pasarelas de CI. Estaba en rojo desde e8b6d25 porque `check-dependencies` aprobaba Next 16.3.4 y el catálogo de pnpm ya tenía 16.3.8; corregido en 1fd8f35 con un anexo de legitimidad. En verde desde entonces. | 1fd8f35 |

## Pendiente

`docs/`, `.planning/`, `ideas-vault/`, `scripts/`, `apps/api/*.json`, `design/`, ver el informe local `.design-import/informe-repositorio-publico.md`. Antes de publicar: contraseñas demo, `LICENSE`, contenido derivado de IGDB, alerta Dependabot #6 y la decisión sobre el historial de Git.

## Fuentes

- `CONVENTIONS.md` (documento único de convenciones).
- [[2026-10-05 - Revision completa del TFG]]
