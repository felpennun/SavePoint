---
tags: [requisitos, tema/seguridad]
---

# Requisitos - Administracion, privacidad y seguridad

- **ADMIN-01/02** (Fase 7): gestionar usuarios y catalogo de demo; supervisar
  imports, jobs y experimentos sin editar la base directamente.
- **SEC-01..08** (Fase 7, salvo SEC-02): permisos por rol/propiedad; inyeccion SQL;
  XSS/CSRF/contenido malicioso; SSRF y redirects; rate-limit, cabeceras y errores;
  pipeline que escanea secretos y dependencias; eventos de auditoria sin credenciales.
- **SEC-02** (Fase 1, hecho): ningun secreto en Git, bundles, logs, imagenes o artefactos.
- **PRIV-01** (Fase 5): allowlist explicita de campos en proyecciones publicas.
- **PRIV-02** (Fase 7): cuenta controlada borrable o anonimizable.

## Enlaces

- [[Allowlist de campos publicos]] · [[Frontera de sesion same-origin]]
- [[Control contra exposicion de informacion]] · [[Fase 7 - Panel de investigacion y hardening]]
