---
tags: [concepto, tema/arquitectura, tema/seguridad]
---

# Frontera de sesion same-origin

Django emite y valida la sesion; el navegador solo llama rutas same-origin de
Next.js, que las reescriben al API. Mutaciones con token CSRF, cookies con
`credentials: same-origin`, logout que invalida la sesion, redirects solo a paths
relativos. Ningun bearer token accesible a JavaScript.

## Enlaces

- [[Monolito modular Django]] · [[Frontend Next.js]] · [[Cuentas simuladas]]
- [[ADR-004 - Sesion Django same-origin]]
