---
tags: [informe, memoria, social, perfil, capturas]
estado: vigente
fecha: 2026-10-04
---

# Informe: qué hemos tocado y qué falta en la memoria

Alcance: todo lo hecho en la sesión de diseño/producto (zips de `design/`) comparado con el contenido actual de
`thesis/sections/*.tex`. **No se ha modificado nada de `thesis/`.** Fuentes canónicas del código:
`apps/api/`, `apps/web/`, `e2e/`; detalle funcional en las notas [[Pagina de amistades]],
[[Pagina de perfil y ajustes]], [[Pagina de inicio]] y [[Vista detallada de recomendaciones]].

Estado del repositorio: ~185 entradas en `git status`, nada confirmado en commit. Migraciones nuevas sin aplicar en
ningún entorno remoto: `accounts/0005`, `accounts/0006`, `social/0003`, `library/0007`.

## 1. Qué cubre hoy la memoria (y por tanto qué es nuevo)

La memoria describe un módulo social mínimo y estático (fases 5-6, cierre del 14/09/2026):

- Requisitos SOCIAL-03 (buscar alias exacto, solicitudes, amistades, bloqueos) y SOCIAL-04 (ver colección, listas y
  comentarios de un amigo), casos de uso CU-11, CU-12 y CU-13, reglas RN-3 y RN-8.
- Modelo de dominio: `User`, `FriendshipRequest`, `Friendship`, `Block` (sección 4, figura `modelo-dominio`).
- API: una sola fila de cuentas/social en la tabla de endpoints (`GET /api/accounts/profiles/<alias>/`).
- Frontend: la lista de rutas menciona "amistades" y "perfil de un amigo" en una frase (sección 6.4); no hay capturas
  del módulo social ni del perfil propio.
- Capturas incluidas hoy como figuras: home claro/oscuro (`fig:ui-claro`, `fig:ui-oscuro`), catálogo (`fig:catalogo`),
  colección (`fig:coleccion`) y recomendaciones (`fig:recomendaciones-ui`). Existen en `thesis/figures/` otras seis
  capturas que no se citan en ningún `.tex` (detalle, fuentes, menú de cuenta, registro, móvil catálogo, móvil
  recomendaciones).

No aparecen en ningún `.tex`: perfil editable, foto/portada, nombre completo, cambio de nombre de usuario, cambio de
contraseña, eliminación de cuenta, exportación Excel, notificaciones, respuesta a recomendaciones, comentarios
múltiples, visibilidad por defecto de listas, estantería de DLC, estadísticas del catálogo.

## 2. Cambios de la sesión

### 2.1 Módulo social (amistades) — nuevo, falta en la memoria

| Cambio | Dónde |
|---|---|
| Página `/friends` en tres columnas: búsqueda y amistades, perfil de la persona elegida, notificaciones | `apps/web/components/FriendsApp.tsx`, `app/[locale]/friends/page.tsx` |
| Búsqueda por nombre de usuario exacto, solicitud, **cancelación** de la solicitud enviada y aceptación | `social/services.py` (`cancel_friendship_request`) |
| Recomendar un juego de la colección con buscador y aviso si la amistad ya lo tiene; se mantiene 1 recomendación/semana por amistad (429) | `GamePicker.tsx`, `social/services.py` |
| **Notificaciones** (modelo `SocialNotice`: solicitud aceptada, recomendación añadida a pendientes) más las pendientes (solicitud o recomendación recibidas); marcar todo como leído; punto rojo en la pestaña Amistades | `social/models.py`, `GET /api/social/notifications/`, `POST …/notifications/read-all/`, `FriendsNavDot.tsx` |
| **Responder a una recomendación** una sola vez: añadir a pendientes (crea la entrada si no existía y avisa a quien la envió) o descartar | `SocialMessage.response/responded_at`, `POST /api/social/messages/<id>/respond/` |
| **Perfil detallado de una amistad** de solo lectura (portada, foto, nombre, pestañas Perfil / Colección / Listas / Comentarios, filtros y medalla de platino); lo privado se anuncia "no disponible"; Eliminar amistad y Bloquear con confirmación | `FriendProfile.tsx`, `social/profiles.py`, `GET /api/social/friends/<alias>/profile/`, `…/friends/<alias>/` (tarjeta) |
| `/messages` redirige a `/friends` (no hay mensajería libre) | `app/[locale]/messages/page.tsx` |
| Se retiran `SocialHub`, `SocialInbox`, `SocialActions`, `ProfileSettings` y `DemoAccountBanner` | `apps/web/components/` |
| Cuentas demo fuera del producto (selector de cuenta pasa a menú de cuenta con foto) | `AccountSwitcher.tsx`, `AppShell.tsx` |

