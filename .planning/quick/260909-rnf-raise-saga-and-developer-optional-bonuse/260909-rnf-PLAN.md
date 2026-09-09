---
quick_id: 260909-rnf
status: complete
---

# Plan: recalibrar bonus opcionales y precision del nucleo

## Objetivo

Aplicar el mismo contrato de similitud a web, workers y evaluacion offline:
bonus maximo de saga/franquicia `0,20`, bonus maximo de desarrollador `0,15`,
y afinidad `F0,5` para que la precision del candidato pese mas cuando una obra
declara muchos generos o plataformas. Recalcular las recomendaciones de Felipe
y archivar una comparativa reproducible.

## Tareas

1. Actualizar la version del contrato, pesos y formula compartida de
   `recommendations.content.similarity`, junto con sus pruebas y el fingerprint
   de configuracion.
2. Actualizar el protocolo, la documentacion de decisiones y el vault vivo para
   reflejar la formula y los nuevos bonus.
3. Reconstruir la evidencia necesaria, reejecutar los diez workers de Felipe,
   comprobar que publican la nueva revision y generar el desglose comparativo.

## Verificacion

- Suite backend de recomendaciones y evaluacion.
- `tsc --noEmit` del frontend.
- Fingerprint y version de similitud nuevos en los snapshots publicados.
- Los diez algoritmos de Felipe terminan correctamente y sus resultados
  reflejan `facet-similarity-v4`.
