# Legitimidad de dependencias: Next.js 16.3.4 → 16.3.8 (2026-10-06)

Anexo fechado a [`dependency-legitimacy.md`](dependency-legitimacy.md), que no se modifica porque su hash está fijado en el registro de evidencia.

## Cambio

| Paquete | Antes | Ahora | Dónde |
|---|---|---|---|
| Next.js | 16.3.4 | 16.3.8 | `catalog:` de `pnpm-workspace.yaml` (resuelto en `pnpm-lock.yaml`) |

El salto lo hizo el commit `e8b6d25` («patch vulnerable web and python dependencies», 2026-10-06) para cerrar vulnerabilidades en la versión anterior. Ese commit no actualizó la lista de versiones aprobadas de `scripts/check-dependencies.ps1`, y la pasarela del CI (`quality-gates.yml`) falló en todos los commits posteriores con `npm dependency is not exactly approved: next@catalog:`.

## Decisión

- **Alcance:** únicamente el salto exacto `16.3.4` → `16.3.8` dentro del major 16. No se añade ningún paquete directo ni ningún override.
- **Aprobación:** el autor pidió alinear la pasarela con las versiones realmente instaladas el 2026-10-06. La aprobación humana de la versión es esa petición; este documento deja constancia de ella y no sustituye la revisión del autor.
- **Cambio en el repositorio:** `scripts/check-dependencies.ps1` aprueba ahora `next` = `16.3.8`.

## Comprobación

- `pnpm-lock.yaml` resuelve `next` a `16.3.8` con el especificador `'catalog:'`.
- `scripts/check-dependencies.ps1` termina con «Dependency allowlist and immutable OCI references validated.».
