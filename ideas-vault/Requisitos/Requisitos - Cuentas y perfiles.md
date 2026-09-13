---
tags: [requisitos, tema/producto]
---

# Requisitos - Cuentas y perfiles

- **AUTH-01** (Fase 1, hecho): iniciar y cerrar sesion en cuenta controlada.
- **AUTH-02** (Fase 2, hecho): cargar usuarios sinteticos claramente marcados.
- **PROF-01** (Fase 5): editar alias, avatar y biografia.
- **PROF-02** (Fase 1, hecho): ver un perfil publico.
- **PROF-03** (Fase 6): el perfil publico solo muestra elementos permitidos.
- **PROF-04** (Fase 6): URL compartible de perfil y listas publicas.

## Reconciliacion de Fase 6 — 2026-09-13

La matriz canonica [[../../.planning/phases/06-public-discovery-and-resilient-enrichment/06-REQUIREMENTS-RECONCILIATION]]
confirma el alcance controlado de `SOCIAL-03`, `SOCIAL-04` y `SOCIAL-05`.
La amistad requiere solicitud y aceptacion; el contenido compartido solo se
proyecta a amistades aceptadas o al propietario. El perfil basico es la
excepcion para una persona no amiga y contiene unicamente alias, avatar,
biografia y la accion contextual de solicitud, conforme a D-07.

`SOCIAL-03` cubre busqueda por alias exacto, solicitudes, amistad, rechazo,
eliminacion, bloqueo y desbloqueo. `SOCIAL-04` cubre las proyecciones
allowlist de perfil, coleccion, listas y comentarios mediante URLs protegidas;
una URL directa no evita la autorizacion y un acceso no permitido usa un 404
generico. `SOCIAL-05` cubre recomendaciones privadas con juego y texto
opcional, la bandeja de mensajes, lectura/no lectura y el punto pendiente,
con un limite direccional de una recomendacion por pareja durante siete dias.

El significado de `public` queda limitado a la relacion autorizada: no implica
visibilidad anonima. La proyeccion de coleccion/lista conserva juego, portada,
ano, plataforma, estado y valoracion personal; los comentarios conservan
alias del autor, texto y fecha. No se exponen copias, compras, precios,
tiendas, ubicaciones ni notas privadas. `SOCIAL-01` y `SOCIAL-02` mantienen su
significado v2 original y no se sustituyen.

## Enlaces

- [[Perfil publico]] · [[Cuentas simuladas]] · [[Allowlist de campos publicos]]
- [[Frontera de sesion same-origin]]
