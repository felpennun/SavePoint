# ADR-005: Paridad mediante imágenes Docker, Compose y PaaS

- **Estado:** Aceptada en local; proveedor público sujeto a checkpoint
- **Fecha:** 2026-09-04
- **Autor de la decisión:** Felipe para la estrategia; alta/coste del proveedor aún requiere autorización explícita.
- **Redacción/evidencia:** agente `gsd-executor`; propuesta asistida revisable.

## Contexto

El tribunal necesita una demo accesible y un entorno local reproducible. Arranque, migraciones, corpus y salud deben coincidir sin descargar datos ni instalar dependencias al iniciar.

## Alternativas consideradas

1. Imágenes multi-stage idénticas, Compose local y PaaS Docker + PostgreSQL gestionado.
2. VPS: más control, pero traslada TLS, parches, backups y monitorización al autor.
3. Platform builds distintos de Docker: reducen configuración, pero debilitan paridad.
4. Kubernetes: coste operativo injustificado para la demo.

## Decisión

Construir `web` y `api` desde Dockerfiles fijados/locks; Compose orquesta `web`, `api`, `db` con healthchecks. El candidato PaaS debe ejecutar las mismas imágenes/commit y PostgreSQL compatible; secretos sólo en runtime. Ninguna creación de recursos o gasto queda autorizada por este ADR. [FUENTES: [Docker Compose](https://docs.docker.com/compose/); [Render Blueprint](https://render.com/docs/blueprint-spec)]

## Evidencia y fuentes

- `infra/compose.yaml`, `apps/api/Dockerfile`, `apps/web/Dockerfile`, locks y `.env.example`.
- Plan 01-11 verificó `docker compose up --build --wait`, healthchecks, import/seed idempotente y ausencia de llamadas externas runtime.
- `scripts/check-secrets.ps1` analiza Git, bundle, imágenes y logs con canaries previos.

## Consecuencias

- Positivas: reconstrucción auditable y menor deriva local/pública; healthchecks sustituyen sleeps.
- Negativas: builds más lentos; diferencias inevitables en TLS, red, almacenamiento y servicio PostgreSQL gestionado.
- Supuesto operativo: coste, región, suspensión, backups y exportación del PaaS son mutables y deben verificarse justo antes del alta.

## Reversibilidad

Las imágenes OCI y `DATABASE_URL` permiten cambiar de PaaS. Exportar PostgreSQL y DNS constituyen la ruta de salida; un cambio de major de PostgreSQL exige prueba de restore.

## Aprobación y revisión

**Estrategia aprobada; despliegue externo pendiente de gate.** La decisión final del proveedor y cualquier coste no se atribuyen al agente.
