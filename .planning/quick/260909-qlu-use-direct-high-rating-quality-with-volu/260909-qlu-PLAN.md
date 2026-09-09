---
quick_id: 260909-qlu
description: Reforzar rating observado y auditar coincidencias de saga y desarrollador en Felipe
status: complete
---

# Plan rápido: rating observado y coincidencias de contenido

## Objetivo

Evitar que el perfil medio de rating por género diluya la valoración IGDB de
una obra candidata cuando esa valoración existe. Auditar con datos reales de
Felipe las coincidencias de género, franquicia y desarrollador de Silksong y
Hades II, corregir la integración si procede y publicar una nueva comparación
de recomendaciones sin ejecutar la evaluación de los 400 usuarios.

## Tareas

1. Cambiar la señal compartida a calidad IGDB directa con potencia cuadrática y
   refuerzo acotado por `total_rating_count`; conservar el perfil por género
   únicamente como fallback para obras sin rating observado. Añadir regresiones
   que demuestren que una nota alta no queda reducida al promedio del género.
2. Consultar la colección y el corpus de Felipe para verificar relaciones,
   elegibilidad y puntuaciones de Hollow Knight, Hades, Elden Ring, Silksong y
   Hades II. Corregir solo los fallos demostrados de importación, perfil,
   explicación o ranking.
3. Invalidar la configuración publicada, relanzar en paralelo los diez workers
   de Felipe sobre la última colección, inspeccionar las dos obras objetivo y
   documentar el resultado en la metodología, el vault y el estado GSD.

## Verificación

- Pruebas dirigidas de recomendaciones y evaluación offline.
- Auditoría SQL/Django de relaciones y elegibilidad de las obras objetivo.
- Diez jobs de Felipe completados con la nueva huella de configuración.
- No ejecutar el estudio offline de los 400 usuarios en esta tarea.
