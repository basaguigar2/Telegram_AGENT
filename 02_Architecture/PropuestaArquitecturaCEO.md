# Propuesta — CEO como módulo compuesto, Capability Registry y ciclo de autoevolución

Estado: Propuesta para revisión (no implementada)
Autor: Claude, como arquitecto, a petición del usuario
Depende de: Constitution.md, Modules/Orchestrator.md, Modules/AgentFrameWork.md, Modules/ModelRouter.md, Schemas/Permissions.md, Roadmap.md

Este documento responde a un encargo explícito: revisar la arquitectura existente contra una nueva filosofía ("JARVIS no es un chatbot, es un Sistema Operativo Personal") y proponer cómo actualizar la documentación. No contiene código ni implementación. Es crítico a propósito, porque eso es lo que se pidió.

---

# 0. Contradicción que hay que resolver antes de nada

Antes de diseñar el CEO, hay una tensión real entre dos decisiones tuyas de la misma conversación, y no puedo avanzar sin nombrarla:

Minutos antes de este encargo, decidiste eliminar toda confirmación excepto para tres acciones (ejecutar un programa, eliminar algo, desplegar a producción). Este nuevo encargo reintroduce "la Constitución", "las políticas" y "los permisos" como cosas que **nada puede romper nunca**. Eso no es necesariamente contradictorio, pero solo funciona si la Constitución **se reescribe** para reflejar la decisión nueva (gate estrecho, solo 3 acciones) en vez de mantenerse como está ahora, que es mucho más amplia.

Ahora mismo, `Constitution.md` dice literalmente:

> Artículo 2: JARVIS nunca ejecutará una acción estratégica sin autorización explícita.
> Artículo 10: JARVIS nunca iniciará un proyecto, publicará contenido, desplegará software o realizará cambios estratégicos sin aprobación del usuario.

Esto es más amplio que "ejecutar, eliminar, desplegar" — cubre "cambios estratégicos" en general, una categoría difusa que en la práctica se ha usado hoy mismo para justificar pedir confirmación en casi todo. Si el Capability Registry y el Policy Engine siguen citando esta Constitución tal cual, vas a recrear exactamente la fricción que acabas de decidir eliminar, sin darte cuenta, porque el CEO "consultará la Constitución" como dice tu encargo, y la Constitución seguirá diciendo "cambios estratégicos" en genérico.

**Recomendación**: reescribir el Artículo 2 y el Artículo 10 para que citen explícitamente solo las tres acciones que decidiste mantener bajo control (ejecutar código, eliminar, desplegar a producción), y quitar la cláusula abierta "cambios estratégicos" — o, si quieres conservar algo de esa cláusula para el futuro (dinero real, por ejemplo, que mencionaste en otra conversación como límite futuro), acotarla con la misma precisión: nombrar la lista cerrada, no una categoría interpretable.

**Decisión pendiente que no has cerrado todavía**: para esas tres acciones, ¿siguen pidiendo tu "sí/no" (como ahora) o quedan bloqueadas del todo dentro del chat, sin posibilidad de hacerlo ni con confirmación? Te lo pregunté antes de que llegara este encargo y no ha quedado resuelto. El resto de este documento asume la opción intermedia (piden confirmación puntual, no están bloqueadas de forma absoluta) porque es la que ya existe en el código como nivel 2, pero es una asunción, no una decisión tuya — corrígeme si no.

---

# 1. El CEO: de "una llamada al modelo" a "módulo compuesto"

## 1.1 Qué hay construido hoy

`agents/ceo_agent.py` es, literalmente, una función que llama a `ollama.chat()` una vez con un prompt y un catálogo, y devuelve una clave. Es exactamente lo que tu encargo dice que el CEO **no debe ser**: "El CEO NO es un modelo de IA."

Esto no es un error de implementación — es el resultado natural de haber construido el CEO como solución a un problema puntual (routing) antes de que existiera esta filosofía. Ahora que existe, hay que reconceptualizarlo, no solo renombrarlo.

## 1.2 Qué dice el encargo que debe ser

Un módulo compuesto por: motor de razonamiento (sustituible) + prompt + Constitución + Principios + Memory Engine + Context Engine + Decision Engine + Policy Engine + Capability Registry + historial de decisiones + configuración del usuario.

Traducido a piezas que ya existen o casi existen en el repo:

