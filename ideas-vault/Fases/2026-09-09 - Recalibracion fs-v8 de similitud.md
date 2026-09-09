# Recalibracion fs-v8 de similitud — 2026-09-09

Fuente canonica: [[../../docs/verification/recommendation-architecture-2026-09-09|contrato compartido de algoritmos]].

Se eleva el bonus maximo de saga/franquicia a `0,20` y el de desarrollador a
`0,15`. Cada uno se calcula como `peso_maximo x afinidad`; tener el campo no
concede puntos sin coincidencia con el perfil del usuario.

El nucleo genero/plataforma mantiene los pesos `0,50` y `0,25`, pero cambia a
afinidad F0,5. La precision del candidato pesa mas que la cobertura del perfil,
reduciendo la ventaja de obras con listas muy amplias de generos o plataformas.
La regla es comun a web, workers y evaluacion offline y se identifica como
`fs-v8` / `facet-similarity-v4`.
