# API v4 de IGDB — evidencia de sondeo autenticado

**Plan:** 01.1-01 Tarea 2 · **Requisito:** DATA-04 · **Issue de GitHub:** #7
**Sondeo ejecutado (ISO-8601 UTC):** 2026-09-05T14:56:27Z
**Operador:** agente de ejecución, contra la API real `https://api.igdb.com/v4` usando las credenciales de aplicación de Twitch proporcionadas por el autor.
**Manejo de credenciales:** `IGDB_CLIENT_ID` / `IGDB_CLIENT_SECRET` se leyeron solo del entorno del proceso. No se imprimió, registró, commiteó ni escribió en este fichero ningún valor de credencial, token OAuth ni cabecera `Authorization`. La presencia se confirmó únicamente por nombre de variable.

Este documento registra observaciones **redactadas, reproducibles y no secretas**. Es la entrada de fuente primaria para `docs/adr/ADR-006-igdb-source.md`.

---

## 1. Autenticación

| Propiedad | Observación |
|---|---|
| Flujo | Twitch OAuth2 `client_credentials` — `POST https://id.twitch.tv/oauth2/token` |
| Estado de la respuesta autenticada | **HTTP 200** — token de acceso obtenido |
| Tipo de token | `bearer` |
| Vida del token | `expires_in` = **4,959,769 s** (~57.4 días) |
| Auth de petición a IGDB | Cabeceras `Client-ID: <client id>` + `Authorization: Bearer <token>` en cada llamada a `https://api.igdb.com/v4/*` |

## 2. Tamaño del catálogo (conteos autenticados)

| Endpoint / consulta | Hora UTC | Estado | Conteo |
|---|---|---|---|
| `POST /v4/games/count` (sin filtro) | 2026-09-05T14:56:28Z | 200 | **Juegos totales: 374555** |
| `POST /v4/games/count` — `where game_type = 0;` | 2026-09-05T14:56:29Z | 200 | **Juegos primarios elegibles (game_type = 0): 312418** |
| `POST /v4/games/count` — `where category = 0;` | 2026-09-05T14:56:28Z | 200 | 0 — el campo legacy `category` está deprecado / ya no se rellena; la API en vivo usa `game_type` |
| `POST /v4/covers/count` | 2026-09-05T14:56:30Z | 200 | 336568 |
| `POST /v4/genres/count` | 2026-09-05T14:56:30Z | 200 | 23 |
| `POST /v4/platforms/count` | 2026-09-05T14:56:31Z | 200 | 220 |

### 2.1 Desglose completo de `game_type` (suma el total sin filtrar)

| game_type | etiqueta | conteo |
|---:|---|---:|
| 0 | main_game | 312418 |
| 1 | dlc_addon | 17615 |
| 2 | expansion | 1736 |
| 3 | bundle | 7134 |
| 4 | standalone_expansion | 504 |
| 5 | mod | 9779 |
| 6 | episode | 976 |
| 7 | season | 866 |
| 8 | remake | 1472 |
| 9 | remaster | 1381 |
| 10 | expanded_game | 2143 |
| 11 | port | 8227 |
| 12 | fork | 135 |
| 13 | pack | 8952 |
| 14 | update | 1217 |
| — | **suma** | **374555** (coincide con `/games/count` sin filtro) |

**Frontera de categoría elegible para el catálogo de SavePoint:** `game_type = 0` (juegos principales) — **312418** filas. game_type 1–14 son entradas no primarias (DLC, bundles, packs, ports, updates, mods, episodes, seasons, remakes/remasters, expansions, forks) y quedan excluidas del catálogo primario, coherente con el precedente existente `RelatedContent` / `is_dlc` en `apps/api/catalogue/models.py`.

## 3. Nombres de campo de Apicalypse (confirmados en vivo)

Consulta: `fields id,name,slug,genres.name,platforms.name,cover.image_id,cover.url,first_release_date,total_rating,url; where id = 1942;` → HTTP 200, 1 fila (`The Witcher 3: Wild Hunt`).

