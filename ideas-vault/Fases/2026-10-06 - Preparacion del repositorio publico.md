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
| CI (`quality-gates.yml`) | Se mantienen todas las pasarelas, pero llevan en rojo desde e8b6d25 (`check-dependencies` no entiende `catalog:` de pnpm). Pendiente de arreglar. | pendiente |

## Pendiente

`docs/`, `.planning/`, `ideas-vault/`, `scripts/`, `apps/api/*.json`, `design/`, ver el informe local `.design-import/informe-repositorio-publico.md`. Antes de publicar: contraseñas demo, `LICENSE`, contenido derivado de IGDB, alerta Dependabot #6 y la decisión sobre el historial de Git.

## Fuentes

- `CONVENTIONS.md` (documento único de convenciones).
- [[2026-10-05 - Revision completa del TFG]]