Tests nuevos: `tests/test_social_friends_page.py`, `apps/web/tests/friends-app.test.ts`, `e2e/friends-page.spec.ts`
(más ajustes en `test_social_visibility.py`, `social-*.test.ts`).

### 2.2 Personalización y perfil — nuevo, falta en la memoria

| Cambio | Dónde |
|---|---|
| Página `/profile` con pestañas **Cuenta, Privacidad, Preferencias, Conexiones, Seguridad** (se llega desde "Editar perfil") | `ProfileEditor.tsx`, `app/[locale]/profile/` |
| Campos nuevos de `AccountProfile`: `display_name` (40), `avatar_preset` (5 avatares), `avatar_image`/`cover_image` (binario, máx. 512 KiB, ya recortadas en el navegador), `username_changed_at`, `default_list_visibility` | `accounts/models.py`, migraciones 0005 y 0006 |
| Foto y portada: subida con recorte en navegador (`ProfileImageCropper`), URL https o avatar predefinido; validación por firma de imagen (magic numbers) | `accounts/services.py` (`detect_image_type`, `set_profile_image`), `GET/PUT/DELETE /api/accounts/me/avatar/` y `me/cover/`; vistas para amistades `profiles/<alias>/avatar/` y `cover/` |
| Cinco favoritos con buscador de juegos | `ProfileFavoritePicker.tsx` |
| **Nombre de usuario editable una sola vez** (3-30 caracteres, comprobación de disponibilidad sin distinguir mayúsculas, prefijo `anonymous-` reservado) | `POST /api/accounts/me/username/`, `GET …/username/availability/` |
| Privacidad: interruptores de Favoritos y Colección y visibilidad por defecto de las listas nuevas. **Dos niveles: Privada y Amistades** (el nivel "Pública" del diseño no existe: las cuentas no son públicas) | `default_list_visibility` + restricción CHECK |
| Seguridad: **cambio de contraseña**, **eliminación definitiva de la cuenta** con contraseña (la señal de recomendaciones ignora el borrado en cascada), exportación **CSV y Excel** | `POST …/me/password/`, `POST …/me/delete/`, `GET /api/library/export/collection.xlsx` (`library/export_xlsx.py`) |
| Conexiones: importación CSV (solo filas `collection` y `copy`); el botón de exportar sale de la colección y vive solo en el perfil | `ProfileEditor.tsx` |
| Preferencias: tema e idioma | `ProfileEditor.tsx` |
| Pruebas: `accounts/tests/test_profile_page.py`, `library/tests/test_export_xlsx.py`, `social-profile.test.ts` ampliado | |

### 2.3 Otros cambios de producto (fuera de social/perfil)

- **Comentarios**: ya no hay un único comentario por usuario y obra (se elimina la restricción
  `library_unique_comment_per_user_work`, migración `library/0007`), paginación de 10, borrado con confirmación
  y exportación con desempate por UUID. **Contradice** la formulación "un comentario por usuario/obra" de la
  evidencia de Fase 5 (`D-04`).
- **DLC y ediciones**: estantería de contenido relacionado en la ficha del juego para cualquier persona; la medalla de
  platino en colección y en la colección de una amistad.
- **Página de inicio** rediseñada (opción 3c): misma estructura con y sin sesión, juego de ejemplo aleatorio (novedades
  con nota y PopScore sin sesión; juegos de la colección con sesión), cifras reales del catálogo
  (`GET /api/catalogue/stats/`, caché 1 h). Siempre se redirige a Inicio tras iniciar sesión.
- **Rendimiento del catálogo**: facetas ligeras en caché (`LITE_FACETS_CACHE_KEY`, 6 h), año mínimo 1950, etiquetas de
  género en español (`catalogue/genre_labels_es.py`, `lib/genre-labels.ts`).
- **Filtros desplegables** (catálogo, colección, colección de una amistad): se cierran al abrir otro, al pulsar fuera
  o con Escape (`FilterDropdownScript` pasa a efecto de cliente).
- **Recomendaciones**: carril "ALGORITMO" + vista detallada (barra de pesos, descripción, tabla con posición, juego,
  motivos y afinidad), selector en ambas vistas, sin scroll de página. Nombres de producto: "Para ti", "Sorpréndeme",
  "Lo último para ti".
- **Sorpréndeme (MMR-pop) usa ahora `content-cbf-mmr-pop-v2`**: pesos efectivos 0.35 parecido / 0.20 nota /
  0.25 popularidad / 0.20 variedad (λ 0.80; base `content-cbf-weighted-pop-v2` 0.4375/0.25/0.3125). Variante solo de
  producto en `PRODUCT_VARIANT_REGISTRY`; el laboratorio y `content-cbf-mmr-pop-v1` no cambian.
