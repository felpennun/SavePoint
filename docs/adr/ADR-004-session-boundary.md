# ADR-004: Sesión Django y frontera same-origin

- **Estado:** Aceptada para la demo controlada
- **Fecha:** 2026-09-04
- **Autor de la decisión:** Felipe
- **Redacción/evidencia:** agente `gsd-executor`; propuesta asistida revisable.

## Contexto

El navegador necesita autenticar mutaciones sin exponer credenciales ni tokens propios. Next.js sirve la UI y Django controla identidad/permisos. [EVIDENCIA: `apps/api/accounts/views.py`, `apps/web/next.config.ts`]

## Alternativas consideradas

1. Sesión/cookie Django y proxy same-origin de `/api`.
2. JWT en almacenamiento del navegador: amplía gestión de emisión, rotación, revocación y riesgo XSS.
3. CORS con credenciales entre orígenes: más configuración y superficie CSRF.
4. Autenticación externa/OIDC: adecuada a futuro, excesiva para cuentas sintéticas controladas.

## Decisión

Django emite y valida la sesión; el navegador sólo llama rutas same-origin de Next.js, que las reescribe al API. Las mutaciones requieren token CSRF, las cookies se envían con `credentials: same-origin`, logout invalida la sesión y los redirects sólo aceptan paths relativos. [FUENTE: [Django CSRF](https://docs.djangoproject.com/en/5.2/ref/csrf/)]

## Evidencia y fuentes

- `apps/web/next.config.ts`, `apps/web/components/LibraryControls.tsx`, `apps/web/app/[locale]/login/page.tsx`.
- `apps/api/accounts/tests/test_auth.py` cubre login, CSRF y logout.
- `e2e/demo-journey.spec.ts` prueba el recorrido en el stack real.
- Plan 01-04 corrigió redirect loop, origen CSRF y fuga de credenciales por submit nativo antes de aceptar el tracer.

## Consecuencias

- Positivas: primitivas mantenidas por Django; ningún bearer token accesible a JS; frontera sencilla.
- Negativas: afinidad al dominio/cookie y configuración cuidadosa tras proxy/TLS; escalado requiere session store compartido.
- Limitación: cuentas controladas y todos los perfiles públicos; no se afirma que sea el diseño final para registro abierto.

## Reversibilidad

La API puede adoptar OIDC/token de corta vida en una fase posterior manteniendo DTO y dominio. El cambio requeriría ADR, migración y nuevas pruebas de amenaza.

## Aprobación y revisión

**Aprobada para Phase 1.** Reabrir antes de permitir registro público, múltiples dominios o clientes nativos.
