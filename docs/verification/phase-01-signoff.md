# Firma de la Fase 1: Slice de demo pública de tres días

**Estado: ACEPTADA** por Felipe (autor), 2026-09-05, contra el commit `1af981e1c97f2c46bf07671ad1ec13fe7461bf7a`, desplegada en `https://save-point-orpin.vercel.app` (API: `https://savepoint-api-37nz.onrender.com`).

Este documento es la aceptación humana final de la Fase 1 según `.planning/phases/01-three-day-public-demo-slice/01-14-PLAN.md`. Enlaza la evidencia automática, el recorrido manual del autor y las decisiones prospectivas del propio autor. No oculta ni suaviza ninguna limitación para presentar la demo como más completa de lo que es.

## Evidencia automática (esta sesión, mismo commit)

| Check | Comando | Resultado |
|---|---|---|
| Suite completa de Playwright | `corepack pnpm exec playwright test` | 32 pasados, 1 saltado (el smoke desplegado se salta sin un `BASE_URL` en vivo; verificado por separado abajo) |
| Barrido de secretos | `powershell -File scripts/check-secrets.ps1` | PASS — 3145 ficheros de Git, 225 ficheros de build, 2 imágenes, ~16KB de logs escaneados, cero matches fuera de allowlist |
| Integridad de evidencia/ledger | `powershell -File scripts/check-evidence.ps1` | PASS — 5 ADRs, 15 entradas de ledger, esquema/tipos/actores/rutas/hashes/cobertura/barrido-de-secretos todos válidos |
| Smoke desplegado (URL real) | `playwright test e2e/deployed-smoke.spec.ts` contra `https://save-point-orpin.vercel.app` | PASS, 2026-09-05T10:00Z, commit `ff5aa2ee7ae460f780187f1fc13298bfb2e12fbe` confirmado idéntico en el `/health/` de Render y el de Vercel |

Nota: el commit confirmado del smoke desplegado (`ff5aa2e...`) precede al commit de este propio documento (`1af981e...`, que solo toca ficheros de docs/ledger/robustez-de-tests, no código de aplicación) — no hubo cambio de código de aplicación entre el smoke y esta firma.

## Criterios de éxito del ROADMAP (Fase 1)

1. **Un visitante puede abrir el despliegue público, iniciar sesión, buscar en el catálogo local e inspeccionar un juego con información de fuente offline.** — Verificado: el recorrido login → catálogo → detalle del smoke desplegado; la página `docs/sources` respaldada por `SourcesView`; la importación de catálogo es solo offline (sin llamadas a proveedor en runtime, confirmado por análisis estático en el Plan 01-11).
2. **Un usuario autenticado puede cambiar estado, valorar y registrar copias mientras la propiedad permanece privada.** — Verificado: `e2e/demo-journey.spec.ts` (la valoración + dos copias sobreviven a la recarga); el serializer de allowlist hecho a mano de `PublicProfileView` (Plan 01-04).
3. **Un visitante autorizado puede ver una recomendación de popularidad a partir de datos demo.** — Verificado: `library/popularity.py::rank_popularity_v1()`, auto-verificado contra los resultados esperados con checksum de `data/demo/seed-v1.json` en cada carga de seed.
4. **Una máquina limpia arranca la demo offline desde instrucciones fijadas, sin ningún secreto en ningún sitio.** — Verificado: la ejecución `docker compose up --build --wait` sobre base de datos fresca del Plan 01-11; `scripts/check-secrets.ps1` PASS arriba.
5. **Usable con teclado, responsive, y evidencia de tesis (fuente/legal, arquitectura, entradas/salidas de agentes, verificación, limitaciones, decisiones del autor) capturada.** — Verificado: `e2e/a11y.spec.ts` (26 tests); `docs/adr/ADR-*.md` (5 ADRs); `docs/methodology/agent-ledger.jsonl` (15 entradas, PASS arriba).

## Recorrido manual del autor

El autor confirmó, contra la URL pública en vivo: el recorrido completo (homepage, login, búsqueda, detalle/procedencia de juego, estado, valoración, copias, colección, perfil público, popularidad, logout) funciona correctamente. No se encontró ningún defecto bloqueante.

