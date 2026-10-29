# CEO

Estado: Diseño (implementado parcialmente -- ver `04_Implementation/agents/ceo_agent.py`)
Depende de: Constitution.md, Modules/Orchestrator.md, Modules/ModelRouter.md, Schemas/CapabilityRegistry.md, Schemas/Permissions.md, MemoryEngine.md, ContextEngine.md, DecisionEngine.md, PolicyEngine.md

---

# Objetivo

El CEO es el único punto de entrada de todas las peticiones del usuario a JARVIS.

---

# Principio fundamental

El CEO NO es un modelo de IA.

Es un módulo compuesto. El modelo de razonamiento es una pieza sustituible dentro de él, seleccionada vía Model Router -- nunca la identidad del módulo.

Si mañana Llama se sustituye por otro modelo, el CEO sigue siendo el mismo módulo, con el mismo comportamiento observable.

---

# Composición

| Pieza | Responsabilidad dentro del CEO |
|---|---|
| Motor de razonamiento | Interpreta el mensaje del usuario. Sustituible vía Model Router -- el CEO nunca nombra un modelo concreto directamente. |
| Prompt del CEO | Instrucciones que gobiernan cómo el motor de razonamiento decide y responde. |
| Constitución | Límite máximo, no negociable por ningún otro módulo (Constitution.md). |
| Principios | Criterios de calidad y estilo de decisión (Principles.md). |
| Memory Engine | Fuente de verdad -- historial reciente, conocimiento, decisiones pendientes. |
| Context Engine | Situación actual del usuario (tiempo disponible, energía, objetivos activos). |
| Decision Engine | Recomendaciones estructuradas cuando la petición lo requiere. |
| Policy Engine | Evalúa las tres acciones de la lista cerrada (Constitution Art. 2): ejecutar, eliminar, desplegar. Para todo lo demás no interviene -- ya no hay "requiere_aprobación" fuera de esa lista. |
| Capability Registry | Catálogo de qué sabe hacer cada agente (Schemas/CapabilityRegistry.md) -- el CEO decide "a quién" leyendo esto, nunca leyendo el código de los agentes. |
| Historial de decisiones | Decisiones pendientes y resueltas (tabla `decision`), para no repetir preguntas ya respondidas. |
| Configuración del usuario | Preferencias explícitas que condicionan cómo actúa el CEO (pendiente de formalizar -- hoy solo existe `telegram_bot/config.json`, que es solo credenciales, no preferencias). |

---

# Responsabilidades

- Ser el único punto de entrada de toda petición del usuario.
- Comprender la intención (motor de razonamiento + prompt).
- Recuperar memoria relevante (Memory Engine).
- Recuperar contexto (Context Engine).
- Consultar la Constitución antes de decidir.
- Consultar el Capability Registry para saber a quién delegar.
- Para las tres acciones de la lista cerrada, consultar Policy Engine y pedir confirmación puntual al usuario.
- Elaborar un plan (qué agente, con qué payload).
- Delegar en el Orchestrator.
- Recibir el resultado del Orchestrator.
- Integrar el resultado en una respuesta.
- Responder al usuario.

---

# Lo que NO hace

El CEO nunca:

- Realiza trabajo especializado directamente (eso es de los agentes).
- Sustituye a un agente.
- Conoce la implementación interna de un agente -- solo su entrada en el Capability Registry.
- Ejecuta código, elimina o despliega sin la confirmación puntual que exige Constitution Art. 2.
- Pide confirmación fuera de esas tres acciones -- ya no existe la categoría abierta "cambios estratégicos".

---

# Flujo de una petición

```
Usuario
  ↓
CEO: comprende intención
  ↓
CEO: recupera memoria relevante (Memory Engine)
  ↓
CEO: recupera contexto (Context Engine)
  ↓
CEO: ¿la petición implica ejecutar / eliminar / desplegar?
  ├─ Sí → Policy Engine evalúa → confirmación puntual sí/no al usuario
  └─ No → continúa sin pedir nada
  ↓
CEO: consulta Capability Registry → decide a qué agente(s) delega
  ↓
Orchestrator: coordina el/los agente(s)
  ↓
CEO: recibe e integra el resultado
  ↓
CEO: responde al usuario
```

---

# Relación con el CEO Agent implementado

`04_Implementation/agents/ceo_agent.py` implementa hoy una versión mínima de este módulo: decide a qué agente delega leyendo `orchestrator.AGENTES_CEO`, con un atajo determinista para el caso "crear un agente" (para no depender solo del criterio del modelo). Todavía no consulta Memory Engine, Context Engine ni Policy Engine antes de decidir -- eso es evolución pendiente, no una contradicción de este documento, siempre que se implemente siguiendo el flujo de arriba.
