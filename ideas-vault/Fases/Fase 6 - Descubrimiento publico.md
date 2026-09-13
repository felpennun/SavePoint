---
tags: [fase/6, roadmap, tema/producto, tema/datos]
---

# Fase 6 - Descubrimiento publico

Meta: los visitantes pueden descubrir vistas ricas del catalogo y perfiles,
conectar mediante amistades aceptadas y compartir dentro de esa relacion las
listas, colecciones y comentarios permitidos, sin contaminar los datos de
investigacion. Incluye proyecciones publicas protegidas, filtrado por todos los
metadatos amplios del catalogo, URLs con comprobacion de amistad y mensajes de
recomendacion entre amigos.

## Decisiones vigentes — 2026-09-13

- La amistad requiere solicitud y aceptacion; rechazar, eliminar y bloquear
  son estados distintos. El bloqueo cancela solicitudes, revoca el acceso,
  oculta mutuamente el contenido e impide nuevas solicitudes.
- La coleccion, las listas y los comentarios marcados como publicos solo son
  visibles para amistades aceptadas. Las URLs directas no saltan la
  autorizacion y devuelven `404` generico a quien no tenga permiso.
- Las amistades ven en la coleccion y listas el juego, portada, ano,
  plataforma, estado y valoracion personal, respetando el orden manual de cada
  lista. Los comentarios se ven dentro de la pagina del juego con alias, texto
  y fecha.
- Las recomendaciones privadas contienen un juego y un mensaje opcional,
  aparecen en una pagina de “Mensajes de amigos” enlazada desde el desplegable
  del perfil y activan un punto rojo cuando estan pendientes. El limite es una
  recomendacion por pareja cada siete dias.
- El backend conserva filtros para todas las dimensiones de `CAT-05`; la
  seleccion visual de filtros queda pendiente de una decision posterior del
  autor.

Fuente canónica: [[../../.planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT]]

## Contrato visual — 2026-09-13

Propuesta de interfaz para la fase: se conserva el sistema CSS first-party
Nocturne, con catálogo GET compartible, filtros completos preparados en backend
sin congelar todavía la selección visual de facetas, perfil mínimo para no
amigos y proyección allowlisted para amistades aceptadas. El módulo de
amistades distingue rechazar, eliminar y bloquear; la bandeja privada se llama
“Mensajes de amigos” y el icono de perfil muestra un punto rojo accesible cuando
hay pendientes.

Fuente canónica: [[../../.planning/phases/06-public-discovery-and-resilient-enrichment/06-UI-SPEC]]

## Implicaciones de planificación — 2026-09-13

La investigación técnica recomienda un módulo Django `social` separado, con
políticas de visibilidad centralizadas, proyecciones allowlist independientes
para perfil básico y amistades, y transiciones de relaciones dentro de
`transaction.atomic()`. La ventana de recomendaciones debe comprobarse por
pareja emisor-receptor y tiempo móvil, con pruebas de concurrencia y de frontera.

El catálogo debe ampliar `search.py` y sus facets a todas las dimensiones de
`CAT-05`; `Publisher` y el mapping de `Edition` necesitan una decisión de fuente
y procedencia antes de modificar el importer. La investigación completa,
incluidos los desajustes que deben reconciliarse en roadmap y requirements,
está en [[../../.planning/phases/06-public-discovery-and-resilient-enrichment/06-RESEARCH]].

## Enlaces

- [[Allowlist de campos publicos]] · [[Perfil publico]] · [[Catalogo]]
- [[Snapshot inmutable]] (aislamiento respecto a investigacion)
- [[Requisitos - Cuentas y perfiles]] · [[Requisitos - Catalogo]]
