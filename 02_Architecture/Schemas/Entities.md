# Schema — Entities

Estado: Borrador v0.1
Depende de: Modules/DataModel.md
Fuente de verdad de escritura: Memory Engine (ninguna entidad se persiste fuera de él)

---

# Principio

Toda entidad de JARVIS comparte un núcleo común de campos (definido abajo) y añade únicamente los campos propios de su tipo. Ningún módulo escribe directamente sobre estos campos salvo el Memory Engine; el resto de módulos proponen cambios que el Memory Engine valida y versiona.

---

# Núcleo común (todas las entidades lo heredan)

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `id` | string (uuid) | sí | Identificador único, inmutable. |
| `type` | enum | sí | Tipo de entidad (ver catálogo). |
| `name` | string | sí | Representación humana. |
| `status` | enum | sí | Estado de ciclo de vida (ver Schemas/Lifecycle.md). |
| `created_at` | datetime | sí | Fecha de creación. |
| `updated_at` | datetime | sí | Fecha de última modificación. |
| `version` | integer | sí | Empieza en 1, incrementa en cada cambio versionado. |
| `previous_version_id` | string (uuid) \| null | sí | Referencia a la versión anterior de esta misma entidad. |
| `source` | string | sí | Origen del dato (agente, módulo o "usuario"). |
| `confidence` | enum (alta \| media \| baja) | no | Solo aplica a entidades derivadas de inferencia (Insight, Decision). |
| `relations[]` | array de Relation | no | Ver Schemas/Relationships.md. |

Regla: ningún campo del núcleo común puede sobrescribirse. Un cambio siempre crea una nueva versión y enlaza `previous_version_id`. Esto ya lo exige Constitution Art. 5 y MemoryEngine.md — aquí queda como contrato de datos, no solo como principio.

---

# Catálogo de entidades

## Usuario

Instancia única por despliegue de JARVIS.

| Campo | Tipo | Obligatorio |
|---|---|---|
| `preferences[]` | array de Preference | no |
| `goals[]` | array de id (Objetivo) | no |
| `principles[]` | array de string | no |
| `constraints[]` | array de Constraint | no |
| `resources[]` | array de id (Recurso) | no |
| `state` | object `{energy, mental_load, available_time, motivation}` | no |

Escritura: solo User Model Engine puede proponer cambios; requiere validación (nunca automático — UserModelEngine.md, "Lo que NO hace").

---

## Objetivo (Goal)

| Campo | Tipo | Obligatorio |
|---|---|---|
| `priority` | enum (estratégico \| importante \| operativo \| prescindible) | sí |
| `target_date` | date \| null | no |
| `metrics[]` | array de string | no |
| `parent_goal_id` | id \| null | no |

Escritura: propuesta por Decision Engine o por el usuario directamente; cambios de prioridad estratégica requieren aprobación explícita (Constitution Art. 10).

---

## Proyecto

| Campo | Tipo | Obligatorio |
|---|---|---|
| `goal_id` | id (Objetivo) | sí |
| `resources[]` | array de id (Recurso) | no |
| `tasks[]` | array de id (Tarea) | no |

Escritura: Orchestrator crea la entidad al aprobarse un flujo; edición de alcance requiere aprobación del usuario.

---

## Tarea (Task)

| Campo | Tipo | Obligatorio |
|---|---|---|
| `description` | string | sí |
| `priority` | enum | sí |
| `estimated_effort` | duration | no |
| `dependencies[]` | array de id (Tarea) | no |
| `assigned_agent_id` | id (Agente) \| null | no |

Escritura: Orchestrator y Automation Engine.

---

## Conocimiento (Knowledge)

| Campo | Tipo | Obligatorio |
|---|---|---|
| `content` | string | sí |
| `topic` | string | sí |
| `reliability` | enum (alta \| media \| baja) | sí |
| `source_resource_id` | id (Recurso) \| null | no |

Escritura: Knowledge Engine propone, Memory Engine valida (debe cumplir: relevante, consistente, no duplicado, relacionado, justificable — ver MemoryEngine.md "Calidad del conocimiento").

---

## Recurso (Resource)

| Campo | Tipo | Obligatorio |
|---|---|---|
| `resource_type` | enum (pdf \| video \| web \| curso \| libro \| otro) | sí |
| `origin_url_or_path` | string \| null | no |
| `retrieved_at` | datetime | sí |

Escritura: Knowledge Engine. Un Recurso nunca se elimina, solo se archiva (Constitution + MemoryEngine.md, tipo "Eliminable").

---

## Decisión (Decision)

| Campo | Tipo | Obligatorio |
|---|---|---|
| `context` | string | sí |
| `alternatives_considered[]` | array de string | sí |
| `reason` | string | sí |
| `result` | enum (aceptada \| rechazada \| pendiente) | sí |
| `related_goal_id` | id \| null | no |

Escritura: Decision Engine propone, el usuario resuelve el campo `result` (Policy Engine bloquea si `result` cambia sin acción del usuario en decisiones de nivel estratégico).

---

## Regla (Rule)

| Campo | Tipo | Obligatorio |
|---|---|---|
| `rule_level` | enum (constitución \| sistema \| personal \| temporal) | sí |
| `expires_at` | date \| null | no (obligatorio si `rule_level = temporal`) |
| `body` | string | sí |

Escritura: reglas de nivel "constitución" nunca se crean ni modifican vía API — son texto fijo en Constitution.md. Las demás las gestiona Policy Engine.

---

## Insight

| Campo | Tipo | Obligatorio |
|---|---|---|
| `pattern` | string | sí |
| `evidence[]` | array de id (referencias a eventos/decisiones) | sí |
| `validated` | boolean | sí (default: false) |

Escritura: User Model Engine o Decision Engine proponen; nunca pasa a formar parte del perfil permanente sin `validated = true` (UserModelEngine.md).

---

## Evento (Event)

Ver definición completa en Schemas/Events.md — aquí solo la referencia como entidad porque los eventos relevantes también se persisten y versionan como el resto.

| Campo | Tipo | Obligatorio |
|---|---|---|
| `event_type` | string | sí |
| `origin_module` | string | sí |
| `payload` | object | sí |
| `outcome` | string \| null | no |

---

# Entidades futuras previstas (no implementar aún)

Negocio, Cliente, Inversión, Agente (como entidad persistida, no solo definición en Agent Framework), Automatización. Cuando se necesiten, heredan el mismo núcleo común — no requieren rediseño del modelo.

---

# Reglas de integridad (aplican a todo el catálogo)

1. Un `id` nunca se reutiliza, ni siquiera tras archivar la entidad.
2. Ninguna entidad puede tener dos versiones activas simultáneamente (`status = activo`).
3. Toda entidad con `confidence = baja` no puede usarse como única evidencia para una Decisión de prioridad "estratégico".
4. Ninguna entidad se elimina físicamente; el estado `archivado` es el único mecanismo de retiro (Constitution Art. 5, MemoryEngine.md).
