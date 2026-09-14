# Verificación de administración, privacidad y auditoría de la Fase 7

## Alcance

Esta evidencia registra el hardening backend de 07-02. Django Admin es la única
superficie administrativa; Next.js no concede ni presenta operaciones de plataforma.

## Autoridad y roles

- Research Viewer recibe evaluation.view_research_panel y
  evaluation.export_research_panel.
- Platform Admin recibe únicamente evaluation.access_platform_admin.
- /admin/ evalúa la capability con request.user.has_perm en una sesión Django.
  is_staff, cookies, nombres y afirmaciones del frontend no participan en la decisión.
- bootstrap_phase7_roles exige UUIDs opacos explícitos de AccountProfile y es
  idempotente. Las cuentas demo y registradas no se incorporan automáticamente.

## ModelAdmin allowlisted

Se registran de forma explícita usuarios/demo, perfiles, obras/releases/ediciones,
metadatos de catálogo, biblioteca controlada, imports, snapshots y jobs. Los imports,
snapshots, vectores, estados derivados y eventos de auditoría son readonly; no existe
una acción de re-run en el panel.

## Privacidad y auditoría

La operación normal anonymize_account se ejecuta en una transacción, desactiva el
usuario, limpia alias, email, nombre, bio y avatar, y revoca sus grupos/permisos. Es
idempotente y conserva únicamente admin_uuid como localizador técnico opaco.

delete_account_irreversibly exige is_superuser y la confirmación exacta DELETE ACCOUNT;
registra el evento antes de borrar y bloquea el borrado de la cuenta activa del operador.
AuditEvent no tiene payload libre, valida valores allowlisted y PostgreSQL rechaza UPDATE
y DELETE mediante trigger.

## Gates ejecutados

    manage.py check                                      PASS
    makemigrations --check --dry-run                    PASS
    pytest audit + phase7 admin security                 PASS
    check-security.ps1                                   PASS (con stack Docker disponible)
    manage.py check --deploy                             PASS
    git diff --check                                     PASS

La suite prueba separación de roles, sesión/CSRF, ausencia de autoasignación, replay de
anonimización, confirmación de borrado, saneamiento y mutación directa del historial.
Los locks y escáneres de secretos se ejecutan desde quality-gates.yml sin añadir
dependencias ni servicios de pago.

## Trazabilidad

ADMIN-01, ADMIN-02, SEC-01, SEC-04, SEC-06, SEC-07, SEC-08, PRIV-02 y OPS-05.

