---
tags: [fase-05, autenticacion, seguridad, decision]
estado: decision-aceptada
fecha: 2026-09-12
---

# Autenticación real como requisito de Fase 5

Felipe ha fijado que la Fase 5 no puede depender únicamente de cuentas demo
sembradas. Debe existir un flujo real de registro e inicio de sesión con:

- usuarios persistidos en PostgreSQL;
- contraseñas hasheadas y validación de fortaleza;
- sesiones protegidas y CSRF;
- autorización owner-scoped para colección, comentarios, listas, favoritos,
  copias y exportaciones;
- respuestas que no permitan enumerar usuarios;
- limitación de intentos abusivos;
- pruebas backend y de navegador del registro, login, persistencia y acceso
  denegado.

El nombre de usuario coincide con el alias público y no es editable. Las cuentas
sintéticas siguen siendo fixtures de demostración separadas de las cuentas
creadas por usuarios reales.

Fuente canónica: [[../../.planning/phases/05-complete-collection-workflows-and-portability/05-CONTEXT|Contexto de Fase 5]].
