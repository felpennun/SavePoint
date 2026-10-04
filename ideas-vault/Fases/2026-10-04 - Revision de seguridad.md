---
tags: [seguridad, despliegue, informe]
estado: vigente
fecha: 2026-10-04
---

# Revisión de seguridad y causa del fallo de despliegue (2026-10-04)

Alcance: CI y despliegue, dependencias (Node y Python), configuración de Django y de Next.js, secretos en el
árbol y en el historial, y las superficies nuevas de esta sesión (imágenes de perfil, cambio de contraseña y de
nombre, borrado de cuenta, notificaciones, listas, exportación a Excel). Es una revisión estática y de configuración,
sin prueba de intrusión ni escáner dinámico.

## 1. Por qué la web no se despliega

- Render despliega la API con `autoDeployTrigger: checksPass` (`infra/render.yaml`): solo despliega si el flujo
  "Quality gates" de GitHub pasa.
- Ese flujo **falla en todos los pushes desde el 14/09** (los 40 últimos). Falla siempre en el primer paso,
  `docker compose up --build --wait`, con `container savepoint-recommendation-worker-* has no healthcheck configured`:
  los workers de recomendación tenían `healthcheck: disable: true` y el ejecutor de CI lo rechaza con `--wait`.
- Consecuencia medida hoy: la API pública en Render sigue en el commit `ff5aa2e` (05/09, 571 commits atrás) y
  `/api/catalogue/stats/` da 404. Vercel sí despliega cada push (todos "success"), así que el frontal nuevo habla con
  una API antigua: `/es` no responde en 60 s y `/es/catalogue` da 500; `/es/login` sí funciona.
- Efecto de seguridad: **las puertas de seguridad de CI nunca llegan a ejecutarse** (`check-security.ps1`,
  `check --deploy`, comprobación de migraciones y pruebas de seguridad de la API van después de ese paso).
- Arreglo preparado (sin commit): `infra/compose.yaml` da a los workers un healthcheck real (comprueba que su propio
  proceso `process_recommendation_jobs` está vivo, sin contarse a sí mismo) en lugar de desactivarlo. Comprobado en
  local: `compose config` válido, `up --wait` con los cuatro workers "healthy", y los pasos posteriores de CI
  ejecutados a mano: `check --deploy` en producción sin incidencias, `makemigrations --check` sin cambios, pruebas de
  seguridad de la API 10/10 y escáner de secretos PASS.
- Falta: hacer push y confirmar que el CI pasa y que Render redespliega (aplicará las migraciones nuevas en el
  arranque). Si algún paso posterior fallara en el ejecutor de CI, aparecerá entonces.

## 2. Hallazgos

| # | Gravedad | Hallazgo | Recomendación |
|---|---|---|---|
| 1 | Alta | Puertas de seguridad de CI inoperantes desde el 14/09 (ver §1). | Subir el arreglo del healthcheck. |
| 2 | Alta | `next` 16.3.4 afectado por GHSA-vcvr-r3jv-pc5j (ejecución remota de código en `next/og` `ImageResponse`, versiones 16.2.0 a 16.3.5). El proyecto **no usa** `next/og` ni imágenes OG generadas, así que no es explotable tal como está, pero está en producción. | Subir a 16.3.6 (versión exacta, con su registro de legitimidad de dependencias). |
| 3 | Media | `urllib3` 2.7.0: tres avisos PYSEC-2026-4175/4176/4177, corregidos en 2.8.0. Llega por `requests`, que solo usa el comando de importación de IGDB fuera de línea (ninguna petición de usuario llama a terceros, RN-9). | Fijar 2.8.0 en el lock. |
| 4 | Media-baja | La subida de foto y portada lee el cuerpo entero (`upload.read()`) antes de comprobar el tope de 512 KiB, y el `PUT` de imágenes no tiene límite de ritmo propio. Una cuenta autenticada podría enviar cuerpos grandes; lo frena el proxy, no la aplicación. | Comprobar `upload.size` antes de leer y añadir un ámbito de throttling para las imágenes. |
| 5 | Baja | `infra/compose.yaml` lleva contraseñas de demostración en claro (`DEMO_PASSWORD`, `DEMO_ACCOUNTS`) y la base local `local_test_only`. Son de entorno local y el repositorio es privado. | Si esas mismas contraseñas están en el Render público, cambiarlas; mejor sacarlas del compose a variables de entorno. |
| 6 | Baja | CSP con `script-src 'unsafe-inline'` (seguimiento ya documentado en `next.config.ts`). | Pasar a nonces con middleware cuando haya tiempo. |
| 7 | Baja | Las imágenes de amistades se sirven con `Cache-Control: private, max-age=3600`; tras eliminar o bloquear a alguien, el navegador del otro puede conservarlas hasta una hora. | Reducir el tiempo o usar `no-store` en esas rutas. |
| 8 | Info | Las imágenes se validan por firma (JPEG, PNG o WebP) y no por descodificación completa; se sirven con tipo fijado, `nosniff` y solo al titular y a amistades aceptadas. Es suficiente para este uso. | Nada. |
| 9 | Info | No se puede activar protección de rama (la cuenta no admite la función en repositorios privados). Hay 8 PR de Dependabot abiertos, entre ellos `djangorestframework` 3.18.1 (parche) y el salto mayor de `django` 6.1.1. | Aplicar parches menores; evaluar el mayor aparte. |

## 3. Lo que está bien

- Django: `check --deploy` en modo producción sin avisos; HSTS de un año con subdominios y precarga, redirección a HTTPS,
  cookies de sesión y CSRF seguras en producción, `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy` y clave secreta de
  50 caracteres como mínimo; autenticación solo por sesión (sin Basic) y CSRF obligatorio.
- Contraseñas: las mismas cuatro validaciones en registro y cambio; cambio, borrado de cuenta y cambio de nombre con
  límite de ritmo; el cambio invalida las demás sesiones.
- Autorización: las proyecciones de perfil son listas explícitas de campos; las listas, comentarios, notificaciones y
  respuestas se filtran siempre por el usuario autenticado; las imágenes de otra persona solo para amistades aceptadas.
- Exportaciones (CSV y Excel): los valores que empiezan por `=`, `+`, `-` o `@` se neutralizan.
- Cabeceras de Next.js: CSP restrictiva (sin objetos, sin marcos ajenos, `base-uri` y `form-action` propios),
  `Permissions-Policy` cerrada, sin `dangerouslySetInnerHTML` ni `eval` en el código.
- Secretos: el escáner del repositorio (código, salida de compilación, capas de imágenes y registros) da PASS; el
  historial solo contiene valores de prueba y señuelos. Imágenes base fijadas por digest; la API y la web corren sin
  root; los permisos del flujo de GitHub son `contents: read`.
- Pruebas: 773 de backend y 66 de frontend pasaron hoy.

## 4. Pendiente de decidir

- Subir el arreglo de CI (desbloquea Render y activa las puertas de seguridad).
- Subir `next` a 16.3.6 y `urllib3` a 2.8.0.
- Endurecer la subida de imágenes (#4).
