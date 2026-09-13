---
phase: "07"
slug: "research-panel-hardening-and-evidence-freeze"
status: approved
shadcn_initialized: false
preset: none
created: "2026-09-14"
reviewed_at: "2026-09-14"
---

# Fase 07 — Contrato de diseño UI

> Contrato visual y de interacción para el panel académico de investigación. Se limita a
> una UI funcional, accesible y verificable para `/{locale}/research`; no abre el overhaul
> visual de catálogo, colección, perfiles, social o recomendaciones.

Fuentes de decisión: `07-CONTEXT.md`, `07-RESEARCH.md`, `07-PATTERNS.md`,
`07-DISCUSSION-LOG.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `CONVENTIONS.md`,
`apps/web/app/[locale]/layout.tsx`, `apps/web/components/AppShell.tsx`,
`apps/web/middleware.ts`, `apps/web/next.config.ts` y `apps/web/app/globals.css`.

## Alcance y principios bloqueados

- La superficie canónica es `/es/research` y `/en/research`. Su contenido es privado y de
  solo lectura: consulta ejecuciones congeladas, compara resultados y descarga evidencia
  saneada. No relanza evaluaciones, no edita resultados y no muta el split `test`.
- Django/DRF es la autoridad de sesión, permisos y allowlists. El frontend no decide si una
  persona es `Research Viewer` ni usa el nombre del usuario, `is_staff` o un cookie como
  sustituto del permiso.
- `Research Viewer` puede consultar y exportar. `Platform Admin` administra usuarios,
  catálogo, imports, jobs y experimentos mediante Django Admin; no existe un modo de
  administración propio dentro de Next.js.
- La interfaz debe ser entendible sin color, teclado o gráfico: cada gráfico tiene una tabla
  semántica equivalente y los archivos descargados proceden de snapshots, no de cálculos del
  cliente.
- No se añaden shadcn, Recharts, una cola, un datastore, un servicio de visualización ni otra
  dependencia recurrente. El tier gratuito y la arquitectura actual siguen siendo válidos.

## Design System

| Propiedad | Valor |
|-----------|-------|
| Tool | **none** — sistema de tokens CSS y componentes React de primera parte |
| Preset | not applicable |
| Component library | none — componentes manuales en `apps/web/components/` |
| Icon library | none — SVG inline accesibles; no se añade una librería de iconos |
| Font | `Inter` para interfaz y `JetBrains Mono` para valores numéricos, hashes e identificadores |
| Styling | Tailwind CSS 4 mediante `@import "tailwindcss"` y utilidades/tokens CSS en `apps/web/app/globals.css` |
| Temas | Oscuro por defecto y claro mediante `ThemeToggle`; los mismos nombres de token deben funcionar en ambos |

No existe `components.json` en el repositorio ni en `apps/web/`. La inspección de
`apps/web/package.json` y del `package.json` raíz tampoco encuentra una biblioteca de
componentes o de gráficos instalada. La ausencia de shadcn se mantiene deliberadamente:
el sistema manual ya existe, el alcance no requiere un kit adicional y toda dependencia
directa nueva exige aprobación humana según `CONVENTIONS.md`.

La shell actual carga los temas server-side desde `sp-theme`, usa `Inter`/`JetBrains Mono`
desde `next/font`, ofrece foco visible global, skip link y targets mínimos de 44px. El panel
reutiliza esas garantías y no redefine tokens por componente.

## Spacing Scale

Se reutilizan literalmente los tokens vigentes de `apps/web/app/globals.css`; no se crean
valores ad hoc.

| Token | Valor | Uso en esta fase |
|-------|-------|------------------|
| `xs` | 4px | Gap entre icono y texto, separación de etiqueta y valor |
| `sm` | 8px | Gap compacto de filtros, acciones y filas de estado |
| `sm` | 8px | Padding horizontal de controles y celdas compactas |
| `md` | 16px | Padding de superficies, gap entre campos y columnas |
| `lg` | 24px | Padding de página, tarjetas y separación entre bloques cercanos |
| `xl` | 32px | Separación entre cabecera, filtros y comparativa |
| `2xl` | 48px | Separación vertical entre comparativa, detalle y descargas |
| `3xl` | 64px | Padding inferior de la página |

Excepciones geométricas, no tokens de espaciado: todos los controles interactivos mantienen
un mínimo de 44×44px; la tabla puede tener `min-width: 760px` dentro de un contenedor con
scroll horizontal propio; nunca se permite scroll horizontal en `body` o `main`.

Reglas: `.sp-page` conserva `max-width: 1180px` y padding lateral `24px` en desktop; por
debajo de 720px usa padding lateral `16px`. Las superficies del panel usan `gap: 16px` y
las secciones principales `gap: 48px`. No se usa margen negativo para compensar el wrapping.

Jerarquía visual: el encabezado del panel y la comparativa de resultados seleccionada son
el foco primario; los filtros orientan la lectura y las descargas son acciones secundarias.
La jerarquía se expresa mediante orden semántico, tamaño tipográfico, superficie y espacio,
no mediante saturación de color ni controles que oculten información metodológica.

## Typography

La UI nueva declara exactamente cuatro tamaños y dos pesos. El texto numérico puede usar
`JetBrains Mono`, pero conserva el mismo tamaño y peso de su rol.

| Rol | Tamaño | Peso | Line Height | Uso |
|-----|--------|------|-------------|-----|
| Body | 16px (`--text-body`) | 400 | 1.5 | Copy, valores de tabla y explicación de resultados |
| Label | 13px (`--text-meta`) | 600 | 1.4 | Etiquetas de filtros, metadatos, badges y encabezados compactos |
| Heading | 22px (`--text-heading`) | 600 | 1.2 | `<h2>` de comparación, detalle, procedencia y descargas |
| Display | 30px (`--text-display`) | 600 | 1.2 | `<h1>` «Panel de investigación» |

No se introduce peso 700 en el panel. Los identificadores, hashes, versiones, recuentos y
tiempos usan `font-family: var(--font-mono)` y `font-variant-numeric: tabular-nums`; nunca
se usan como texto de párrafo. Los títulos largos envuelven: no se recortan con CSS si ello
oculta información metodológica.

## Color

La distribución 60/30/10 se aplica sobre los tokens actuales, incluidos sus equivalentes
de tema claro.

| Rol | Valor | Uso |
|-----|-------|-----|
| Dominante (60%) | `--color-surface-base`: `#161826` dark / `#f7f7fa` light | Fondo de página y espacio exterior |
| Secundario (30%) | `--color-surface-raised`: `#232532` / `#fdfdff`; `--color-surface-overlay`: `#292b31` / `#eceef4` | Superficies de filtros, tarjetas, tabla, estados y shell |
| Accent (10%) | `--color-accent`: `#9184d9` / `#5d5294`; texto `--color-accent-text` | CTA de exportación, navegación Research activa, enlaces, filtro seleccionado, foco y serie de gráfico seleccionada |
| Destructive | `--color-danger`: `#f0808a` / `#b3262c` | No se usa: el panel no tiene acciones destructivas |

