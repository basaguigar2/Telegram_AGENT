# Schema — Permissions

Estado: Borrador v0.1
Depende de: Modules/PolicyEngine.md, Modules/AgentFrameWork.md, Modules/AutomationEngine.md
Autoridad de evaluación: Policy Engine (ningún otro módulo se autoconcede permisos)

---

# Nota de consistencia antes de nada

`AgentFrameWork.md` define 5 niveles de autonomía (0 Consulta, 1 Asistente, 2 Operador supervisado, 3 Operador autónomo limitado, 4 Autónomo estratégico — no permitido) y `AutomationEngine.md` define, por separado, otros 5 niveles casi calcados (0 Manual, 1 Asistido, 2 Automático controlado, 3 Autónomo limitado, 4 Autónomo estratégico — no permitido). Son la misma escala aplicada dos veces con nombres distintos. Aquí las unifico en una sola escala de autonomía porque tener dos escalas paralelas es exactamente el riesgo que la auditoría marcó como "complejidad innecesaria" — con dos escalas, un agente y una automatización podrían tener el "mismo" nivel numérico significando cosas distintas. Si prefieres mantenerlas separadas por alguna razón que no veo, dímelo y lo revierto.

---

# Escala única de autonomía (sustituye a las dos anteriores)

| Nivel | Nombre | Puede hacer | Requiere aprobación |
|---|---|---|---|
| 0 | Consulta / Manual | Solo responde o informa. No ejecuta nada. | — |
| 1 | Asistido | Prepara información (resúmenes, informes, propuestas). | El usuario decide si se usa. |
| 2 | Supervisado | Ejecuta tareas operativas de bajo riesgo. | Confirmación puntual antes de ejecutar. |
| 3 | Autónomo limitado | Mantiene procesos definidos sin supervisión constante, dentro de límites explícitos. Incluye guardar, generar, sobrescribir e integrar (revisión de arquitectura CEO, PropuestaArquitecturaCEO.md). | Ninguna. |
| 4 | Autónomo estratégico | Lista cerrada de tres acciones, nunca una categoría abierta: ejecutar código generado, eliminar, desplegar a producción. | Confirmación puntual sí/no siempre, sin excepción (Constitution Art. 2 y 10). |

Tanto un Agente (`AgentFrameWork.md`) como una Automatización (`AutomationEngine.md`) referencian esta misma escala mediante el campo `autonomy_level` en su definición, en vez de mantener cada uno su propia tabla.

---

# Matriz de permisos por entidad

Quién puede proponer un cambio (`propose`) y quién puede ejecutar la transición final (`commit`) — `commit` sobre memoria permanente es siempre exclusivo de Memory Engine.

| Entidad | Puede `propose` | Puede `commit` | Requiere aprobación de usuario |
|---|---|---|---|
| Usuario (perfil) | User Model Engine | Memory Engine | Sí, siempre |
| Objetivo | Usuario, Decision Engine | Memory Engine | Sí, si es prioridad estratégico |
| Proyecto | Orchestrator, Decision Engine | Memory Engine | Sí, en creación y en cierre |
| Tarea | Orchestrator, Automation Engine | Memory Engine | No, si nivel de autonomía ≥ 2 |
| Conocimiento | Knowledge Engine | Memory Engine | No |
| Recurso | Knowledge Engine | Memory Engine | No |
| Decisión | Decision Engine | Memory Engine (registro), Usuario (resultado) | Sí, siempre en el campo `result` |
| Regla (constitución) | — (fija, no editable vía sistema) | — | N/A |
| Regla (sistema/personal/temporal) | Policy Engine, Usuario | Memory Engine | Sí, si es de nivel "sistema" |
| Insight | User Model Engine, Decision Engine | Memory Engine | Sí (campo `validated`) |
| Evento | Cualquier módulo | Memory Engine | No |

---

# Resultados de evaluación (Policy Engine)

Heredado de `PolicyEngine.md`: toda acción evaluada devuelve `permitido`, `requiere_aprobación` o `bloqueado`. Aquí se ata a la escala de autonomía:

- `permitido`: la acción está dentro del `autonomy_level` del agente/automatización que la solicita.
- `requiere_aprobación`: la acción excede el nivel actual pero no está en la lista de bloqueadas.
- `bloqueado`: la acción es de nivel 4 o contradice una Regla de nivel "constitución" — no hay excepción posible sin cambiar la Constitución misma.

---

# Auditoría de permisos

Cada evaluación de Policy Engine debe persistirse como un Evento de tipo `policy.evaluated` (Schemas/Events.md) con `context = {action, requesting_module, autonomy_level_required, autonomy_level_granted, result}`. Esto conecta directamente con la responsabilidad "auditoría" que ya describe `PolicyEngine.md`, dándole una estructura de datos concreta en vez de dejarla como intención.
