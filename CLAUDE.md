# CLAUDE.md

Instrucciones para Claude Code (y asistentes de la familia Claude) en el repositorio SavePoint.

## Convenciones del proyecto

**Lee y aplica [`CONVENTIONS.md`](CONVENTIONS.md).** Es el documento canónico. Lo esencial:

### Idioma (vigente desde 2026-09-06)

- **Español**: toda la documentación de la tesis (`docs/**`), toda la conversación con el
  autor, todos los prompts que escribas para otras IA, y la prosa nueva de `.planning/**`.
- **Inglés**: el código — identificadores, comentarios de código, mensajes de commit, nombres
  de tests, cadenas de log, nombres de rama.
- **Se conservan en su idioma original**: las citas legales textuales (Twitch DSA / FAQ de
  IGDB), y los tokens neutrales (IDs de requisito, rutas, hashes, URLs, nombres de env var,
  comandos).
- Detalles y matices (encabezados de ADR que exige `check-evidence.ps1`, gates de contenido a
  actualizar en paralelo, pins de hash del ledger, fotos congeladas que no se re-traducen):
  ver `CONVENTIONS.md` §1.

No hace falta ningún comando para recargar esto: `CLAUDE.md` y `AGENTS.md` se cargan al inicio
de cada sesión, y la memoria automática guarda `language-conventions.md` fijada. Para GSD,
`/gsd-resume-work` recarga el contexto de planificación.

## Vault vivo de Obsidian

Antes de trabajar, consulta `ideas-vault/`. Al terminar, actualiza el vault con cada
información, decisión, requisito, resultado, limitación o cambio relevante que hayas
producido. Enlaza siempre con la fuente canónica y no guardes secretos, credenciales,
datos personales ni logs brutos. La política completa está en
[`ideas-vault/README.md`](ideas-vault/README.md) y la plantilla en
[`ideas-vault/Conceptos/Vault vivo y sincronizacion.md`](ideas-vault/Conceptos/Vault vivo y sincronizacion.md).
El vault es un espejo conceptual vivo: `CONVENTIONS.md`, `AGENTS.md`, `docs/` y `.planning/`
siguen siendo las fuentes canónicas.

## Contexto del proyecto y stack

Ver [`AGENTS.md`](AGENTS.md) (proyecto, stack, requisitos, arquitectura) y `.planning/`
(`PROJECT.md`, `STATE.md`, `ROADMAP.md`, fases).
