---
quick_id: 260909-mdo
status: complete
---

# Resumen

La respuesta autenticada de biblioteca ahora incluye `display_rating`,
calculado en bloque con la fórmula combinada vigente de IGDB y SavePoint. La
colección y la sección de continuación de la portada lo pasan a `GameCard` como
`ScorePill`; las estrellas del usuario siguen siendo independientes.

## Verificación

- API: 39 pruebas pasadas (`library`, copias y `display_rating`).
- Frontend: 16 pruebas pasadas.
- TypeScript: `tsc --noEmit` correcto.
- Aplicación: contenedores API/web recreados y saludables; `/es/collection`
  responde HTTP 200.
