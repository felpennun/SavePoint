---
quick_id: 260909-lq9
status: complete
---

# Resumen

Se mantiene sin cambios la fórmula combinada de `display_rating` (IGDB más
SavePoint). Los algoritmos y sus resultados internos no incorporan esa señal:
el valor se añade únicamente al serializar respuestas destinadas a la UI.

Las tarjetas del inicio, catálogo, novedades y recomendaciones consumen ahora
`display_rating`, igual que la ficha de juego. Las snapshots antiguas se
hidratan en la capa de presentación para conservar la misma cifra sin relanzar
los algoritmos.

Verificación completada:

- 60 pruebas backend de catálogo y recomendaciones.
- 16 pruebas frontend y comprobación TypeScript.
- API y web saludables.
- Comprobación real: `grand-theft-auto-v` devuelve `89.07` tanto en tarjeta como
  en ficha.
