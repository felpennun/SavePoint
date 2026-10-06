# Método de trabajo asistido por agentes y controles metodológicos

## Propósito y alcance

SavePoint se ha desarrollado con asistencia de agentes de IA para investigar, diseñar, planificar, implementar y documentar. Este documento describe, de forma general y válida para todo el proyecto, cómo se organizó ese trabajo y qué controles separan lo que propone una herramienta de lo que se verifica y de lo que decide el autor. No afirma que un agente sea autor académico, revisor independiente ni responsable de una decisión humana: el autor del TFG conserva la responsabilidad sobre la selección, la verificación, la modificación y la presentación de todo el contenido.

Hay tres supuestos metodológicos que debe confirmar el autor conforme a la política de su titulación; hasta entonces son supuestos marcados, no conclusiones académicas:

- **[AGENT-01]** rol, actor, objetivo y responsabilidad por evento son atribución suficiente;
- **[AGENT-02]** referencias a artefactos y sus huellas SHA-256 permiten reproducibilidad sin publicar conversaciones completas;
- **[AGENT-03]** distinguir `proposal`, `automated-check` y `author-decision` separa bien contribución, verificación y autoría.

## Roles y responsabilidades

| Actor o rol | Qué hace | Responsabilidad y límite |
|---|---|---|
| Autor humano (Felipe) | Define el alcance y acepta o rechaza las decisiones | Responsable de la decisión académica; revisa fuentes, licencias, resultados y texto final. |
| Agente investigador | Recopila y sintetiza evidencia | Propone; etiqueta cada afirmación como fuente, evidencia o supuesto. No concede derechos ni aprueba tecnología. |
| Agente de interfaz | Convierte requisitos en contrato y en pantallas | Propone y ejecuta; la accesibilidad automática no sustituye la revisión humana de reflow y lector de pantalla. |
| Agente planificador | Divide el alcance en planes verificables | Propone la secuencia y los criterios de cierre; no declara completado el producto. |
| Agente ejecutor | Implementa, prueba y corrige | Produce comprobaciones automáticas; no se presenta como verificación independiente. |
| Herramientas deterministas | Pruebas, linters, sumas de verificación, validadores | Producen observaciones repetibles para un commit; no emiten juicio académico. |

## Propuesta, verificación y decisión

Todo lo que ocurre en el proyecto cae en una de tres categorías, y no se confunden:

- **Propuesta del agente:** diseños, hipótesis y cambios candidatos, vinculados a un plan. No constituyen evidencia ni decisión por sí solos.
- **Verificación automática:** pruebas, sumas de verificación, validadores de contrato y comprobaciones documentales. Prueban solo lo que declara su comando sobre un commit concreto. Un fallo impide cerrar el plan o queda registrado como limitación.
- **Decisión del autor:** los puntos de control y las decisiones de arquitectura (ADR) recogen qué alternativa ratificó el autor. Un resultado automático que pasa nunca se convierte en aprobación humana, y la interpretación académica de los resultados no se decide por una métrica aislada.

Si un mismo agente escribió la implementación y su prueba, se señala esa falta de independencia.

## Controles metodológicos

**Contra las alucinaciones.** Una propuesta generada por IA no es evidencia por sí misma. Cada afirmación técnica se enlaza al menos con código ejecutable, una prueba automatizada, un dato de un snapshot inmutable o una fuente primaria citada.

- El corpus evaluado se identifica por `corpus_version` y `snapshot_sha256`; el ejecutor rechaza una ejecución si falta una valoración congelada de una obra gobernada o si hay deriva de versión.
- Los resultados salen de `apps/api/evaluation/runner.py` y se guardan en un artefacto JSON, no de una explicación redactada a mano.
- Las explicaciones de las recomendaciones (`apps/api/recommendations/content/explain.py`) se derivan de una tabla de contribución determinista. Ni los recomendadores ni el generador de usuarios sintéticos usan un modelo de lenguaje para producir recomendaciones, usuarios o evidencia.
- Las afirmaciones sobre las fuentes de datos externas se contrastan con las decisiones de arquitectura correspondientes (ADR-006 y ADR-008).

