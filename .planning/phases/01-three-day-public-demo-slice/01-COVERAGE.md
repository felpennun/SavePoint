# Cobertura de integración externa — adquisición Wikidata/Commons

## Decisión

La adquisición de la instantánea se considera una integración con APIs externas de preparación de datos. La aplicación desplegada y local no integra ninguna API externa en runtime: importa artefactos versionados y funciona sin red.

## Superficie de capacidades

| Capacidad externa | Decisión | Razón y límite |
|---|---|---|
| Wikidata Query Service/SPARQL | INTEGRATE (offline acquisition only) | Obtener QID, títulos, aliases y metadatos estructurados CC0 con consulta, fecha de corte, User-Agent y respuesta archivados |
| Wikimedia Commons metadata/file pages | INTEGRATE (offline review only) | Revisar licencia, autor, URL y atribución por asset; no asumir que CC0 de Wikidata cubre imágenes |
| Descarga en arranque o request | OPT-OUT | Rompería reproducibilidad, disponibilidad offline y aislamiento del corpus |
| Credenciales/API keys | OPT-OUT | Estas fuentes no las requieren para el flujo elegido; no se incorpora ningún secreto |
| Enriquecimiento vivo | OPT-OUT | Pertenece a Phase 4 y no puede modificar la instantánea de investigación |
| URL proporcionada por usuario | OPT-OUT | No existe fetch genérico; la adquisición sólo usa hosts HTTPS allowlisted y consultas versionadas |

## Contrato de adquisición

El comando de adquisición es explícito, aplica timeout, límite de tamaño, ritmo conservador, User-Agent identificable y allowlist de hosts. Escribe primero a un área temporal, valida formato y sólo promueve una instantánea cuando el manifiesto contiene fuente, URL, licencia, fecha UTC, revisión/fecha de corte, consulta, recuento y SHA-256. Los assets llevan manifiesto separado y cualquier elemento no revisado usa el placeholder propio. Los fallos, 429, respuestas parciales, HTML inesperado, checksum incorrecto o licencia ausente impiden la promoción. Ningún dato externo se interpreta como HTML ejecutable.

## Seguridad y reproducibilidad

- No hay llamada externa desde `web`, `api`, seed, migraciones ni health checks.
- No se siguen redirects fuera de la allowlist ni se aceptan esquemas distintos de HTTPS.
- La instantánea promovida es inmutable; el importador verifica checksum e idempotencia.
- La evidencia registra consulta, herramientas, resultado, revisión humana de media y decisión del autor.
