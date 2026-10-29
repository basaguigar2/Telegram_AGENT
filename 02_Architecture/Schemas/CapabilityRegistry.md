# Schema — Capability Registry

Estado: Diseño (implementado como `orchestrator.AGENTES_CEO`, versión estructurada)
Depende de: Modules/CEO.md, Modules/AgentFrameWork.md, Schemas/Permissions.md

---

# Objetivo

Catálogo central donde cada agente publica qué sabe hacer, para que el CEO decida a quién delega sin conocer la implementación interna de ningún agente.

---

# Distinción importante con algo ya eliminado

Este registro **no es** un agente que juzga con un modelo cada tarea (eso existió como "Capability Agent" y se eliminó porque era un filtro con criterio flojo que bloqueaba tareas que sí se podían resolver localmente). El Capability Registry es un catálogo estático -- cada agente declara sus datos una vez, como un manifiesto -- no hay ninguna llamada a un modelo para consultarlo.

---

# Contrato de una entrada

Cada agente en el registro publica:

| Campo | Descripción |
|---|---|
| `clave` | Identificador único, coincide con la clave de `orchestrator.REGISTRY`. |
| `descripcion` | Para qué sirve, en lenguaje que el CEO pueda usar para decidir cuándo delegarle algo. |
| `entradas` | Qué necesita recibir para funcionar. |
| `salidas` | Qué devuelve. |
| `herramientas` | Qué usa por dentro (ej. memory_engine, ollama) -- informativo, el CEO no lo necesita para decidir pero ayuda a auditar. |
| `autonomy_level` | Nivel de la escala única (Schemas/Permissions.md). Determina si Policy Engine interviene (solo si implica ejecutar/eliminar/desplegar). |

---

# Implementación real

`orchestrator.AGENTES_CEO` es la versión en código de este registro. Hasta la revisión de arquitectura CEO era un `dict[clave, descripcion]` (solo el primer campo de la tabla de arriba). Se amplía a `dict[clave, dict]` con los campos completos -- ver `orchestrator_integrator.py` para cómo se generan las entradas al integrar un agente nuevo.

---

# Decisión: tabla `task` (activada 2026-08-31)

`db/schema.sql` definía una entidad `task` desde el principio del proyecto sin que ningún
agente la usara -- todo pasaba por `knowledge` o `decision`. Apareció el caso de uso real
que faltaba: el tablero multi-negocio de AGENTE (RelacionConAGENTE.md). Se activó
extendiendo la tabla con `business_line`, `business_phase` y `related_knowledge_id` en vez
de crear una entidad o base de datos nueva. Generador Agent y Seguimiento Agent son los
primeros en usarla.
