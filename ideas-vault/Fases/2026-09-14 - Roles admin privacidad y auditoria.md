---
fecha: 2026-09-14
estado: aceptada
fuente: .planning/phases/07-research-panel-hardening-and-evidence-freeze/07-02-SUMMARY.md
---

# Roles, administración y privacidad de la fase 07

La administración operativa queda separada del panel de investigación: `Research Viewer`
concede únicamente lectura/exportación publicada y `Platform Admin` concede acceso a un
Django Admin allowlisted. El acceso administrativo se decide exclusivamente en servidor con
`evaluation.access_platform_admin`; no depende de `is_staff`, cookies, nombres ni rutas del
cliente Next.js.

La provisión de roles requiere UUID técnico explícito de cuenta y no se asigna por defecto a
cuentas demo o registradas. La operación normal es desactivar y anonimizar de forma
transaccional e idempotente. El borrado irreversible queda reservado a un superusuario, exige
confirmación exacta y registra primero un evento de auditoría.

`AuditEvent` solo acepta acciones, tipos, resultados y referencias opacas allowlisted. Un
trigger PostgreSQL rechaza actualizaciones y borrados, por lo que el historial es append-only.
Los ModelAdmin de auditoría, jobs, snapshots y metadatos experimentales son de solo lectura.

## Fuentes relacionadas

- [[../Conceptos/Vault vivo y sincronizacion]]
- [[../../.planning/phases/07-research-panel-hardening-and-evidence-freeze/07-02-PLAN]]
- [[../../docs/verification/phase-07-admin-security]]