Accent reservado para: CTA «Exportar evidencia», enlace activo de Research en la shell,
enlaces de procedencia/descarga, borde del filtro seleccionado, foco visible y una única
serie seleccionada del gráfico. No se usa para pintar todos los controles, cada algoritmo,
cada número alto, el texto de la tabla ni para comunicar éxito. Las diferencias entre
algoritmos se expresan con etiqueta y patrón/forma además del tono.

Estados: `--color-info` solo para aviso informativo o estado de sesión; `--color-success`
solo para confirmación de descarga/lectura válida; `--color-danger` solo para un error o
fallo de carga. Nunca se comunica permiso, ranking o calidad únicamente por color.

## Copywriting Contract

Toda cadena nueva debe tener paridad en `apps/web/i18n/es.ts`, `apps/web/i18n/en.ts` y
`dictionary.ts`. Las etiquetas técnicas pueden conservar los tokens de datos (`nDCG@K`,
`SHA-256`, `commit`) junto a una explicación humana.

| Elemento | Español | Inglés |
|----------|---------|---------|
| Título de página | `Panel de investigación` | `Research panel` |
| Introducción | `Resultados congelados y reproducibles para comparar algoritmos, cohortes y ejecuciones.` | `Frozen, reproducible results for comparing algorithms, cohorts, and runs.` |
| Identidad de acceso | `Research Viewer · Solo lectura` | `Research Viewer · Read-only` |
| Operación administrativa | `Platform Admin · Operaciones en Django Admin` | `Platform Admin · Operations in Django Admin` |
| Filtro de ejecución | `Ejecución` | `Run` |
| Filtro de algoritmo | `Algoritmo` | `Algorithm` |
| Filtro de cohorte | `Cohorte` | `Cohort` |
| Filtro de métrica | `Métrica del gráfico` | `Chart metric` |
| Aplicar filtros | `Aplicar filtros` | `Apply filters` |
| Restablecer | `Restablecer filtros` | `Reset filters` |
| CTA primaria | `Exportar evidencia` | `Export evidence` |
| Sección comparativa | `Comparación de resultados` | `Results comparison` |
| Sección de detalle | `Detalle de la evidencia` | `Evidence details` |
| Sección de procedencia | `Procedencia y limitaciones` | `Provenance and limitations` |
| Sección de descargas | `Descargas` | `Downloads` |
| Empty heading | `No hay resultados congelados` | `No frozen results` |
| Empty body | `No hay ejecuciones publicadas que coincidan con estos filtros. Restablece los filtros o revisa el estado de publicación.` | `No published runs match these filters. Reset the filters or check the publication status.` |
| Error de carga | `No se pudo cargar la evidencia. Inténtalo de nuevo; si el problema continúa, verifica el estado del API.` | `We couldn't load the evidence. Try again; if the problem continues, check the API status.` |
| Reintento | `Reintentar carga` | `Retry loading` |
| Exportación ocupada | `Preparando descarga…` | `Preparing download…` |
| Exportación correcta | `Descarga preparada.` | `Download ready.` |
| Valor ausente | `No disponible` | `Not available` |
| 404 neutro | `Página no encontrada` | `Page not found` |
| 404 neutro, cuerpo | `La página que buscas no está disponible.` | `The page you are looking for is not available.` |
| Destructivo | `No hay acciones destructivas en este panel.` | `This panel has no destructive actions.` |

