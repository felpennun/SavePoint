# Fase 7: Panel de investigación, hardening y congelación de evidencia - Contexto

**Recopilado:** 2026-09-14
**Estado:** Listo para planificación revisada

<domain>
## Límite de la fase

La Fase 7 debe convertir los resultados de recomendación y evaluación en un panel de
investigación reproducible, endurecer la administración y la operación, probar la
recuperación y congelar la evidencia de tesis. La aplicación debe seguir usando
PostgreSQL como fuente transaccional, artefactos offline inmutables y la separación
entre Next.js, Django/DRF y trabajos de investigación.

La fase también debe cerrar el gate de lanzamiento de la aplicación: una instalación
desplegada debe renderizar contenido visible en el navegador, permitir el flujo de
autenticación previsto y demostrar sus rutas críticas. El overhaul visual completo de
todas las superficies queda para después de esta fase.

</domain>

<decisions>
## Decisiones de implementación

### Acceso y alcance del panel

- **D-07-01:** El panel tendrá una ruta independiente `/research`, con variantes
  localizadas `/es/research` y `/en/research`. El enlace se mostrará únicamente a
  usuarios autorizados de investigación.
- **D-07-02:** El panel será privado. Una petición sin sesión se redirigirá al login;
  una cuenta autenticada sin el permiso requerido recibirá una respuesta neutra
  `404`, sin revelar la existencia del panel.
- **D-07-03:** La autorización se basará en permisos y grupos de Django, no en una
  comprobación del frontend. El grupo `Research Viewer` podrá consultar y exportar;
  inicialmente solo la cuenta responsable del TFG pertenecerá a él. Las cuentas demo
  y los usuarios registrados no se incorporarán automáticamente.
- **D-07-04:** El grupo `Research Viewer` no podrá modificar ni relanzar evaluaciones.
  El panel solo leerá resultados congelados y expondrá exportaciones saneadas.

### Administración y control de cambios

- **D-07-05:** Habrá dos niveles separados: `Research Viewer` para lectura/exportación
  del panel y `Platform Admin` para usuarios, catálogo, imports y jobs. La cuenta del
  autor podrá pertenecer a ambos grupos.
- **D-07-06:** Las operaciones administrativas se realizarán mediante Django Admin;
  no se construirá una segunda interfaz administrativa en Next.js en esta fase.
- **D-07-07:** La desactivación o anonimización será la operación normal para usuarios
  y datos sensibles. El borrado irreversible quedará reservado a una operación segura
  de superusuario y deberá quedar auditado.
- **D-07-08:** La auditoría será append-only y saneada: actor, acción, recurso,
  instante, resultado y referencia de operación. Nunca almacenará contraseñas,
  tokens, cookies ni payloads sensibles.
- **D-07-09:** La fase se diseña con coste recurrente cero: sin upgrades automáticos,
  tarjeta ni nuevos servicios de pago. La arquitectura debe poder migrar más adelante
  a recursos de pago sin cambiar los contratos de aplicación.

### Backups y recuperación

- **D-07-10:** La recuperación incluirá un volcado de PostgreSQL, manifiestos y
  artefactos saneados versionados. Los secretos no se respaldarán; se regenerarán en
  el entorno de destino.
- **D-07-11:** Se generará un backup automático diario y otro manual antes de
  migraciones, imports, despliegues o cambios de configuración importantes.
- **D-07-12:** Se conservarán siete copias diarias y cuatro semanales. Los dumps de
  base de datos serán privados; solo los artefactos saneados podrán formar parte de
  releases o del repositorio cuando sea lícito y necesario.
- **D-07-13:** Una vez al mes se restaurará una copia en una base de datos desechable,
  verificando checksums, migraciones, recuentos esenciales y un smoke test de la
  aplicación.

### Panel y evidencia final

- **D-07-14:** El panel presentará una comparativa interactiva con filtros por
  ejecución, algoritmo y cohorte, detalle de métricas, tiempos, parámetros,
  procedencia y limitaciones, y enlaces de descarga.
- **D-07-15:** Cada comparación combinará gráficos con tablas accesibles y
  exportables para que los resultados sean comprensibles y auditables con teclado o
  lector de pantalla.
- **D-07-16:** El paquete final de evidencia será versionado y reproducible e incluirá
  ejecución, commit, corpus, protocolo, semillas, configuración, métricas, tiempos,
  entorno, hashes, limitaciones, procedencia y contribución de agentes.
