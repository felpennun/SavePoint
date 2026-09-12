# Fase 5: Complete Collection Workflows and Portability - Registro de discusión

> **Solo registro de auditoría.** No usar como entrada de planificación,
> investigación o ejecución. Las decisiones están en `05-CONTEXT.md`.

**Fecha:** 2026-09-12
**Fase:** 5 - Complete Collection Workflows and Portability
**Áreas discutidas:** Identidad y sesión real, perfil y privacidad, comentarios por juego, listas personalizadas, exportación de colección

---

## Identidad y sesión real

| Opción | Descripción | Seleccionada |
|--------|-------------|--------------|
| Solo cuentas demo | Permite trabajar únicamente con usuarios sembrados. | |
| Registro y login reales | Persiste usuarios, valida credenciales, autoriza por propietario y protege el flujo completo. | ✓ |

**Elección del usuario:** La Fase 5 debe tener registro e inicio de sesión
reales, con validación, autorización, seguridad y persistencia en base de datos.
**Notas:** Las cuentas sintéticas permanecen como demo separada; el usuario de
login es también el alias público inmutable.

---

## Perfil y privacidad

| Opción | Descripción | Seleccionada |
|--------|-------------|--------------|
| Alias editable | Permite cambiar el identificador visible del perfil. | |
| Alias igual al usuario | El alias coincide con el usuario de login y no se edita. | ✓ |
| Público/privado | Colecciones y favoritos pueden ser visibles o privados. | ✓ |
| Solo amigos | Requiere una relación de amistad y controles sociales. | Diferida |

**Elección del usuario:** Alias igual al usuario y no editable; añadir biografía,
avatar y una estantería editable de cinco favoritos con privacidad.
**Notas:** Se implementará público/privado. La opción solo para amigos se difiere
porque no existe todavía un sistema de amistades.

## Comentarios por juego

| Opción | Descripción | Seleccionada |
|--------|-------------|--------------|
| Un comentario por usuario y juego | El autor puede crear, editar y eliminar su comentario. | ✓ |
| Varios comentarios | Permite historial o múltiples comentarios por juego. | |

**Elección del usuario:** Un comentario por usuario y juego, con sección de
comentarios en la ficha del juego.
**Notas:** El usuario puede ver sus comentarios; la visibilidad de comentarios
de amigos se deja para cuando exista la relación social.

## Listas personalizadas

| Opción | Descripción | Seleccionada |
|--------|-------------|--------------|
| Listas manuales de la colección | El usuario crea listas, añade juegos y los ordena manualmente. | ✓ |
| Listas automáticas | El sistema calcula el contenido a partir de filtros o señales. | |

**Elección del usuario:** Listas personalizadas de la colección, con privacidad
pública o privada.
**Notas:** La lista no es una recomendación ni una búsqueda guardada.

## Exportación de colección

| Opción | Descripción | Seleccionada |
|--------|-------------|--------------|
| Solo CSV visible | Exporta los datos que el usuario puede ver en la página. | ✓ |
| CSV y JSON con importación | Añade JSON, vista previa de importación y conflictos por fila. | Diferida |

**Elección del usuario:** Solo exportación CSV con los datos visibles en la
aplicación.
**Notas:** JSON e importación quedan fuera de esta fase y requieren reconciliar
PORT-02 y PORT-03.

## Criterio del agente

- Elegir la implementación concreta del avatar, estados de conservación,
  representación de precio/moneda y constraints secundarios, manteniendo la
  privacidad y validación backend.
- Impedir duplicados dentro de una misma lista salvo que el diseño posterior
  justifique otra cosa.

## Ideas diferidas

- Red de amistades y visibilidad “solo amigos”.
- JSON e importación de datos.
