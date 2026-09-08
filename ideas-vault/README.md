# ideas-vault - Nube de ideas de SavePoint (Obsidian)

Vault de Obsidian generado el 2026-09-08 como **mapa conceptual navegable y espejo vivo**
del repositorio: fases, ADR, requisitos y conceptos de producto, datos, arquitectura,
recomendadores, evaluacion y metodologia, todos enlazados entre si.

## Como abrirlo

1. Abrir Obsidian -> "Open folder as vault" -> elegir esta carpeta
   (`SavePoint/ideas-vault`).
2. Empezar por `00 - Indice.md`.
3. Abrir la **Vista Grafica** (icono de grafo en la barra izquierda) para ver la
   nube completa. Los colores por carpeta/tema estan preconfigurados en
   `.obsidian/graph.json`.

## Alcance y limites

- Es un resumen conceptual a fecha 2026-09-08 de `docs/**`, `.planning/**`,
  `AGENTS.md` y `CONVENTIONS.md`. **No es fuente canonica**; ante cualquier duda
  mandan los documentos del repo.
- No sustituye a las fuentes canonicas ni a los artefactos de evidencia. Se puede
  reconstruir, pero mientras exista debe mantenerse sincronizado con el trabajo.
- No contiene secretos, cookies, tokens, credenciales, datos personales ni logs brutos.

## Politica de mantenimiento

Todas las LLM y colaboradores deben consultar este vault al comenzar una tarea y actualizarlo
antes de terminarla cuando produzcan informacion nueva, una decision, un requisito, un
resultado experimental, una limitacion o un cambio relevante de arquitectura o producto.

Cada actualizacion debe:

1. Usar la carpeta tematica adecuada (`ADR/`, `Conceptos/`, `Fases/`, `Mapas/` o
   `Requisitos/`).
2. Incluir fecha y estado cuando se trate de una decision o una propuesta.
3. Enlazar con la fuente canonica y con las notas relacionadas cuando proceda.
4. Evitar sobrescribir trabajo paralelo; anadir una nota fechada o editar solo el apartado
   afectado.

Si algo aun no esta aprobado, debe marcarse como `Propuesta`, nunca como decision aceptada.
La guia y plantilla minima estan en [[Conceptos/Vault vivo y sincronizacion]].

## Regenerar o sincronizar

El generador esta fuera del repo, en el scratchpad de la sesion
(`build_vault.sh`). Si se regenera, hay que revisar y conservar las notas vivas y sus
actualizaciones manuales; no se debe borrar el vault sin comprobar antes los cambios.