Todas estas rutas de campo actuales resolvieron sin error:

- `id`, `name`, `slug`, `first_release_date` (segundos unix), `total_rating` (float 0–100), `url`
- `genres.name` (expansión por punto) — devolvió `Role-playing (RPG)`, `Adventure`
- `platforms.name` (expansión por punto) — devolvió 6 plataformas
- `cover.image_id` — devolvió `coaarl`
- `cover.url` — devolvió `//images.igdb.com/igdb/image/upload/t_thumb/coaarl.jpg`

El supuesto A3 (RESEARCH.md) queda **confirmado**: `genres.name`, `platforms.name`, `cover.image_id`, `first_release_date`, `total_rating` son actuales.

## 4. Rate limiting y cuota (derivado del sondeo + fuente primaria)

**Conclusión de cuota: NO existe ninguna cuota mensual de peticiones en la API v4 actual con Twitch-OAuth.**

- Fuente primaria — `https://api-docs.igdb.com/` › *Rate Limits* (cita textual en inglés): "There is a rate limit of 4 requests per second. If you go over this limit you will receive a response with status code 429 Too Many Requests. You are able to have up to 8 open requests at any moment in time."
- No se declara ningún tope mensual en ningún sitio de la documentación primaria. La cifra histórica de "50,000 requests/month" se aplicaba al tier pre-Twitch (RapidAPI) deprecado y no aplica. El supuesto A1 (RESEARCH.md) queda **confirmado**.
- Cabeceras de rate-limit: la API de IGDB **no devolvió cabeceras `X-RateLimit-*` / `RateLimit-*`** en ninguna respuesta — solo `Content-Type` y `Date`. El estado de rate-limit no es observable desde las cabeceras; un cuerpo `429` es la única señal.
- Comportamiento observado: 12 llamadas `POST /v4/games/count` secuenciales seguidas sin pacing del lado del cliente devolvieron todas **HTTP 200** (sin 429). Los round-trips secuenciales no superaron 4 req/s.
- Tope de concurrencia de multiquery (observado): un `POST /v4/multiquery` con 15 subconsultas devolvió **HTTP 400** — cuerpo `{"title":"Too Many Concurrent queries","details":"The maximum amount of concurrent request is at 10 queries"}`. Dividido en dos multiqueries de ≤10 subconsultas, ambas devolvieron HTTP 200.

**Regla de pacing del importador para el Plan 01.1-02:** ritmo de ≤4 requests/second, ≤8 concurrent open requests, ≤10 subconsultas por multiquery, con backoff consciente de 429. Ningún presupuesto de días-para-completar viene forzado por un tope mensual.

## 5. Términos: caché / almacenamiento / redistribución / atribución / portadas

Rigen dos fuentes primarias, y se recogen aquí **textualmente en inglés** porque no están perfectamente alineadas.

### 5.1 Twitch Developer Services Agreement (acuerdo legal paraguas)

Fuente: `https://legal.twitch.com/legal/developer-agreement/` (obtenido 2026-09-05), sección II ("Program Materials"), cita textual:

> "Do not store copies of Twitch Content or Program Materials, unless you: (a) obtain prior written authorization from Twitch (through these terms or otherwise); (b) control the rights associated with such content; or (c) cache such information for only a twenty-four hour time period without further sharing it with third parties. **Re-syndication and re-distribution of Program Materials or data as available from a Twitch API is prohibited.**"

> "You must delete all Twitch Data collected upon termination of this Agreement, revocation, or reduction in scope of end user authorization, or upon Twitch's or the end user's request…"

### 5.2 FAQ de la documentación de la API de IGDB (la guía escrita del propio operador)

Fuente: `https://api-docs.igdb.com/` › *Getting Started* / *License* / *Business related FAQ* (obtenido 2026-09-05), cita textual:

