# Validación de usuarios sintéticos

Este informe describe una población generada de forma paramétrica. Sus resultados son evidencia de simulación y no deben interpretarse como evidencia sobre usuarios reales (EVAL-10).

- Semilla: `20260911`
- Versión de corpus: `2026.09.2`
- Usuarios generados: **400**
- Sin historial (0 juegos): **10**
- Cohorte cold-start (1–4 juegos): **0**
- Historial normal (5–10 juegos): **46**
- Historial intensivo (>10 juegos): **344**

## Resumen por arquetipo

| Arquetipo | Usuarios | Biblioteca media | Mín. | Máx. | Distribución de ratings | Estados |
|---|---:|---:|---:|---:|---|---|
| sin-historial-monogenero | 5 | 0.00 | 0 | 0 |  |  |
| sin-historial-omnivoro | 5 | 0.00 | 0 | 0 |  |  |
| cold-start-monogenero | 33 | 15.79 | 10 | 20 | sin rating: 43, 2: 55, 3: 54, 4: 51, 5: 53, 6: 58, 7: 81, 8: 30, 9: 40, 10: 56 | abandoned: 27, completed: 281, pending: 126, playing: 87 |
| cold-start-explorador | 33 | 14.42 | 10 | 19 | sin rating: 50, 4: 45, 5: 44, 6: 41, 7: 78, 8: 86, 9: 95, 10: 37 | abandoned: 35, completed: 179, pending: 122, playing: 140 |
| cold-start-generoso | 34 | 13.65 | 10 | 20 | sin rating: 42, 6: 45, 7: 108, 8: 98, 9: 86, 10: 85 | abandoned: 13, completed: 218, pending: 97, playing: 136 |
| normal-monogenero | 80 | 15.20 | 10 | 20 | sin rating: 117, 2: 102, 3: 109, 4: 141, 5: 129, 6: 105, 7: 223, 8: 103, 9: 93, 10: 94 | abandoned: 81, completed: 660, pending: 199, playing: 276 |
| normal-omnivoro | 80 | 14.82 | 10 | 20 | sin rating: 116, 4: 107, 5: 105, 6: 103, 7: 214, 8: 220, 9: 213, 10: 108 | abandoned: 69, completed: 565, pending: 235, playing: 317 |
| normal-explorador | 80 | 15.25 | 10 | 20 | sin rating: 141, 6: 161, 7: 222, 8: 249, 9: 233, 10: 214 | abandoned: 70, completed: 434, pending: 303, playing: 413 |
| intensivo-veterano | 50 | 14.44 | 10 | 20 | sin rating: 69, 6: 78, 7: 144, 8: 139, 9: 135, 10: 157 | abandoned: 46, completed: 377, pending: 105, playing: 194 |

## Interpretación

La misma semilla, versión de corpus y especificación de arquetipos deben producir los mismos identificadores de obra, estados y valoraciones. Las cohortes sin historial y cold-start se mantienen separadas para evaluar el enrutamiento con historial insuficiente. La generación no incorpora datos personales ni pretende estimar la distribución de jugadores reales.