- Capturas actualizadas: `e2e/artifacts/review-2026-10-04/` (sustituyen a `review-2026-09-06`).

## 3. Qué debería entrar en la memoria

Ordenado por prioridad. Las referencias de sección son las actuales de `thesis/sections/`.

### 3.1 Obligatorio (la memoria queda desactualizada o contradictoria sin esto)

1. **Sección 4 (análisis)**
   - Requisitos: ampliar SOCIAL-03/04 (cancelar solicitud, perfil detallado) y añadir uno para SOCIAL-05
     (recomendaciones privadas con respuesta y cooldown de 7 días; ya está completo en `.planning/REQUIREMENTS.md`,
     pero la memoria no lo lista). Añadir requisitos de perfil (editar nombre, foto, portada, favoritos, nombre de
     usuario una vez) y de privacidad (PRIV-03 está como *v2 diferido* en el repo y ahora está cubierto en parte:
     interruptores de favoritos y colección, visibilidad por defecto de listas).
   - Casos de uso: añadir "Editar perfil y privacidad", "Responder a una recomendación", "Exportar la colección (CSV y
     Excel)" y "Eliminar la cuenta".
   - Regla de negocio nueva: el nombre de usuario solo se cambia una vez; la visibilidad solo tiene dos niveles.
   - Revisar RN-8 ("sin sesión no se ve ninguna cuenta") frente a la implementación: quien no es amistad solo ve el
     nombre de usuario, no el contenido.
   - Corregir cualquier mención a un comentario único por obra.
2. **Sección 4/5 (modelo de datos)**: `SocialNotice`, campos de respuesta en `SocialMessage` y campos de perfil en
   `AccountProfile`. Hay que regenerar `modelo-dominio` (el script `thesis/figures/generate_diagrams.py` ya está
   modificado en el árbol de trabajo, sin verificar contra esta lista).
3. **Sección 5 (API)**: la tabla de endpoints solo lista 1 ruta social/cuentas. Añadir: `me/avatar|cover|password|
   username|delete`, `profiles/<alias>/avatar|cover`, `social/notifications/`, `social/friends/<alias>/(profile/)`,
   `social/messages/<id>/respond/`, `library/export/collection.xlsx`, `catalogue/stats/`.
4. **Sección 5 (privacidad/seguridad)**: la proyección de perfil sigue por lista explícita de campos; añadir la
   validación de imágenes por firma, el límite de 512 KiB, la regla de que las imágenes solo se sirven por vistas
   acotadas al titular o a una amistad aceptada, y el borrado de cuenta con contraseña con auditoría sin actor.
5. **Sección 6 (frontend y pruebas)**: actualizar la frase de rutas (añadir `/profile` y la página de amistades como
   tres columnas) y las cifras de verificación (`736 / 70 / 56` son del cierre del 14/09; las suites actuales han
   cambiado: Vitest 66 pasados, pytest `recommendations`+`evaluation` 273 pasados; hay que repetir la regresión
   completa antes de citar números).
6. **Aviso de coherencia con el cambio de pesos de MMR-pop** (decisión tuya: no reflejarlo). Hoy la memoria dice en
   5.x/6.x/7.x que la web publica `content-cbf-mmr-pop-v1`, y la aplicación publica `…-v2`. Opciones: (a) dejarlo
   así y asumir que el tribunal puede ver 0.35/0.20/0.25/0.20 en pantalla frente a 0.44/0.20/0.16/0.20 en el texto;
   (b) una nota breve de que la web usa una reconfiguración de producto de la variante, sin tocar el laboratorio ni
   las tablas v15. Es la única discrepancia entre memoria y aplicación que ya es visible en la UI.

### 3.2 Recomendable

- Subsección nueva "Módulo social y personalización" (en 6.x, tras Frontend) con: flujo de amistad, notificaciones,
  recomendación con respuesta, perfil propio por pestañas, perfil de amistad de solo lectura, decisiones de diseño
  (sin feed, sin mensajería libre, dos niveles de visibilidad, nombre de usuario una vez). Mantener el tono
  impersonal del resto de la memoria.
- Una mención en 6.x al rediseño de Inicio y a la vista detallada de recomendaciones, con las capturas de abajo.
- Decisión de producto "las cuentas demo salen del producto" (el diagrama de despliegue ya se rehízo sin pasos de demo).
- Exportación a Excel junto a la exportación CSV (PORT-01 solo menciona CSV).

### 3.3 Opcional

- Estadísticas del catálogo y caché de facetas (rendimiento).
- Etiquetas de género en español.
- Filtros desplegables accesibles.

## 4. Capturas nuevas

