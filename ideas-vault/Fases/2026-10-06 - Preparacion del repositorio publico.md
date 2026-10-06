# 2026-10-06 - Preparación del repositorio público

Estado: en curso. Criterio del autor: en GitHub solo lo que permite que la web funcione, el TFG y los mockups. **Todo se conserva en local**; lo que sale de GitHub se deja de versionar (`git rm --cached` + `.gitignore`), nunca se borra del disco.

## Decisiones tomadas, carpeta por carpeta

| Carpeta o fichero | Decisión | Commit |
|---|---|---|
| `e2e/artifacts/` | Sale de GitHub (capturas que regeneran las pruebas). Se mantienen los specs y `fixtures/hostile.json`, que leen dos tests de la API. | 05a7948 |
| `thesis/` y `TFG/` | La memoria pasa a vivir en `TFG/` con la versión exportada de Prism. En `TFG/` solo queda lo que debe verse en GitHub. | e1d6fbf |
| `.claude/`, `.codex/`, `.agents/`, `.github/{gsd-core,skills,agents,scripts,hooks,...}` | Salen de GitHub (instalación local de GSD, 2.955 ficheros). En `.github/` se quedan `workflows/` y `dependabot.yml`. El método se enlaza desde el README (GSD 1.12.0). | este cambio |
| `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md` | Salen de GitHub y siguen en local. Su contenido general se fusiona en `CONVENTIONS.md`, que pasa a ser el documento único (idioma ahora en §2, issues en §5). | este cambio |

## Pendiente

`docs/`, `.planning/`, `ideas-vault/`, `scripts/`, `apps/api/*.json`, `design/`, ver el informe local `.design-import/informe-repositorio-publico.md`. Antes de publicar: contraseñas demo, `LICENSE`, contenido derivado de IGDB, alerta Dependabot #6 y la decisión sobre el historial de Git.

## Fuentes

- `CONVENTIONS.md` (documento único de convenciones).
- [[2026-10-05 - Revision completa del TFG]]
