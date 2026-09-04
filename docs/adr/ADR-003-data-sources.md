# ADR-003: Snapshot Wikidata y licencias de Commons por asset

- **Estado:** Aceptada y corpus congelado
- **Fecha:** 2026-09-04
- **Autor de la decisión:** Felipe (`corpus aprobado`)
- **Redacción/evidencia:** agentes de investigación/ejecución; verificación automática y decisión humana separadas.

## Contexto

El catálogo debe ser citable, legalmente defendible, estable y utilizable sin red. Los datos estructurados y los archivos multimedia no comparten necesariamente licencia. [FUENTES: [Wikidata licensing](https://www.wikidata.org/wiki/Wikidata:Licensing); [Commons reuse](https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia/en)]

## Alternativas consideradas

1. Snapshot curado de Wikidata + revisión individual de Commons + placeholder propio.
2. RAWG/IGDB en runtime: más metadata, pero credenciales, cuotas, términos y deriva.
3. Scraping/fair use de carátulas: descartado por procedencia y reutilización no defendibles.
4. Sin imágenes: legalmente simple, pero reduce la calidad de la demo.

## Decisión

Congelar 150 juegos de datos estructurados Wikidata declarados CC0. Conservar consulta, URL, corte UTC y SHA-256. Tratar cada archivo Commons por separado: sólo `candidate` con autor, licencia, URL de licencia y fuente completas; en otro caso, placeholder propio. No consultar proveedores en runtime.

## Evidencia y fuentes

- `data/raw/wikidata-games.json`, SHA-256 `a2b5d8d1f4388b21a03a5c3c983840e38db2c5e176613913985a5e38f7408159`.
- `data/manifests/catalogue.json` y `data/manifests/assets.json` enlazan el snapshot.
- `docs/verification/catalogue-freeze.md`: 150 juegos, 19 assets revisados, 17 admitidos y 2 placeholders; aprobación humana explícita.
- `scripts/acquire_catalogue.py --validate-only` y pruebas del importador verifican estructura/checksums.

## Consecuencias

- Positivas: evaluación repetible, procedencia visible, cero dependencia runtime.
- Negativas: snapshot envejece; cobertura y licencias requieren trabajo editorial; metadata puede ser incompleta.
- Límite legal: la aprobación documenta diligencia y decisión del autor, no constituye asesoramiento jurídico ni garantiza derechos fuera de los términos citados.

## Reversibilidad

Cada cambio crea una nueva versión con nuevo hash y nueva revisión humana. QID se conserva como identificador externo; UUID interno evita acoplar identidad del producto a la fuente.

## Aprobación y revisión

**Aprobada.** Cualquier cambio de query, snapshot o asset invalida el freeze y exige repetir adquisición, checks y decisión humana.
