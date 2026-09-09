---
quick_id: 260909-udz
status: complete
---

# Resumen: variantes MMR compartidas

## Resultado

Se implementaron exactamente dos algoritmos nuevos:

- `content-cbf-mmr-v1`, basado en `content-cbf-weighted-v1`.
- `content-cbf-mmr-pop-v1`, basado en `content-cbf-weighted-pop-v1`.

Las nueve variantes existentes permanecen registradas y operativas. MMR se
aplica únicamente como capa de reordenación, con `lambda = 0,80`, sobre un pool
acotado y usando similitud coseno de los vectores fs-v9.

## Integración

- Ranker compartido para arranque en frío y perfiles con historial.
- Dos workers Docker dedicados, ejecutables en paralelo.
- Dos estanterías localizadas en español e inglés.
- Rejilla y protocolo offline actualizados de 28 a 30 configuraciones.
- Tests unitarios de diversidad y validación del contrato.
- Evidencia en `docs/verification/recommendation-mmr-felipe-2026-09-09.md`.

## Verificación

- 134 tests de recomendaciones y evaluación: pasan.
- TypeScript estricto: pasa.
- Configuración Compose: válida.
- Snapshot de Felipe: 12 de 12 trabajos `succeeded`; las dos variantes MMR
  publican 20 resultados cada una.

