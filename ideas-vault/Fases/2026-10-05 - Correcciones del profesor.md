---
tags: [tfg, correcciones, memoria]
estado: en curso
fecha: 2026-10-05
---

# Correcciones del profesor (registro)

La memoria de `thesis/` se sincronizó el 2026-10-05 con `SavePoint TFG (2).zip`, la versión que ya lleva algunas
correcciones (12 ficheros cambian: bibliografía y secciones 00 a 08). Aquí se anota cada corrección pendiente o hecha.

## Hechas por Claude

1. **Capítulo "Diseño y arquitectura": falta un diagrama de clases/entidades.** El capítulo 4 tenía un modelo de
   dominio simplificado (solo nombres de entidad). Ahora la sección "Modelo de datos, API y sesión" incluye tres
   diagramas de entidades con atributos, claves y cardinalidades, generados desde los modelos reales de Django
   (Figuras 5.2 catálogo, 5.3 biblioteca y cuentas, 5.4 amistades y recomendaciones), con un párrafo que explica la
   notación, y el capítulo 4 enlaza a ellos. Generador reproducible: `scripts/thesis-figures/generate_modelo_datos.py`
   (paso 1 con Django extrae `models_meta.json`; paso 2 con matplotlib dibuja; cada atributo se valida contra el modelo).
   La tabla de endpoints (`tab:endpoints`) pasa de `[H]` a flotante para evitar media página en blanco.
   La memoria queda en 95 páginas.

## Pendientes

Las demás correcciones del profesor, a medida que el autor las vaya indicando.

Relacionado: [[2026-10-05 - Informe y plan para manana]].
