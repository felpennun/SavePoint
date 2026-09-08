---
tags: [concepto, tema/recomendadores]
---

# Explicabilidad

Cada recomendacion presenta una explicacion **determinista** basada en evidencia
real del modelo (REC-08): `matched_genres` en el heuristico, y una tabla de
contribucion determinista mas el termino de rating persistido en el recomendador
de contenido (`apps/api/recommendations/content/explain.py`). Se descartan
explicitamente las explicaciones generativas por no ser fieles ni auditables.

## Enlaces

- [[Heuristico de gusto por generos]] · [[Recomendador basado en contenido]]
- [[Control contra alucinaciones]] · [[Versionado de resultados]]
