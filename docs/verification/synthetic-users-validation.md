# Validación de usuarios sintéticos

Este informe describe la población sintética titular de la Fase 3. Sus
resultados son evidencia de simulación y no deben interpretarse como evidencia
sobre usuarios reales (EVAL-10).

- Semilla: `20260909`
- Versión de corpus: `2026.09.2`
- Usuarios nuevos generados: **400**
- Usuarios activos para evaluación: **400**
- Usuarios heredados de Fase 2 conservados para auditoría: **200**
- Entradas de biblioteca activas: **2.868**
- Usuarios activos con `OwnedCopy`: **381**
- Copias activas: **1.026**

## Cohortes

| Cohorte | Usuarios | Regla |
|---|---:|---|
| Sin historial | 10 | 0 juegos |
| Historial escaso / cold-start | 100 | 1–4 juegos |
| Historial normal | 240 | 5–10 juegos |
| Historial intensivo | 50 | más de 10 juegos |

El `user_split` congelado para esta población es `train = 240`,
`validation = 80`, `test = 80`, con semilla `20260908`.

## Reglas de selección

- Las bibliotecas se han generado desde el corpus gobernado `2026.09.2`.
- La regla general de selección exige `rating_count >= 1`.
- La selección es escalonada y pondera cada obra por tramos crecientes de
  `rating_count` (1–4, 5–19, 20–99, 100–499, 500–1999, ≥2000), con pesos
  1/2/4/8/16/32. Así el número de bibliotecas que contienen una obra aumenta
  con su volumen de valoraciones sin concentrar todo el corpus en los éxitos.
- El snapshot vigente no contiene obras con `rating_count >= 1` y rating IGDB
  nulo; por ello no se fuerzan excepciones que contradigan el umbral solicitado.
- Las valoraciones de los usuarios sintéticos se generan con la semilla y el
  arquetipo; algunas entradas tienen copias físicas o digitales cuando existe
  un lanzamiento compatible.

La comprobación sobre la BD confirma el gradiente esperado de exposición media
por obra: 1,04 usuarios en `1–4` ratings; 1,10 en `5–19`; 1,23 en `20–99`;
1,32 en `100–499`; 1,70 en `500–1999`; y 2,11 en `>=2000`.

## Sustitución de la población anterior

Los 400 usuarios nuevos sustituyen a los 200 de Fase 2 como población activa
del marcador `synthetic-eval-user`. Las 200 cuentas y sus bibliotecas antiguas
no se han borrado: permanecen con el marcador histórico
`synthetic-eval-user-phase2` para conservar la trazabilidad de la comparación
v1.

La misma semilla, versión de corpus y especificación de arquetipos deben
producir los mismos identificadores de obra, estados y valoraciones. La
generación no incorpora datos personales ni pretende estimar la distribución de
jugadores reales.

La ejecución de referencia se hizo con:

```text
docker compose -f infra/compose.yaml run --rm api python manage.py generate_synthetic_users --seed 20260909 --corpus-version 2026.09.2 --dry-run
```

El comando valida primero la población y solo después permite persistirla. La población
titular se persistió con el mismo seed y corpus indicados arriba. La salida de persistencia
contiene únicamente conteos y anclas UUID; no incluye contraseñas ni datos
personales. Las cuentas se identifican mediante `seed_key` y anclas derivadas con
`uuid.uuid5`. Su exclusión del baseline `rank_popularity_v1` evita que la simulación altere
la superficie pública de la aplicación.
