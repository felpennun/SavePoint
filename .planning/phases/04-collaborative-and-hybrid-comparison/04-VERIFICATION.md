---
phase: 04-collaborative-and-hybrid-comparison
status: verified
---

# Verificación de la Fase 4

## Alcance verificado

- `cf-user-knn-v1` y `hybrid-weighted-cf-v1` están disponibles en web y
  offline, sin alterar las once variantes de contenido previas.
- Compose declara 14 workers: 13 personales y uno de género.
- El snapshot de Felipe publicó 14 trabajos correctamente y contiene 13
  estanterías personales; las nuevas estanterías tienen 20 resultados cada
  una.
- El comando offline paralelo y su contrato de tiempos están implementados.

## Evidencia ejecutada

- `docker compose -f infra/compose.yaml run --rm api pytest apps/api -q` —
  `482 passed`.
- `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web exec tsc --noEmit` — correcto.
- `docker compose -f infra/compose.yaml config --services` — incluye los dos
  workers nuevos.
- Verificación DB de Felipe — 14 trabajos `succeeded`; 13 secciones personales
  y género con 20 resultados.

## Pendiente deliberado

La ejecución final sobre los 400 usuarios y el análisis estadístico de sus
resultados queda para el siguiente paso de la fase. Esta implementación solo
prepara el ejecutor paralelo y sus controles de integridad.
