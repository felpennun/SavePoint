# ADR-005: Compose local y demo pública gratuita dividida

- **Estado:** Aceptada; provisión sujeta a sesión humana
- **Fecha:** 2026-09-04
- **Autor de la decisión:** Felipe; topología pública aprobada sin tarjeta ni recursos de pago.
- **Redacción/evidencia:** agente `gsd-executor`; propuesta asistida revisable.

## Contexto

El tribunal necesita una demo accesible y un entorno local reproducible. La restricción añadida de coste cero y ausencia de tarjeta impide usar un único PaaS con predeploy y las dos imágenes Docker.

## Alternativas consideradas

1. Compose local con ambas imágenes; Vercel Hobby para Next.js, Render Free para la imagen API y Neon Free para PostgreSQL.
2. Un solo PaaS de pago para ambas imágenes y PostgreSQL: mayor paridad binaria y predeploy, rechazado por coste/tarjeta.
3. VPS: más control, pero traslada TLS, parches, backups y monitorización al autor.
4. Kubernetes: coste operativo injustificado para la demo.

## Decisión

Compose sigue construyendo `web` y `api` desde Dockerfiles y orquesta PostgreSQL con healthchecks. La demo pública usa Vercel Hobby para el workspace Next.js, Render Free para `apps/api/Dockerfile` y Neon Free para PostgreSQL. Vercel hace proxy same-origin a Render. La equivalencia es funcional, de versiones, commit y datos; el frontend público no usa su imagen Docker. No se introducirá tarjeta ni se habilitará ningún recurso de pago. [FUENTES: [Docker Compose](https://docs.docker.com/compose/); [Render Free](https://render.com/docs/free); [Vercel Hobby](https://vercel.com/docs/plans/hobby); [Neon plans](https://neon.com/docs/introduction/plans)]

## Evidencia y fuentes

- `infra/compose.yaml`, `infra/render.yaml`, `apps/api/Dockerfile`, `apps/web/vercel.json`, `neon.ts`, locks y `.env.example`.
- Neon project `autumn-breeze-06234770`, branch `production`: enlazado y reconciliado mediante `neon deploy` sin diferencias; `.neon` y `.env.local` permanecen locales e ignorados.
- `neon.ts` declara `auth: true` como política de infraestructura ya presente; SavePoint conserva autenticación Django y no integra Neon Auth en esta fase.
- Plan 01-11 verificó Compose, healthchecks, import/seed idempotente y ausencia de llamadas externas runtime.
- `scripts/check-secrets.ps1` analiza Git, bundle, imágenes, logs y fuentes de despliegue con canarios previos.

## Consecuencias

- Positivas: coste cero sin tarjeta; sesión browser same-origin; API sigue usando su imagen y corpus offline.
- Negativas: el frontend público no es la misma imagen; Render duerme tras inactividad y carece de predeploy gratis; los tres proveedores tienen cuotas/suspensión mutables.
- Supuesto operativo: límites, región, retención, backups y exportación deben verificarse justo antes del alta; Compose es el fallback canónico.

## Reversibilidad

La imagen API, el workspace Next.js y `DATABASE_URL` permiten cambiar de proveedor. El rollback público debe fijar el mismo commit en Vercel y Render. Exportar PostgreSQL cuando el plan lo permita constituye la ruta de salida; nunca se presume que Free incluya restore o backups.

## Aprobación y revisión

**Topología aprobada; alta externa pendiente de sesión humana.** La autorización excluye expresamente introducir una tarjeta o activar recursos de pago.
