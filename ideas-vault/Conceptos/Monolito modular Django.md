---
tags: [concepto, tema/arquitectura]
---

# Monolito modular Django

Backend Django 5.2 LTS + DRF 3.18 para identidad, reglas y persistencia. Modulos
por dominio (`accounts`, `catalogue`, `library`, `recommendations`, `evaluation`)
que comparten despliegue y PostgreSQL. El dominio es relacional y CRUD-heavy, y
Django aporta auth, ORM, validacion, migraciones y admin maduros.

## Enlaces

- [[Frontend Next.js]] · [[PostgreSQL]] · [[Jobs offline]] · [[Frontera de sesion same-origin]]
- [[ADR-001 - Monolito modular Django + Next.js]] · [[Stack de backend e investigacion]]
