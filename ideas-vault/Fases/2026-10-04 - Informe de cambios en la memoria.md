---
tags: [informe, memoria, social, perfil, capturas]
estado: vigente
fecha: 2026-10-04
---

# Informe de cambios en la memoria (módulo social y personalización)

Cierra el plan de [[2026-10-04 - Informe de cambios pendientes de la memoria]] con cambios pequeños, sin secciones
nuevas. Todo está en el árbol de trabajo, **sin commit**. La memoria compila sin errores ni avisos
(91 páginas; eran 89).

## 1. Textos (`thesis/sections/`)

### 04_analisis.tex
- **Modelo de dominio (prosa):** una frase nueva sobre `AccountProfile` (nombre completo, biografía, foto, portada y
  ajustes de privacidad) y `SocialNotice` (avisos de solicitud aceptada y de recomendación añadida a pendientes).
- **Requisitos funcionales:** dos filas nuevas, `PROF-01` (editar el perfil y su visibilidad) y `SOCIAL-05` (recomendar
  juegos a un amigo y responder a las recibidas). Ambos ya contaban como completos en la tabla de trazabilidad
  (PROF 3/3, SOCIAL 3/3), así que **no cambian los totales (86/88)**. `SOCIAL-04` pasa de "quien no es amigo no ve nada
  de la cuenta" a "solo ve el nombre de usuario", que es lo que hace la aplicación.
- **Tabla de requisitos:** se le aplica `\tablecompact` (letra `\small` y menos separación de columnas) porque, con
  las dos filas nuevas, no cabía en una página. Cambia solo su aspecto.
- **Casos de uso:** `CU-14` (editar el perfil y la privacidad, PROF-01) y `CU-15` (responder a una recomendación,
  SOCIAL-05).
- **Reglas de negocio:** `RN-10` (el nombre de usuario se cambia una sola vez; la visibilidad admite solo dos niveles:
  privada o visible para las amistades).

### 05_diseno_arquitectura.tex
- **Tabla de endpoints:** cuatro filas nuevas: imagen de perfil y portada (`me/avatar/`, `me/cover/`); cambio de nombre
  de usuario, contraseña y eliminación de cuenta; notificaciones y respuesta a recomendaciones; exportación a Excel.
- **Seguridad de la proyección de perfil:** un párrafo breve: imágenes recortadas y comprimidas en el navegador, límite
  de 512 KiB, validación por firma de formato en el servidor, servidas solo al titular y a sus amigos aceptados; la
  eliminación de la cuenta exige contraseña y su evento de auditoría no lleva actor (auditoría de solo anexado).
- **Corrección:** "el selector de cuenta" pasa a "el menú de cuenta".

### 06_implementacion.tex
- **Rutas del frontend:** se añade "el perfil propio".
- **Tres capturas con un párrafo** (sin subsección nueva), tras las de recomendaciones: amistades
  (`fig:amistades`), perfil propio (`fig:perfil`) y acceso + registro (`fig:acceso`, dos imágenes en una figura).
- **Verificación:** una frase que dice que el 4 de octubre de 2026 se repitieron las suites de backend y frontend
  (773 y 66 pruebas, todas en verde) y que el recorrido de navegador no se repitió tras esos cambios. La cifra
  736/70/56 del cierre de la Fase 7 se mantiene, porque es una fecha concreta.

## 2. Capturas (`thesis/figures/`, tema oscuro)

| Figura | Archivo | Origen |
|---|---|---|
| Amistades | `09-amistades-oscuro.png` | sesión de felipe, `froste` seleccionado, notificaciones tal como estaban |
| Perfil propio (pestaña Cuenta) | `10-perfil-oscuro.png` | sesión de felipe |
| Acceso | `06-iniciar-sesion-oscuro.png` | sin sesión, recortada a la altura del formulario |
| Registro | `07-registro-oscuro.png` | sin sesión, recortada |

El acceso y el registro solo existen sin sesión (con sesión redirigen a Inicio), por eso no están hechas con felipe.
Las demás capturas de la memoria (inicio, catálogo, colección, recomendaciones) ya eran de felipe y no se tocaron.
La captura de amistades también se actualizó en `e2e/artifacts/review-2026-10-04/con-sesion/`.

## 3. Diagramas

Regenerados con el script original, con cambios mínimos:
- `modelo-dominio.pdf`: `SocialNotice` y `AccountProfile` en el grupo "Cuentas y amistades", con flecha a `User`.
- `casos-uso.pdf`: `CU-14` y `CU-15`, con el actor "Persona usuaria" recolocado en vertical para que no se crucen líneas.

El resto de diagramas no se ha regenerado. El script quedó en `scripts/thesis-figures/generate_diagrams.py` (ya no
vive en `thesis/`, que contiene solo lo necesario para compilar).

## 4. Qué no se ha cambiado, a propósito

- **Pesos de MMR-pop:** la memoria sigue diciendo `content-cbf-mmr-pop-v1`, y la web publica `…-v2`. Es decisión tuya.
- Ninguna sección o subsección nueva; no se han tocado los capítulos 1-3, 7 y 8.
- No se ha escrito nada sobre estantería de DLC, comentarios múltiples, estadísticas del catálogo ni filtros.
- El diagrama de arquitectura, el de despliegue y el resto de figuras no se han tocado.

## 5. Antes de entregar

- **Datos en las capturas:** las cuentas de amistades que aparecen (`froste`, `Thor`, etc.) son usuarios de prueba del propio autor; no hay datos de terceras personas.
- **Recorrido de navegador (Playwright):** sin repetir tras los cambios de interfaz; la memoria lo dice así.
- **Commit y push:** pendientes. Archivos cambiados: 3 `.tex`, 2 PDF de diagramas, 4 PNG nuevos, la captura de
  e2e, `scripts/thesis-figures/` y los informes del vault.
