# Policy Engine

Estado: Diseño

---

# Objetivo

El Policy Engine es el sistema encargado de garantizar que todas las acciones de JARVIS respeten sus principios, reglas y límites establecidos.

Su función es actuar como una capa de control entre la intención y la ejecución.

El Policy Engine no decide qué hacer.

Decide qué está permitido hacer.

---

# Misión

Responder a una única pregunta:

> ¿Puede JARVIS realizar esta acción respetando sus principios, reglas y permisos?

---

# Principio fundamental

La capacidad de ejecutar una acción nunca debe superar los límites establecidos por la arquitectura.

JARVIS puede ser inteligente.

Pero siempre debe estar controlado.

---

# Responsabilidades

- Evaluar acciones propuestas.
- Aplicar reglas del sistema.
- Aplicar preferencias del usuario.
- Aplicar restricciones.
- Verificar permisos.
- Bloquear acciones no autorizadas.
- Solicitar aprobación cuando sea necesario.
- Mantener trazabilidad de decisiones.
- Garantizar cumplimiento de la Constitución de JARVIS.

---

# Lo que NO hace

El Policy Engine nunca:

- Decide prioridades.
- Recomienda objetivos.
- Sustituye al Decision Engine.
- Ejecuta acciones.
- Modifica reglas automáticamente.
- Cambia los principios fundamentales.

---

# Jerarquía de políticas

Las reglas tienen diferentes niveles de autoridad.

---

## Nivel 1 - Constitución de JARVIS

Máxima autoridad.

Nunca puede ser modificada por agentes.

Ejemplos:

- El usuario mantiene el control estratégico.
- No publicar sin aprobación.
- No desplegar a producción sin supervisión.
- La memoria es la fuente de verdad.

---

## Nivel 2 - Políticas del sistema

Reglas de funcionamiento.

Ejemplos:

- Qué modelos pueden utilizarse.
- Qué tareas requieren aprobación.
- Qué información puede compartirse.

---

## Nivel 3 - Reglas personales

Preferencias y criterios del usuario.

Ejemplos:

- Presupuesto máximo.
- Marcas preferidas.
- Prioridades personales.

---

## Nivel 4 - Reglas temporales

Situaciones puntuales.

Ejemplos:

- Esta semana priorizar un proyecto.
- Durante vacaciones reducir carga.

---

# Flujo de validación

Toda acción sigue este proceso:

Solicitud de acción

↓

Decision Engine propone

↓

Policy Engine evalúa

↓

Resultado

↓

Permitido

o

↓

Requiere aprobación

o

↓

Bloqueado

---

# Resultados posibles

## Permitido

La acción cumple todas las reglas.

Puede continuar.

---

## Requiere aprobación

La acción puede ser válida pero necesita confirmación humana.

Ejemplos:

- Crear un proyecto nuevo.
- Comprar algo.
- Enviar información externa.

---

## Bloqueado

La acción contradice una regla superior.

Ejemplos:

- Publicar automáticamente.
- Eliminar memoria crítica.
- Ejecutar acciones financieras no autorizadas.

---

# Ejemplos

## Desarrollo de software

Propuesta:

"Subir aplicación a producción."

Evaluación:

- ¿Está permitido desplegar?
- ¿Existe aprobación?

Resultado:

Bloqueado hasta aprobación del usuario.

---

## Compras

Propuesta:

"Comprar una camiseta encontrada online."

Evaluación:

- ¿Existe necesidad?
- ¿Cumple presupuesto?
- ¿Coincide con preferencias?

Resultado:

Puede recomendar.

La compra requiere decisión humana.

---

## Gestión de conocimiento

Propuesta:

"Eliminar documento antiguo."

Evaluación:

- ¿Existe histórico?
- ¿Puede perder valor?

Resultado:

Archivar.

No eliminar automáticamente.

---

# Integración con otros módulos

## Memory Engine

Consulta:

- Reglas almacenadas.
- Historial.
- Decisiones anteriores.

---

## User Model Engine

Consulta:

- Preferencias.
- Restricciones.
- Principios personales.

---

## Context Engine

Utiliza:

- Situación actual.
- Información relevante.

---

## Decision Engine

Recibe:

- Permiso.
- Restricción.
- Necesidad de aprobación.

---

## Orchestrator

Utiliza:

- Resultado de validación antes de ejecutar.

---

# Eventos

## Escucha

- Acción propuesta.
- Solicitud de automatización.
- Petición de agente.
- Cambio de reglas.

---

## Genera

- Acción permitida.
- Acción bloqueada.
- Solicitud de aprobación.
- Registro de decisión.

---

# Auditoría

Toda evaluación debe registrar:

- Acción evaluada.
- Fecha.
- Módulo solicitante.
- Reglas aplicadas.
- Resultado.
- Motivo.

---

# Evolución

Las políticas pueden evolucionar.

Pero:

- La Constitución requiere revisión estratégica.
- Las reglas personales pueden cambiar.
- Las reglas temporales caducan.

Toda modificación debe quedar versionada.

---

# Objetivo final

Garantizar que JARVIS pueda ser cada vez más autónomo sin perder alineación con sus principios.

El Policy Engine permite aumentar la capacidad del sistema manteniendo siempre el control humano.