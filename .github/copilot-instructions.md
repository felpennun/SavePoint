<!-- GSD Configuration — managed by gsd-core installer -->
# Instructions for GSD

- Use the gsd-core skill when the user asks for GSD or uses a `gsd-*` command.
- Treat `/gsd-...` or `gsd-...` as command invocations and load the matching file from `.github/skills/gsd-*`.
- When a command says to spawn a subagent, prefer a matching custom agent from `.github/agents`.
- Do not apply GSD workflows unless the user explicitly asks for them.
- After completing any `gsd-*` command (or any deliverable it triggers: feature, bug fix, tests, docs, etc.), ALWAYS: (1) offer the user the next step by prompting via `ask_user`; repeat this feedback loop until the user explicitly indicates they are done.
<!-- /GSD Configuration -->

# Convenciones del proyecto SavePoint

Documento canónico: `CONVENTIONS.md` (raíz). Léelo antes de trabajar. Lo esencial:

## Idioma (vigente desde 2026-09-06)

- **Español**: toda la documentación de la tesis (`docs/**`), toda la conversación con el
  autor, todos los prompts que escribas para otra IA, y la prosa nueva en `.planning/**`.
- **Inglés**: el código — identificadores, comentarios de código, mensajes de commit, nombres
  de tests, cadenas de log, nombres de rama.
- **Se conservan en su idioma original**: las citas legales textuales (Twitch DSA / FAQ de
  IGDB), y los tokens neutrales de idioma (IDs de requisito, rutas, hashes, URLs, nombres de
  variables de entorno, comandos).
- Al traducir un documento con gate determinista (`scripts/verify-igdb-*.ps1`), actualiza los
  patrones del gate en el mismo commit; si está fijado por hash en
  `docs/methodology/agent-ledger.jsonl`, refresca el pin. Ver `CONVENTIONS.md` §1.

Este fichero se lee automáticamente al inicio de cada sesión; no hace falta ningún comando.
Empujón manual: *"Antes de empezar, lee `CONVENTIONS.md` y revisa `.planning/`."*