La página 404 nunca dice «sin permiso», «Research Viewer», «investigación» ni diferencia
un recurso inexistente de una cuenta autenticada sin el permiso requerido. Un `401` por
sesión caducada redirige a login con `next` same-origin; no se muestra el contenido previo.

## Wireframes y contrato de pantalla

### Desktop (≥ 821px)

```text
[AppShell: marca | Home Catálogo Colección ... Research activo | idioma | tema | cuenta]
┌──────────────────────────────────────────────────────────────────────────────┐
│ Panel de investigación                                                       │
│ Resultados congelados y reproducibles…                 [Research Viewer]     │
│ [Platform Admin · Django Admin] (solo si la capacidad ya está autorizada)    │
├──────────────────────────────────────────────────────────────────────────────┤
│ FILTROS                                                                       │
│ [Ejecución ▼] [Algoritmo ▼] [Cohorte ▼] [Métrica del gráfico ▼]              │
│                                                   [Aplicar] [Restablecer]     │
├──────────────────────────────────────────────────────────────────────────────┤
│ Comparación de resultados                                                     │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Gráfico SVG responsive: métrica elegida, etiquetas y escala visible       │ │
│ │ Leyenda textual; el orden y los valores se corresponden con la tabla     │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────────────┐ │
│ │ Tabla completa: algoritmo · cohorte · n · métricas · tiempo               │ │
│ └──────────────────────────────────────────────────────────────────────────┘ │
├───────────────────────────────┬──────────────────────────────────────────────┤
│ Detalle de la evidencia       │ Procedencia y limitaciones                   │
│ ejecución, protocolo, params │ corpus, snapshot, hashes, límites            │
├───────────────────────────────┴──────────────────────────────────────────────┤
│ Descargas: [Exportar evidencia] [CSV] [JSON] [Figura SVG]                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Móvil (320px–820px y zoom 400%)

```text
[AppShell compacta + menú con focus trap]
Panel de investigación
intro
[Research Viewer · Solo lectura]
[Platform Admin…] (si aplica)
┌ Filtros ┐
│ Ejecución        [▼] │
│ Algoritmo        [▼] │
│ Cohorte          [▼] │
│ Métrica gráfico  [▼] │
│ [Aplicar] [Restablecer]│
└────────────┘
Comparación de resultados
[gráfico SVG a todo el ancho, leyenda y resumen textual]
[tabla dentro de scroll horizontal etiquetado; no scroll de página]
Detalle de la evidencia
Procedencia y limitaciones
Descargas
[Exportar evidencia]
[CSV] [JSON] [Figura SVG]
```

El DOM y el orden semántico son los mismos en desktop y móvil. La tabla no se sustituye por
tarjetas en móvil: el contenedor puede desplazarse horizontalmente y anuncia cómo hacerlo;
así se conserva una única fuente visible y auditable. El gráfico reduce su escala visual,
no sus datos. Las acciones de descarga pasan a una columna y conservan 44px de alto.

## Componentes y estados

### Componentes de fase

| Componente | Contrato |
|------------|----------|
| `AppShell` | Se reutiliza. Mantiene skip link, temas, idioma, menú móvil, cuenta y orden de foco. Recibe una capacidad server-side para mostrar Research solo a personal autorizado; la sesión presente por sí sola no basta. |
| `ResearchPage` | Server Component en `apps/web/app/[locale]/research/page.tsx`. Lee cookies/params, llama al API same-origin y entrega DTOs allowlisted al panel; nunca calcula métricas ni autoriza en cliente. |
| `ResearchAccessState` | Mapea sesión ausente a login y `403/404` a la página 404 neutra global. No renderiza un mensaje de forbidden que revele el panel. |
| `ResearchPanel` | Orquesta filtros, resumen, gráfico, tabla, detalle y descargas. Usa un único `main` y un único anuncio de estado por operación. |
| `ResearchFilters` | Formulario GET accesible con controles nativos o el patrón existente `sp-dropdown`. Opciones proceden del API; los valores desconocidos no se inventan. `Aplicar filtros` es explícito y conserva locale. |
| `ResearchComparisonChart` | SVG inline con `viewBox`, etiquetas y barras/series con texto visible. No usa `<canvas>`, hover-only ni una escala escondida. El gráfico no es la fuente primaria. |
| `ResearchComparisonTable` | `<table>` real con `<caption>`, `scope`, orden del backend y valores exactos. Replica la métrica seleccionada y ofrece todas las columnas de auditoría necesarias. |
| `ResearchEvidenceDetails` | Agrupa `<dl>` de run, protocolo, corpus, commit, seed, parámetros, entorno, hashes y limitaciones. Deja `No disponible` cuando el backend entrega `null`. |
| `ResearchExports` | Enlaces/controles a descargas same-origin generadas por backend. El cliente no serializa DTOs ni cambia nombres, hashes o valores. |
| Estado de ruta | Skeleton geometry-matched para filtros, gráfico, cinco filas de tabla y bloques de detalle; `aria-hidden` en decoración y un único `role=status`. |

### Estados obligatorios

| Estado | Contrato visual y de interacción |
|--------|----------------------------------|
| Loading inicial | Mantiene la shell y muestra skeletons de la geometría final. Un solo `role="status" aria-live="polite"` anuncia «Cargando…» una vez. No se deja una pantalla blanca. |
| Loading de filtros | El botón aplicado queda ocupado/disabled con texto «Cargando…»; los filtros conservan su valor y no se duplica la petición por cada checkbox. |
| Populated | Renderiza resultados reales del API: gráfico, tabla, detalles, limitaciones y descargas. La tabla y el gráfico comparten el mismo orden y filtro. |
| Empty | Mantiene título, filtros y explicación; muestra el heading/body del contrato y `Restablecer filtros`. No muestra tarjetas falsas, ejes vacíos ni ceros inventados. |
| Error total | Mantiene shell y encabezado; presenta un único `role="alert"` con el copy de error y `Reintentar carga`. Nunca muestra stack trace, URL interna, SQL o payload. |
| Error parcial | Si falta una familia no crítica, la sección conserva su título y muestra `No disponible`/aviso local; las demás filas no se borran ni se renombran. Si el contrato no permite una comparativa fiable, degrada a error total. |
| Forbidden | Cuenta autenticada sin permiso: respuesta 404 neutra indistinguible de inexistente. No se monta el panel, no se muestra el nombre de la ruta y no se permite reintentar desde un estado que revele existencia. |
| Sesión ausente | Middleware y backend conducen a `/{locale}/login?next=/{locale}/research`; el login conserva solo una ruta same-origin validada. No se precarga ningún dato del panel. |
| Sesión caducada | Un `401` posterior vuelve al login; el estado de UI no presenta resultados cacheados como actuales. |
| Exportación | El enlace respeta filtros y formato; mientras se prepara, anuncia «Preparando descarga…». Tras respuesta válida, anuncia «Descarga preparada.»; no se promete un archivo si el API falla. |

## Contrato con API y datos visibles

Las rutas exactas se coordinan con `07-01-PLAN.md`, pero deben conservar estas formas y
semánticas. Todas requieren el permiso Django específico de `Research Viewer`, usan
`GET`, son `no-store` y devuelven DTOs allowlisted.

| Endpoint recomendado | Consulta | Respuesta UI requerida |
|----------------------|----------|-------------------------|
| `GET /api/evaluation/runs/` | Lista de ejecuciones publicadas y opciones de filtros | `runs[]` con `run_id` display-safe, estado, fecha, protocolo, corpus y hashes permitidos; `algorithms[]`, `cohorts[]` y `metrics[]` allowlisted. |
| `GET /api/evaluation/comparison/` | `run`, `algorithm`, `cohort`, `metric` allowlisted | `run`, `filters`, `rows[]`, `metric_definitions[]`, `timings`, `provenance`, `limitations` y `downloads`. La secuencia de `rows[]` llega ordenada y no se vuelve a ordenar en React. |
| `GET /api/evaluation/artifacts/` | Identidad del artefacto saneado asociado a la ejecución | Metadatos y checksum, nunca dump privado, logs crudos, ruta absoluta, credencial, cookie, token o identificador personal innecesario. |
| `GET /api/evaluation/exports/` | `run`, `algorithm`, `cohort`, `format=csv|json|svg` | Descarga con `Content-Disposition` y nombre seguro; contenido derivado del snapshot inmutable y con checksum/referencia de ejecución. El formato `svg` es la figura visual; CSV/JSON son datos/metadatos, no una recalculación del cliente. |

Forma mínima de los datos consumidos:

```text
RunSummary:
  run_id, status, published_at, protocol_version, corpus_version
  commit_sha, artifact_sha256, candidate_manifest_sha256, seed_count

