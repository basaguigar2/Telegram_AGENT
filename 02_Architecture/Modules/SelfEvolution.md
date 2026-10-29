# Self Evolution

Estado: Diseño (implementado parcialmente -- ver memory_engine.create_insight / pending_insights)
Depende de: Schemas/Entities.md (entidad Insight), Schemas/Events.md, MemoryEngine.md

---

# Objetivo

JARVIS debe poder mejorar continuamente, pero nunca modificándose sin control. Este documento define cómo una limitación detectada se convierte en una propuesta de mejora trazable, nunca en un cambio silencioso.

---

# Distinción con `flag_for_claude`

Ya existe `memory_engine.flag_for_claude()`, pero resuelve un caso distinto: una tarea puntual del usuario que excede lo que el modelo local puede hacer ahora mismo. La autoevolución es otra cosa: el propio sistema, sin que el usuario pida nada, detecta un patrón repetido de limitación y lo deja anotado para revisión futura. No se mezclan en el mismo mecanismo.

---

# Por qué se reutiliza la entidad Insight

`Schemas/Entities.md` ya define Insight como "patrón detectado", con ciclo de vida `detectado -> validado -> descartado` (Schemas/Lifecycle.md) y tabla `insight` (`pattern`, `validated`) en el esquema real. Una propuesta de mejora del sistema es, en el fondo, un tipo concreto de Insight -- no hace falta una entidad nueva para algo que el esquema ya modela.

---

# Proceso (9 pasos)

1. **Detectar una limitación.** Cualquier módulo puede detectarla -- hoy, el candidato natural es Supervisor Agent, que ya revisa el registro de eventos en busca de patrones (ejecuciones fallidas, bloqueos repetidos).
2. **Registrar la limitación.** `memory_engine.create_insight(pattern, source)` -- queda en estado `detectado`.
3. **Analizar el impacto.** Manual por ahora (el usuario lo revisa) -- no hay análisis automático de impacto todavía, sería sobre-ingeniería sin datos suficientes de uso real.
4. **Proponer una mejora.** Texto libre dentro del propio `pattern`, o una segunda entrada de Insight enlazada -- se decide caso a caso, no hay estructura rígida todavía.
5. **Justificar técnicamente.** Igual que 4, parte del contenido del Insight.
6. **Solicitar aprobación cuando corresponda.** Un Insight nunca se auto-aplica -- `validated` solo lo cambia el usuario (mismo patrón que `resolve_decision`, nunca automático).
7. **Implementar la mejora mediante los agentes adecuados.** Trabajo humano + Builder Agent, como cualquier otro cambio de código -- la autoevolución no se salta el resto de la arquitectura, solo alimenta de dónde salen las ideas.
8. **Validar que funciona.** Igual que cualquier cambio: pruebas antes de dar por bueno.
9. **Registrar el aprendizaje.** Se marca el Insight como `validado` y queda en el histórico -- nunca se borra, solo se archiva si deja de ser relevante.

---

# Backlog

El backlog de autoevolución de JARVIS es la lista de Insights con `validated = 0` (`memory_engine.pending_insights()`), ordenados por fecha. No es una tabla nueva ni una vista especial, es una consulta sobre lo que ya existe.
