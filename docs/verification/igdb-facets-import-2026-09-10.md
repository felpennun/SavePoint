# Verificación de la importación de facetas IGDB — 2026-09-10

## Alcance

Se verificó directamente la base de datos local después de la importación
aditiva de `themes`, `game_modes`, `player_perspectives` y `keywords`. Esta
comprobación valida la existencia, las asociaciones y la integridad estructural
de los datos. No realiza todavía análisis semántico ni depuración.

Las facetas siguen fuera del corpus gobernado, de la huella de contenido y de
los recomendadores. Por tanto, su presencia en la base de datos no cambia los
resultados reproducibles ya congelados.

## Resultado de la comprobación

Catálogo total consultado: **331.000 obras**.

| Faceta | Valores distintos | Obras con al menos un valor | Resultado esperado | Estado |
|---|---:|---:|---:|---|
| `themes` | 22 | 179.744 | 22 / 179.744 | PASS |
| `player_perspectives` | 7 | 128.185 | 7 / 128.185 | PASS |
| `game_modes` | 6 | 234.761 | 6 / 234.761 | PASS |
| `keywords` | 6.546 | 131.829 | 6.546 / 131.829 | PASS |

Además:

- no se detectaron nombres nulos o vacíos en ninguna tabla de facetas;
- no se detectaron IDs `igdb_id` duplicados en ninguna tabla;
- el número de asociaciones M2M distintas coincide con el número de obras con
  al menos un valor en las cuatro facetas;
- los resultados coinciden con `apps/api/igdb-facets-import-evidence.json`.

La comprobación confirma que la otra importación ha alojado correctamente los
datos en el esquema actual. No implica que todos los valores sean todavía
adecuados para análisis: especialmente `keywords` es un conjunto abierto y
puede contener sinónimos, ruido, etiquetas de baja frecuencia o valores que
requieran interpretación.

## Trabajo aplazado

Por decisión del autor, el análisis y la depuración se harán en una etapa
posterior, sin bloquear la interfaz que continuará desarrollándose. Ese trabajo
deberá quedar versionado y reproducible e incluir, como mínimo:

1. medir cobertura, valores ausentes, frecuencia y cola larga por faceta, tanto
   sobre el catálogo completo como sobre el corpus gobernado;
2. revisar nombres, codificación, sinónimos y valores anómalos, manteniendo el
   valor bruto importado y separando cualquier tabla de normalización;
3. definir, con una decisión explícita, qué facetas pasan a la siguiente
   versión de los vectores de contenido y cuáles permanecen solo como metadatos;
4. si alguna faceta entra en los algoritmos, actualizar de forma coordinada el
   corpus, las huellas, la caché, el protocolo offline, los workers web y sus
   pruebas de paridad;
5. generar un nuevo informe de calidad y una evidencia de comparación antes de
   usar las facetas en una evaluación.

Hasta entonces, la política es **importar y conservar, pero no gobernar ni
consumir algorítmicamente** estas facetas.

## Fuente y reproducibilidad

- Fuente de conteos comparados: `apps/api/igdb-facets-import-evidence.json`.
- Verificación: consulta Django contra el PostgreSQL de `infra/compose.yaml`,
  contando filas de las cuatro tablas y obras relacionadas.
- Fecha: 2026-09-10.
