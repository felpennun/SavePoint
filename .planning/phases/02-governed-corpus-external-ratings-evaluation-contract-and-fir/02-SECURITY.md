---
phase: "02"
slug: "governed-corpus-external-ratings-evaluation-contract-and-fir"
status: verified
# Solo cuentan las amenazas abiertas de severidad alta o crítica.
threats_open: 0
asvs_level: 1
created: "2026-09-08"
---

# Fase 2 — Seguridad

> Contrato de seguridad de la fase: registro de amenazas, riesgos aceptados y trazabilidad de la auditoría.

---

## Fronteras de confianza

| Frontera | Descripción | Datos que la atraviesan |
|----------|-------------|-------------------------|
| Navegador ↔ Next.js ↔ Django | Navegación y proxy *same-origin* con sesión Django y protección CSRF | Cookie de sesión, token CSRF, formularios y respuestas JSON |
| Visitante anónimo ↔ API pública | Catálogo, detalle de obras, perfiles públicos y agregados permitidos | Metadatos públicos y conteos agregados |
| Usuario autenticado ↔ biblioteca y recomendador | Operaciones limitadas siempre a `request.user` | Estado, valoración, copias y perfil de preferencias |
| Django ↔ PostgreSQL | Persistencia transaccional del producto y de la investigación | Datos de usuarios, catálogo, procedencia y artefactos versionados |
| Trabajos offline ↔ fuentes externas | Importación gobernada desde IGDB y fuentes de ratings autorizadas | Credenciales solo por entorno y metadatos externos |
| Corpus congelado ↔ evaluación | Ejecución reproducible contra una versión y un *snapshot* explícitos | Vectores, particiones, semillas, métricas y hashes |
| Repositorio ↔ registros e imágenes OCI | Resolución de dependencias y construcción de runtimes | Código, lockfiles, imágenes base y metadatos de procedencia |

---

## Registro de amenazas

Los 51 controles definidos durante la planificación se conservan en las tablas `<threat_model>` de `02-01-PLAN.md` a `02-13-PLAN.md`. Esta tabla agrupa su verificación por plan; los identificadores individuales `T-02-XX-YY` siguen siendo la referencia canónica.

| Amenazas | Categorías principales | Severidad | Disposición | Mitigación y evidencia | Estado |
|----------|------------------------|-----------|-------------|-----------------------|--------|
| `T-02-01-01..04` | Alteración, exposición, disponibilidad | 1 alta, 2 medias, 1 baja | Mitigar / aceptar | Corpus versionado, checksum determinista, salida agregada y ejecución offline; `02-01-SUMMARY.md` | cerradas |
| `T-02-02-01..05` | Alteración, exposición, SSRF | 3 altas, 2 medias | Mitigar | Snapshot insert-only, redacción, host fijo, redirects rechazados y reconciliación determinista; `02-02-SUMMARY.md` | cerradas |
| `T-02-03-01..04` | Inyección, disponibilidad, exposición | 1 alta, 1 media, 2 bajas | Mitigar / aceptar | ORM parametrizado, allowlists, límites de facetas y proceso offline por lotes; `02-03-SUMMARY.md` | cerradas |
| `T-02-04-01..03` | XSS, disponibilidad, exposición | 1 media, 2 bajas | Mitigar / aceptar | Escape de React, `URLSearchParams` y catálogo exclusivamente público; `02-04-SUMMARY.md` | cerradas |
| `T-02-05-01..05` | Exposición, alteración, disponibilidad | 3 altas, 2 medias | Mitigar | Scoping por usuario, agregados, separación producto/investigación, límites y proyecciones allowlist; `02-05-SUMMARY.md` | cerradas |
| `T-02-06-01..03` | XSS, exposición | 1 alta, 2 medias | Mitigar | Sin HTML interpretado, datos del usuario autenticado y conteos agregados; `02-06-SUMMARY.md` | cerradas |
| `T-02-07-01..02` | Exposición, alteración | 2 bajas | Mitigar / aceptar | Nombres accesibles persistentes y tokens CSS sin ejecución; `02-07-SUMMARY.md` | cerradas |
| `T-02-08-01..04` | Alteración, exposición | 1 alta, 3 medias | Mitigar | Split de test de un solo uso, rejilla acotada, simulación declarada y versión de corpus fijada; `02-08-SUMMARY.md` | cerradas |
| `T-02-09-01..04` | Exposición, suplantación, alteración | 1 alta, 3 medias | Mitigar | Marcadores sintéticos, etiquetado, salida agregada y transacción atómica; `02-09-SUMMARY.md` | cerradas |
| `T-02-10-01..04` | Alteración, cadena de suministro, disponibilidad | 1 alta, 2 medias, 1 baja | Mitigar / aceptar | Lectura desde snapshot, gate de dependencias, ejecución offline y semilla explícita; `02-10-SUMMARY.md` | cerradas |
| `T-02-11-01..05` | Alteración, exposición, integridad, disponibilidad | 3 altas, 2 medias | Mitigar | Registro cerrado de algoritmos, scoping por usuario, snapshot, explicaciones numéricas y límites; `02-11-SUMMARY.md` | cerradas |
| `T-02-12-01..03` | Exposición, XSS | 1 alta, 1 media, 1 baja | Mitigar | Gate de sesión, escape de React y arranque en frío explícito; `02-12-SUMMARY.md` | cerradas |
| `T-02-13-01..05` | Alteración, exposición, repudio | 3 altas, 1 media, 1 baja | Mitigar | Candidatos compartidos, drift fail-closed, test de un solo uso y manifiesto trazable; `02-13-SUMMARY.md` | cerradas |
| `AF-SEC-01` | Exposición / cadena de suministro | alta | Mitigar | Datos locales y artefactos de autoría excluidos del contexto Docker; imagen API reducida y revisada | cerrada |
| `AF-SEC-02` | Cadena de suministro | crítica | Mitigar | Runtimes exactos actualizados, digests fijados y gestores globales retirados; Trivy sin hallazgos altos/críticos | cerrada |
| `AF-SEC-03` | Disponibilidad | media | Mitigar | Throttles compartidos para recomendaciones y popularidad, con regresiones automatizadas | cerrada |
| `AF-SEC-04` | SSRF / redirect inseguro | media | Mitigar | Cliente IGDB configurado para no seguir redirects en token ni API | cerrada |
| `AF-SEC-05` | Exposición / cadena de suministro | media | Mitigar | Gitleaks sobre todo el historial, alertas de GitHub y configuración semanal de Dependabot | cerrada |
| `X-SEC-01` | Garantía operativa | media | Mitigar | Añadir CI que ejecute gates de seguridad, suites y build en cada cambio | abierta, por debajo del umbral alto |
| `X-SEC-02` | Alteración | baja | Transferir | Proteger `main` cuando el plan de GitHub lo permita o el repositorio sea público | abierta, por debajo del umbral alto |

