# Schema — Relationships

Estado: Borrador v0.1
Depende de: Schemas/Entities.md
Fuente de verdad de escritura: Memory Engine

---

# Principio

JARVIS no organiza información en carpetas; la organiza en relaciones (Constitution implícita, MemoryEngine.md, DataModel.md). Toda relación es una entidad de segundo orden: tiene tipo, dirección, y puede versionarse igual que las entidades que conecta.

---

# Estructura de una relación

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `id` | string (uuid) | sí | Identificador único de la relación. |
| `type` | enum | sí | Tipo de relación (ver catálogo). |
| `source_id` | id | sí | Entidad origen. |
| `source_type` | enum | sí | Tipo de la entidad origen. |
| `target_id` | id | sí | Entidad destino. |
| `target_type` | enum | sí | Tipo de la entidad destino. |
| `created_at` | datetime | sí | Fecha de creación de la relación. |
| `created_by` | string | sí | Módulo o agente que la propuso. |

Una relación nunca se edita: si deja de ser válida, se marca `status = archivada` (mismo principio que las entidades) y, si aplica, se crea una nueva.

---

# Catálogo de relaciones

| Tipo | Origen → Destino | Cardinalidad | Semántica |
|---|---|---|---|
| `has_goal` | Usuario → Objetivo | 1:N | El usuario persigue este objetivo. |
| `belongs_to` | Proyecto → Objetivo | N:1 | El proyecto existe para avanzar este objetivo. |
| `has_task` | Proyecto → Tarea | 1:N | La tarea forma parte del proyecto. |
| `depends_on` | Tarea → Tarea | N:N | Bloqueo de dependencia entre tareas. |
| `uses_resource` | Proyecto → Recurso | N:N | El proyecto consume este recurso. |
| `supports` | Conocimiento → Decisión | N:N | El conocimiento fue evidencia de la decisión. |
| `modifies` | Decisión → Proyecto \| Objetivo | N:1 | La decisión alteró el estado de la entidad destino. |
| `derived_from` | Conocimiento → Recurso | N:1 | El conocimiento fue extraído de este recurso. |
| `evidence_for` | Evento → Insight | N:N | El evento sirve como evidencia del patrón detectado. |
| `governed_by` | Cualquier entidad → Regla | N:N | La entidad está sujeta a esta regla al evaluarse en Policy Engine. |
| `assigned_to` | Tarea → Agente (futuro) | N:1 | Agente responsable de ejecutar la tarea. |
| `version_of` | Cualquier entidad → misma entidad (versión anterior) | 1:1 | Ya cubierto por `previous_version_id` en el núcleo común; esta relación es redundante y NO debe implementarse aparte — ver nota abajo. |

---

# Nota de consistencia con MemoryEngine.md — resuelta

`MemoryEngine.md` describía la cadena de relación de ejemplo con dos conceptos que no existían en el catálogo de entidades: "Área" y "Persona". Se ha corregido el ejemplo en `MemoryEngine.md` para usar solo entidades ya definidas (`Proyecto → Objetivo → Recursos → Decisiones → Conocimiento`). Si en el futuro se necesitan `Área` o `Persona` como entidades reales, deben añadirse primero a este documento y a `Schemas/Entities.md` antes de reaparecer en ningún ejemplo.

---

# Redundancia detectada: `version_of`

`previous_version_id` ya vive en el núcleo común de toda entidad (Schemas/Entities.md). No hace falta una relación `version_of` aparte — sería la misma información modelada dos veces, justo el tipo de duplicidad que el Memory Engine dice evitar ("todo dato existe una única vez"). La dejo listada arriba solo para descartarla explícitamente.

---

# Reglas de integridad

1. Una relación nunca conecta una entidad consigo misma salvo `depends_on` entre tareas distintas (nunca una tarea depende de sí misma).
2. Toda relación `modifies` debe poder trazarse hasta una Decisión con `result = aceptada`.
3. Las relaciones no tienen ciclo de vida propio más allá de activa/archivada — no se versionan como las entidades, se sustituyen.
