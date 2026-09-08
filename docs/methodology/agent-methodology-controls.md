# Controles metodológicos frente al uso de IA (AGENT-04)

Este documento fija los controles aplicados durante el desarrollo y la evaluación de SavePoint. Su objetivo es separar las decisiones propuestas por herramientas de IA de las decisiones verificadas en el repositorio y de las decisiones finalmente adoptadas por el autor del TFG.

## 1. Control contra alucinaciones

Las propuestas generadas por una IA no se consideran evidencia por sí mismas. Cada afirmación técnica debe enlazarse con al menos uno de estos elementos: código ejecutable, prueba automatizada, dato de un snapshot inmutable o fuente primaria citada.

- El corpus evaluado se identifica mediante `corpus_version` y `snapshot_sha256`.
- El runner rechaza una ejecución si falta un `CorpusRatingSnapshot` para una obra gobernada con rating o si existe deriva de versión.
- Los resultados se generan desde `apps/api/evaluation/runner.py` y se conservan en un artefacto JSON, no desde una explicación redactada manualmente.
- Las explicaciones de `apps/api/recommendations/content/explain.py` se derivan de una tabla de contribución determinista y del término de rating persistido. Ni el recomendador ni `apps/api/evaluation/synthetic.py` usan un LLM para generar recomendaciones, usuarios o evidencia.
- Las afirmaciones sobre IGDB y RAWG se contrastan con `docs/adr/ADR-008-external-ratings.md` y `docs/verification/igdb-catalogue-freeze.md`.

La revisión humana sigue siendo necesaria para interpretar los resultados y decidir qué conclusiones son defendibles en el TFG.

## 2. Control contra sesgo

La comparación usa los mismos usuarios sintéticos, la misma partición leave-one-out, el mismo conjunto de candidatos por usuario y las mismas exclusiones para todos los algoritmos. De esta forma, una diferencia de métricas no se atribuye a una población o a un conjunto de candidatos diferente.

- `apps/api/evaluation/candidates.py` es el único constructor del conjunto de candidatos.
- `apps/api/evaluation/runner.py` comprueba que cada algoritmo recibe y devuelve el mismo universo permitido.
- La generación de usuarios está fijada por semilla y marcada con `synthetic-eval-user`.
- Los ocho arquetipos de `apps/api/evaluation/archetypes.py` equilibran deliberadamente los ejes de géneros preferidos, tamaño de biblioteca y generosidad al puntuar; el resultado observado se audita en `docs/verification/synthetic-users-validation.md` (Plan 02-09).
- Para obras sin rating observado, `apps/api/recommendations/content/combine.py` usa la mediana marcada de los géneros como fallback y propaga `rating_term_is_fallback`; nunca introduce silenciosamente un valor imputado como si procediera de IGDB o RAWG.
- La documentación distingue evidencia de simulación de evidencia sobre usuarios reales; la primera no se generaliza automáticamente a una población externa.

El corpus está gobernado y versionado, pero puede reflejar los sesgos de cobertura y popularidad de sus fuentes. Por ello, el TFG debe presentar el alcance de la muestra y no afirmar representatividad general.

## 3. Control contra errores

Los errores de implementación se controlan con pruebas unitarias, de integración y de contrato. Las métricas se calculan mediante funciones independientes (`precision_at_k`, `recall_at_k`, `ndcg_at_k` y `map_at_k`) y se registran para `K` igual a 5, 10 y 20.

- Las variantes del recomendador están registradas en `apps/api/recommendations/content/variants.py`.
- El protocolo congelado se almacena en `docs/methodology/protocol.json`.
- Las semillas de leave-one-out, partición de usuarios y generación sintética quedan congeladas en el protocolo y en el informe del Plan 02-09.
- `CorpusRatingSnapshot` conserva observaciones inmutables por `corpus_version`; el checksum del snapshot y el del corpus gobernado permiten detectar deriva de datos.
- El comando `run_evaluation` valida los argumentos, el corpus activo, el snapshot y el marcador de ejecución consumido.
- Los tests de `apps/api/evaluation/tests/test_runner.py` cubren el conjunto compartido, la deriva del snapshot, la cobertura y la forma del artefacto.
- El build de Next.js y las suites de backend se ejecutan antes de cerrar el plan.

Si una ejecución no puede producir un artefacto completo, se documenta como pendiente o fallida; nunca se sustituyen sus métricas por valores estimados.

## 4. Control contra exposición de información

Los artefactos de evaluación no publican información personal innecesaria. El resultado conserva identificadores técnicos necesarios para reproducibilidad, pero la documentación narrativa presenta agregados y no una tabla de actividad individual de los usuarios sintéticos.

- Las recomendaciones de usuario requieren autenticación y siempre se calculan sobre `request.user`.
- `ContentRecsView` y `OwnedGamesDlcView` usan exclusivamente `request.user`; no aceptan un usuario objetivo. Sus serializers y proyecciones de respuesta aplican allowlists explícitas para impedir ensanchamientos accidentales del contrato (Planes 02-05 y 02-11).
- `apps/api/catalogue/ratings.py` y `apps/api/library/popularity.py` restringen el cálculo vivo al conjunto de cuentas autorizado; las cuentas `synthetic-eval-user` no alteran el baseline público. Los conteos se agregan y no se exponen filas de usuarios concretos.
- Los clientes y comandos de importación aplican `redact()` antes de emitir errores o trazas, y las credenciales solo se referencian por nombre de variable de entorno.
- Las claves, cookies, tokens y logs con secretos quedan fuera de commits, issues y artefactos citados.
- Las carátulas y datos externos se muestran con su procedencia y licencia cuando corresponde.

## 5. Separación entre propuesta, verificación y decisión

- **Propuesta del agente:** diseños, hipótesis y cambios candidatos quedan vinculados a un `PLAN.md`; no constituyen evidencia ni decisión por sí solos.
- **Verificación automática:** tests, checksums, validadores de protocolo y gates documentales prueban propiedades concretas y dejan comandos reproducibles. Un fallo impide cerrar el plan o queda registrado como limitación.
- **Decisión del autor:** los checkpoints y ADR registran qué alternativa ratificó Felipe. La interpretación académica del artefacto, incluida la ordenación entre algoritmos, permanece bajo revisión del autor y no se decide automáticamente por una métrica aislada.

## Evidencia y revisión

La evidencia de cada ejecución se relaciona con el plan que la produce y con el commit de código que la genera. Antes de incorporar los resultados al TFG, el autor debe revisar el artefacto JSON, el protocolo, las limitaciones de simulación y la interpretación de las diferencias entre algoritmos.

Referencias principales: `02-08-SUMMARY.md`, `02-09-SUMMARY.md`, `02-11-SUMMARY.md`, `02-13-PLAN.md`, `docs/methodology/protocol.json`, `docs/verification/synthetic-users-validation.md` y `docs/adr/ADR-008-external-ratings.md`.
