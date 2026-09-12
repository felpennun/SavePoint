# Fase 5: Complete Collection Workflows and Portability - Contexto

**Recopilado:** 2026-09-12
**Estado:** Listo para planificación

<domain>
## Límite de la fase

La Fase 5 completa la curación personal de la colección: edición de biografía y
avatar, comentarios por juego, listas personalizadas ordenables, metadatos
avanzados de copias, privacidad básica de las proyecciones y exportación CSV de
los datos que el usuario puede ver en la aplicación. El alias sigue siendo el
usuario de autenticación y no se edita.

La fase no incorpora una red social ni amistades. Por tanto, la privacidad
efectiva en esta fase se limita a `público` o `privado`; `solo amigos` queda
preparado como decisión futura, no como permiso simulado sin relación de
amistad real.

</domain>

<decisions>
## Decisiones de implementación

### Perfil y privacidad

- **D-01:** El alias público coincide con el nombre de usuario de login y no es
  editable. Añadir biografía y avatar como datos editables del perfil.
- **D-02:** La colección y la estantería de cinco juegos favoritos tienen una
  opción de privacidad `pública` o `privada`. La estantería de favoritos es
  editable y está limitada a cinco juegos.
- **D-03:** La opción `solo amigos` se difiere junto con el sistema de
  amistades; no se implementa una visibilidad que el backend no pueda resolver
  de forma verificable.

### Comentarios por juego

- **D-04:** Cada usuario puede mantener un único comentario por juego. El
  comentario se crea, edita y elimina desde una sección de comentarios del
  juego.
- **D-05:** El autor siempre puede consultar y gestionar su propio comentario.
  La visibilidad de comentarios de terceros queda restringida por privacidad;
  la variante para amigos se habilitará únicamente cuando exista el modelo de
  amistades correspondiente.

### Listas personalizadas

- **D-06:** Las listas son colecciones manuales de juegos que el usuario ha
  añadido a su colección. El usuario puede crearlas, editarlas, eliminarlas y
  ordenar manualmente sus juegos.
- **D-07:** Cada lista tiene privacidad `pública` o `privada`. No se añade una
  privacidad de amigos en esta fase.

### Portabilidad

- **D-08:** La portabilidad de esta fase se limita a exportación CSV. El
  contenido exportado corresponde a los datos visibles en la aplicación y no
  expone campos privados no presentes en esa proyección.
- **D-09:** JSON e importación con vista previa, errores por fila y conflictos
  deterministas quedan fuera de la implementación actual. La planificación
  debe señalar que PORT-02 y PORT-03 siguen pendientes y proponer la
  reconciliación explícita de esos requisitos con el roadmap, sin ocultar la
  reducción de alcance.

### Decisiones que quedan a criterio del agente

- La representación técnica del avatar, siempre que respete validación,
  límites de tamaño, atribución y ausencia de secretos.
- La taxonomía concreta de estados de conservación y la representación de
  precio/moneda, siempre que los campos sean auditables, opcionales cuando
  proceda y no se filtren en proyecciones privadas.
- Si una lista puede contener un juego varias veces; se recomienda impedir
  duplicados y mantener un orden explícito estable.
- La forma visual exacta de la sección de comentarios, respetando los patrones
  accesibles existentes y sin cambiar el contrato público de recomendaciones.

</decisions>

<canonical_refs>
## Referencias canónicas

**Los agentes posteriores deben leer estas referencias antes de planificar o
implementar.**

### Alcance y requisitos

- `.planning/ROADMAP.md` — objetivo, criterios de éxito y requisitos asignados
  a la Fase 5.
- `.planning/REQUIREMENTS.md` — PROF-01, LIB-03, LIB-04, INV-03, INV-04,
  PORT-01, PORT-02, PORT-03, PORT-04 y PRIV-01.
- `.planning/PROJECT.md` — límites de v1, privacidad, inventario y
  reproducibilidad.
- `CONVENTIONS.md` — idioma, trazabilidad, secretos y mantenimiento del vault.
- `ideas-vault/README.md` — política del vault vivo y enlaces a fuentes
  canónicas.

### Decisiones previas

- `.planning/phases/01-three-day-public-demo-slice/01-CONTEXT.md` — frontera
  del demo, perfiles públicos, copias físicas/digitales y campos avanzados
  diferidos.
- `.planning/phases/01.1-real-scale-catalogue-and-product-experience/01.1-CONTEXT.md`
  — decisiones de producto y límites que dejaron comentarios, listas e
  importación/exportación para una fase posterior.