ComparisonRow:
  algorithm_id, algorithm_label, cohort_id, cohort_label, evaluable_count
  metrics: { name, value|null, unit, higher_is_better }
  timing: { wall_ms|null, cpu_ms|null }

Comparison:
  run, filters, rows[], metric_definitions[], provenance, limitations, downloads[]
```

El frontend solo presenta los valores. No redondea para ordenar, no convierte unidades,
no calcula medias, intervalos, diferencias, rangos o significación estadística y no cruza
dos ejecuciones por su cuenta. Si una métrica es `null`, muestra `No disponible` y conserva
la explicación de por qué falta si el backend la proporciona.

### Permisos y navegación

- `apps/web/middleware.ts` debe tratar `/research` como ruta autenticada para producir la
  redirección a login cuando no hay `sessionid`. Esto es una mejora de navegación; la
  autorización real se repite en Django y en cada endpoint.
- `AppShell` no puede construir el enlace Research a partir de `isAuthenticated` solamente,
  porque el layout actual solo conoce la presencia del cookie. Debe recibir una proyección
  server-side de capacidades, o resolverla mediante el endpoint de sesión ya autorizado.
  El enlace se renderiza solo si `can_view_research === true`; cuentas demo y cuentas
  registradas sin grupo no lo ven.
- El enlace Research usa `aria-current="page"` en `/research` y conserva el patrón de
  navegación desktop/mobile existente. El menú mobile lo incluye solo en el mismo caso y
  conserva focus trap, Escape y devolución del foco.
- `Platform Admin` no es una pestaña ni un selector de modo. Si la capacidad administrativa
  ya está autorizada y existe una ruta Django Admin accesible en el despliegue, puede mostrarse
  un enlace secundario a esa superficie existente; si no está verificada, se muestra solo la
  etiqueta informativa y no se fabrica `/admin` en Next.js.

## Accesibilidad

- Un único `<h1>`; cada bloque tiene `<h2>` y, cuando corresponde, `<h3>`. Los filtros están
  agrupados en `<form aria-label="Filtros de investigación">` y los grupos de opciones tienen
  nombre visible. No se usa un `div` con click como control.
- Los controles tienen mínimo 44×44px, foco global de 2px con offset de 2px y contraste AA
  en ambos temas. El foco no se elimina durante scroll de tabla, popovers o descarga.
- El gráfico es `figure` con título y descripción; su SVG puede tener `aria-hidden="true"`
  porque la tabla equivalente queda visible y asociada mediante `aria-describedby`. Las
  etiquetas de ejes, métrica, unidad, algoritmo y cohorte aparecen también como texto.
- La tabla usa `caption`, encabezados con `scope="col"`, encabezado de fila cuando proceda,
  `tabular-nums` y valores completos. El contenedor horizontal tiene `tabindex="0"`, nombre
  accesible y texto de ayuda visible en móvil; el scroll no se delega a un gesto exclusivo.
- Estados de carga usan un solo anuncio polite; errores usan un único `role="alert"`. Los
  avisos parciales se asocian al bloque afectado. Nunca se anuncian hashes o filas repetidas
  como mensajes de estado.
- El color no es la única señal: cada barra tiene etiqueta, los filtros muestran estado
  seleccionado textual y los estados tienen texto. Se respeta `prefers-reduced-motion`; no
  hay animación obligatoria en skeleton, gráfico o focus.
- El panel debe pasar axe en dark/light y una revisión manual de teclado: skip link, shell,
  filtros, popover, tabla, detalles, enlaces de descarga y retorno de foco tras cerrar menú.

## Responsive y reflow

- Desktop: dos columnas solo para los bloques de detalle; comparativa y tabla ocupan el ancho
  completo. La shell y su máximo de 1180px se mantienen intactos.
- 820px o menos: una columna; filtros envuelven en filas y sus paneles no salen del viewport.
  El gráfico ocupa el ancho disponible y la leyenda se envuelve.
- 480px o menos: filtros y descargas pasan a columna; el CTA primaria ocupa el ancho. El
  texto de etiquetas, nombres de algoritmo y limitaciones puede envolver en cualquier punto.
- A 320px y 400% de zoom no hay overflow horizontal de `html`, `body` ni `main`. Solo la
  tabla posee scroll interno anunciado. No se ocultan columnas críticas con `display:none`;
  si la tabla excede el viewport, el usuario puede recorrer todas sus columnas.
- La página mantiene el mismo DOM accesible en todos los breakpoints. No se crean controles
  hover-only, tooltip-only o una segunda versión móvil de los datos.

## UI Considerations

> Cobertura de estados shape-rooted conforme a `ui-consideration-probe.md`. La copy de empty
> y error se referencia desde `## Copywriting Contract`; no se duplica aquí.

