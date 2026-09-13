# Firma de Fase 6 — Descubrimiento público y enriquecimiento resiliente

**Fecha:** 2026-09-13  
**Issue:** #58  
**Plan:** `06-09-PLAN.md`  
**Estado:** cierre técnico y documental; verificación browser completa diferida por
limitaciones del entorno.

## Requisitos

| Requisito | Resultado | Evidencia principal |
|---|---|---|
| PROF-03 | Cumplido | Proyecciones allowlist y ausencia de campos privados |
| PROF-04 | Cumplido | Política server-side y `404` genérico para URLs no autorizadas |
| CAT-05 | Cumplido | Catálogo PostgreSQL, facets, procedencia y snapshots con hash |
| SOCIAL-03 | Cumplido | Alias exacto y solicitudes aceptar/rechazar/eliminar/bloquear/desbloquear |
| SOCIAL-04 | Cumplido | Proyecciones owner/friend/basic y URLs protegidas |
| SOCIAL-05 | Cumplido | Recomendaciones privadas, bandeja, badge, lectura y cooldown de siete días |

## Cobertura D-01..D-15

| Decisión | Cobertura y evidencia |
|---|---|
| D-01 | Búsqueda GET, facets y paginación del catálogo |
| D-02 | URL compartible de detalle y fuente/procedencia visible |
| D-03 | Búsqueda por alias exacto y relación bidireccional |
| D-04 | Hub de amistades y acciones contextuales por estado |
| D-05 | Rechazo, eliminación, bloqueo y desbloqueo como transiciones distintas |
| D-06 | Colección/listas/comentarios solo para owner o amistad aceptada |
| D-07 | Perfil no-amigo reducido a la proyección básica |
| D-08 | URL directa no autorizada o bloqueada responde `404` genérico |
| D-09 | Proyección de colección con campos allowlist y sin inventario/precios |
| D-10 | Listas públicas con slug estable y orden manual conservado |
| D-11 | Comentarios con alias, texto inerte y fecha en el detalle |
| D-12 | No se exponen estadísticas globales en perfiles protegidos |
| D-13 | Recomendación privada dirigida a una amistad concreta |
| D-14 | Bandeja privada, badge textual accesible y `mark_read` |
| D-15 | Fan-out a varias amistades y cooldown direccional de siete días |

## Gates ejecutados

- PostgreSQL 18.6 en Compose; `check`, migraciones, plan vacío y
  `makemigrations --check --dry-run` pasan.
- Regresión API: `43 passed`; sentinel PostgreSQL/snapshots: `5 passed`.
- `check-dependencies.ps1` y `check-secrets.ps1`: `PASS`; no se publican secretos,
  cookies, credenciales ni logs brutos.
- TypeScript: `tsc --noEmit` pasa. Vitest focalizado de catálogo/social: `19 passed`.
- Los SHA-256 y la procedencia completa están en
  [`phase-06-catalogue-enrichment.md`](phase-06-catalogue-enrichment.md). No se
  relanzó evaluación offline ni se hicieron llamadas HTTP a proveedores externos.

## Seguridad y privacidad

La autorización permanece en Django; Next.js solo transporta la sesión mediante el
proxy same-origin y CSRF. Se cubren IDOR/404, bloqueo, cooldown, XSS de texto social,
allowlists y aislamiento de snapshots conforme a T-06-09-01..07 y el gate de
dependencias/secretos. Los journeys preparados atraviesan el stack real y no usan
respuestas mock para saltar Django.

## Limitaciones y aceptación visual

El anfitrión tiene Playwright instalado y pudo lanzar Chromium, pero la imagen Compose
`web` no incluye la configuración/entorno de Playwright ni monta `e2e/`. El primer
intento host obtuvo 1 journey de catálogo aprobado, 1 fallo de la aserción de 400%
por doble simulación de zoom y 1 social omitido por no disponer de las variables de
ejecución; la aserción de zoom se corrigió en el commit posterior. El reintento fue
interrumpido al priorizar el cierre documental, por lo que no se declara una pasada
browser completa.

La pasada completa de ambos journeys, axe, teclado, foco, 320px y 400% queda
**deferred** con evidencia de los comandos y resultados anteriores; no se presenta
como aprobación browser. El backend, contratos, regresión y evidencia reproducible sí
quedan cerrados. No se instalaron navegadores ni se consignaron credenciales.

## Actualización UAT — 2026-09-13

Tras instalar temporalmente Chromium y sus librerías dentro de un contenedor efímero,
el journey de catálogo se ejecutó contra el stack Compose publicado y terminó con **2/2
tests PASS**, incluyendo filtros/facets, ausencia de llamadas externas, 320 px, reduced
motion, axe y el reflow equivalente a 400% de zoom. La prueba social completa se mantiene
diferida porque este entorno no expone `DEMO_USERNAME` ni `DEMO_PASSWORD`; Playwright la
omite de forma segura sin inventar cuentas ni credenciales.

## Fuentes canónicas

- [`06-REQUIREMENTS-RECONCILIATION.md`](../../.planning/phases/06-public-discovery-and-resilient-enrichment/06-REQUIREMENTS-RECONCILIATION.md)
- [`06-09-PLAN.md`](../../.planning/phases/06-public-discovery-and-resilient-enrichment/06-09-PLAN.md)
- [`phase-06-catalogue-enrichment.md`](phase-06-catalogue-enrichment.md)
- [`CONVENTIONS.md`](../../CONVENTIONS.md)
