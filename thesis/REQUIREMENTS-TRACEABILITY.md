# Trazabilidad de requisitos de SavePoint

Fuentes: `.planning/REQUIREMENTS.md:8-263`, modelos y servicios de `apps/api/`,
planes y firmas de fase. Esta matriz no inventa flujos: cualquier enlace no probado se
marca literalmente `% PENDIENTE: confirmar con el autor`.

## Actores (10)

| actor | alcance y fuente | frontera |
| --- | --- | --- |
| Usuario no autenticado | Perfil básico público, `PROF-02` y `PROF-03`. | Sin contenido protegido. |
| Usuario autenticado | Biblioteca, listas, valoraciones y recomendaciones. | Permisos validados por backend. |
| Propietario de una colección | Gestiona su colección y datos privados. | Propiedad de recurso. |
| Amigo aceptado | Accede a proyecciones allowlisted. | `SOCIAL-04`; nunca permiso universal. |
| Research Viewer | Consulta resultados de investigación. | `evaluation/access.py`; distinto de administrador. |
| Platform Admin | Gestiona demo, importaciones, trabajos y experimentos. | `ADMIN-01`, `ADMIN-02`. |
| Sistema de importación | Procesa catálogo y entradas importadas. | Servicios de catálogo y biblioteca. |
| Sistema de evaluación | Ejecuta protocolo offline y publica artefactos. | `apps/api/evaluation/`. |
| Sistema de backup | Genera copia documentada. | `OPS-04`. |
| Sistema de recuperación | Restaura según procedimiento documentado. | `docs/deployment/backup-recovery.md`. |

## Requisitos de información (23)

| entidad | modelo o contrato demostrable | exposición o carencia |
| --- | --- | --- |
| Usuario | `accounts/models.py` | Privado salvo proyección autorizada. |
| Perfil | `accounts/models.py`, `PROF-01..04` | Allowlist pública. |
| Juego | `catalogue/models.py` | Catálogo y procedencia. |
| Obra canónica | `catalogue/models.py`, `CAT-04` | Identificador independiente de API. |
| Edición | `catalogue/models.py`, `INV-02` | `% PENDIENTE: confirmar con el autor` para detalle de relación. |
| Plataforma | `catalogue/models.py` | Metadato de catálogo. |
| Entrada de biblioteca | `library/models.py`, `LIB-01` | Propietario y permisos. |
| Valoración | `library/models.py`, `LIB-02` | Privada salvo allowlist. |
| Copia física | `library/models.py`, `INV-04` | Privada. |
| Copia digital | `library/models.py`, `INV-02` | Privada. |
| Lista | `library/models.py`, `LIB-04` | URLs autorizadas. |
| Comentario | `library/models.py`, `LIB-03` | Proyección autorizada. |
| Amistad | `social/models.py`, `SOCIAL-03` | Relación controlada. |
| Solicitud de amistad | `social/models.py`, `SOCIAL-03` | No equivale a amistad. |
| Bloqueo | `social/models.py`, `SOCIAL-03` | Oculta e impide interacción. |
| Mensaje social | `social/models.py` | `% PENDIENTE: confirmar con el autor` para contrato final. |
| Recomendación social | `social/models.py`, `SOCIAL-05` | Cooldown de siete días. |
| Snapshot | `catalogue/corpus.py`, `DATA-06` | Inmutable para experimento cerrado. |
| Ejecución experimental | `evaluation/models.py`, `EVAL-01..03` | Offline y versionada. |
| Algoritmo | `recommendations/`, `REC-01..05` | Identidad publicada. |
| Métrica | `evaluation/metrics.py` | Resultado por artefacto. |
| Artefacto | `evaluation/models.py`, `EVAL-12` | `% PENDIENTE: confirmar con el autor` para recalculabilidad agregada. |
| Procedencia | `catalogue/models.py`, `DATA-02`, `DATA-05` | Fuente, fecha y checksum. |

## Requisitos no funcionales (14)

