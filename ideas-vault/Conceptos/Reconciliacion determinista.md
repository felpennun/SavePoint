---
tags: [concepto, tema/datos, fase/2]
---

# Reconciliacion determinista

Reglas deterministas para reconciliar identificadores de fuente y valores en
conflicto (DATA-07), sin coincidencias difusas. La identidad canonica de una obra
es el `id` de IGDB via `SourceRecord(source="igdb")`. Una respuesta RAWG se
asocia por: (1) `slug` exacto; (2) titulo normalizado + ano simultaneos; (3) si
no hay coincidencia unica, se descarta y se cuenta como no emparejada. Para
resolver a un unico rating: usar IGDB si `rating_count >= 1000`, si no la fuente
con mas votos, empate a favor de IGDB, y si nada sirve, mediana marcada de
generos como fallback explicito.

## Enlaces

- [[Identificadores canonicos]] · [[Ratings externos]] · [[IGDB]] · [[RAWG]]
- [[ADR-008 - Ratings externos gobernados y RAWG]]
