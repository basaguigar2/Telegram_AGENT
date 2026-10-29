# Schema — Lifecycle

Estado: Borrador v0.1
Depende de: Schemas/Entities.md
Fuente de verdad de transición de estado: Memory Engine (ejecuta la transición); Policy Engine (autoriza transiciones sensibles)

---

# Principio

Toda entidad tiene un campo `status` (núcleo común, Schemas/Entities.md). Este documento define qué valores puede tomar ese campo por tipo de entidad y qué transiciones son válidas. Una transición no listada aquí no debe poder ejecutarse.

---

# Estados genéricos (aplican a casi toda entidad)

`activo` → `pausado` → `activo` (reversible)
`activo` → `finalizado` (terminal, pero no elimina)
`finalizado` → `archivado` (terminal)
`activo` → `archivado` (solo si se abandona sin finalizar)

`archivado` es siempre terminal salvo reactivación explícita del usuario (`archivado` → `activo`, requiere aprobación — no es automática).

---

# Ciclo de vida por entidad

## Objetivo

`propuesto → activo → (pausado ↔ activo) → conseguido | abandonado → archivado`

Un Objetivo nunca pasa de `propuesto` a `activo` sin que el usuario lo confirme (Constitution Art. 1 y 10).

---

## Proyecto

Recoge el ejemplo de `DataModel.md` ("Idea → Evaluación → Proyecto → Activo → Finalizado → Archivado") pero corrigiendo una imprecisión: ese ejemplo mezcla estados de una Idea con estados de un Proyecto como si fueran la misma entidad. Formalizado:

`idea (aún no es Proyecto, vive como Conocimiento tipo "idea") → evaluación → creado → activo → (pausado ↔ activo) → finalizado → archivado`

Un Proyecto solo existe como entidad desde `creado` en adelante; antes de eso es una Idea (ver Knowledge Engine, clasificación "Idea").

---

## Tarea

`pendiente → en_progreso → (bloqueada ↔ en_progreso) → completada | fallida → archivada`

Corresponde 1:1 con los "Estados de ejecución" ya definidos en `Orchestrator.md` (Pendiente, En ejecución, Bloqueado, Completado, Fallido) — aquí solo se añade `archivada` como estado terminal común a todas las entidades, que Orchestrator.md no incluía.

---

## Conocimiento

`propuesto → validado → activo → (desactualizado) → archivado`

`propuesto`: extraído por Knowledge Engine, aún no evaluado. `validado`: pasó los criterios de calidad de MemoryEngine.md. `desactualizado`: existe una versión más reciente pero se conserva por trazabilidad.

---

## Recurso

`capturado → procesado → archivado`

Nunca `eliminado` — coincide con MemoryEngine.md ("Eliminable... nunca se elimina automáticamente").

---

## Decisión

`propuesta → pendiente_aprobación → aceptada | rechazada`

Terminal en `aceptada` o `rechazada`; no se archiva porque ya es, en sí misma, un registro histórico permanente (no ocupa espacio de "memoria activa").

---

## Regla

`activa → (modificada → nueva versión activa) → derogada`

Si `rule_level = temporal`: transición automática `activa → derogada` al llegar `expires_at`, sin intervención humana (es la única transición automática de todo el sistema de reglas).

---

## Insight

`detectado → validado | descartado`

`detectado`: patrón identificado, `validated = false` en el núcleo. `validado`: el usuario lo confirmó y `validated = true`; solo entonces puede alimentar el perfil del User Model Engine. `descartado`: terminal, se conserva como evidencia de que se evaluó.

---

## Evento

Ver Schemas/Events.md — usa su propio campo `status` (`emitido → procesado | fallido`), no el ciclo de vida genérico de entidades, porque un evento no se "archiva": es inmutable desde que se emite.

---

# Regla de integridad transversal

Ninguna transición hacia `archivado` puede ejecutarse si existen relaciones activas de tipo `depends_on` o `modifies` que apunten a esa entidad sin resolver — evita archivar, por ejemplo, un Proyecto del que aún depende una Tarea activa.
