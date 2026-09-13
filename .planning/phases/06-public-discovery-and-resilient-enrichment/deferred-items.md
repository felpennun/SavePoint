# Elementos diferidos de la Fase 6

## Verificación de navegador pendiente

- La ejecución declarada `docker compose -f infra/compose.yaml run --rm web pnpm --dir apps/web test -- --run catalogue-filters` ejecuta también `components/__tests__/nav-overflow.test.tsx`.
- Esa suite no puede iniciar porque la imagen web no contiene el binario Chromium de Playwright.
- La incidencia es preexistente y está fuera del write-set de `06-05`; las pruebas focalizadas de `catalogue-filters` y TypeScript sí pasan.
