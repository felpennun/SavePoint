---
tags: [fase/3, fase/4, tema/evaluacion, resultado, decision-pendiente]
---

# Protocolo v15 — leave-fraction-out sobre el tag dominante: fundamento y alternativas descartadas

Decisión de diseño tomada el 2026-09-12, sustituyendo el leave-one-out de un único positivo
(protocolo v14) por un mecanismo que retira una fracción adaptativa de las obras del tag de
contenido más pesado en el propio perfil del usuario. Este documento recoge el fundamento
científico de la elección y, explícitamente, por qué se descartaron las alternativas
consideradas en la misma sesión.

## Qué se implementó

`evaluation/splits.py::leave_fraction_out_dominant_tag`:

1. Se calcula el perfil de contenido completo del usuario y su tag más pesado (`dominant_tag`).
2. Se localiza el pool de obras elegibles (relevancia D-17 + piso de rating externo ≥70,
   protocolo v14) que comparten ese tag — tamaño *M*.
3. `n = máx(1, mín(M, techo(fracción × M)))`, con `fracción = 0.3` (`protocol.split.dominant_tag_fraction`).
4. Se simula retirar esas *n* obras y se recalcula el perfil sin ellas. Si el tag deja de ser
   el primero en ese perfil recalculado, se reduce *n* en 1 y se repite — **salvo que n ya sea
   1**, en cuyo caso se acepta igualmente aunque el tag quede desplazado (el mínimo de 1 manda
   sobre la condición de dominancia).
5. Se registra `achieved_rank` (1 si se mantuvo dominante, ≥2 si se desplazó) como dato
   descriptivo, no como criterio de exclusión.

Verificado sobre los 400 usuarios antes de congelar (fracción=0.3): 0% se queda sin ningún
ejemplo del tag; 78,6% conserva el tag en 1er puesto, 10,9% pasa a 2º, 4,7% a 3º, 5,7% a 4º
o peor.

## Fundamento científico

### 1. Familia "All-but-N" / "Given-N" (Breese, Heckerman y Kadie, 1998; Herlocker et al., 2004)

El protocolo clásico de partición para evaluar recomendadores sobre un historial de usuario
define dos familias, ya con nombre en la literatura desde Breese, Heckerman y Kadie
(*"Empirical Analysis of Predictive Algorithms for Collaborative Filtering"*, UAI 1998) y
sistematizadas por Herlocker, Konstan, Terveen y Riedl (*"Evaluating Collaborative Filtering
Recommender Systems"*, ACM TOIS 2004):

- **All-but-N**: se retiran N valoraciones del perfil del usuario y se comprueba si el
  sistema las recupera. El leave-one-out que usábamos en protocolos v6-v14 es el caso
  particular N=1.
- **Given-N**: al revés — se da al modelo solo N valoraciones (perfil deliberadamente
  pequeño) y se mide si predice el resto, normalmente mucho más numeroso.

Lo implementado hoy es **All-but-N generalizado**, donde N ya no es fijo globalmente sino
adaptativo por usuario (proporcional al tamaño de su propio pool del tag dominante). Esto
está dentro del marco ya establecido, no es una invención sin precedente — solo cambia cómo
se determina N.

### 2. Sesgo de popularidad en la selección del retenido (Cremonesi, Koren y Turrin, 2010; Steck, 2011)

Ya aplicado en protocolo v14 (piso `heldout_min_external_rating=70`) y heredado sin cambios
aquí: el ítem retenido debe superar un piso de calidad catalogada, no solo el gusto personal
del usuario, para que el acierto no dependa parcialmente de la popularidad/calidad del ítem
en vez de solo del modelado de gusto.

### 3. Perfiles de contenido multi-rasgo ponderados (Pazzani y Billsus, *"Content-Based
Recommendation Systems"*, 2007 — capítulo de referencia estándar en sistemas de recomendación
basados en contenido)

Justifica por qué un tag desplazado a 2º o 3er puesto **sigue siendo una señal válida**, no
un fallo de la prueba: un perfil de contenido es, por diseño en toda la familia de sistemas
basados en contenido (y en el nuestro concretamente, `facet_similarity()`), una **suma
ponderada sobre todos los rasgos coincidentes**, no una decisión de un único rasgo ganador.
Retirar obras del rasgo #1 reduce su peso relativo, pero el algoritmo evaluado sigue
utilizando ese rasgo (con menos peso) exactamente igual que utilizaría cualquier otro —
probar la recuperación de un tag que pasó a ser #2 sigue siendo una prueba fiel a cómo el
sistema realmente puntúa, no una prueba distinta.

### 4. Granularidad de la métrica y potencia estadística (Herlocker et al., 2004, discusión
sobre sensibilidad de la comparación a la métrica elegida)

Con leave-one-out, `Recall@K` es binario (0 o 1) por usuario — una única observación de baja
información. `evaluation/metrics.py` ya está escrito para el caso general multi-positivo
("*written for the general multi-positive case so Phase 3 can reuse them unchanged*"), así
que retener varias obras por usuario convierte esa métrica en continua, con más potencia
estadística para las mismas 79-80 personas del split de test — el problema que limitaba las
comparaciones por pares en el resultado de protocolo v12 (§8.4 de
`evaluation-results-400-test-2026-09-10.md`).

## Por qué NO se usaron las otras alternativas consideradas

Todas se discutieron explícitamente en la sesión antes de decidir; se descartaron por
motivos concretos, no por preferencia arbitraria.