- **D-07-17:** El cierre de fase queda bloqueado hasta superar un gate completo:
  backend, frontend, autorización del panel, navegador visible, autenticación,
  accesibilidad, responsive, backups/restauración, dependencias, secretos, health
  checks y evidencia final.

### Criterio económico operativo

- El tier gratuito se acepta para la demo académica y una web pequeña, asumiendo
  arranque en frío, límites de almacenamiento/cómputo y ausencia de SLA. No se
  presentará como producción de alta disponibilidad.
- Los trabajos pesados de evaluación seguirán fuera de las peticiones HTTP. No se
  añadirá infraestructura nueva para ocultar los límites del tier gratuito.
- El tamaño real de PostgreSQL se medirá después de importar el catálogo completo;
  el tamaño del dump comprimido no se tratará como sustituto de esa medición.

### Decisiones ya heredadas

- La privacidad server-side, los DTOs allowlisted, el proxy same-origin, el contrato
  de PostgreSQL, la procedencia local y los snapshots congelados de la Fase 6 son
  precondiciones.
- No se relanzará el split de evaluación consumido ni se modificarán snapshots
  científicos congelados.
- El overhaul visual completo de catálogo, colección, perfiles, social,
  recomendaciones y panel se planificará después de esta fase; aquí solo se exige la
  funcionalidad visible, accesible y verificable necesaria para el gate.

### Decisiones que quedan a criterio del agente

- La librería concreta de gráficos, siempre que las tablas sean equivalentes y
  accesibles, los valores subyacentes sean exportables y no se conviertan en la fuente
  académica primaria.
- El formato exacto del paquete saneado y la herramienta de rotación de backups,
  siempre que respeten las retenciones, los checksums y la ausencia de secretos.
- La forma concreta de representar permisos Django en código, siempre que el backend
  imponga los grupos/permisos y las pruebas cubran acceso permitido y denegado.

</decisions>

<canonical_refs>
## Referencias canónicas

**Los agentes posteriores deben leer estas referencias antes de planificar o implementar.**

### Alcance, requisitos y estado

- `.planning/ROADMAP.md` — objetivo, criterios de éxito y requisitos de la Fase 7.
- `.planning/REQUIREMENTS.md` — requisitos EVAL-13, EVAL-14, ADMIN-01, ADMIN-02,
  SEC-01, SEC-03 a SEC-08, PRIV-02, OPS-04, OPS-05, QUAL-01, QUAL-04, DOC-05,
  DOC-06, AGENT-05, AGENT-06, PORT-02 y PORT-03.
- `.planning/PROJECT.md` — límites de v1, reproducibilidad, audiencia controlada y
  restricciones de arquitectura.
- `.planning/STATE.md` — decisiones acumuladas, limitaciones de Fase 6 y estado de
  transición a la Fase 7.
- `CONVENTIONS.md` — idioma, trazabilidad, seguridad, issues y sincronización del
  vault.
- `ideas-vault/README.md` — política de mantenimiento y contenido permitido del vault.

### Decisiones y evidencia de fases anteriores

- `.planning/phases/06-public-discovery-and-resilient-enrichment/06-CONTEXT.md` —
  privacidad social, perfiles, listas, comentarios, filtros y límites heredados.
- `.planning/phases/06-public-discovery-and-resilient-enrichment/06-VERIFICATION.md` —
  cobertura de Fase 6, limitaciones browser y gate pendiente de demostración.
- `docs/verification/phase-06-signoff.md` — firma, evidencia y limitaciones de la
  verificación de Fase 6.
- `docs/deployment/public-demo.md` — topología gratuita aprobada, contratos de
  despliegue, secretos y limitaciones de proveedores.
- `.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-RESEARCH.md` —
  investigación local y restricciones para el panel, hardening y evidencia.
- `.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-PATTERNS.md` —
  patrones de implementación identificados para la fase.

### Arquitectura y código reutilizable

- `.planning/codebase/ARCHITECTURE.md` — separación de capas, sesiones, API y flujo
  offline.
- `.planning/codebase/STACK.md` — versiones fijadas y herramientas aprobadas.
- `.planning/codebase/CONVENTIONS.md` — nombres, validación y protección de datos.
- `.planning/codebase/CONCERNS.md` — riesgos conocidos de seguridad, despliegue y
  verificación.
