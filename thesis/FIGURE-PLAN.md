# Plan compacto de figuras y capturas

Cada elemento necesita un `caption`, `label`, cita previa en el texto y fuente o
especificación de generación. `pendiente` significa que no existe un asset verificable:
no se fabrica una captura para cerrar el inventario. Las capturas deben anonimizar datos
de cuentas demo y no mostrar secretos, identificadores internos ni contenido privado.

| figure_id | tipo, fuente y estado | capítulo | caption | label | cita previa requerida | variante |
| --- | --- | --- | --- | --- | --- |
| F-01 | Diagrama del problema; especificación propia, pendiente. | Introducción | Relación entre colección, señales y recomendación reproducible. | `fig:problema` | Definir el problema antes de citar. | N/A |
| F-02 | Casos de uso; `REQUIREMENTS-TRACEABILITY.md`, pendiente. | Requisitos | Actores y fronteras de SavePoint. | `fig:casos-uso` | Presentar actores y reglas. | N/A |
| F-03 | Arquitectura; `apps/api/`, `apps/web/`, `infra/`, pendiente. | Diseño | Arquitectura modular de SavePoint. | `fig:arquitectura` | Explicar componentes y límites. | N/A |
| F-04 | Entidad-relación; modelos Django, pendiente. | Diseño | Modelo de datos de catálogo, biblioteca, social y evaluación. | `fig:er` | Describir entidades antes de citar. | N/A |
| F-05 | Flujo de adquisición; catálogo y ADR-006, pendiente. | Datos | Adquisición y procedencia de datos. | `fig:adquisicion-datos` | Explicar fuentes y licencia. | N/A |
| F-06 | Flujo de gobierno; congelaciones, pendiente. | Datos | Gobierno, validación y congelación del corpus. | `fig:gobierno-datos` | Explicar inmutabilidad experimental. | N/A |
| F-07 | Flujo de snapshots; evaluación y catálogo, pendiente. | Diseño | Snapshot y artefacto reproducible. | `fig:snapshots` | Presentar separación web y experimento. | N/A |
| F-08 | Flujo GSD; `.planning/`, pendiente. | Metodología | Ciclo de discusión, planificación, ejecución y verificación. | `fig:gsd` | Explicar metodología asistida. | N/A |
| F-09 | Flujo experimental; protocolo v15, pendiente. | Metodología experimental | Corpus, población, split, ranking y métricas. | `fig:flujo-experimental` | Definir protocolo antes de citar. | N/A |
| F-10 | Diagrama de señales; `SIGNAL-MATRIX.md`, pendiente. | Algoritmos | Señales de contenido, rating, popularidad e interacción. | `fig:senales` | Presentar representación y límites. | N/A |
| F-11 | Cálculo de recomendación; código actual, pendiente. | Algoritmos | De perfil, candidatas y score a recomendación explicable. | `fig:calculo-recomendacion` | Explicar exclusiones y ranking. | N/A |
| F-12 | Híbrido y MMR; `hybrid.py`, `diversity.py`, pendiente. | Algoritmos | Combinación híbrida y reordenación MMR. | `fig:hibrido-mmr` | Definir composición y diversidad. | N/A |
| F-13 | Gráfica de resultados por algoritmo; artefacto v15, pendiente. | Resultados | nDCG publicado por algoritmo y K. | `fig:resultados-algoritmo` | Delimitar población y protocolo antes de citar. | N/A |
| F-14 | Gráfica por métrica; artefacto v15, pendiente. | Resultados | Precisión, recall, nDCG y MAP por K. | `fig:resultados-metricas` | Definir métricas antes de citar. | N/A |
| F-15 | Gráfica de cohortes; artefacto v15, pendiente. | Resultados | Resultados por cohorte de la publicación v15. | `fig:resultados-cohortes` | Explicar elegibilidad y tamaño de cohorte. | N/A |
| C-01 | Inicio; ruta de `apps/web/`, pendiente. | Diseño de interfaz | Pantalla de inicio de SavePoint. | `fig:ui-inicio` | Introducir interfaz y estado de demo. | Desktop y mobile |
| C-02 | Catálogo y filtros; rutas y E2E, pendiente. | Diseño de interfaz | Catálogo y filtrado del videojuego. | `fig:ui-catalogo-filtros` | Explicar búsqueda y filtros. | Desktop y mobile |
| C-03 | Detalle de juego; catálogo, pendiente. | Diseño de interfaz | Detalle, procedencia y acciones sobre una obra. | `fig:ui-detalle` | Explicar catálogo y procedencia. | Desktop y mobile |
| C-04 | Colección e inventario; biblioteca, pendiente. | Diseño de interfaz | Biblioteca personal y copias físicas o digitales. | `fig:ui-coleccion` | Explicar propiedad y privacidad. | Desktop y mobile |
| C-05 | Perfil y privacidad; cuentas/social, pendiente. | Diseño de interfaz | Perfil y límites de proyección pública. | `fig:ui-perfil-privacidad` | Explicar roles y allowlist. | Desktop y mobile |
| C-06 | Social y amistades; `apps/api/social/`, pendiente. | Diseño de interfaz | Relaciones, bloqueos y recomendaciones sociales. | `fig:ui-social` | Explicar reglas sociales. | Desktop y mobile |
| C-07 | Listas y comentarios; biblioteca, pendiente. | Diseño de interfaz | Listas y comentarios de la biblioteca. | `fig:ui-listas-comentarios` | Explicar permisos de recurso. | Desktop y mobile |
| C-08 | Recomendaciones; recomendaciones, pendiente. | Diseño de interfaz | Recomendaciones y explicación publicada. | `fig:ui-recomendaciones` | Delimitar cálculo online y evidencia offline. | Desktop y mobile |
| C-09 | Panel de investigación; evaluación, pendiente. | Diseño de interfaz | Panel de comparación de artefactos y métricas. | `fig:ui-panel-investigacion` | Explicar acceso Research Viewer. | Desktop y mobile |
| C-10 | Exportaciones e importación; biblioteca, pendiente. | Implementación | Exportación de colección y flujo de importación. | `fig:ui-exportacion` | Explicar portabilidad y validación. | Desktop y mobile |
| C-11 | Administración; evaluación y catálogo, pendiente. | Implementación | Administración de demo, trabajos y experimentos. | `fig:ui-administracion` | Explicar frontera Platform Admin. | Desktop |

## Condiciones de cierre

- F-13 a F-15 deben generarse desde artefactos v15 inmutables, nunca desde valores
  transcritos manualmente.
- C-01 a C-11 requieren una captura desktop y mobile salvo C-11, que solo exige
  desktop por ser una interfaz administrativa.
- Ningún elemento marcado pendiente se puede citar como figura existente ni usar para
  afirmar que una prueba de usabilidad, accesibilidad o despliegue ya se completó.