*Estado: abierta · cerrada · abierta por debajo del umbral alto (no bloqueante).*

---

## Registro de riesgos aceptados

| Riesgo | Amenaza | Justificación | Aceptado por | Fecha |
|--------|---------|---------------|--------------|-------|
| Ejecuciones offline extensas | `T-02-01-04`, `T-02-03-03`, `T-02-10-03` | No ocupan workers HTTP, trabajan por lotes y forman parte del procedimiento de investigación supervisado. | Felipe, mediante aprobación y cierre de los planes | 2026-09-08 |
| Catálogo público | `T-02-04-03` | La superficie solo expone metadatos de catálogo ya definidos como públicos y no incorpora datos personales. | Felipe, mediante aprobación y cierre del plan | 2026-09-08 |
| Tokens CSS modificables | `T-02-07-02` | Las propiedades CSS no introducen ejecución y el build valida la sintaxis. | Felipe, mediante aprobación y cierre del plan | 2026-09-08 |

---

## Evidencia de verificación

- `scripts/check-secrets.ps1`: limpio en Git, outputs de build, imágenes y logs.
- `scripts/check-history-secrets.ps1`: 310 commits y 55,17 MB inspeccionados en la pasada previa al checkpoint, sin filtraciones.
- Trivy 0.74.0: cero vulnerabilidades `HIGH`/`CRITICAL` corregibles en `savepoint-api:latest` y `savepoint-web:latest`.
- OSV-Scanner 2.4.0 y `pnpm audit --prod`: sin vulnerabilidades conocidas en los lockfiles de producción.
- `manage.py check --deploy`: cero observaciones con configuración segura de producción.
- Suites: 396 tests de API y 34 tests web superados; build de Next.js completado.
- Gates de dependencias y evidencia: superados.

## Trazabilidad de auditoría

| Fecha | Amenazas totales | Cerradas | Abiertas | Responsable |
|-------|------------------|----------|----------|-------------|
| 2026-09-08 | 58 | 56 | 2 no bloqueantes | Codex, con autorización del autor |

---

## Firma

- [x] Todas las amenazas tienen disposición (`mitigate`, `accept` o `transfer`).
- [x] Los riesgos aceptados están documentados.
- [x] `threats_open: 0` confirmado para severidades alta y crítica.
- [x] `status: verified` establecido en el frontmatter.

**Aprobación:** verificada técnicamente el 2026-09-08; las dos mejoras operativas no bloqueantes quedan registradas para seguimiento.
