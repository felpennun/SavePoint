# Convenciones del proyecto SavePoint

> Documento único de convenciones para quien trabaje en este repositorio, sea una persona o un
> asistente de IA. Reúne las reglas de idioma, de código y commits, de dependencias y secretos,
> y el flujo de trabajo con asistentes y con issues. Si otra instrucción entra en conflicto con
> esta, **manda esta**.

---

## 1. Proyecto y principios

SavePoint es una aplicación web para catalogar la colección y los pendientes de videojuegos
personales, inspirada en Goodreads y Letterboxd, y es también la plataforma de un Trabajo Fin
de Grado (TFG) que compara recomendadores basados en contenido, colaborativos e híbridos con
experimentos reproducibles, usuarios sintéticos y resultados explicables.

**Valor central:** que los usuarios reciban recomendaciones útiles y explicables a partir de una
colección bien organizada, y que cada resultado algorítmico siga siendo reproducible y
defendible en la memoria.

Restricciones que guían las decisiones:

- **Reproducibilidad académica.** Experimentos, generación de datos sintéticos, configuraciones
  y resultados deben poder repetirse; la comparación de recomendadores es una contribución
  central.
- **Legalidad y procedencia de los datos.** El uso de datasets y APIs respeta sus licencias y
  términos, y cada fuente es trazable.
- **Doble entrega.** Una aplicación desplegada y un entorno local documentado y reproducible.
- **Audiencia inicial controlada.** Demostración académica con cuentas simuladas, sin operación
  pública sin límites.
- **Accesibilidad y diseño adaptable.** Los flujos principales funcionan en escritorio y móvil y
  siguen prácticas de interacción accesibles.
- **Stack justificado.** Cada tecnología se elige con evidencia y queda registrada como
  decisión de arquitectura (ADR).

---

## 2. Idioma (regla vigente desde 2026-09-06)

| Ámbito | Idioma | Qué incluye |
|---|---|---|
| **Documentación del TFG** | **Español** | La memoria y todo el registro de evidencia: decisiones de arquitectura (ADR), verificaciones, metodología, despliegue y firmas de fase. Los documentos nuevos se redactan directamente en español. |
| **Conversación y prompts** | **Español** | Las respuestas de un asistente al autor y los prompts que un asistente escriba para *otra* IA que trabaje en este proyecto. |
| **Planificación** | **Español** para prosa nueva | Estado, hoja de ruta, planes, resúmenes y verificaciones. El material heredado en inglés se pasa a español cuando se toca; no hace falta un barrido retroactivo. |
| **Código** | **Inglés** | Identificadores, comentarios *de código*, mensajes de commit, nombres de tests, cadenas de log y nombres de rama. Es la convención estándar y mantiene el código portable. |

### Matices que se respetan siempre

- **Citas textuales en su idioma original.** Los términos legales citados literalmente
  (Twitch Developer Services Agreement, FAQ de IGDB) se conservan **en inglés** dentro de prosa
  en español. Traducir una cita legal destruye su valor probatorio.
- **Tokens neutrales de idioma.** No se traducen los identificadores de código, los IDs de
  requisito (`CAT-02`, `DATA-04`…), las rutas de fichero, los hashes de commit, las URLs, los
  nombres de variables de entorno ni los comandos.
- **Encabezados de ADR.** Cada ADR lleva exactamente estas siete secciones: `## Contexto`,
  `## Alternativas consideradas`, `## Decisión`, `## Evidencia y fuentes`, `## Consecuencias`,
  `## Reversibilidad` y `## Aprobación y revisión`, más la cadena `Autor de la decisión` y al
  menos una URL `https://`.
- **Fotos congeladas fechadas.** Los documentos que son el registro de un instante concreto se
  dejan tal cual y no se re-traducen.
- **Documentos con comprobación automática.** Si un documento tiene una comprobación
  determinista de su contenido, o su hash está fijado en el registro de evidencia que
  mantiene el autor, al traducirlo o editarlo se actualizan en el **mismo commit** los
  patrones de la comprobación y el hash fijado, y se añade la entrada de registro que lo
  documenta.

---

## 3. Código, commits y calidad