- `.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-CONTEXT.md`
  — modelo de obras, releases, ediciones y entradas de biblioteca que la fase
  debe reutilizar.

### Implementación existente

- `.planning/codebase/ARCHITECTURE.md` — separación Next.js/Django/PostgreSQL,
  proyecciones y restricciones relacionales.
- `.planning/codebase/STACK.md` — versiones y herramientas aprobadas.
- `.planning/codebase/CONVENTIONS.md` — patrones de nombres, validación y
  protección de datos.
- `apps/api/accounts/models.py` — identidad demo y relación con el usuario de
  Django.
- `apps/api/accounts/serializers.py` — proyección pública construida mediante
  allowlist explícita.
- `apps/api/accounts/views.py` — endpoints de cuenta, perfil público y sesión.
- `apps/api/library/models.py` — `LibraryEntry`, `OwnedCopy`, estados, rating e
  idempotencia de copias.
- `apps/api/library/serializers.py` — DTOs existentes de rating y copias.
- `apps/api/library/services.py` — transacciones, ownership y configuración
  completa de una obra.
- `apps/api/library/views.py` — endpoints owner-scoped de colección, copias y
  configuración.
- `apps/api/library/urls.py` — contrato de rutas de biblioteca existente.
- `apps/web/app/[locale]/collection/page.tsx` — superficie de colección y
  punto de integración de listas/exportación.
- `apps/web/app/[locale]/profiles/[alias]/page.tsx` — perfil público.
- `apps/web/app/[locale]/games/[id]/page.tsx` — detalle de juego y futura
  sección de comentarios.

</canonical_refs>

<code_context>
## Perspectivas del código existente

### Activos reutilizables

- `LibraryEntry` ya impone una relación única usuario-obra y separa estado/rating
  de las copias.
- `OwnedCopy` ya admite múltiples copias, release, edición, formato e
  idempotency key; las nuevas propiedades deben extender esta entidad sin mover
  estado ni rating desde la obra.
- `build_public_profile` construye una allowlist manual; debe seguir siendo el
  patrón para no filtrar notas privadas, precios, ubicación o detalles de copia.
- `save_library_configuration` y las vistas owner-scoped proporcionan la base
  transaccional para editar colección y copias.
- Las páginas Next.js existentes y los componentes de colección/detalle ofrecen
  los puntos de integración visual, pero la implementación UI se coordinará con
  la otra sesión y no se modifica durante esta discusión.

### Patrones establecidos

- PostgreSQL y Django ORM son obligatorios; no se introduce SQLite ni otro
  almacén para listas, comentarios o exportaciones.
- Validación backend autoritativa, restricciones relacionales, ownership por
  `request.user` y respuestas allowlisted son requisitos de seguridad.
- Las operaciones de escritura de biblioteca son idempotentes o transaccionales
  cuando pueden producir duplicados o estados parciales.
- Las exportaciones deben ser derivadas de proyecciones explícitas y
  neutralizar fórmulas de hoja de cálculo.

### Puntos de integración

- Nuevos endpoints de perfil, comentarios, listas y exportación se conectarán a
  las rutas Django existentes sin alterar el contrato público de recomendaciones.
- El modelo de datos debe relacionar comentarios y elementos de lista con el
  usuario y la obra, con constraints de ownership/uniqueness.
- La visibilidad pública debe reutilizar una política allowlist y distinguir
  claramente datos públicos de datos owner-scoped.

</code_context>

<specifics>
## Detalles concretos

- El usuario quiere una estantería exactamente de cinco juegos favoritos,
  editable y sometida a privacidad.
- En la ficha de un juego debe existir una sección de comentarios.
- Las listas personalizadas son listas de juegos de la colección, no listas
  algorítmicas ni búsquedas guardadas.
- El CSV debe contener los datos visibles en la página; no se ha autorizado
  añadir JSON ni importación en esta fase.

</specifics>

<deferred>
## Ideas diferidas

- Sistema de amistades y privacidad `solo amigos` para colecciones, favoritos,
  listas y comentarios; pertenece a una ampliación social posterior.
- Exportación JSON e importación con previsualización, validación por fila y
  resolución determinista de conflictos; PORT-02 y PORT-03 requieren una
  decisión de roadmap antes de implementarse.

</deferred>

---

*Fase: 5 - Complete Collection Workflows and Portability*
*Contexto recopilado: 2026-09-12*
