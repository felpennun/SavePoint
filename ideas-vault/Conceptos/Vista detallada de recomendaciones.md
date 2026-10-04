---
tags: [producto, recomendaciones, ui]
estado: vigente
fecha: 2026-10-04
---

# Vista detallada de recomendaciones

La pagina de recomendaciones conserva su vista principal (una estanteria con scroll por algoritmo) y
tiene arriba a la derecha un boton de cuadricula que cambia a la vista del artboard 1c
(`SavePoint Ideas.dc.html`): un carril "ALGORITMO" a la izquierda para elegir uno de los tres algoritmos
publicados y, a la derecha, solo el algoritmo elegido con su titulo, la barra de pesos, la descripcion y una
tabla con posicion, juego, "por que" (las etiquetas que mas suman) y afinidad. La vista y el algoritmo se
recuerdan en el navegador.

- Pesos mostrados (reales, de `recommendations/content/variants.py`): weighted 0.70 contenido y 0.30 calidad;
  recency 0.40 novedad y 0.20 contenido, calidad y popularidad; mmr-pop (variante de producto `content-cbf-mmr-pop-v2`, 2026-10-04) 0.35 parecido, 0.20 nota, 0.25 popularidad y 0.20 variedad (0.80 x la mezcla weighted-pop-v2 0.4375/0.25/0.3125, mas 0.20 de penalizacion por parecido entre juegos). Es una variante nueva solo de producto (`PRODUCT_VARIANT_REGISTRY`): `content-cbf-mmr-pop-v1`, el laboratorio offline y la memoria no cambian.
- Del carril del diseno no se incluye el boton "Comparar dos".
- Los chips "menos" del diseno (`- SOULSLIKE`) no existen: los algoritmos publicados no restan etiquetas.

Relacionado: [[Pagina de inicio]].
