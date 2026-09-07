# Validación de usuarios sintéticos

Este informe describe una población generada de forma paramétrica. Sus resultados son
evidencia de simulación y no deben interpretarse como evidencia sobre usuarios reales
(EVAL-10).

- Semilla: `20260907`
- Versión de corpus: `2026.09.1`
- Usuarios generados: **200**
- Cohorte cold-start (1–3 juegos): **25**

## Resumen por arquetipo

| Arquetipo | Usuarios | Biblioteca media | Mín. | Máx. | Distribución de ratings | Estados |
|---|---:|---:|---:|---:|---|---|
| monogenero-severo | 25 | 10.56 | 5 | 15 | sin rating: 35, 2: 35, 3: 49, 4: 33, 5: 34, 6: 39, 7: 39 | abandoned: 23, completed: 151, pending: 68, playing: 22 |
| monogenero-generoso | 25 | 10.08 | 5 | 15 | sin rating: 42, 6: 56, 7: 33, 8: 37, 9: 45, 10: 39 | abandoned: 28, completed: 122, pending: 73, playing: 29 |
| omnivoro-medio | 25 | 30.08 | 20 | 39 | sin rating: 106, 4: 114, 5: 121, 6: 98, 7: 102, 8: 122, 9: 89 | abandoned: 70, completed: 339, pending: 246, playing: 97 |
| completista-saga | 25 | 27.84 | 20 | 39 | sin rating: 95, 4: 99, 5: 103, 6: 90, 7: 105, 8: 105, 9: 99 | abandoned: 53, completed: 475, pending: 105, playing: 63 |
| explorador-novedades | 25 | 28.84 | 21 | 40 | sin rating: 98, 4: 88, 5: 104, 6: 104, 7: 98, 8: 121, 9: 108 | abandoned: 76, completed: 175, pending: 290, playing: 180 |
| coleccionista-pendientes | 25 | 59.12 | 50 | 70 | sin rating: 225, 4: 227, 5: 208, 6: 177, 7: 202, 8: 209, 9: 230 | abandoned: 66, completed: 236, pending: 1034, playing: 142 |
| jugador-ocasional-cold-start | 25 | 2.12 | 1 | 3 | sin rating: 7, 4: 8, 5: 4, 6: 6, 7: 10, 8: 12, 9: 6 | abandoned: 5, completed: 20, pending: 21, playing: 7 |
| veterano-biblioteca-grande | 25 | 60.84 | 51 | 69 | sin rating: 232, 6: 264, 7: 248, 8: 257, 9: 263, 10: 257 | abandoned: 156, completed: 825, pending: 311, playing: 229 |

## Interpretación

La misma semilla, versión de corpus y especificación de arquetipos deben producir los
mismos identificadores de obra, estados y valoraciones. La cohorte cold-start se mantiene
separada para evaluar el enrutamiento con historial insuficiente. La generación no incorpora
datos personales ni pretende estimar la distribución de jugadores reales.

La ejecución de referencia se hizo con:

```text
docker compose -f infra/compose.yaml run --rm api python manage.py generate_synthetic_users --seed 20260907 --dry-run --validation-report /workspace/apps/api/synthetic-report.md
```

El comando valida primero la población y solo después permite persistirla. La salida de
persistencia contiene únicamente conteos y anclas UUID; no incluye contraseñas ni datos
personales. Las cuentas se identifican mediante `seed_key` y anclas derivadas con
`uuid.uuid5`. Su exclusión del baseline `rank_popularity_v1` evita que la simulación altere
la superficie pública de la aplicación.