Generadas en `e2e/artifacts/review-2026-10-04/{sin-sesion,con-sesion}/` (1440×900, oscuro y claro; móvil 390×844).

### 4.1 Imprescindibles (módulo social y personalización)

| Captura | Archivo | Figura propuesta | Sección |
|---|---|---|---|
| Amistades (tres columnas) | `con-sesion/09-amistades-oscuro.png` | `fig:amistades` | módulo social |
| Perfil de una amistad, pestaña Colección con filtros | **falta**: hay que capturarla con una amistad con colección visible (el script actual solo hace `/profiles/felipe`) | `fig:perfil-amistad` | módulo social |
| Perfil propio (pestaña Cuenta) | `con-sesion/10-perfil-oscuro.png` | `fig:perfil-propio` | personalización |
| Perfil, pestaña Privacidad y pestaña Seguridad | **falta**: el script solo captura la pestaña por defecto | `fig:perfil-privacidad` | personalización |
| Notificaciones con una recomendación pendiente | **falta**: requiere una recomendación recibida | `fig:notificaciones` | módulo social |
| Menú de cuenta | `con-sesion/13-menu-cuenta-oscuro.png` | `fig:menu-cuenta` | personalización |

### 4.2 Sustituir las figuras que ya están (se han quedado antiguas)

| Figura actual | Sustituir por |
|---|---|
| `fig:ui-claro` / `fig:ui-oscuro` (home) | `sin-sesion/01-inicio-claro.png` y `…-oscuro.png` (Inicio nuevo) |
| `fig:catalogo` (catálogo recortado) | `sin-sesion/03-catalogo-filtros-oscuro.png` (recortar a la barra + primera fila) |
| `fig:coleccion` | `con-sesion/05-coleccion-oscuro.png` (nueva barra de filtros, medalla de platino) |
| `fig:recomendaciones-ui` | `con-sesion/07-recomendaciones-detallada-oscuro.png`; añadir `08-recomendaciones-sorprendeme-*` si se decide mostrar los pesos |
| Resto de `captura-*.png` no citadas | regenerar o eliminar; no se referencian |

### 4.3 Cómo añadirlas

1. **Privacidad antes de copiar.** Las capturas con sesión de felipe muestran su foto, nombre completo, biografía y
   favoritos reales. Para la memoria es mejor repetirlas con una cuenta de prueba (nombre ficticio, foto de avatar
   predefinido) o difuminar esos campos. No usar datos de terceras personas (amistades reales).
2. **Capturar con el mismo script** (`scratchpad/caps.cjs`: Playwright + sesión inyectada) añadiendo las pestañas del
   perfil, la colección de una amistad y un estado de notificaciones con datos sembrados. Resolución 1440×900 y
   recorte a la zona de interés cuando la página tenga mucho vacío (como `captura-catalogo-recorte.png`).
3. **Nombres y destino**: copiar a `thesis/figures/` con prefijo `captura-` (`captura-amistades.png`,
   `captura-perfil.png`, `captura-perfil-privacidad.png`, `captura-notificaciones.png`,
   `captura-perfil-amistad.png`) y sustituir las existentes manteniendo el nombre para no tocar los `\includegraphics`.
4. **Entorno LaTeX** (el patrón que ya usa la memoria): `\begin{figure}[htp]`, `\includegraphics[width=0.85\textwidth]`,
   pie con "Fuente: captura del proyecto." y `\label{fig:…}`; en el texto, citar con `Figura~\ref{…}` y aclarar, como
   en `fig:recomendaciones-ui`, que son capturas de interfaz y no evidencia de resultados.
5. **Tema**: usar una sola variante por figura (oscuro como principal; claro solo en el par de la portada, que ya
   sigue el patrón de `fig:ui-claro/oscuro`).
6. **Móvil**: una captura (`movil-05-recomendaciones.png` o `movil-06-amistades.png`) basta para sostener la
   afirmación de diseño adaptable.
7. **Verificación**: compilar con `latexmk`, comprobar que ninguna figura invade márgenes y actualizar la lista de
   figuras (`TFG.lof`) generada.

## 5. Antes de empezar a escribir

- Repetir la regresión completa (pytest, Vitest y Playwright) y anotar los números reales; los de la memoria están
  desactualizados.
- Decidir la opción (a) o (b) del punto 3.1.6.
- Confirmar si `PRIV-03` pasa de "v2 diferido" a "completo (parcial)" en `.planning/REQUIREMENTS.md` y en la tabla de
  requisitos, para que la memoria y el repositorio digan lo mismo.
- Nada de lo anterior está confirmado en commit ni cerrado en issues de GitHub; si se va a mapear a planes GSD, cada
  plan necesita su issue (convención del proyecto).
