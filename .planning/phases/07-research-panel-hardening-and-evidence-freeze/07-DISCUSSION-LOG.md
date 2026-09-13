# Fase 7: Panel de investigación, hardening y congelación de evidencia - Registro de discusión

> **Solo trazabilidad.** Este documento conserva las alternativas consideradas. Las
> decisiones que deben usar los agentes están en `07-CONTEXT.md`.

**Fecha:** 2026-09-14
**Fase:** 07-panel de investigación, hardening y congelación de evidencia
**Áreas discutidas:** visibilidad del panel, administración y roles, backups y recuperación, cierre y evidencia final

---

## Visibilidad del panel

| Opción | Descripción | Seleccionada |
|---|---|---|
| Protegido para administradores/staff | Solo cuentas autorizadas consultan ejecuciones, artefactos y métricas. | ✓ |
| Público en lectura | Cualquier visitante consulta resultados y comparativas. | |
| Mixto | Resumen público y detalle protegido. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Ruta independiente `/research` | Enlace visible solo para staff. | ✓ |
| Menú de perfil/administración | Acceso más oculto dentro del menú. | |
| Ambos | Navegación y menú administrativo. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Grupo y permiso específico | Django decide el acceso; inicialmente se selecciona la cuenta del autor. | ✓ |
| `is_staff` general | Cualquier cuenta staff obtiene acceso. | |
| Rol personalizado | Campo o sistema propio de roles. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Consultar y exportar | Sin modificar ni relanzar evaluaciones. | ✓ |
| Consultar, exportar y relanzar | Permite iniciar nuevas evaluaciones desde el panel. | |
| Control completo | También modifica administración y datos. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Resumen y artefactos saneados | Métricas, parámetros, versiones, hashes y limitaciones sin secretos. | ✓ |
| Todo el contenido interno | Incluye logs técnicos completos. | |
| Solo informes legibles | PDF/HTML o tablas sin artefactos estructurados. | |

**Elección del autor:** panel privado, ruta independiente, permiso Django específico,
lectura/exportación y artefactos saneados.

**Aclaración:** sin sesión se usará el flujo de login; con sesión pero sin permiso se
recomienda una respuesta neutra `404`.

---

## Administración y roles

| Opción | Descripción | Seleccionada |
|---|---|---|
| Dos niveles separados | `Research Viewer` y `Platform Admin`; el autor puede pertenecer a ambos. | ✓ |
| Un único grupo staff | El mismo grupo consulta y administra. | |
| Solo superusuario | Una cuenta global controla todo. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Django Admin + `/research` separado | Gestión madura y panel académico independiente. | ✓ |
| Interfaz administrativa propia | Next.js concentra también la administración. | |
| Ambos | Dos interfaces para las mismas operaciones. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Anonimización/desactivación por defecto | El borrado irreversible queda restringido y auditado. | ✓ |
| Borrado desde Admin | Eliminación con confirmación dentro del panel. | |
| No permitir borrados | Solo desactivar o retirar registros. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Auditoría append-only saneada | Actor, acción, recurso, fecha, resultado y referencia; sin secretos. | ✓ |
| Registro HTTP completo | Conserva cada petición técnica. | |
| Solo errores/cambios críticos | No audita operaciones normales. | |

**Elección del autor:** roles separados, Django Admin, operaciones reversibles por
defecto y auditoría append-only sin datos sensibles.

**Restricción adicional:** coste recurrente cero, sin tarjeta ni upgrades automáticos;
la arquitectura debe quedar preparada para escalar posteriormente.

---

## Backups y recuperación

| Opción | Descripción | Seleccionada |
|---|---|---|
| PostgreSQL + artefactos versionados | Dumps privados y manifiestos/artefactos saneados versionados. | ✓ |
| Solo snapshots del proveedor | Dependencia completa del proveedor de base de datos. | |
| Paquete completo externo | Configuración y datos en almacenamiento separado de pago potencial. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Diario + antes de cambios | Backup diario y copia previa a migraciones, imports o despliegues. | ✓ |
| Semanal + antes de cambios | Menos consumo, mayor pérdida potencial. | |
| Solo manual | Sin automatización. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| 7 diarias + 4 semanales | Dumps privados; artefactos saneados publicables cuando proceda. | ✓ |
| 3 más recientes | Retención histórica reducida. | |
| Indefinida | Mayor trazabilidad y mayor retención de datos personales. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Restauración mensual completa | Entorno desechable, checksums, migraciones, recuentos y smoke test. | ✓ |
| Verificar solo generación | Comprueba que el archivo se crea. | |
| Restaurar solo ante incidencia | No prueba la recuperación de forma preventiva. | |

**Elección del autor:** backup diario, copia previa a cambios críticos, retención 7+4
y restauración mensual comprobada.

---

## Cierre y evidencia final

| Opción | Descripción | Seleccionada |
|---|---|---|
| Comparativa interactiva | Filtros por ejecución/algoritmo/cohorte, detalle y descargas. | ✓ |
| Informe-resumen único | Página fija con conclusiones y enlaces. | |
| Explorador técnico | Prioriza tablas y artefactos sin tanta interpretación. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Gráficos + tablas accesibles | Comparación visual y lectura/exportación auditable. | ✓ |
| Solo tablas | Máxima simplicidad numérica. | |
| Principalmente gráficos | Más visual, pero menos auditable sin tablas. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Paquete versionado reproducible | Incluye ejecución, commit, corpus, protocolo, semillas, entorno, hashes, limitaciones, procedencia y agentes. | ✓ |
| Solo métricas y conclusiones | Evidencia resumida. | |
| Logs y datos internos sin filtrar | Máximo detalle, con riesgo de exposición. | |

| Opción | Descripción | Seleccionada |
|---|---|---|
| Gate completo de lanzamiento | Backend, frontend, navegador, auth, permisos, accesibilidad, responsive, backups, seguridad, health y evidencia. | ✓ |
| Solo backend/frontend automatizado | No garantiza que el sitio sea visible y utilizable. | |
| Solo panel y documentación | Deja la aplicación pública sin validar. | |

**Elección del autor:** panel comparativo accesible, paquete reproducible y gate
completo. La pantalla vacía del navegador bloquea el cierre.

---

## Criterio del agente

- La librería de gráficos, el formato exacto de artefactos saneados y la representación
  técnica de permisos quedan abiertos mientras respeten las decisiones de `07-CONTEXT.md`.

## Ideas diferidas

- Overhaul visual completo después de la Fase 7.
- Interfaz administrativa propia en Next.js.
- Upgrades automáticos o infraestructura de pago.