- **Formato de commit:** [Conventional Commits](https://www.conventionalcommits.org/) en
  inglés: `<tipo>(<ámbito>): <resumen>`, con los tipos `feat`, `fix`, `docs`, `test`, `chore`,
  `build` y `refactor`. El resumen va en imperativo y minúsculas, sin punto final, y explica el
  *porqué* más que el *qué*. El detalle está en [`CONTRIBUTING.md`](CONTRIBUTING.md).
- **Atribución:** los commits hechos con ayuda de un asistente terminan con una línea
  `Co-Authored-By: <modelo> <noreply@anthropic.com>`.
- **Pruebas:** todo cambio de comportamiento lleva su prueba. Se ejecutan `pytest` para la API,
  `vitest` para la web y Playwright para los recorridos de extremo a extremo (ver el README).
- **Dependencias:** toda dependencia directa nueva o cambio de versión exige aprobación humana
  explícita, una fila en el registro de legitimidad de dependencias y su entrada en el
  registro de evidencia.
- **Secretos:** nunca se imprime, registra, versiona ni escribe el valor de una credencial,
  token o cadena de conexión; solo se nombra la variable. Tampoco en issues, commits o PR, ni
  siquiera fragmentos o nombres de host de un proveedor real (Neon, Render, Vercel).
- **Datos de terceros:** los volcados masivos de IGDB no se versionan (`data/snapshots/` está
  ignorado a propósito). Las portadas se enlazan, no se copian.

---

## 4. Trabajo con asistentes de IA y método GSD

El desarrollo se ha hecho con asistentes de IA (Codex y Claude Code) siguiendo
el método **Get Stuff Done (GSD)**: <https://github.com/gsd-build/get-shit-done>. La memoria del
TFG describe cómo se aplicó, qué controles se pusieron y qué parte del trabajo es de los agentes
y cuál del autor.

- **Material de desarrollo local.** Lo que instala GSD (comandos, agentes, hooks, habilidades) y
  los ficheros de instrucciones de cada asistente (`CLAUDE.md`, `AGENTS.md`,
  `.github/copilot-instructions.md`) viven en el equipo del autor y no se publican en este
  repositorio. Todos apuntan a este documento, que es la fuente.
- **Carga automática.** Cada asistente lee su fichero de instrucciones al empezar la sesión; no
  hace falta ningún comando para recargar las convenciones. Para forzarlo en cualquier
  herramienta basta con pedir: **"Antes de empezar, lee `CONVENTIONS.md` y revisa la
  planificación."**
- **Planificación.** El estado del proyecto, la hoja de ruta y el par plan/resumen de cada
  paso se guardan en `.planning/`, y la fuente de verdad operativa es ese árbol.
- **Vault de Obsidian.** `ideas-vault/` es el registro conceptual vivo del proyecto. Se
  consulta al empezar una tarea y se actualiza al terminarla si hay información nueva, una
  decisión, un requisito, un resultado experimental, una limitación o un cambio relevante. Cada
  nota enlaza con su fuente canónica (ADR, plan, evidencia): el vault resume y conecta, pero no
  sustituye a esas fuentes. En trabajo paralelo no se sobrescriben notas ajenas: se añade una
  nota fechada o se edita solo el apartado afectado, y lo propuesto se marca como propuesta
  hasta su aprobación. Nunca se guardan secretos, cookies, tokens, credenciales, datos
  personales ni registros sin revisar.

---

## 5. Ciclo de vida de las issues de GitHub

La política de [`CONTRIBUTING.md`](CONTRIBUTING.md) se aplica a todas las personas y asistentes,
no solo al agente que ejecuta GSD. Todo trabajo superior a un arreglo trivial tiene una issue
en GitHub y, cuando proceda, un elemento en el tablero del proyecto.

- Al planificar una fase se crea o reconcilia **una issue por cada plan**, se etiqueta con la
  fase, se añade al tablero y se escribe `github_issue: <número>` en el encabezado del plan.
- Durante la ejecución, los commits parciales usan `Refs #N`. El commit que incorpora el
  resumen del plan y lo cierra usa `Closes #N`; si no hay un commit único de cierre, la issue se
  cierra directamente tras verificar el resumen y sus criterios.
- Una issue no se cierra porque exista código o un resumen provisional: hay que comprobar
  integración, verificación y estado del plan. Las tareas paralelas no integradas permanecen
  abiertas y se reconcilian antes de dar la fase por cerrada.
- Antes de informar de una fase como cerrada, la issue de cada plan debe estar en el estado
  correcto y sincronizada con el tablero. Si GitHub no permite la operación, se documenta el
  bloqueo y no se simula el cierre.

La persona o el asistente responsable cierra la issue sin esperar otra instrucción cuando la
tarea está completada, integrada y verificada. Si el trabajo sigue pendiente o pertenece a una
rama paralela no integrada, la issue permanece abierta.

---

*Creado el 2026-09-06 y unificado el 2026-10-06, con las reglas que antes estaban repartidas
entre los ficheros de instrucciones de cada asistente. Cambiar una convención requiere una
decisión del autor.*
