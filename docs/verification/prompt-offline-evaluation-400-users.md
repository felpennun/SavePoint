# Prompt operativo para iniciar la evaluación offline

Copia este prompt a la otra LLM:

```text
Trabajas en SavePoint. Tu tarea es ejecutar y documentar la evaluación offline
final de los algoritmos sobre la población sintética de Fase 3. No rediseñes el
sistema ni cambies fórmulas durante esta tarea.

Lee primero, en este orden:
1. AGENTS.md y CONVENTIONS.md.
2. docs/verification/evaluation-checkpoint-400-users-2026-09-10.md.
3. docs/methodology/protocol.json.
4. docs/methodology/evaluation-protocol.md.
5. docs/methodology/recommendation-algorithms.md.
6. apps/api/evaluation/runner.py,
   apps/api/evaluation/protocol.py,
   apps/api/evaluation/candidates.py,
   apps/api/evaluation/splits.py y
   apps/api/evaluation/management/commands/run_evaluation_parallel.py.

Objetivo exacto:
- corpus 2026.09.2;
- protocolo 12;
- población sintética activa de 400 cuentas;
- split fijo 240 train / 80 validation / 80 test;
- ejecutar únicamente test, una sola vez, sobre los 16 algoritmos declarados;
- producir un artefacto JSON completo y una evaluación estadística defendible
  para el TFG.

Gate obligatorio antes de calcular:
1. Comprueba que protocol.json sigue teniendo protocolo 12, corpus 2026.09.2,
   las mismas semillas y los mismos hashes.
2. Ejecuta:
   docker compose -f infra/compose.yaml exec -T api python manage.py audit_synthetic_population --corpus-version 2026.09.2
3. Ejecuta el preflight sin algoritmos:
   docker compose -f infra/compose.yaml exec -T api python manage.py validate_recommender_inputs --corpus-version 2026.09.2 --validation-date 2026-09-10 --evidence-json /workspace/apps/api/evaluation-input-preflight-2026-09-10.json
4. Ejecuta la suite específica:
   docker compose -f infra/compose.yaml exec -T api pytest /workspace/apps/api/evaluation -q
5. Comprueba que no existe apps/api/.evaluation-test-run.json.
6. Comprueba el estado Git. Si hay cambios sin commit en protocol.json,
   apps/api/evaluation/** o apps/api/recommendations/**, DETENTE: son cambios
   relevantes para la reproducibilidad. No los descartes, no los mezcles con
   cambios de apps/web y no ejecutes el test final hasta que el responsable
   haya congelado ese estado con un commit identificable. Los cambios de UI de
   la otra LLM no deben tocarse.
7. Si todos los gates pasan, registra el SHA de commit, fecha UTC, versión de
   Docker/Compose y que no se modificó el protocolo después del freeze.

No hagas estas cosas:
- no uses --force-new-protocol;
- no regeneres ni actualices los 400 usuarios;
- no ejecutes validation para seleccionar parámetros ahora;
- no cambies seeds, K, relevancia, exclusiones, candidatos ni pesos;
- no llames a IGDB/RAWG ni a ninguna API externa;
- no reencoles trabajos web, no reconstruyas la interfaz y no toques apps/web;
- no borres contenedores, volúmenes, imágenes ni artefactos existentes.

Ejecución final, solo después del gate:
docker compose -f infra/compose.yaml exec -T api python manage.py run_evaluation_parallel --corpus-version 2026.09.2 --split test --max-workers 4 --evidence-json /workspace/apps/api/evaluation-400-test-2026-09-10.artifact.json

Usa cuatro procesos como límite conservador para PostgreSQL. No aumentes la
concurrencia sin evidencia; si la base de datos muestra errores, conserva el
artefacto de fallo, detén la ejecución y reporta el error. No relances test
automáticamente: el protocolo consume el test una sola vez al terminar con
éxito.

Después de ejecutar:
1. Verifica que el JSON tiene status succeeded, 16 algoritmos, 79 usuarios
   evaluables en test y skipped_user_count = 1 por falta de positivo elegible.
2. Verifica que todos los algoritmos comparten protocol_sha256,
   snapshot_sha256, popscore_snapshot_sha256, feature_set_version, split y
   split_manifest_sha256.
3. Calcula y guarda el SHA-256 del JSON sin modificarlo después.
4. Conserva también el preflight y el resultado de los tests, sin secretos ni
   logs brutos.
5. Redacta una nota en español en docs/verification/ con el nombre
   evaluation-results-400-test-2026-09-10.md. Debe incluir tablas por algoritmo
   y K, nDCG@10 como headline, precision/recall/MAP, cobertura, diversidad,
   novedad, concentración, tiempos, cohortes, intervalos de confianza,
   Wilcoxon pareado, Friedman si es estimable, ajuste de Holm, omisiones y
   amenazas a la validez.
6. Interpreta el resultado como simulación sobre arquetipos, no como evidencia
   de usuarios reales. Explica que el contraste es pareado por usuario y que
   train solo alimenta CF/novedad, validation sirve para selección y test es
   una comparación final de un solo uso.
7. Cita la base científica ya recogida en recommendation-algorithms.md:
   evaluación de ranking de Järvelin y Kekäläinen, evaluación de
   recomendadores de Herlocker et al., diversidad/MMR de Carbonell y
   Goldstein, y diversidad/novedad de McNee et al. No inventes fuentes ni
   presentes los valores locales como constantes universales.

Si cualquier gate falla, no ejecutes el cálculo. Devuelve un informe breve con
el gate fallido, la evidencia observable y la acción necesaria. Si termina con
éxito, devuelve rutas de todos los artefactos, hashes, counts, algoritmo
ganador solo bajo este protocolo y las limitaciones; no declares que un método
es universalmente superior.
```

