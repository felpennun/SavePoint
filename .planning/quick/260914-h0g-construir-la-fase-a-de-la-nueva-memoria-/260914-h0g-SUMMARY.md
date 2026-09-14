---
quick_id: 260914-h0g
phase: quick-260914-h0g
plan: 01
status: complete
github_issue: 71
subsystem: thesis-inventory
tags: [thesis, reproducibility, traceability]
provides:
  - Manifiesto de fuentes con aliases, hashes y rangos de cobertura.
  - Seis matrices de inventario antes de la redacción en LaTeX.
  - Gate determinista de inventario con canarios de fallo.
affects:
  - Esqueleto LaTeX y redacción posterior de la memoria.
---

# Fase A de la memoria: resumen de inventario

La Fase A dejó una base trazable para reconstruir la memoria de SavePoint sin convertir
suposiciones, resultados sintéticos ni cambios posteriores de protocolo en afirmaciones
académicas.

## Artefactos entregados

- `thesis/SOURCE-MANIFEST.json`: 742 fuentes con aliases, hash y cobertura por rangos;
  los 68 elementos del ZIP histórico coinciden con sus homólogos extraídos.
- `thesis/STRUCTURE-MAP.md`: estructura comparada de plantilla ETSII, los dos TFG de
  referencia y la memoria histórica, con un mapa propuesto centrado en recomendación.
- `thesis/EVIDENCE-MATRIX.md`: afirmaciones acotadas, fuentes, evidencias, límites y
  contradicciones que deben conservarse en la memoria.
- `thesis/ALGORITHM-MATRIX.md`: los 16 identificadores publicados por v15, sus resultados
  K=5, K=10 y K=20, además de la separación explícita respecto de v16.
- `thesis/SIGNAL-MATRIX.md`: señales, transformaciones, pesos, fórmulas, pruebas y sesgos
  demostrados por código o protocolo.
- `thesis/REQUIREMENTS-TRACEABILITY.md`: actores, entidades, requisitos no funcionales,
  reglas y cadenas de trazabilidad con huecos marcados.
- `thesis/FIGURE-PLAN.md`: diagramas, gráficas y capturas requeridos, distinguiendo los
  existentes de los pendientes.

## Checkpoints realizados

| Checkpoint | Commit | Resultado |
| --- | --- | --- |
| Manifiesto de fuentes | `ea0e37f` | Manifiesto validado y preservado antes de las matrices. |
| Estructura comparada | `cfc14d7` | Plantilla, referencias e historial distinguidos con localizadores. |
| Evidencia | `76e4b5f` | Límites, contradicciones y contrato de autoría registrados. |
| Algoritmos v15 | `223c4cf` | Inventario de 16 IDs y resultados publicados, separado de v16. |
| Señales | `29d4d22` | Fórmulas y pesos documentados solo cuando están demostrados. |
| Requisitos | `6072c76` | Trazabilidad compacta y huecos no inventados. |
| Figuras | `1fb1deb` | Plan de evidencia visual sin generar ni alterar figuras. |
| Vault | pendiente de hash | Enlace conceptual mínimo al inventario canónico. |

## Verificación

- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-thesis-inventory.ps1 -Scope Sources`
  terminó con `Thesis inventory verification passed for scope: Sources`.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-thesis-inventory.ps1 -Scope Recommendations`
  terminó con `Thesis inventory verification passed for scope: Recommendations`.
- `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify-thesis-inventory.ps1 -Scope Full`
  terminó con `Thesis inventory verification passed for scope: Full`.
- Se ejecutó `git diff --check` antes de cada checkpoint atómico.

## Límites y asuntos pendientes

- La evidencia v15 usa población sintética, 79 usuarios evaluables y un único *run*
  publicado. No permite generalizar resultados a usuarios reales ni declarar superioridad
  fuera del corpus, del *snapshot* y del protocolo publicado.
- v15 (`fs-v12-curated-tags-idf`) y v16 (`fs-v13-family-weighted-tags`) son evidencias
  distintas. La memoria debe tratarlas como tales y no reinterpretar métricas v15 con
  parámetros v16.
- Las contradicciones de estado entre `STATE.md`, `ROADMAP.md` y requisitos abiertos se
  registraron, pero no se resolvieron artificialmente.
- La inspección visual exhaustiva de los PDF de referencia, los flujos completos de casos
  de uso, las capturas de interfaz y algunos resultados de pruebas están marcados como
  `% PENDIENTE: confirmar con el autor` cuando faltaba una fuente verificable.
- Felipe Peña Núñez es el único autor del trabajo. Las herramientas asistidas por agentes
  forman parte de una metodología gobernada, revisada y validada por el autor.

## Continuidad

La siguiente fase puede crear el esqueleto LaTeX desde la plantilla ETSII y redactar solo a
partir de las fuentes canónicas inventariadas. Para el límite operativo de 150 páginas, la
memoria principal debe priorizar algoritmos, protocolo, resultados y decisiones; la
trazabilidad extensa, las tablas de detalle y la evidencia repetitiva deben trasladarse a
anexos o mantenerse como artefactos versionados citados.