- "The IGDB.com API is free for non-commercial usage under the terms of the Twitch Developer Service Agreement."
- "One of the principles behind IGDB.com is accessibility of data. We wish to share the data with anyone who wants to build cool video game oriented websites, apps and services."
- FAQ Q2: "What is the price of the API? The API is free for both non-commercial and commercial projects."
- FAQ Q3: "**Am I allowed to store/cache the data locally? Yes. In fact, we prefer if you store and serve the data to your end users.** You remain in control over your user experience, while alleviating pressure on the API itself."
- FAQ Q4: "We expect fair attribution, i.e. attribution that is visible to your users and located in a static location (e.g. not in a change log)."
- FAQ Q5: "**You are allowed to keep all data you retrieve from the API and we will not ask you to remove the data in case of partnership termination.**"
- Sección de imágenes: "Images that are removed or replaced from IGDB.com exist for 30 days before they are removed. Keep that in mind when designing cache logic."

### 5.3 Reconciliación (la conclusión que codifica el ADR)

- **Conclusión sobre caché:** el límite general de caché de 24 horas de la DSA está sujeto a su propio carve-out (a) — "prior written authorization from Twitch (**through these terms or otherwise**)". La documentación oficial publicada de la API de IGDB, de la subsidiaria de Twitch/Amazon que opera la API, es esa autorización escrita "otherwise": concede explícitamente el almacenamiento local indefinido y el servicio a usuarios finales (FAQ Q3) y la retención post-terminación (FAQ Q5). SavePoint almacena metadatos estructurados de IGDB localmente y los sirve desde su propia base de datos, y trata la FAQ como el permiso operativo de referencia.
- **Conclusión sobre atribución / redistribución:** SavePoint muestra **atribución justa, visible y estática a IGDB.com** (página de fuentes + pie) aunque sea un proyecto académico no comercial, y **no** re-sindica ni redistribuye el dataset en bloque — sin dump público de datos, sin compartir con terceros, sin una API propia que re-sirva filas de IGDB en bloque. Esto satisface tanto la prohibición de redistribución de la DSA como la expectativa de atribución de la FAQ.
- **Conclusión sobre hotlink vs. mirror de portadas:** las portadas se sirven por **hotlink** a `https://images.igdb.com/igdb/image/upload/t_{size}/{hash}.jpg` (donde `{hash}` es `cover.image_id`), que IGDB documenta como el mecanismo previsto. Las portadas **no se replican localmente en la Fase 01.1** — el mirroring local de imágenes se apoya con más fuerza en el permiso de almacenamiento para "Twitch Content" y arrastra la carga documentada de reconciliación por la ventana de eliminación de imágenes de 30 días. Una portada ausente o que falla cae de vuelta al placeholder de primera parte de la Fase 1 (D-06 / D-07). El mirroring local solo se revisa si la fiabilidad del hotlink resulta inadecuada.

---

## Reproducción

```
# entorno: IGDB_CLIENT_ID y IGDB_CLIENT_SECRET definidos (los valores nunca se imprimen)
# 1. token:   POST https://id.twitch.tv/oauth2/token?client_id=…&client_secret=…&grant_type=client_credentials
# 2. conteos: POST https://api.igdb.com/v4/games/count            (body: "" | "where game_type = 0;")
#             POST https://api.igdb.com/v4/{covers,genres,platforms}/count
# 3. campos:  POST https://api.igdb.com/v4/games  body: fields id,name,slug,genres.name,platforms.name,cover.image_id,cover.url,first_release_date,total_rating,url; where id = 1942;
# 4. límites: 12x POST /v4/games/count (observar 429s); POST /v4/multiquery con >10 subconsultas (observar el tope de concurrencia HTTP 400)
```

Los conteos derivan con el tiempo a medida que cambia el dataset de IGDB; las marcas de tiempo ISO-8601 UTC de arriba fijan los valores puntuales de este sondeo. El Plan 01.1-02 vuelve a medir el conteo elegible inmediatamente antes de importar y apunta a ≥90% de esa medición fresca (y > 100,000 obras primarias).
