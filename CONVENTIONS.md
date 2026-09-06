# Convenciones del proyecto SavePoint

> Documento canónico de convenciones para **cualquier** asistente de IA que trabaje en
> este repositorio (Claude Code, GitHub Copilot, Codex u otro), y para colaboradores
> humanos. Si otra instrucción entra en conflicto con esta, **manda esta**.

---

## 1. Idioma (regla vigente desde 2026-09-06)

| Ámbito | Idioma | Qué incluye |
|---|---|---|
| **Documentación de la tesis** | **Español** | Todo `docs/` (ADRs, `docs/verification/`, `docs/methodology/`, `docs/deployment/`, firmas de fase), y cualquier prosa que forme parte del registro de evidencia de la tesis. Los documentos nuevos se redactan directamente en español. |
| **Conversación** | **Español** | Todas las respuestas del asistente al autor. Todos los prompts que un asistente escriba para *otra* IA que trabaje en este proyecto. |
| **Planificación GSD** | **Español** para prosa nueva | `.planning/**` (STATE, ROADMAP, PLAN/SUMMARY, RESEARCH, CONTEXT, VERIFICATION, deferred-items…). El material heredado en inglés se pasa a español cuando se toca; no hace falta un barrido retroactivo salvo que el autor lo pida. |
| **Código** | **Inglés** | Identificadores, comentarios *de código*, mensajes de commit, nombres de tests, cadenas de log, nombres de rama. Convención estándar de software: el código se mantiene convencional y portable. |

### Matices que se respetan siempre

- **Citas textuales en su idioma original.** Los términos legales citados literalmente (p. ej. Twitch Developer Services Agreement, FAQ de IGDB en `docs/verification/igdb-api-probe.md` §5 y `docs/adr/ADR-006`) se conservan **en inglés** dentro de un marco de prosa en español. Traducir una cita legal destruye su valor probatorio.
- **Tokens neutrales de idioma no se traducen:** identificadores de código, IDs de requisito (`CAT-02`, `DATA-04`…), rutas de fichero, hashes de commit, URLs, nombres de variables de entorno, comandos.
- **Encabezados de ADR:** `scripts/check-evidence.ps1` exige exactamente estos siete en cada `docs/adr/ADR-*.md`:
  `## Contexto`, `## Alternativas consideradas`, `## Decisión`, `## Evidencia y fuentes`,
  `## Consecuencias`, `## Reversibilidad`, `## Aprobación y revisión` — más la cadena literal
  `Autor de la decisión` y al menos una URL `https://`.
- **Fotos congeladas fechadas** (p. ej. `docs/verification/phase-01-signoff.2026-09-05T10-45.md`)
  se dejan tal cual: son registros históricos de un instante, no se re-traducen.
- **Gates de contenido:** si traduces un documento que tiene un gate determinista
  (`scripts/verify-igdb-adr.ps1`, `scripts/verify-igdb-probe.ps1`, el here-string de
  `scripts/verify-igdb-fresh-import.ps1`), actualiza los patrones de ese gate en el **mismo
  commit** para que casen el texto español. Los comentarios e identificadores del script
  siguen en inglés; solo sus patrones de coincidencia pasan a español.
- **Pins de hash del ledger:** `docs/methodology/agent-ledger.jsonl` fija hashes SHA-256
  (forma LF, como los guarda Git) de artefactos concretos. Si traduces un artefacto fijado,
  refresca su pin al nuevo hash LF (`git show HEAD:<ruta> | sha256sum`) en el mismo commit y
  añade una entrada de ledger que lo documente (enfoque de "foto congelada", ya usado en la
  Fase 1).

---

## 2. Cómo carga cada herramienta estas convenciones (no hace falta ningún comando)

Cada asistente lee su fichero de instrucciones **automáticamente al empezar cada sesión**.
No existe ni hace falta un comando para "recargar convenciones"; basta con que la regla esté
en el fichero que cada herramienta lee, y lo está:

| Herramienta | Fichero que lee automáticamente | Comando útil (opcional) |
|---|---|---|
| **Claude Code** | `CLAUDE.md` + `AGENTS.md` (raíz) | memoria automática con `language-conventions.md` **fijada** (pinned) → aplica en toda sesión futura sin intervención. Para forzar relectura a mitad de sesión: pídelo en lenguaje natural ("relee `CONVENTIONS.md`"). `/memory` inspecciona la memoria. |
| **GitHub Copilot** | `.github/copilot-instructions.md` | — |
| **Codex / otros agentes** | `AGENTS.md` (estándar cross-tool) | — |
| **Workflows GSD** (`/gsd-*`) | `AGENTS.md` + `.planning/PROJECT.md` + `.planning/STATE.md` | `/gsd-resume-work` recarga STATE + contexto de planificación al inicio de sesión. |

Si en algún momento quieres un empujón manual para *cualquier* IA, una frase sirve:
**"Antes de empezar, lee `CONVENTIONS.md` y revisa `.planning/`."**

---

## 3. Otras convenciones vigentes (resumen; la fuente de detalle está enlazada)

- **Dependencias:** toda dependencia directa nueva o cambio de versión exige aprobación humana
  explícita + fila en `docs/verification/dependency-legitimacy.md` + fila en
  `scripts/check-dependencies.ps1` + entrada de ledger. Ver `docs/adr/ADR-006` y
  `docs/verification/dependency-legitimacy.md`.
- **Secretos:** nunca se imprime, loguea, commitea ni escribe un valor de credencial, token
  o cadena de conexión. Solo por nombre de variable. Ver `docs/deployment/public-demo.md` y
  la nota "Higiene de secretos" de `docs/verification/repo-review-2026-09-06.md`.
- **Sin datos en bloque de IGDB en Git:** el `pg_dump` de ~93 MB en `data/snapshots/` está
  gitignored a propósito (ADR-006 §4).
- **Commits:** convencionales, en inglés; los mensajes de commit de un asistente terminan con
  `Co-Authored-By: <modelo> <noreply@anthropic.com>` cuando aplique.

---

*Creado 2026-09-06. Cambiar esta convención requiere una decisión del autor y actualizar los
punteros en `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md` y `.planning/PROJECT.md`.*