| Pieza del CEO | Ya existe como | Estado real |
|---|---|---|
| Motor de razonamiento | `ollama.chat()` con `MODEL_NIVEL_2` | Hardcodeado, no sustituible sin tocar código |
| Prompt del CEO | `PROMPT_CEO` en `ceo_agent.py` | Existe, pero mezclado con la lógica de llamada |
| Constitución | `Constitution.md` | Existe, necesita reescritura (ver sección 0) |
| Principios | `Principles.md` | Vacío (scaffold intencional, no rellenado) |
| Memory Engine | `memory_engine.py` | Implementado y en uso |
| Context Engine | `context_engine.py` | Implementado (Fase 3) pero el CEO actual no lo consulta |
| Decision Engine | `decision_engine.py` | Implementado, pero solo lo usa Advisor Agent, no el CEO |
| Policy Engine | `policy_engine.py` | Implementado, pero el CEO actual no lo consulta antes de decidir — solo cada agente lo consulta por separado, después |
| Capability Registry | `orchestrator.AGENTES_CEO` (dict nombre→descripción de una línea) | Versión mínima, insuficiente (ver sección 3) |
| Historial de decisiones | `memory_engine.pending_decisions()` / tabla `decision` | Existe pero el CEO no lo usa como memoria conversacional |
| Configuración del usuario | No existe ningún fichero de config de usuario fuera de `config.json` (tokens de Telegram) | Gap real |

**Lo que esto revela**: el CEO de hoy es solo la punta del iceberg (el prompt + el modelo). Las piezas de abajo existen casi todas, pero **desconectadas entre sí** — cada una se construyó para un flujo distinto (Advisor usa Decision Engine, Builder usa Policy Engine, nadie usa Context Engine excepto Advisor). El CEO como módulo compuesto no es "construir cosas nuevas", es **conectar lo que ya existe bajo un mismo punto de entrada**, más rellenar dos huecos reales (Principios vacío, configuración de usuario inexistente).

## 1.3 Propuesta de documentación

Crear `Modules/CEO.md` (no existe hoy) con esta estructura, separando explícitamente "el módulo" de "el modelo":

- Objetivo, misión (igual que el resto de módulos, para consistencia de formato).
- Sección "Composición" listando las piezas de la tabla anterior, cada una con su fichero real.
- Sección "El modelo es sustituible" explicando que el motor de razonamiento se selecciona vía Model Router (sección 4) y que ningún otro módulo depende de qué modelo concreto responde.
- Flujo de una petición: recibir → recuperar memoria relevante → recuperar contexto (Context Engine) → analizar restricciones (Policy Engine) → consultar Constitución → consultar Capability Registry → elaborar plan → delegar en Orchestrator → recibir resultado → integrar → responder.

---

# 2. Orchestrator: ya está bien diseñado, pero el diagrama no incluye al CEO

`Modules/Orchestrator.md` ya dice, casi palabra por palabra, lo que pide tu encargo: "No decide qué debe hacerse. Decide quién debe hacerlo." Y en la sección "Lo que NO hace" ya prohíbe decidir objetivos, cambiar prioridades, sustituir al usuario. Esto está bien y no hace falta rehacerlo.

Lo que falta es el CEO en el diagrama. El flujo documentado hoy es:

```
Solicitud → Context Engine → Decision Engine → Policy Engine → Orchestrator → Agente → Resultado → Validación → Memoria
```

No hay ningún punto de entrada/salida hacia el usuario ni ninguna mención al CEO — este documento se escribió antes de que existiera el concepto. Hay que actualizarlo a:

```
Usuario → CEO (comprende, recupera memoria/contexto, consulta Constitución/Policy Engine/Capability Registry, elabora plan) → Orchestrator (coordina) → Agente(s) → Orchestrator → CEO (integra resultado, genera respuesta) → Usuario
```

Esto también resuelve una inconsistencia de implementación: hoy `orchestrator.dispatch()` lo llaman directamente `daily_briefing.py` y, de forma indirecta, `bot.py` a través de cada agente — pero **no hay un punto único por el que todo pase**. El propio Orchestrator.md ya dice "recibe tareas aprobadas", dando a entender que algo aprueba antes — ese algo debería ser siempre el CEO, nunca el bot de Telegram directamente.

---

# 3. Capability Registry: existe una versión mínima, hay que decidir cuánto crece

`orchestrator.AGENTES_CEO` ya es, en esencia, un Capability Registry embrionario: una clave por agente y una descripción de una frase. Funciona para que el CEO decida "a quién", que es lo único que necesitaba hasta ahora.

