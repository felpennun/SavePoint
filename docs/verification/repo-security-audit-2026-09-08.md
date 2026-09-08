# Auditoría integral de seguridad y limpieza del repositorio

**Fecha:** 2026-09-08

**Alcance:** historial Git completo, código Django/DRF y Next.js, autenticación, autorización, consultas, importadores, recomendadores, dependencias bloqueadas, imágenes OCI, configuración de despliegue, artefactos locales y documentación de evidencia.

**Criterio de bloqueo:** hallazgos abiertos de severidad alta o crítica.

## Resultado ejecutivo

La auditoría termina sin hallazgos altos o críticos abiertos. Se localizaron cinco carencias corregibles en esta pasada: datos locales incluidos innecesariamente en el contexto de build, imágenes base desactualizadas, endpoints de ranking costosos sin throttle específico, seguimiento de redirects en el cliente IGDB y ausencia de un gate sobre todo el historial Git. Las cinco se corrigieron y verificaron.

Quedan dos mejoras no bloqueantes y explícitas: incorporar los gates a CI y activar protección de `main`. La segunda no está disponible actualmente para este repositorio privado con el plan de GitHub en uso; no se ha simulado una garantía que la plataforma no ofrece.

## Hallazgos y correcciones

| ID | Severidad | Hallazgo | Corrección | Estado |
|----|-----------|----------|------------|--------|
| `AF-SEC-01` | Alta | El contexto de Docker podía transportar un dump local de PostgreSQL y borradores de localización a capas de build. | `.dockerignore` excluye datasets locales, resultados experimentales temporales y material de autoría/tooling. | Cerrado |
| `AF-SEC-02` | Crítica | Las imágenes base fijadas acumulaban vulnerabilidades conocidas altas y críticas en paquetes del sistema y tooling global. | Python 3.13.15-slim y Node 24.20.0-slim fijados por digest; pnpm 11.26.0; retirada de pip/npm/Corepack del runtime cuando ya no son necesarios. | Cerrado |
| `AF-SEC-03` | Media | Recomendaciones y popularidad podían forzar cálculos repetidos sin un límite específico. | Scopes compartidos de 30/min y 60/min, respectivamente, con tests de regresión. | Cerrado |
| `AF-SEC-04` | Media | El cliente IGDB aceptaba el comportamiento de redirects por defecto de `requests`. | `allow_redirects=False` tanto en la obtención de token como en la consulta autenticada, con test. | Cerrado |
| `AF-SEC-05` | Media | El scanner local cubría el árbol actual, pero no todo el historial. | Gate Gitleaks reproducible y fijado por imagen/digest, allowlist mínima de falsos positivos y Dependabot semanal. | Cerrado |

## Cobertura técnica

### Secretos y exposición de información

- El scanner del proyecto no encontró credenciales en los 3.513 ficheros seguidos, outputs de build, imágenes o logs inspeccionados.
- Gitleaks revisó 310 commits en la pasada previa al checkpoint, 55,17 MB en total, sin filtraciones. Los únicos falsos positivos eran hashes SHA-256 de manifiestos GSD y un identificador sintético de test; la allowlist está limitada por ruta y valor exactos.
- Los placeholders locales de Compose permanecen identificados como datos inertes de desarrollo; ninguna credencial real se incorporó a Git, documentación, imágenes o Issues.

### Aplicación y fronteras de confianza

- DRF utiliza autenticación de sesión; login y registro están protegidos por CSRF y throttle.
- Las vistas de biblioteca y recomendación limitan las operaciones a `request.user`; no aceptan un usuario objetivo controlado por el cliente.
- Los campos públicos se proyectan mediante allowlists explícitas. No se encontró `fields = "__all__"` en serializers.
- No se encontraron llamadas a `eval`, `exec`, deserialización insegura con pickle/YAML, SQL interpolado, `shell=True` ni HTML dinámico marcado como seguro.
- Las consultas parametrizan filtros y ordenamientos mediante ORM y allowlists. Los endpoints costosos añadidos recientemente tienen límites de frecuencia.
- La CSP mantiene `unsafe-inline` para scripts por la forma de bootstrap de Next.js actual. Es una concesión de defensa en profundidad, no un XSS conocido; no hay interpolación en el único uso estático de `dangerouslySetInnerHTML`.

### Cadena de suministro y contenedores

- OSV-Scanner inspeccionó 20 dependencias Python y 205 paquetes pnpm sin vulnerabilidades conocidas reportadas.
- `pnpm audit --prod --audit-level=high` terminó limpio.
- Trivy terminó con cero hallazgos altos o críticos corregibles en ambas imágenes finales.
- Los Dockerfiles usan imágenes por digest, usuarios sin privilegios y etapas separadas. El runtime no conserva gestores de paquetes globales innecesarios.
- PostgreSQL no publica un puerto al host y los servicios aplican `no-new-privileges` en Compose.

### Calidad y reproducibilidad

- API: 396 tests superados sobre PostgreSQL.
- Web: 34 tests superados con Chromium real; build de producción completado.
- Django: `check --deploy` sin observaciones con variables de producción seguras.
- `check-dependencies.ps1`, `check-evidence.ps1`, `check-secrets.ps1` y `check-history-secrets.ps1`: superados.

## Limpieza conservadora

Se eliminan únicamente cachés, resultados de test y artefactos regenerables. Se conservan deliberadamente el dump local gobernado, los lotes de localización activos, `.env.local`, volúmenes de PostgreSQL, referencias académicas y cualquier cambio de usuario. El borrador de un worktree huérfano se trata por separado y solo se retira tras comprobar que su rama sigue siendo recuperable y que `main` contiene la implementación posterior verificada.

## Seguimiento no bloqueante

1. Añadir una workflow de CI fijada que ejecute escaneo de secretos/historial, gates de dependencias/evidencia, tests y build. Requiere acordar frecuencia y consumo de minutos.
2. Activar reglas de protección para `main` cuando el plan de GitHub lo permita o cambie la visibilidad del repositorio.

El registro de amenazas de fase, incluidos los 51 controles definidos durante la planificación, está en [`02-SECURITY.md`](../../.planning/phases/02-governed-corpus-external-ratings-evaluation-contract-and-fir/02-SECURITY.md).
