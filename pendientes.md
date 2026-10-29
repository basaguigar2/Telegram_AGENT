# Pendientes — Auditoría interna de AGENTE/JARVIS

Estado: generado por auditoría del 2026-09-01.

**Nota de alcance importante**: el documento original "AGENTE — Guía de
Construcción Detallada" (roadmap de 8 fases, organigrama de 5 equipos:
Trading, Asistente/Jarvis, Soporte a Claude, Scouter, Auditoría Interna) no
está guardado como archivo en este repositorio. Esta auditoría compara la
implementación real contra los dos únicos documentos de referencia que sí
existen aquí: `02_Architecture/RelacionConAGENTE.md` (decisión de reconciliar
AGENTE como capa sobre JARVIS, 2026-08-31) y `02_Architecture/Roadmap.md`
(roadmap propio de JARVIS, 5 fases, previo a AGENTE). Donde el alcance
original de un equipo no está documentado en ningún sitio accesible aquí
(ej. el detalle completo de "Soporte a Claude"), se marca explícitamente en
vez de asumirlo.

Solo se listan aquí los elementos PARCIAL o PENDIENTE — ver el resumen
completo (incluyendo lo CUMPLIDO) en la tabla que acompaña esta auditoría.

---

## Equipo: Trading — DESCARTADO (2026-09-01)

Línea de negocio eliminada por completo, código y tareas programadas
incluidos. Ver `RelacionConAGENTE.md` para el detalle de por qué (backtesting
riguroso completo, paper trading real corrido, y aun así el rédito esperado
con 300€ no compensaba el esfuerzo ni el riesgo real). No queda nada
pendiente de este equipo — no se retoma salvo que el usuario lo pida de
nuevo explícitamente y desde cero.

## Equipo: Contenido/afiliados (segunda vía de Scouter, sin filtro de marca)

- **Generador Agent — publicación real** — PARCIAL. Genera el artículo
  completo (SEO, tabla comparativa, enlace placeholder) y lo deja en fase
  `borrador_listo`, pero nunca publica en ningún sitio porque no existe
  WordPress real todavía (decisión explícita del usuario). Falta: crear el
  sitio WordPress y conectar su API (candidato natural para n8n, según la
  decisión de reconciliación, en vez de reconstruirlo en Python).

## Equipo: Scouter (organigrama principal, con filtro de marca/moat)

- **Scouter con criterio de marca/moat** — PENDIENTE. El documento AGENTE
  menciona un "criterio de cribado ya definido" de marca/moat para este
  equipo, pero ese criterio no existe en ningún documento disponible en
  este proyecto. Se decidió construir el Investigador para la vía paralela
  sin marca (contenido de afiliados) en su lugar, pero el Scouter real —
  el que filtraría oportunidades de negocio con marca propia — sigue sin
  diseñarse ni construirse.

## Equipo: Auditoría Interna (transversal a varias líneas de negocio)

- **Supervisor Agent — cobertura multi-negocio real** — PARCIAL. Cubre
  JARVIS mismo y la línea de contenido/afiliados (artículos con datos sin
  verificar, ideas sin fuente trazable, tareas huérfanas), pero esas reglas
  están escritas a mano para esa línea concreta (dependen directamente de
  `generador_agent`/`investigador_agent`). Trading no tiene ninguna regla
  de auditoría todavía (ej. nada que revise anomalías del paper trading o
  del proceso de cribado), y no hay un mecanismo genérico que active
  auditoría automáticamente cuando se añada una línea de negocio nueva —
  cada línea requiere código de auditoría nuevo a mano.

## Equipo: Soporte a Claude

- **Alcance completo del equipo** — INDETERMINADO (no PARCIAL ni PENDIENTE
  con certeza). Lo único construido y verificado es el flujo
  `estrategico` → `memory_engine.flag_for_claude()` →
  `pending_for_claude()`: JARVIS marca una pregunta de rumbo/arquitectura
  como "esto le toca a Claude" y queda visible para que el usuario la traiga
  él mismo a una conversación con Claude (nunca se llama a la API
  automáticamente, decisión explícita — Constitution Art. 9). No hay forma
  de confirmar aquí si el documento original de AGENTE definía un alcance
  mayor para este equipo (ej. entrega de código a revisión automática,
  integración con `/code-review`), porque ese documento no está disponible
  en este proyecto. Recomendado: si el usuario recuerda un alcance más
  amplio para "Soporte a Claude", describirlo para poder auditarlo de
  verdad en la próxima pasada.

## Infraestructura (transversal, parte del roadmap de AGENTE, no de JARVIS)

- **Raspberry Pi 24/7, Wake-on-LAN, UptimeRobot** — PENDIENTE. Descartado
  explícitamente del alcance actual: todo corre en el portátil del usuario
  vía Tareas Programadas de Windows (bot de Telegram, daily briefing).
  Sería necesario si se quiere disponibilidad 24/7 independiente de que el
  portátil esté encendido.
- **n8n en producción** — PENDIENTE / alcance reducido a propósito. Por
  decisión del 2026-08-31, n8n queda reservado solo para integraciones con
  APIs de terceros que no merece la pena reconstruir en Python (ej. publicar
  en WordPress cuando exista el sitio) — no hay ningún workflow de n8n
  construido todavía porque todavía no ha hecho falta ninguno.
- **Supabase** — PENDIENTE / descartado por decisión explícita. Se decidió
  extender el SQLite ya existente de JARVIS en vez de introducir Supabase,
  mientras no haga falta acceso remoto real a la base de datos.