**Contra el sesgo.** La comparación usa los mismos usuarios sintéticos, la misma partición, el mismo conjunto de candidatas por usuario y las mismas exclusiones para todos los algoritmos, de modo que una diferencia de métricas no se atribuye a poblaciones distintas.

- `apps/api/evaluation/candidates.py` es el único constructor del conjunto de candidatas y el ejecutor comprueba que cada algoritmo recibe y devuelve el mismo universo permitido.
- La generación de usuarios está fijada por semilla y marcada como sintética; los arquetipos equilibran los ejes de géneros preferidos, tamaño de biblioteca y generosidad al puntuar.
- Una valoración ausente nunca se imputa en silencio como si viniera de una fuente externa: el fallback por género se marca y se propaga.
- Se distingue siempre la evidencia de simulación de la evidencia sobre usuarios reales. El corpus puede arrastrar los sesgos de cobertura y de popularidad de sus fuentes, y la memoria presenta el alcance de la muestra sin afirmar representatividad general.

**Contra los errores.** Las pruebas unitarias, de integración y de contrato cubren el código. Las métricas se calculan con funciones independientes y probadas, el protocolo está congelado en `docs/methodology/protocol.json` y el comando `run_evaluation` valida argumentos, corpus activo, snapshot y marcador de ejecución consumida. Si una ejecución no puede producir un artefacto completo, se documenta como pendiente o fallida; nunca se sustituyen sus métricas por valores estimados.

**Contra la exposición de información.** Los artefactos no publican datos personales innecesarios: conservan identificadores técnicos para reproducir y la documentación presenta agregados, no la actividad individual de los usuarios sintéticos.

- Las recomendaciones de un usuario exigen autenticación y se calculan siempre sobre `request.user`; las respuestas aplican listas explícitas de campos permitidos.
- Los clientes y comandos de importación redactan los errores antes de emitirlos y las credenciales solo se referencian por el nombre de su variable de entorno.
- Claves, cookies, tokens y registros con secretos quedan fuera de commits, issues y artefactos citados. Las portadas y datos externos se muestran con su procedencia y su licencia.

## Herramientas, modelos y reproducibilidad

El trabajo se hizo con Codex (familia `gpt-5`) y con Claude Code (familia Claude) según la tarea, siguiendo el método *Get Stuff Done* (<https://github.com/gsd-build/get-shit-done>). La versión exacta de un modelo no siempre la expone el entorno; cuando falta se anota `unknown` y nunca se infiere. Un nombre de modelo no basta para reproducir una salida probabilística: lo reproducible son los artefactos versionados, las sumas de verificación, los comandos y las decisiones humanas.

## Registro de evidencia

Durante el desarrollo el autor mantuvo un registro de evidencia con los eventos materiales: un objeto por evento con fecha UTC, tipo (`proposal`, `automated-check` o `author-decision`), actor, objetivo, entradas y salidas con su ruta y su SHA-256, herramientas, resultado (`pass`, `fail`, `changed`, `accepted` o `rejected`), limitaciones y responsabilidad. Los fallos y las alternativas rechazadas se registran igual que los éxitos, y una nueva observación se añade sin reescribir las anteriores. Excluye conversaciones completas, prompts, valores de secretos, datos personales y salidas que puedan contenerlos.

Ese registro y sus comprobaciones automáticas se conservan en el repositorio de desarrollo del autor y no se publican aquí. Su carácter *append-only* es una convención auditable, no una garantía criptográfica: Git conserva las revisiones, pero un actor con permiso de escritura podría reescribir el historial.

## Limitaciones y amenazas a la validez

- Una suma de verificación prueba la identidad de los bytes, no la veracidad ni la calidad.
- Un agente no es un evaluador independiente de su propia propuesta.
- Proveedores, modelos y herramientas cambian; no se garantiza reconstruir exactamente una salida en lenguaje natural.
- El registro recoge una selección de eventos materiales, no telemetría exhaustiva.
- Los patrones de búsqueda de credenciales reducen el riesgo de publicar información sensible, pero no demuestran su ausencia: antes de publicar, el autor revisa el diff y las condiciones de redistribución de cada entrada.
- La suficiencia de este formato para el TFG depende de las normas académicas y de la aprobación final del autor y del tutor.
