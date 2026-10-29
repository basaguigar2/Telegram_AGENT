# Schema — Events

Estado: Borrador v0.1
Depende de: Modules/EventFlow.md, Schemas/Entities.md
Fuente de verdad de escritura: cualquier módulo puede emitir un evento; solo Memory Engine lo persiste.

---

# Principio

JARVIS funciona por eventos, no por llamadas directas entre módulos (EventFlow.md). Este documento formaliza la estructura que `EventFlow.md` ya describe en prosa ("todo evento debe contener: identificador, tipo, fecha, origen, contexto, resultado") en un esquema concreto.

---

# Estructura de un evento

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `id` | string (uuid) | sí | Identificador único del evento. |
| `type` | enum | sí | Ver catálogo de tipos. |
| `occurred_at` | datetime | sí | Cuándo ocurrió (no cuándo se procesó). |
| `origin_module` | string | sí | Módulo, agente o "usuario" que lo generó. |
| `context` | object | sí | Datos mínimos para interpretar el evento sin consultar nada más. |
| `related_entity_ids[]` | array de id | no | Entidades afectadas o referenciadas. |
| `outcome` | string \| null | no | Qué ocurrió después (se rellena al cerrar el evento). |
| `status` | enum (emitido \| procesado \| fallido) | sí | Estado de procesamiento del propio evento. |

---

# Catálogo de tipos de evento

Agrupados según `EventFlow.md`:

| Categoría | Tipos | Flujo típico |
|---|---|---|
| Entrada | `capture.created` (nota, PDF, enlace, documento importado) | Entrada → Inbox → Knowledge Engine → Memory Engine |
| Conocimiento | `knowledge.extracted`, `relation.created`, `knowledge.updated` | Knowledge Engine → Memory Engine → actualización de contexto |
| Usuario | `goal.created`, `preference.changed`, `habit.changed` | Interacción usuario → User Model Engine → validación → memoria |
| Decisión | `recommendation.generated`, `decision.approved`, `decision.rejected` | Context Engine → Decision Engine → Policy Engine → usuario |
| Ejecución | `task.assigned`, `agent.started`, `result.received` | Orchestrator → Agente → resultado → validación → memoria |
| Externos | `external.news`, `external.market_change`, `calendar.event` | Entra directamente al Context Engine como fuente de contexto |

Cualquier tipo nuevo debe añadirse a esta tabla antes de emitirse — un evento sin tipo catalogado no debe poder persistirse (evita que `Automation Engine` o un agente nuevo invente tipos de evento ad hoc sin que quede registrado en ningún sitio, que es justo el riesgo que señalaba la auditoría sobre falta de contratos verificables).

---

# Eventos críticos (requieren supervisión reforzada)

Heredado de `EventFlow.md`: cambios en reglas, decisiones financieras, modificación de principios, acciones externas. Estos eventos, además de los campos estándar, deben incluir:

| Campo adicional | Tipo | Obligatorio |
|---|---|---|
| `requires_approval` | boolean | sí (siempre `true` para esta categoría) |
| `approved_by` | string \| null | sí, se rellena solo tras aprobación explícita |

---

# Gestión de fallos

Si `status = fallido`: el evento se conserva (nunca se elimina, mismo principio que las entidades), se registra el motivo en `outcome`, y se emite un nuevo evento de tipo `event.recovery_needed` si procede reintentar. Esto formaliza lo que `EventFlow.md` describe como "registrar error, mantener información, intentar recuperación, informar si requiere intervención humana".

---

# Reprocesamiento

Un evento con `related_entity_ids[]` puede reprocesarse contra una versión mejorada de un modelo de IA sin perder su `occurred_at` original — el reprocesamiento genera un nuevo evento `knowledge.reextracted` que referencia el evento original vía `context.reprocessed_from_event_id`, nunca sobrescribe el evento original.
