---
tags: [concepto, tema/arquitectura]
---

# Contenedores y CI

uv + `pyproject.toml` + `uv.lock` para Python; pnpm + `pnpm-lock.yaml` para
frontend; Docker Engine + Compose v2 (servicios `web`, `api`, `db`, `mlflow`
opcional, mas un runner de experimentos de un solo uso); Dockerfiles multi-stage;
GitHub Actions ejecuta tests de backend contra PostgreSQL, tests de frontend,
generacion/diff de esquema, builds de contenedor, smoke de Playwright y checks de
integridad de locks. Imagenes y dependencias siempre fijadas, nunca `latest`.

## Enlaces

- [[Paridad de despliegue]] · [[Reproducibilidad academica]] · [[Testing y calidad]]
- [[ADR-005 - Paridad de despliegue gratuito]]