| Alternativa | Por qué se descartó |
|---|---|
| **Given-N puro** (perfil deliberadamente pequeño, predecir el resto) | Exige reducir el perfil del usuario a un puñado de valoraciones — contradice directamente el trabajo de esta misma sesión (subir `guaranteed_eligible_minimum`, tag por usuario) para que el perfil tenga señal robusta. Given-N se usa típicamente para estudiar comportamiento de arranque en frío, una pregunta de investigación distinta a "¿recupera contenido afín a un gusto ya consolidado?". |
| **K-fold sobre todos los positivos** | Usa toda la señal del usuario (ventaja real), pero cuesta K pasadas de cálculo por usuario y no se centra en el tag dominante — la pregunta de investigación del autor es específicamente sobre el género favorito, no sobre el historial completo repartido en bloques arbitrarios. |
| **Predicción de rating (RMSE/MAE)** | Mide si el sistema acierta la *nota* que pondría el usuario, no si el *ranking* prioriza bien el contenido — pregunta de investigación distinta. McNee, Riedl y Konstan (2006, *"Being accurate is not enough"*) es precisamente el argumento ya citado en este proyecto para no conformarse con métricas de precisión de predicción como sustituto de calidad de ranking. |
| **Solo más allá del acierto (cobertura/diversidad/novedad, sin retirar nada)** | Ya se usa como complemento (§6 de los resultados de protocolo v12/v14) — pero no contesta "¿recupera lo que ya sabemos que le gusta?" en absoluto, al no haber ningún ítem de verdad-base retenido contra el que comparar. |
| **Retirar N fijo global (1, o 3) sin ajuste adaptativo** | Probado esta misma sesión con N=1 (arranque en frío en 74% de usuarios bajo la población anterior) y N=3 (arranque en frío en 19% incluso tras subir el mínimo garantizado, más un 21% de vuelco de dominancia con el tag compartido). Ninguno escala con cuánta biblioteca tiene cada usuario del tag en cuestión — la fracción adaptativa sí. |
| **Exigir que el tag se mantenga #1 sin excepción** | Habría excluido usuarios en los que ningún *n* ≥ 1 preserva la dominancia — contradice el argumento del punto 3 (un tag en 2º/3er puesto sigue siendo señal real, per `facet_similarity`) y habría vuelto a reducir la muestra evaluable sin necesidad. |

## Correcciones encontradas durante la primera corrida real (mismo día)

### 1. El tag dominante se comparaba contra la plataforma (bug)

La primera implementación calculaba el "tag dominante" con
`max(profile_inputs.positive.items(), key=...)` sobre el diccionario **completo** del
perfil — que mezcla `tag:*`, `platform:*`, `franchise:*` y `developer:*` en las mismas
claves. Si la plataforma acumulaba más peso bruto que cualquier tag individual (habitual en
un usuario que tiene casi todo en la misma plataforma), el usuario quedaba excluido del
estudio por "no tener un tag dominante" — aunque sí lo tuviera.

El autor lo detectó en vivo, con el argumento correcto: `facet_similarity()` (el código real
de puntuación, usado por los 16 algoritmos tanto en web como offline) trata cada familia de
faceta como una señal **independiente**, combinadas después con pesos fijos del sistema
(`FACET_WEIGHTS["tag"]=0.75`, `FACET_WEIGHTS["platform"]=0.25`, constantes, no dependientes
de los datos del usuario) — el género nunca compite contra la plataforma en la puntuación
real, así que tampoco debería competir en la selección de qué retirar para el estudio.
Corregido: tanto la búsqueda del tag dominante como la comprobación de rango tras la
retirada se restringen ahora a claves `tag:*` únicamente. Verificado: el bug nunca tocó
`facet_similarity()`/`combine()` ni ninguna recomendación real (web u offline, en ningún
protocolo anterior) — estaba aislado en esta función nueva de selección de candidatos para
el estudio, no en el camino de puntuación.

### 2. Caída a leave-one-out simple en vez de excluir al usuario

Diseño inicial: si `leave_fraction_out_dominant_tag` no se podía construir para un usuario
(sin ninguna señal de tag de contenido en su perfil, o su tag dominante sin candidatas que
pasen el piso de rating), se excluía del estudio. El autor lo cuestionó con una corrida real
en marcha: esos usuarios sí tienen un positivo elegible de verdad — el mecanismo simple
(protocolo v6-v14) puede usarlo perfectamente, así que excluirlos no es necesario ni
realista.

Corregido en `evaluation/candidates.py::build()`: si `leave_fraction_out_dominant_tag`
devuelve `None` bajo la estrategia `leave_fraction_out_dominant_tag_per_user`, se cae al
`leave_one_out` simple para ese usuario específico, en vez de propagar la exclusión. **Solo
queda excluido un usuario con cero positivos elegibles en absoluto** (los 10 del arquetipo
`no_history`, que ningún mecanismo puede evaluar) — el resto siempre entra en el estudio,
con el mecanismo más específico cuando se puede construir, con el genérico cuando no.

No se registra todavía, en el propio artefacto, qué mecanismo se usó para cada usuario
(fracción vs. respaldo de un único ítem) — se puede inferir de forma aproximada por el
tamaño de `heldout_work_ids` (siempre 1 en el respaldo, variable en el mecanismo de
fracción), pero un campo explícito quedaría más claro para el capítulo de metodología del
TFG. Pendiente, no bloqueante.

## Pendiente

Lanzar la evaluación real bajo protocolo v15 con ambas correcciones aplicadas. Ver la
sesión de esta misma fecha para el estado exacto de la implementación.
