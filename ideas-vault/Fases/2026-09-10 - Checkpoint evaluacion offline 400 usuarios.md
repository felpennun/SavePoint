---
fecha: 2026-09-10
estado: checkpoint técnico superado; freeze de código pendiente
tipo: fase/evidencia
---

# Checkpoint: evaluación offline sobre 400 usuarios sintéticos

La auditoría viva confirma que SavePoint puede iniciar la evaluación final sin
cambiar el protocolo: corpus activo `2026.09.2`, protocolo 12, 400 cuentas
aisladas, split `240/80/80`, snapshots de ratings y PopScore coincidentes,
13.621 candidatas y test sin consumir. La suite de evaluación pasa 95 tests.

La unidad de análisis será el usuario. Hay 390 perfiles con un positivo
elegible y 10 perfiles sin historial que no pueden participar en leave-one-out;
se conservan como cohorte descriptiva de cold start. El test asigna 80 cuentas y
producirá 79 observaciones evaluables. Esto debe aparecer explícitamente en la
interpretación del TFG.

El gate científico todavía requiere congelar con un commit el protocolo y el
código de evaluación/recomendación que ahora están modificados sin commit. Los
cambios de `apps/web` pertenecen a otra LLM y no deben tocarse.

Fuente canónica: [checkpoint de verificación](../../docs/verification/evaluation-checkpoint-400-users-2026-09-10.md).
Prompt operativo: [prompt para iniciar el cálculo](../../docs/verification/prompt-offline-evaluation-400-users.md).
Metodología: [protocolo de evaluación](../../docs/methodology/evaluation-protocol.md) y
[algoritmos y base científica](../../docs/methodology/recommendation-algorithms.md).

Relacionado: [[2026-09-09 - Estadistica reproducible]], [[2026-09-10 - Sincronizacion nocturna y corpus dinamico]] y
[[Fase 3 - Recomendadores explicables y baselines]].