Tu encargo pide más: qué sabe hacer, qué no sabe hacer, qué herramientas usa, qué entradas acepta, qué devuelve, qué permisos tiene — y explícitamente "el CEO nunca conocerá implementaciones, solo capacidades". Esto ya es cierto en la práctica (el CEO nunca importa el código interno de un agente, solo su nombre), pero el registro actual no tiene estructura para lo demás.

**Nota importante para no repetir un error ya cometido**: hace poco existió un "Capability Agent" que juzgaba con un modelo local si una tarea "era para local o para Claude" — lo eliminamos porque era un filtro con criterio flojo que bloqueaba cosas que sí se podían hacer. El Capability Registry que pide este encargo **no es lo mismo**: no es un juez que evalúa con un modelo cada vez, es un catálogo estático que cada agente declara una vez (como un manifiesto). Merece la pena dejarlo explícito en la documentación para que nadie confunda ambos conceptos en el futuro y reintroduzca el filtro eliminado por error.

Propuesta de documentación: `Schemas/CapabilityRegistry.md`, definiendo el contrato mínimo que cada entrada del registro debe declarar (objetivo, entradas, salidas, herramientas, nivel de autonomía — reutilizando la escala única de `Schemas/Permissions.md`, no inventando una nueva). La implementación real (ampliar `AGENTES_CEO` de string a dict estructurado) queda para cuando decidas pasar a construir.

---

# 4. Independencia de modelo: documentada desde el principio, nunca implementada

Esto es el gap más serio que he encontrado, y tu encargo lo señala directamente como principio ("nunca dependerá de un modelo concreto... sustituir Llama por GPT, Claude, Qwen, Gemma, Kimi u otro modelo sin modificar la arquitectura").

`Modules/ModelRouter.md` existe desde el principio de este proyecto y dice cosas correctas (Nivel 1/2/3, "recurso estratégico no herramienta diaria"). Pero **no existe ningún `model_router.py`**. Cada agente elige su modelo así, hardcodeado, repetido en cada archivo:

```python
MODEL_NIVEL_2 = "llama3.1:8b"
```

Esto aparece, literalmente igual, en `ceo_agent.py`, `builder_agent.py`, `creative_agent.py`, `process_narrator_agent.py`. Si mañana quieres cambiar de `llama3.1:8b` a otro modelo, hay que tocar cuatro archivos a mano — exactamente lo contrario de "sustituible sin modificar la arquitectura". El Artículo 6 de la Constitución ("Ningún modelo de IA es imprescindible") lleva sin cumplirse desde que se escribió.

**Recomendación**: cuando toque implementar, centralizar esto en un único punto (el `model_router.py` que nunca se llegó a construir) del que cada módulo pida "dame el modelo de nivel 2" en vez de nombrarlo. Es la pieza que hace verdad la frase "el modelo es sustituible" en vez de dejarla como aspiración en un documento.

---

# 5. "Nunca debe existir el estado perdido" — ya se cumple en la práctica, falta hacerlo explícito

Buena noticia: esto ya funciona, por accidente más que por diseño. El fallback de `ceo_agent.decide()` ante cualquier fallo es `{"agente": "nota", "texto": mensaje}` — es decir, si todo falla, el mensaje se guarda como memoria de todas formas. Eso ya satisface "nunca perdido" para el caso más común de fallo.

Lo que falta es hacerlo un contrato explícito y verificable, no un efecto colateral. Propuesta: documentar los estados terminales que pide tu encargo, y mapear cada uno a lo que ya existe en el esquema, sin inventar tablas nuevas (siguiendo el principio ya establecido en este proyecto de reusar antes de crear):

| Estado terminal | Tabla/mecanismo ya existente |
|---|---|
| Resuelto | Respuesta directa del CEO, sin persistencia adicional necesaria |
| Guardado como memoria | `knowledge` (vía `create_knowledge`) |
| Convertido en conocimiento | `knowledge` |
| Convertido en tarea | `task` (existe en el esquema, pero ningún agente la usa todavía — gap) |
| Convertido en idea | Sin tabla propia hoy — o se trata como `knowledge` con `topic="idea"`, o se crea algo nuevo. Decisión pendiente. |
| Pendiente de información | Nuevo estado conversacional, no persistente — el CEO pregunta y espera |
| Pendiente de decisión | `decision` (result='pendiente') |
| Registrado como mejora del sistema | Ver sección 6 (backlog) |