Applicable state considerations resolved: **6 covered, 2 backstop, 0 unresolved**.

| Categoría | Elemento(s) | Estado | Resolución / Motivo |
|-----------|-------------|--------|---------------------|
| empty | Ejecuciones, filtros y filas de comparación | ✅ covered | Cero resultados muestra el empty state localizado y Restablecer filtros; nunca muestra ejes, filas o métricas inventadas. |
| loading | Ruta, filtros, gráfico, tabla y descargas | ✅ covered | Skeleton geometry-matched y un único status polite; los controles conservan contexto y no dejan pantalla blanca. |
| error | API, exportación y bloque parcial | ✅ covered | Error total usa alert y retry; error parcial se queda en el bloque afectado, sin stack trace ni fallback que parezca resultado. |
| populated | Comparativa, tabla y detalles | ✅ covered | El gráfico y la tabla representan el mismo DTO ordenado por backend; procedencia, limitaciones y descargas quedan visibles. |
| partial | Métrica, timing, portada inexistente no aplica, procedencia incompleta | ✅ covered | `null` se presenta como No disponible y conserva la fila; si la comparativa deja de ser fiable, se degrada a error total. |
| overflow | Tabla, leyenda, filtros y texto metodológico | ✅ covered | Solo la tabla hace scroll interno; leyendas/filtros envuelven y `main` no desborda a 320px/400%. |
| zero-one-many | Runs, algoritmos, cohortes y filas | 🧪 backstop | La UI conserva lectura con cero, uno y muchos; Playwright debe verificar copy singular/plural, altura, orden y ausencia de ejes vacíos. |
| long-text | Labels, algorithm IDs, limitaciones, hashes y traducciones | 🧪 backstop | Playwright/axe debe comprobar wrapping a 30% de expansión y 400% de zoom, sin truncar valores ni perder accesibilidad. |

