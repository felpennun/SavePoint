# Método de trabajo asistido por agentes

## Propósito y alcance

Este documento describe cómo SavePoint conserva evidencia técnica de investigación, diseño, planificación y ejecución asistidas. No afirma que un agente sea autor académico, revisor independiente ni responsable de una decisión humana. El autor del TFG conserva responsabilidad sobre selección, verificación, modificación y presentación del contenido.

Supuestos que debe confirmar el autor conforme a la política de su titulación:

- [AGENT-01] rol, actor, objetivo y responsabilidad por entrada son atribución suficiente;
- [AGENT-02] referencias y SHA-256 permiten reproducibilidad sin publicar conversaciones completas;
- [AGENT-03] `proposal`, `automated-check` y `author-decision` separan adecuadamente contribución, verificación y autoría.

Hasta esa confirmación, estos puntos son **supuestos metodológicos marcados**, no conclusiones académicas.

## Roles y responsabilidades

| Actor/rol | Objetivo | Responsabilidad y límite |
|---|---|---|
| Autor humano (`Felipe`) | Define alcance y acepta/rechaza decisiones | Responsable de la decisión académica; revisa fuentes, licencias, resultados y texto final. |
| `gsd-phase-researcher` | Recopila y sintetiza evidencia | Propone; debe etiquetar fuente, evidencia o supuesto. No concede derechos ni aprueba tecnología. |
| `gsd-ui-researcher` / implementador UI | Convierte requisitos en contrato y UI | Propone y ejecuta; accesibilidad automática no sustituye reflow/lector de pantalla humano. |
| `gsd-planner` | Divide alcance en planes verificables | Propone secuencia y gates; no declara completado el producto. |
| `gsd-executor` | Implementa, prueba y registra correcciones | Puede producir checks automatizados; no se presenta como verificación independiente. |
| Herramientas deterministas | Hash, tests, linters, checkers | Producen observaciones repetibles para un commit; no emiten juicio académico. |

## Runtime y modelo

Las entradas registran `runtime` y `model` sólo cuando el entorno los expone. En esta fase el runtime es Codex; la familia disponible se registra como `gpt-5` y la versión exacta no fue expuesta al repositorio. Se dice `unknown`, nunca se infiere, cuando un dato no está disponible. Un nombre de modelo no basta para reproducir una salida probabilística: la evidencia reproducible son los artefactos versionados, hashes, comandos y decisiones humanas.

## Protocolo

1. Registrar el objetivo y artefactos de entrada antes o al consolidar un resultado.
2. Etiquetar cada evento con exactamente uno de tres tipos: `proposal`, `automated-check`, `author-decision`.
3. Identificar actor humano o rol de agente por separado; una decisión humana usa `actor.kind=human`.
4. Referenciar inputs/outputs redistribuibles por ruta relativa y SHA-256. No guardar prompts completos, conversaciones, variables de entorno, cookies, credenciales ni logs brutos.
5. Enumerar herramientas/comandos sin sus secretos y registrar resultado (`pass`, `fail`, `changed`, `accepted`, `rejected`) y limitaciones.
6. Registrar fallos, alternativas rechazadas y correcciones igual que los éxitos. Una nueva observación se añade; no se reescriben entradas históricas.
7. Ejecutar `powershell -ExecutionPolicy Bypass -File scripts/check-evidence.ps1`. El checker prueba primero canaries inválidos y luego valida el ledger real.

## Formato append-only

`docs/methodology/agent-ledger.jsonl` contiene un objeto JSON independiente por línea. Campos obligatorios: `timestamp` UTC, `type`, `actor`, `objective`, `inputs`, `outputs`, `tools`, `result`, `limitations`, `responsibility`. Cada artefacto usa `path` relativo al repositorio y `sha256` hexadecimal de 64 caracteres. El ledger no se referencia a sí mismo, porque su hash cambiaría al anexar una entrada.

Append-only es una convención auditable, no un WORM criptográfico: Git conserva las revisiones y el checker detecta corrupción de referencias en el estado actual, pero un actor con escritura podría reescribir historial. Para evidencia final se debe firmar/taggear el commit o archivar el release con checksum.

## Verificación y correcciones

Un `automated-check` prueba sólo lo que declara su comando y commit. Si un agente escribió tanto implementación como prueba, se identifica esa falta de independencia. La revisión manual se registra como `author-decision`, nunca transformando un PASS automático en aprobación humana. Las correcciones preservan el resultado anterior mediante una entrada `fail` y otra `changed`/`pass` enlazada a nuevos artefactos.

## Privacidad, seguridad y redistribución

El ledger admite rutas, hashes, comandos sanitizados y resúmenes. Excluye texto completo de conversaciones, valores de secretos, datos personales y salidas que puedan contenerlos. `check-evidence.ps1` busca patrones de credenciales y tokens, pero no demuestra ausencia absoluta de información sensible. Antes de publicar, el autor debe revisar manualmente el diff y las condiciones de redistribución de cada input.

## Limitaciones y amenazas a validez

- Los hashes prueban identidad de bytes, no veracidad ni calidad.
- Un agente no es un evaluador independiente de su propia propuesta.
- Proveedores, modelos y tooling pueden cambiar; una reconstrucción exacta de lenguaje natural no está garantizada.
- El ledger de Phase 1 es una selección de eventos materiales, no telemetría exhaustiva.
- La suficiencia del formato para el TFG depende de las normas académicas y de la aprobación final del autor/tutor.
