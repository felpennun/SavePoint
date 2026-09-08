---
tags: [metodologia, obsidian, agentes, sincronizacion]
estado: vigente
fecha: 2026-09-08
---

# Vault vivo y sincronizacion

## Proposito

`ideas-vault/` es el espejo conceptual vivo de SavePoint para Obsidian. Sirve para conectar
decisiones, conceptos, requisitos, fases y evidencias de forma navegable. No sustituye a las
fuentes canonicas del repositorio: `CONVENTIONS.md`, `AGENTS.md`, `docs/` y `.planning/`.

## Regla para todas las LLM

Toda LLM o colaborador debe:

1. Consultar el vault al comenzar una tarea.
2. Actualizarlo antes de terminar si la tarea produce informacion nueva, una decision, un
   requisito, un resultado experimental, una limitacion o un cambio relevante de arquitectura
   o producto.
3. Enlazar la nota con la fuente canonica (por ejemplo, un ADR, `CONTEXT`,
   `DISCUSSION-LOG`, plan, resumen o artefacto de verificacion).
4. Enlazar tambien las notas relacionadas cuando ayude a conservar la navegacion conceptual.

En trabajos paralelos no se sobrescriben notas ajenas. Se anade una nota fechada o se edita
unicamente el apartado afectado. Las propuestas se marcan como `Propuesta` hasta que el autor
las apruebe.

## Ubicacion

- `ADR/`: decisiones arquitectonicas y de datos.
- `Conceptos/`: definiciones, metricas, reglas y metodologia transversal.
- `Fases/`: alcance, estado y decisiones especificas de cada fase.
- `Mapas/`: indices y relaciones entre areas.
- `Requisitos/`: requisitos funcionales, de datos, experimentacion y operacion.

## Seguridad y mantenimiento

No se guardan secretos, cookies, tokens, credenciales, datos personales ni logs brutos. Los
cambios del vault se conservan en Git junto con el trabajo que los motiva cuando sea posible.
Si se regenera el vault, se revisan las notas manuales para no perder decisiones o enlaces
incorporados desde la generacion inicial.

## Issues de GitHub

La política de [`CONTRIBUTING.md`](../../CONTRIBUTING.md) y la sección 5 de
[`CONVENTIONS.md`](../../CONVENTIONS.md) son globales para todas las LLM y colaboradores.
El trabajo no trivial se registra en una issue; cada plan GSD tiene una issue en el board y
`github_issue` en el frontmatter. Los avances usan `Refs #N` y el cierre usa `Closes #N` solo
cuando el `SUMMARY`, la integración y la verificación del plan están completos. Las tareas
paralelas no integradas permanecen abiertas.

La LLM responsable cierra automáticamente la issue cuando la tarea está completada, integrada
y verificada, sin esperar otra instrucción del autor. Las tareas pendientes o paralelas no
integradas permanecen abiertas.

## Plantilla minima

```markdown
---
fecha: YYYY-MM-DD
estado: propuesta | vigente | descartada
fuente: [[ruta o nota canonica]]
---

# Titulo

## Que ha cambiado

Descripcion breve y verificable.

## Impacto

Que decisiones, requisitos o tareas afecta.

## Enlaces relacionados

- [[Nota relacionada]]
```