## Navegación y estados de acceso

| Situación | Resultado observable exigido |
|-----------|------------------------------|
| Sin sesión | Redirección a `/{locale}/login?next=/{locale}/research`; la página de login es la única superficie visible y no conoce DTOs del panel. |
| Sesión sin `Research Viewer` | Respuesta neutra 404 idéntica a un recurso inexistente, desde la página y desde cada endpoint. El enlace Research no aparece. |
| `Research Viewer` | Enlace visible en la shell y página poblada si hay ejecuciones; badge de solo lectura; no hay acciones de mutate/re-run. |
| Autor con ambos grupos | Se mantiene badge de Research Viewer y, como información separada, Platform Admin/Django Admin. El panel no obtiene controles de administración. |
| Sesión expirada durante uso | Login same-origin; no se muestra un resultado cacheado como vigente. |
| Filtros inválidos o stale | El API valida allowlists; la UI no fabrica opciones. Se ignoran/restablecen de forma determinista y se conserva el locale. |

## Verificación exigida a planner/executor

1. La página localizada existe en `/es/research` y `/en/research`, compila y conserva
   `AppShell`, el tema, idioma, skip link y menú mobile.
2. Un usuario sin sesión es redirigido a login; una cuenta autenticada sin permiso no puede
   inferir la ruta por el enlace y recibe 404 genérico; `Research Viewer` sí ve y consulta.
   La prueba debe cubrir directamente la respuesta backend, no solo la visibilidad del link.
