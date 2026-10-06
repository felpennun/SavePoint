# Cómo contribuir a SavePoint

SavePoint es un proyecto académico de una sola persona (un Trabajo Fin de Grado), pero acepta
issues y propuestas. Las reglas completas están en [`CONVENTIONS.md`](CONVENTIONS.md); aquí va lo
mínimo para contribuir.

## Antes de empezar

1. Levanta el entorno local siguiendo el [`README`](README.md) (`docker compose -f infra/compose.yaml up --build --wait`).
2. Abre una [issue](https://github.com/felpennun/SavePoint/issues) para cualquier cambio que no
   sea un arreglo trivial, y explica el problema antes de proponer la solución.
3. Trabaja en una rama y abre una pull request contra `main`.

## Pruebas

Un cambio de comportamiento lleva su prueba. Antes de abrir la PR ejecuta:

```sh
docker compose -f infra/compose.yaml run --rm api pytest apps/api -q
corepack pnpm --dir apps/web test --run
```

Los recorridos de extremo a extremo (Playwright) se lanzan con
`corepack pnpm exec playwright test e2e/ --project=chromium`.

## Mensajes de commit

Formato [Conventional Commits](https://www.conventionalcommits.org/) en inglés:

```
<tipo>(<ámbito>): <resumen>

[cuerpo opcional: el porqué, no el qué]

[Refs #<issue> | Closes #<issue>]
```

- **Tipos:** `feat`, `fix`, `docs`, `test`, `chore`, `build`, `refactor`.
- **Resumen:** en imperativo y minúsculas, sin punto final.
- **Issues:** `Refs #N` enlaza el commit con la issue sin cerrarla; `Closes #N` la cierra cuando el
  commit llega a `main`. La referencia va como línea aparte, no en el resumen.
- Si el cambio se hizo con ayuda de un asistente de IA, el commit termina con
  `Co-Authored-By: <modelo> <noreply@anthropic.com>`.

## Qué nunca va en un commit, una issue o una PR

- Cadenas de conexión, contraseñas, claves de API, tokens o cookies, ni siquiera fragmentos
  ocultados ni nombres de host de un proveedor real (Neon, Render, Vercel).
- Capturas o registros que no se hayan revisado antes con ese criterio.

## Licencia de las contribuciones

Al enviar una contribución aceptas que se publique bajo la misma licencia que el resto del
repositorio.
