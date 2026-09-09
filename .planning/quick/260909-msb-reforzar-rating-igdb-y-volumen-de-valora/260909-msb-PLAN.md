---
quick_id: 260909-msb
status: complete
---

# Reforzar rating IGDB y volumen de valoraciones

1. Crear una señal compuesta y compartida de calidad-confianza: rating IGDB
   con potencia 2 y volumen de `total_rating_count` normalizado.
2. Usar esa señal en las combinaciones web/offline sin incluir `display_rating`
   ni duplicar el volumen como señal independiente.
3. Actualizar contrato, explicaciones, fingerprints y pruebas; invalidar la
   configuración anterior mediante una nueva versión de señales.