3. Test frontend: la secuencia y los valores de filas/tableta coinciden con `rows[]`; no hay
   `sort`, agregación, cálculo de métricas ni datos fixture en el componente.
4. Test de filtros: ejecución, algoritmo, cohorte y métrica se envían como allowlist, se
   conservan al aplicar/restablecer y no provocan requests duplicadas por interacción interna.
5. Test de estados loading, empty total, error total, error parcial, `null` de métricas/timing,
   401, 403/404 y descarga fallida; ningún estado deja una pantalla blanca.
6. Test de paridad ES/EN para todas las cadenas nuevas y ausencia de vocabulario que revele
   permisos en el 404 neutro.
7. Playwright desktop y 320px: no hay overflow horizontal de página; la tabla tiene scroll
   interno etiquetado; los controles/descargas miden al menos 44px; el mismo orden de DOM se
   conserva en ambos viewports y a 400% de zoom.
8. axe-core en tema oscuro y claro, recorrido completo por teclado, foco visible, `caption`
   y encabezados semánticos de tabla, equivalencia textual del SVG y respeto de reduced motion.
9. La exportación conserva filtros, `run_id`, formato, versión y checksum procedentes del API;
   no genera ni descarga secretos, dumps privados, logs crudos o rutas absolutas.
10. El chequeo final integra el panel con los gates de `07-05-PLAN.md`: TypeScript, Vitest,
    Playwright, axe, secretos, dependencias, headers, health y evidencia reproducible.

## Diferido explícitamente

- Overhaul visual completo de la aplicación y una segunda pasada de densidad/imaginería.
- Interfaz administrativa propia en Next.js; las operaciones viven en Django Admin.
- Relanzar entrenamientos/evaluaciones, editar snapshots o recalcular métricas en navegador.
- Gráficos avanzados, zoom, dashboards en tiempo real, filtros libres no allowlisted y
  visualizaciones que no tengan una tabla equivalente.
- PNG/PDF generado por un servicio externo, un proveedor de charts, Redis, almacenamiento
  de pago o cualquier dependencia recurrente que no esté justificada por benchmark.
- Exposición pública o mixta de resultados; el panel no se convierte en una página pública
  de tesis durante esta fase.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| Ninguno | Ninguno | No aplica — `Tool: none`, sin shadcn ni registros de terceros |

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS
- [ ] Dimension 7 Inventory Provenance: PASS — no aplica con `Tool: none`

**Approval:** approved
