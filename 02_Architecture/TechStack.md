# Tech Stack

Estado: Decisión inicial v0.1
Depende de: Modules/IAGateway.md, Modules/ModelRouter.md, Schemas/*

---

# Hardware de referencia

HP Victus · Intel i7 · 16 GB RAM · NVIDIA RTX 3050 Ti Laptop (4 GB VRAM) · Intel UHD Graphics (integrada, no se usa para IA).

El límite real es la VRAM (4 GB), no la RAM ni la CPU. El stack está elegido para no superar ese límite en el uso diario.

---

# Runtime de modelos locales

**Ollama** (sobre llama.cpp).

Motivo: gestiona cuantización, offload a GPU/CPU y cambio de modelo sin configuración manual — encaja directamente con el principio de IAGateway/ModelRouter de que cambiar de modelo no debe requerir reconstruir el sistema. Expone una API HTTP local sencilla de integrar.

---

# Modelos locales (por nivel, según ModelRouter.md)

| Nivel | Uso | Modelo recomendado | Tamaño en disco (Q4) | Cabe en 4GB VRAM |
|---|---|---|---|---|
| 1 — Automatización simple | Clasificar, etiquetar, resumir corto | Llama 3.2 3B o Phi-3.5-mini (3.8B) | ~2 GB | Sí, con margen |
| 2 — Trabajo intelectual medio | Informes, investigación inicial, brainstorming | Llama 3.1 8B o Qwen2.5 7B | ~4.5-5 GB | Ajustado — offload parcial a RAM, sigue siendo rápido |
| 3 — Trabajo crítico | Arquitectura, estrategia, decisiones importantes | Claude vía IA Gateway (no local) | — | No aplica — por diseño no debe correr en local |

Regla práctica: si un modelo de nivel 2 no da la calidad necesaria, la escalada va directa a Claude (Nivel 3) — no tiene sentido perseguir un modelo de 13B+ en esta GPU, el salto de calidad no compensa la lentitud.

---

# Embeddings / búsqueda semántica

`nomic-embed-text` o `bge-small-en` vía Ollama. Ambos corren en CPU sin problema y son suficientes para indexar Conocimiento y Recursos (Schemas/Entities.md) sin tocar la GPU, que queda libre para el modelo de generación.

---

# Almacenamiento (Memory Engine)

**SQLite** como motor de persistencia.

Motivo: JARVIS es de un solo usuario, no necesita un servidor de base de datos separado; SQLite es un único archivo, fácil de versionar/respaldar, y su modelo relacional encaja bien con el esquema ya definido (Entities + Relationships son, en esencia, tablas y claves foráneas). Se añade la extensión `sqlite-vec` para guardar los embeddings de Conocimiento junto a las mismas filas, sin una base de datos vectorial aparte.

Se descarta Postgres/otros motores de servidor por ahora: añaden infraestructura que este hardware y este caso de uso (un usuario, ejecución local) no necesitan. Si en el futuro JARVIS pasa a multiusuario o a servidor remoto, migrar de SQLite a Postgres es un cambio acotado porque el esquema conceptual (Schemas/) no cambia.

---

# Lenguaje / runtime de la aplicación

**Python**.

Motivo: es el ecosistema con mejor soporte nativo para Ollama, llama-cpp-python, sqlite-vec y librerías de orquestación (si se necesitan más adelante). Minimiza fricción para todo lo que no sea razonamiento de modelo (ingestión, clasificación local, cron de automatizaciones, API interna).

---

# Resumen de dónde vive cada módulo

| Módulo | Corre en |
|---|---|
| Memory Engine | Python + SQLite (local, siempre) |
| Knowledge Engine | Python + modelo local Nivel 1/2 (Ollama) |
| Context Engine | Python, lógica pura, sin modelo de IA propio |
| Policy Engine | Python, reglas explícitas, sin modelo de IA |
| Decision Engine | Modelo local Nivel 2 por defecto; escala a Claude (Nivel 3) en decisiones estratégicas |
| Orchestrator | Python, coordina llamadas a Ollama y a Claude vía IA Gateway |
| Automation Engine | Python + cron/scheduler local |
| IA Gateway | Python, capa de abstracción entre Ollama (local) y Claude (API) |

---

# Objetivo de este stack

Que el 80-90% del uso diario (clasificar, resumir, mantener memoria, automatizaciones) corra por completo en tu Victus sin coste ni dependencia de red, y que Claude quede reservado exactamente para lo que `ModelRouter.md` ya definía: arquitectura, decisiones estratégicas y revisión crítica — minimizando el gasto de tokens sin perder calidad donde de verdad importa.
