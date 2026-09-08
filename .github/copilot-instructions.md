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

Antes de trabajar, lee `CONVENTIONS.md`, `AGENTS.md`, `.planning/` y el vault
`ideas-vault/`. El proyecto usa español para la documentación de tesis, la planificación y
la conversación; el código, identificadores, comentarios de código, tests, logs y mensajes de
commit se mantienen en inglés.

## Vault vivo de Obsidian

`ideas-vault/` es un espejo conceptual vivo, no una fuente canónica. Cada LLM o colaborador
debe consultarlo al comenzar una tarea y actualizarlo antes de terminarla si produce
información nueva, una decisión, un requisito, un resultado experimental, una limitación o un
cambio relevante de arquitectura o producto. Las notas deben enlazar con la fuente canónica
correspondiente (`CONVENTIONS.md`, `AGENTS.md`, `docs/` o `.planning/`) y con notas relacionadas
cuando proceda.

En trabajo paralelo, no sobrescribas notas ajenas: añade una nota fechada o edita únicamente
el apartado afectado. Marca las propuestas como `Propuesta` hasta su aprobación. Nunca guardes
en el vault secretos, cookies, tokens, credenciales, datos personales ni logs brutos.

Consulta [`ideas-vault/README.md`](../ideas-vault/README.md) y la plantilla
[`ideas-vault/Conceptos/Vault vivo y sincronizacion.md`](../ideas-vault/Conceptos/Vault%20vivo%20y%20sincronizacion.md)
para el procedimiento completo.