- `.planning/codebase/STRUCTURE.md` — ubicación de rutas, aplicaciones, componentes y
  tests.
- `apps/api/config/settings.py` — configuración de sesiones, seguridad y PostgreSQL.
- `apps/api/config/urls.py` — integración de rutas API.
- `apps/web/middleware.ts` — localización, protección de rutas y redirección al login.
- `apps/web/next.config.ts` — proxy same-origin, rewrites y cabeceras de seguridad.
- `apps/web/components/AppShell.tsx` — navegación y punto de integración del enlace
  staff.
- `apps/web/lib/api.ts` y `apps/web/lib/client-api.ts` — fetch SSR, sesión, proxy y
  CSRF.
- `apps/api/accounts/` — usuarios, sesiones, permisos y proyecciones allowlisted.
- `apps/api/evaluation/` — protocolo, ejecuciones, métricas y artefactos offline.
- `apps/web/app/[locale]/` — rutas localizadas y superficies de aplicación existentes.

</canonical_refs>

<code_context>
## Contexto del código existente

### Activos reutilizables

- `apps/api/evaluation/` y sus artefactos versionados ya contienen el protocolo,
  métricas, algoritmos, ejecuciones y procedencia que el panel debe leer sin mutar.
- `apps/api/accounts/` ya usa autenticación de Django y proyecciones explícitas; sus
  patrones sirven para permisos, respuestas neutras y ausencia de filtrado.
- `apps/web/AppShell.tsx`, `AccountSwitcher.tsx` y el middleware existente permiten
  integrar el enlace staff sin exponerlo a usuarios normales.
- Las suites pytest, Vitest y Playwright existentes ofrecen la base para los gates de
  autorización, navegador, responsive y accesibilidad.
- `infra/compose.yaml`, los scripts de verificación y los dumps existentes permiten
  probar restauraciones localmente sin contratar servicios adicionales.

### Patrones establecidos

- El backend es la autoridad de identidad, permisos y privacidad; el middleware y la
  UI solo mejoran la navegación y no sustituyen la autorización.
- PostgreSQL es la fuente transaccional; no se añade otro almacén como fuente de
  verdad para panel, auditoría o backups.
- Los experimentos se ejecutan offline y los resultados publicados son inmutables,
  versionados y recalculables a partir de sus metadatos.
- Las respuestas públicas y administrativas deben construirse con allowlists y no
  incluir secretos, datos privados ni logs sin sanear.
- Las pruebas de navegador deben atravesar el stack real cuando el gate afirma que la
  aplicación es utilizable; una suite que solo compile no cierra el gate visual.

### Puntos de integración

- La ruta Next.js `/[locale]/research` debe consultar endpoints Django protegidos por
  el permiso de investigación.
- Django Admin debe exponer los modelos administrativos con permisos separados y
  auditoría saneada.
- El pipeline de backup debe conectarse a PostgreSQL, artefactos versionados,
  checksums y un entorno desechable de restauración.
- El gate final debe unir health check, login, rutas públicas, panel staff, pruebas de
  privacidad, exportación saneada, responsive y accesibilidad.

</code_context>

<specifics>
## Detalles específicos

- El autor quiere mantener el coste recurrente en cero y no introducir tarjeta ni
  upgrades automáticos.
- La cuenta del autor será la primera cuenta seleccionada para `Research Viewer` y
  `Platform Admin`; los usuarios demo no recibirán privilegios de investigación.
- El panel no relanzará evaluaciones: leerá y exportará únicamente resultados
  saneados.
- El navegador no puede mostrar una pantalla vacía. Esa comprobación es un requisito
  explícito de cierre, no una mejora cosmética opcional.

</specifics>

<deferred>
## Ideas diferidas

- Overhaul visual completo de todas las superficies después de terminar la Fase 7.
- Interfaz administrativa propia en Next.js; Django Admin será suficiente para esta
  fase.
- Automatización de upgrades de proveedores o contratación de almacenamiento de pago;
  se revisará solo cuando las métricas de uso demuestren que el tier gratuito no basta.

</deferred>

---

*Fase: 07-Panel de investigación, hardening y congelación de evidencia*
*Contexto recopilado: 2026-09-14*