**Reutilizado de la cobertura automática del Plan 01-10** (no re-recorrido a mano esta sesión, según la propia frontera honesta de ese plan): los escaneos axe ES/EN × móvil/escritorio y el recorrido completo solo con teclado están cubiertos por `e2e/a11y.spec.ts`.

**Abierto, explícitamente no re-verificado por el autor esta sesión** (arrastrado de la checklist manual del Plan 01-10, `docs/verification/phase-01-manual.md`):
- Reflow al 400% de zoom
- Una pasada básica con lector de pantalla (NVDA/VoiceOver)

**Corrección (encontrada por el verificador independiente de la Fase 1, 2026-09-05):** un borrador anterior de este documento decía que estas eran "las únicas dos casillas sin marcar" en `docs/verification/phase-01-manual.md`. Eso sobreestimaba las cosas -- toda casilla de ese documento está sin marcar, por el diseño deliberado del propio Plan 01-10, que reserva la confirmación-por-casilla para un revisor humano incluso en las secciones que su suite automática ya cubre (ver la nota "Automated coverage" de ese plan). La afirmación exacta es más estrecha: de las secciones de esa checklist, solo estos dos ítems concretos (400% zoom, lector de pantalla) **no tienen evidencia sustituta en absoluto**, automática ni manual. Toda otra sección tiene evidencia automática real (26 tests de `e2e/a11y.spec.ts`) aunque su casilla también siga sin marcar a la espera de una pasada manual completa. Estos dos no bloquean esta firma porque el resto de la cobertura automática de axe/teclado/reflow-a-320px ya da evidencia de accesibilidad fuerte (si no exhaustiva), y el autor juzgó la demo aceptable para firmar con esta limitación concreta y nombrada en vez de un hueco no declarado.

## Decisiones del autor y próximos pasos (registrado para la tesis)

El autor aceptó la Fase 1 como entregada y pidió una fase de seguimiento inmediata, priorizada así (ordenación del propio autor, no el default del agente):

1. **Importación masiva de catálogo + rediseño de interfaz** (primera prioridad)
2. Sistema de login real con usuarios precargados (segunda prioridad)
3. Ordenación/filtrado de catálogo (por plataforma, género, etc.) y filtros de búsqueda (alcance a confirmar durante la planificación de esa fase)
4. Una página de recomendaciones independiente (por género / gusto del usuario)

**Decisión de fuente de datos:** se eligió IGDB sobre RAWG o escalar la tubería Wikidata existente para la importación masiva de catálogo. El autor señaló explícitamente que la cobertura completa de imágenes de portada en todo el catálogo importa y puede entregarse de forma incremental tras la importación inicial, sin bloquear el resto del trabajo de esa fase. Esta decisión, y su justificación, se registra aquí para el log de decisiones de la tesis y se elaborará en el ADR propio de esa fase una vez planificada.

Estas son **mejoras para una fase nueva**, no defectos del alcance propio entregado de la Fase 1 — los cinco criterios de éxito propios de la Fase 1 (arriba) están todos cumplidos por lo que ya existe.

## Limitaciones (declaradas, no ocultadas)

- El catálogo de la demo (150 juegos) y el modelo de cuentas (una cuenta demo) son intencionadamente pequeños, acordes al alcance propio de demo controlada de tres días de la Fase 1; la fase nueva aborda esto directamente.
- El tier gratuito de Render duerme tras 15 minutos de inactividad (documentado en `docs/deployment/public-demo.md`); un visitante puede ver un retardo de arranque en frío de ~1 minuto.
- El reflow al 400% de zoom y una pasada con lector de pantalla siguen siendo ítems abiertos de la checklist manual (ver arriba).
- `docs/methodology/agent-ledger.jsonl` registra una referencia a artefacto histórico genuinamente irrecuperable (un borrador intermedio de `scripts/check-secrets.ps1` de una ejecución de agente distinta que se sobreescribió antes de commitearse) — divulgado honestamente en los campos `unverifiable_inputs`/`limitations` de esa entrada en vez de ocultado o falseado.

---
*Firmado: 2026-09-05*
*Commit: `1af981e1c97f2c46bf07671ad1ec13fe7461bf7a`*
