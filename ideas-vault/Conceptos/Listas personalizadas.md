---
tags: [concepto, tema/producto, fase/5]
---

# Listas personalizadas

El usuario crea, edita, borra y **reordena** listas de juegos propias (LIB-04),
ademas de comentarios propios (LIB-03). Junto con la edicion de perfil y la
portabilidad, forman el nucleo de curacion completa de la coleccion en la Fase 5.

**Modelo backend (Plan 05-02):** `CustomList`/`CustomListItem` es el agregado
primario y unico de esta capacidad -- no es un alias de otra entidad; antes de
la Fase 5 no existia ninguna representacion de listas manuales de juegos en el
backend. El reordenamiento usa concurrencia optimista (`version` +
`expected_version`, HTTP 409 ante version obsoleta) y cada item exige
pertenencia previa a la coleccion del propietario (`LibraryEntry`). Cada lista
exporta sus elementos en el CSV de portabilidad (`record_type=list_item`); ver
[[Importacion y exportacion]].

## Enlaces

- [[Importacion y exportacion]] · [[Perfil publico]] · [[Fase 5 - Coleccion y portabilidad]]
