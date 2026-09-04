# ADR-001: Monolito modular Django con frontend Next.js

- **Estado:** Aceptada para Phase 1
- **Fecha:** 2026-09-04
- **Autor de la decisión:** Felipe (aprobación de dependencias y ejecución de la fase)
- **Redacción/evidencia:** agente `gsd-executor`; su texto es propuesta asistida y queda sujeto a revisión del autor del TFG.

## Contexto

SavePoint necesita en tres días un recorrido público completo y, después, una plataforma reproducible de experimentos. El dominio es relacional y CRUD-heavy, mientras que los perfiles públicos y la UI requieren renderizado web accesible. [EVIDENCIA: `.planning/PROJECT.md`; `.planning/phases/01-three-day-public-demo-slice/01-SKELETON.md`]

## Alternativas consideradas

1. Django + DRF como monolito modular y Next.js como frontend separado.
2. FastAPI + SQLAlchemy: menor armazón inicial, pero obliga a componer autenticación, administración, validación y migraciones.
3. Django templates + HTMX: reduce duplicación de contratos, pero ofrece una base menos natural para el panel experimental rico previsto.
4. Microservicios: descartados por coste operativo y de trazabilidad para un proyecto individual.

## Decisión

Usar un monolito modular Django/DRF para identidad, reglas y persistencia, con un frontend Next.js/TypeScript. Los módulos se separan por dominio (`accounts`, `catalogue`, `library`) pero comparten despliegue y PostgreSQL. Los algoritmos futuros se ejecutan como jobs explícitos, nunca dentro de peticiones HTTP. [DECISIÓN HUMANA: conjunto tecnológico autorizado en `docs/verification/dependency-legitimacy.md`]

## Evidencia y fuentes

- Implementación: `apps/api/config/urls.py`, `apps/api/accounts`, `apps/api/catalogue`, `apps/api/library`, `apps/web/app`.
- Versiones, procedencia y aprobación: `docs/verification/dependency-legitimacy.md`, `uv.lock`, `pnpm-lock.yaml`.
- [Django authentication](https://docs.djangoproject.com/en/5.2/topics/auth/default/) y [Next.js App Router](https://nextjs.org/docs/app).

## Consecuencias

- Positivas: integridad y autenticación maduras; límites de dominio legibles; UI SSR; dos runtimes pero una arquitectura operable.
- Negativas: contrato API y tipos pueden divergir; dos builds y dos imágenes; no hay aislamiento independiente por servicio de dominio.
- Limitación: Phase 1 prueba un slice de demo, no escalabilidad ni suficiencia del diseño para el estudio completo.

## Reversibilidad

Los límites de dominio y la API permiten sustituir Next.js por templates/HTMX sin migrar datos. Extraer un servicio sólo se considerará tras medir una necesidad; las migraciones Django y contratos HTTP son el seam de salida.

## Aprobación y revisión

**Aprobada para Phase 1.** Supuesto marcado: estos cinco ADR cubren las decisiones materiales de la fase; el autor debe confirmar en la revisión final del TFG si existe otra decisión que merezca ADR propio.
