---
quick_id: 260909-udz
status: complete
---

# Plan: variantes MMR compartidas

## Objetivo

Añadir dos algoritmos de reordenación diversificada MMR: una variante sobre la
relevancia existente y otra que conserve la relevancia PopScore de la variante
Weighted-Pop. Ambas deben ejecutarse con el mismo código en web y offline,
tener worker y estantería propios, y mantener intactas las nueve variantes
publicadas actuales.

## Decisiones

- MMR se aplica después de puntuar el pool de candidatas y antes de limitar a
  los 20 resultados publicados.
- El primer elemento es el de mayor relevancia base; cada elemento posterior
  maximiza `lambda * relevancia - (1 - lambda) * max_similarity_selected`.
- `lambda = 0,80` para mantener la relevancia dominante y reducir duplicados.
- La variante normal usa la relevancia `content-cbf-weighted-v1`; la variante
  PopScore usa `content-cbf-weighted-pop-v1`.
- La similitud de diversidad reutiliza la similitud de facetas fs-v9, no una
  nueva fuente de metadatos ni una penalización permanente de la puntuación.

## Tareas

1. Añadir la selección MMR compartida al ranker y registrar las dos variantes.
2. Añadir los dos workers, sus jobs y las dos estanterías localizadas.
3. Añadir ambas configuraciones a la rejilla offline y al contrato/fingerprint.
4. Cubrir invariantes, documentar la decisión y verificar web/offline.

## Verificación

- Tests backend de ranker, selección MMR, contrato y workers.
- Tests frontend y TypeScript.
- Configuración Docker válida con dos workers nuevos.
- Snapshot de Felipe recalculado con 12 secciones y publicación atómica.
