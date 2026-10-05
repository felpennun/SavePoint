---
tags: [producto, privacidad, experiencia]
fecha: 2026-10-06
estado: vigente
fuente: "[[../../apps/api/library/views.py]]"
---

# Invariantes de colección y sesión

## Qué ha cambiado

- El número de copias mostrado en la colección cuenta solo las copias de la persona autenticada.
- La API expone si el juego pertenece a la colección de esa persona; la interfaz usa ese dato para ofrecer el formulario de comentario.
- La lectura de comentarios visibles no depende de pertenecer a la colección. La API sigue exigiendo pertenencia para crear comentarios.
- El login, el cierre de sesión y el registro recargan el inicio localizado. Las páginas dinámicas no se conservan en la caché de navegación del cliente, para refrescar la sesión y el juego aleatorio del inicio.

## Impacto

Estas reglas mantienen los datos de inventario separados por propietario, hacen explícita la elegibilidad para comentar y evitan que una página dinámica reutilizada muestre el estado de sesión o el contenido aleatorio anterior.

## Fuentes canónicas

- `apps/api/library/views.py`
- `apps/web/components/GameComments.tsx`
- `apps/web/app/[locale]/login/page.tsx`
- `apps/web/app/[locale]/register/page.tsx`
- `apps/web/components/AccountSwitcher.tsx`
- `apps/web/next.config.ts`

## Enlaces relacionados

- [[Requisitos - Backlog listas e inventario]]
- [[Requisitos - Cuentas y perfiles]]
- [[Frontera de sesión same-origin]]
