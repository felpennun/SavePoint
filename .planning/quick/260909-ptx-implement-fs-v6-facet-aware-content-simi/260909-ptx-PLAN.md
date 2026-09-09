---
quick_id: 260909-ptx
description: Implementar fs-v6 con similitud por facetas y probarla con Felipe
status: complete
---

# Plan rápido: similitud de contenido fs-v6

## Objetivo

Sustituir el coseno directo de vectores dispersos por una similitud de contenido
con núcleo de género/plataforma y un bonus opcional, personalizado y acotado,
por coincidencia de saga o desarrollador. La misma arquitectura debe ser usada
por el ranker web, los workers y el runner offline.

## Tareas

1. Implementar la versión `fs-v6` en el módulo compartido de contenido. El
   núcleo conservará la prioridad género `0,50` y plataforma `0,25`, sin
   penalizar la ausencia de metadatos opcionales. Saga `0,15` y desarrollador
   `0,10` solo podrán aportar cuando coincidan con valores presentes en el
   perfil ponderado del usuario; se aplicará un bonus acotado que no pueda
   dominar al núcleo.
2. Adaptar perfil, explicaciones, caché, protocolo y contratos para que web,
   workers y evaluación offline consuman exactamente la misma función y
   versión. Invalidar la caché anterior mediante `fs-v6`, sin borrar datos.
3. Añadir pruebas de ausencia, coincidencia y no coincidencia de saga/
   desarrollador, regresión del núcleo género/plataforma y paridad de versión.
   Ejecutar los workers únicamente para la cuenta `felipe` y comprobar que el
   resultado publicado usa `fs-v6`; no lanzar la evaluación de los 400 usuarios.

## Verificación

- Suite dirigida de recomendaciones y evaluación offline en Docker.
- Comprobación de que ningún candidato obtiene bonus solo por tener saga o
  desarrollador.
- Comprobación de que la caché y los DTO declaran `fs-v6`.
- Comprobación del estado de los trabajos y snapshot de `felipe`.