El hueco real aquí es la tabla `task`: existe en `db/schema.sql` desde el principio pero ningún agente la usa (todos usan `knowledge` o `decision`). Vale la pena decidir si de verdad hace falta una entidad Tarea separada de Conocimiento, o si es complejidad que no se está usando.

---

# 6. Autoevolución y Backlog: no existe nada de esto todavía

Este es el segundo gap serio. Hoy no hay ningún mecanismo que detecte una limitación, la registre, y la convierta en una propuesta de mejora — el ciclo de 9 pasos que describe tu encargo no tiene ni una pieza construida.

Lo más cercano que existe es `flag_for_claude()`, pero resuelve un problema distinto: "esto requiere el juicio de Claude ahora mismo", no "el sistema detectó una limitación estructural en sí mismo". Son casos de uso diferentes que conviene no mezclar:

- `flag_for_claude`: una tarea puntual del usuario que excede lo local. Ya construido, funciona.
- Backlog de autoevolución: el propio sistema, sin que el usuario pida nada, nota "esto lo he tenido que resolver mal tres veces" o "me falta un agente para X" y lo deja anotado para revisión futura. No construido.

**Recomendación de esquema** (sin implementar todavía): reutilizar la tabla `insight` que ya existe (`pattern`, `validated`) en vez de crear una tabla nueva — es literalmente para esto ("Insight" en `Schemas/Entities.md` ya se describe como patrón detectado). Un backlog de autoevolución es, en el fondo, un tipo concreto de Insight: "patrón = limitación detectada + mejora propuesta", con el mismo ciclo detectado→validado→descartado que ya tiene la tabla. No hace falta inventar una entidad nueva para algo que el esquema ya modela.

Documentación a crear: una sección en `Modules/AgentFrameWork.md` (o un documento nuevo `Modules/SelfEvolution.md`) que defina el proceso de 9 pasos y cómo se ata a `insight` + `event` (cada paso del ciclo genera un evento, igual que ya hace todo lo demás en el sistema).

---

# 7. Duplicaciones que ya existían y siguen sin resolver

No relacionado directamente con este encargo, pero lo he visto al revisar los documentos y no tiene sentido callarlo: `Modules/AgentFrameWork.md` sigue teniendo su propia tabla de niveles 0-4 (Consulta/Asistente/Operador supervisado/Operador autónomo limitado/Autónomo estratégico), pese a que `Schemas/Permissions.md` ya se escribió específicamente para unificar esa escala y dice explícitamente "esto sustituye a las dos anteriores". Nadie volvió a `AgentFrameWork.md` para quitar la tabla vieja. Es un resto de una consolidación a medias — cosmético, pero conviene limpiarlo cuando se actualice este documento, para que no haya dos fuentes de verdad sobre lo mismo otra vez.

---

# 8. Qué NO cambiaría de lo ya construido

Para que quede claro que esto no es "tirarlo todo": el patrón de "proponer → escribir solo si hay archivo de por medio → registrar evento" que usa Builder Agent, el escaneo de seguridad antes de ejecutar, el patrón determinista de `orchestrator_integrator.py` (edición de texto sin modelo para cambios mecánicos), y la regla de nunca sobrescribir/borrar en Memory Engine — todo esto sigue siendo válido bajo la nueva filosofía sin cambios. No es chatbot-vs-sistema-operativo lo que estaba mal ahí, es la capa de decisión de arriba (CEO/Orchestrator desconectados) la que hay que recomponer.

---

# 9. Siguiente acción recomendada

No construir nada todavía, como pediste. El orden que propongo para cuando decidas pasar a implementación (y que puedes reordenar):

1. Cerrar la decisión pendiente de la sección 0 (confirmación puntual vs. bloqueo absoluto para ejecutar/eliminar/desplegar) — todo lo demás depende de esto.
2. Reescribir Constitution.md Art. 2 y Art. 10 con la lista cerrada de tres acciones.
3. Crear `Modules/CEO.md` formalizando el módulo compuesto.
4. Actualizar el diagrama de `Modules/Orchestrator.md` para incluir al CEO como entrada/salida.
5. Decidir el alcance real del Capability Registry (¿cuánto se amplía `AGENTES_CEO`?) y documentarlo en `Schemas/CapabilityRegistry.md`.
6. Decidir si la tabla `task` se empieza a usar de verdad o se retira del alcance actual.
7. Documentar el ciclo de autoevolución y su anclaje a `insight`.
8. Limpiar la tabla de niveles duplicada en `AgentFrameWork.md`.
9. Solo entonces: implementar Model Router real (el gap más antiguo y más ignorado del proyecto).