| requisito | criterio, evidencia y límite |
| --- | --- |
| Reproducibilidad | `EVAL-01..03`, artefactos v15; una ejecución, no multi-semilla. |
| Accesibilidad | `QUAL-03`, `QUAL-04`; evidencia final por suite `% PENDIENTE: confirmar con el autor`. |
| Diseño responsive | `QUAL-03`; capturas y prueba final pendientes. |
| Seguridad | `SEC-01..08`; `phase-07-admin-security.md`; no equivale a pentest externo. |
| Privacidad | `PRIV-01`, `PRIV-02`, `PROF-03..04`; autoridad backend. |
| Legalidad | `DATA-01`, `DATA-04`, `DATA-08`; depende de licencias vigentes. |
| Procedencia | `DATA-02`, `DATA-05`, congelaciones. |
| Trazabilidad | Planes, resúmenes, verificaciones y manifestos. |
| Integridad | ORM, validación y snapshots; detalle de prueba `% PENDIENTE: confirmar con el autor`. |
| Disponibilidad | `OPS-01`; estado de servicio al defender `% PENDIENTE: confirmar con el autor`. |
| Portabilidad | `OPS-02`, `OPS-03`, `PORT-01`. |
| Mantenibilidad | ADR, módulos y tests; métrica `% PENDIENTE: confirmar con el autor`. |
| Auditabilidad | `SEC-08`, artefactos y hashes. |
| Rendimiento | Tiempos de evaluación v15; carga web `% PENDIENTE: confirmar con el autor`. |

## Reglas de negocio (11)

| regla | implementación, test y evidencia |
| --- | --- |
| Listas y colecciones compartidas solo para amistades aceptadas. | `social/policies.py`, `SOCIAL-04`; prueba concreta `% PENDIENTE: confirmar con el autor`. |
| No hay acceso privado por rutas alternativas. | `PROF-04`; autorización server-side y 404 genérico. |
| Rechazar solicitud no equivale a bloquear. | `SOCIAL-03`; `% PENDIENTE: confirmar con el autor` para test puntual. |
| Eliminar amistad no equivale a bloquear. | `SOCIAL-03`; `% PENDIENTE: confirmar con el autor` para test puntual. |
| Bloquear impide interacción y oculta relación. | `SOCIAL-03`; `social/policies.py`. |
| Recomendaciones sociales limitadas a una por semana. | `SOCIAL-05`; cooldown direccional de siete días. |
| Snapshots de investigación inmutables. | `DATA-06`, congelaciones de catálogo. |
| Research Viewer y Platform Admin son capacidades distintas. | `evaluation/access.py`, `ADMIN-01..02`. |
| La interfaz no recalcula resultados científicos. | Panel y artefactos publicados; `% PENDIENTE: confirmar con el autor` para prueba UI puntual. |
| Datos privados no aparecen en proyecciones públicas. | `PROF-03`, `INV-05`, `PRIV-01`. |
| Autoridad de permisos en backend. | `SEC-01`, `social/policies.py`. |

## Cadena de trazabilidad y casos de uso mínimos

| requisito | caso de uso | fase | plan | código | test | evidencia | sección futura |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `AUTH-01`, `PROF-01..04` | CU-01: gestionar cuenta y perfil | 1, 5 y 6 | Planes de fase correspondientes | `accounts/`, `social/` | `% PENDIENTE: confirmar con el autor` | Signoffs 01, 05 y 06 | Requisitos y diseño. |
| `LIB-01..04`, `INV-01..05`, `PORT-01` | CU-02: gestionar biblioteca, copia y lista | 1 y 5 | Planes de fase 05 | `library/` | `% PENDIENTE: confirmar con el autor` | `phase-05-signoff.md` | Requisitos e implementación. |
| `SOCIAL-03..05`, `PRIV-01` | CU-03: gestionar relación y recomendación social | 6 | Planes de fase 06 | `social/` | `% PENDIENTE: confirmar con el autor` | `phase-06-signoff.md` | Requisitos y seguridad. |
| `REC-01..09`, `EVAL-01..03`, `EVAL-09..10` | CU-04: consultar recomendación y experimento | 2, 4 y 7 | Planes de fase 04 y 07 | `recommendations/`, `evaluation/` | Tests de evaluación y recomendaciones | Evidencia v15 | Algoritmos y metodología experimental. |
| `ADMIN-01..02`, `SEC-01..08`, `OPS-04` | CU-05: administrar, respaldar y recuperar | 7 | Planes de fase 07 | `evaluation/`, `infra/` | `% PENDIENTE: confirmar con el autor` | `phase-07-admin-security.md`, `backup-recovery.md` | Operación, seguridad y despliegue. |

Los flujos principal, alternativo, de error y postcondición detallados quedan
`% PENDIENTE: confirmar con el autor` hasta su extracción controlada de API, tests y
evidencia. Esta matriz no los inventa.
