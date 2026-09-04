# Handoff técnico — Fase 01

**Estado:** planificación aprobada; lista para `$gsd-execute-phase 1`  
**Fecha:** 2026-09-04  
**Rama:** conservar la rama actual; no crear ni cambiar ramas durante el flujo GSD.

## Objetivo

Entregar en tres días una demo pública y reproducible de SavePoint: login controlado, catálogo legal local, ficha con procedencia, backlog, rating en medias estrellas, múltiples copias, perfil público allowlisted y baseline determinista de popularidad. El mismo commit debe arrancar offline mediante Docker Compose y no debe exponer secretos.

## Fuentes de verdad que debe leer otra LLM

1. `AGENTS.md` — restricciones técnicas y de seguridad del proyecto.
2. `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md` y `STATE.md` — alcance y estado.
3. `01-CONTEXT.md` — veinte decisiones cerradas del usuario (`D-01`–`D-20`).
4. `01-UI-SPEC.md` — contrato visual y de interacción aprobado.
5. `01-RESEARCH.md` — arquitectura, dataset/licencias, seguridad, despliegue y validación.
6. `01-VALIDATION.md` — estrategia Nyquist y mapa de pruebas.
7. `01-PATTERNS.md` — repositorio greenfield; 0 análogos de código existentes.
8. `01-SKELETON.md` — contrato del walking skeleton.
9. `01-COVERAGE.md` — cobertura de adquisición offline Wikidata/Commons; ninguna API externa en runtime.
10. `01-SOURCE-AUDIT.md` — trazabilidad de requisitos, decisiones y fuentes.
11. `01-01-PLAN.md`…`01-16-PLAN.md` — contrato ejecutable en 12 olas.

## Decisiones arquitectónicas vigentes

- Next.js/React/TypeScript para web; Django/DRF/Python 3.13 para API; PostgreSQL como único camino canónico, incluso en integración.
- Monolito modular con frontera browser→same-origin→API y autenticación por sesión/CSRF.
- Identidad primaria generalizada `GameWork → GameRelease/Platform/Edition → OwnedCopy`; DLC ligado al juego base, no backlog independiente.
- Snapshot curado y citable de Wikidata CC0; cada asset de Commons se aprueba y atribuye individualmente; placeholder para lo no aprobado.
- Búsqueda local tolerante; interfaz ES/EN según usuario; rating almacenado exactamente en half-steps.
- Baseline de popularidad determinista, versionado y alimentado por interacciones demo con cutoff y digest.
- Render Blueprint es el objetivo inicial, con checkpoint humano y alternativa PaaS sin alterar el contrato Docker/Compose.

## Gates humanos bloqueantes

- Antes de instalar: verificar nombres oficiales, registro, mantenedores/enlaces, versiones compatibles y lockfiles de cada dependencia.
- Antes de importar: firmar `APPROVED` para corpus y allowlist/licencias de carátulas.
- Antes del login E2E: suministrar/rotar credenciales demo sólo en runtime; nunca escribirlas en Git, logs o artefactos.
- Antes del smoke público: autorizar/provisionar el PaaS, registrar URL HTTPS, host y commit, y exigir smoke verde.

## Historial de revisión

- Revisión inicial: 7 bloqueadores y 2 avisos (scaffold, migraciones, endpoints, despliegue y tamaño de planes).
- Revisión 1: bloqueadores anteriores resueltos; quedaron persistencia de rating/copias, seed y cuatro planes sobredimensionados.
- Revisión 2: se dividió a 14 planes; quedó el orden temporal del seed y una auditoría obsoleta.
- Revisión final: 16 planes. `01-15` crea la cuenta runtime antes del login; `01-16` carga interacciones después del dominio y antes de perfil/popularidad. Auditoría regenerada.
- Veredicto independiente final: `## VERIFICATION PASSED`.

## Evidencia determinista al cerrar planificación

- Requisitos de Fase 1: 23/23 cubiertos.
- Decisiones de contexto: 20/20 cubiertas.
- Planes: 16 en 12 olas; dependencias acíclicas y sin conflictos de archivos en la misma ola.
- Verificaciones declaradas: 37 comandos; 0 bloqueadores y 0 avisos de dirección de fallo.
- Cada plan incluye `threat_model` ASVS L1, bloqueo de amenazas high, `must_haves`, artefactos producidos y tareas con `read_first`, acción concreta, aceptación y verificación.

## Reanudación de bajo consumo

Ejecutar `$gsd-execute-phase 1`. No volver a investigar ni replanificar salvo que un gate falle. Cargar sólo el PLAN de la ola activa y sus dependencias directas; usar este handoff y `STATE.md` como índice. Tras cada ola, registrar resultados, hashes, decisiones humanas y limitaciones sin copiar secretos ni conversaciones completas.
