# Roadmap

Estado: v0.1
Depende de: TechStack.md, Schemas/*, Modules/MemoryEngine.md

---

# Principio

No se construye ningún módulo de razonamiento (Decision, Policy, Orchestrator) hasta que exista un Memory Engine funcional. Sin memoria real, esos módulos no tienen nada que consultar y su desarrollo sería teórico.

---

# Fase 0 — Base de datos (actual)

- Esquema SQLite ejecutable a partir de Schemas/Entities.md y Schemas/Relationships.md.
- Ollama instalado en local con al menos un modelo Nivel 1 y uno Nivel 2 (ver TechStack.md).

Criterio de salida: puedes guardar y leer una entidad real en SQLite desde tu máquina.

---

# Fase 1 — Memory Engine mínimo

- CRUD básico sobre las entidades del núcleo común (create, versionar, archivar — nunca borrar).
- Sin interfaz todavía; basta con scripts Python o una API local sencilla.

Criterio de salida: puedes capturar una nota, que quede guardada como Conocimiento versionado, y recuperarla.

---

# Fase 2 — Un único flujo end-to-end

- Captura (nota de voz o texto) → Knowledge Engine (clasificación con modelo local Nivel 1) → Memory Engine.
- Un solo agente, sin Orchestrator todavía — la lógica de "a quién le toca" se hardcodea.

Criterio de salida: el ciclo completo de EventFlow.md ("Captura → Procesamiento → Conocimiento → Memoria") funciona de punta a punta con datos reales tuyos, no de prueba.

---

# Fase 3 — Context Engine + Decision Engine

- Construir contexto real a partir de Memory Engine + estado básico del usuario.
- Decision Engine con modelo local Nivel 2, escalando a Claude solo si se declara explícitamente necesidad de Nivel 3.

Criterio de salida: JARVIS puede responder "¿qué hago esta tarde?" con una recomendación basada en datos reales, no en un ejemplo de la documentación.

---

# Fase 4 — Policy Engine + Orchestrator + segundo agente

- Solo se construye cuando exista más de un agente real que coordinar.
- Antes de esta fase, cualquier automatización pasa directamente por Automation Engine sin necesidad de Orchestrator.

Criterio de salida: dos agentes distintos ejecutan tareas coordinadas sin comunicarse directamente entre sí.

---

# Fuera de alcance por ahora

Executive Dashboard visual, ADRs formales, SystemManual completo, Blueprints. Se escriben cuando haya algo real que documentar, no antes — evita repetir el problema que señaló la auditoría inicial (mucha documentación, poco código).
