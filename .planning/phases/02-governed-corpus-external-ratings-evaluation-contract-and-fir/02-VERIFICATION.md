---
phase: 02-governed-corpus-external-ratings-evaluation-contract-and-fir
status: human_needed
verified_at: 2026-09-08
verifier: Codex
---

# Verificación de la Fase 2

## Resultado automático

| Gate | Comando o evidencia | Resultado |
|---|---|---|
| Tests de evaluación | `docker compose -f infra/compose.yaml run --rm --no-deps api pytest apps/api/evaluation -q` | PASS — 69 passed |
| Evidencia metodológica | `powershell -ExecutionPolicy Bypass -File scripts/check-evidence.ps1` | PASS — ADRs y ledger válidos |
| Protocolo congelado | `docs/methodology/protocol.json` | PASS — versión 2, corpus y snapshot resueltos |
| Artefacto de primera comparación | `docs/verification/evaluation-run-first.artifact.json` | PASS — cinco algoritmos, K=5/10/20, hashes y seeds |
| Informe reproducible | `docs/verification/evaluation-run-first.md` | PASS — métricas, interpretación y limitaciones |

## Cobertura de criterios de la fase

1. Corpus gobernado, diccionario, checksum y reporte de calidad: cubierto por los freezes de
   corpus de los planes 02-01 y 02-02.
2. Ratings con procedencia, fecha y snapshot inmutable: cubierto por 02-02 y el freeze de
   `CorpusRatingSnapshot`; las reglas de conflicto quedan en ADR-008.
3. Búsqueda tolerante, filtros multi-selección y presentación de catálogo: cubierto por los
   planes de catálogo y su evidencia de pruebas.
4. Protocolo, relevancia, candidatos compartidos, exclusiones, split y semillas: cubierto por
   02-08 y el runner de 02-13.
5. Baselines, recomendador de contenido, exclusión de biblioteca, explicaciones y cold start:
   cubierto por 02-09, 02-10 y 02-11; la primera comparación queda en el artefacto final.
6. Documentación, amenazas a la validez y controles AGENT-04: cubierto por
   `evaluation-protocol.md`, `agent-methodology-controls.md`, ADR-008 y este informe.

## Revisión humana pendiente

El artefacto muestra `nDCG@10 = 0.000` para los cinco algoritmos. El resultado se ha
conservado como hallazgo de simulación, sin repetir el test ni ajustar el protocolo después
de observarlo. Antes de marcar la fase como aceptada, el autor debe confirmar que acepta esta
interpretación y las limitaciones: población sintética, un único positivo por usuario,
catálogo elegible amplio y ausencia de evidencia sobre usuarios reales.

<human-check>
Estado: pendiente de firma del autor.
</human-check>
