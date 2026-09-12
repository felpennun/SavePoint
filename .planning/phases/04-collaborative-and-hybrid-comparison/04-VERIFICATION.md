---
phase: 04-collaborative-and-hybrid-comparison
status: completed_with_limitations
completed: 2026-09-12
nyquist_compliant: true
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

## Cierre final y limitación metodológica

La ejecución final del protocolo v15 terminó con **16/16 algoritmos** y
**79/80 usuarios evaluables**. El único usuario omitido no tenía historial y,
por tanto, no tenía un positivo retenible para el protocolo de test.

La evidencia canónica está en `docs/verification/evaluation-results-400-test-2026-09-12-v15.md`
y `docs/verification/evaluation-checkpoint-400-users-2026-09-12-v15.md`. El
artefacto conserva resultados por usuario, métricas de ranking, cobertura,
diversidad, novedad, contrastes pareados y tiempos para `cf-user-knn-v1` y
`hybrid-weighted-cf-v1`, junto con las variantes anteriores.

La ejecución usó el runner paralelo con `max_workers=2` y `serial_tail=5`;
el tiempo de pared registrado fue 4.297,9 s (aprox. 1 h 12 min).

La fase queda aceptada con una limitación metodológica explícita: el resultado
v15 es una única ejecución consumida del split `test`, con una semilla de
evaluación. El bootstrap y los contrastes pareados describen incertidumbre
interna de ese run, pero no sustituyen una sensibilidad entre semillas. No se
relanzará el split consumido; una extensión multi-semilla requerirá un protocolo,
población, split y artefacto nuevos. Esta limitación no invalida la comparación
interna congelada, pero impide presentar sus conclusiones como estabilidad
general frente a otras semillas.

Los criterios REC-04, REC-05 y DOC-03 quedan formalizados en
`docs/verification/phase-04-signoff-2026-09-12.md`.
