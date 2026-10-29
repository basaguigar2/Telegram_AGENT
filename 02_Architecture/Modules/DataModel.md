# Data Model

Estado: Diseño

---

# Objetivo

El Data Model define la estructura conceptual de la información dentro de JARVIS.

Su función es establecer qué entidades existen, cómo se relacionan y cómo evolucionan con el tiempo.

Es la base sobre la que funcionarán:

- Memory Engine.
- Knowledge Engine.
- User Model Engine.
- Decision Engine.
- Orchestrator.
- Dashboard.

---

# Principio fundamental

JARVIS no organiza información únicamente mediante carpetas.

JARVIS organiza información mediante entidades y relaciones.

El valor del sistema no está solo en almacenar información.

Está en comprender cómo se conecta.

---

# Concepto de entidad

Una entidad representa cualquier elemento relevante dentro del sistema.

Ejemplos:

- Persona.
- Proyecto.
- Objetivo.
- Recurso.
- Decisión.
- Tarea.
- Conocimiento.
- Evento.

---

# Propiedades de una entidad

Toda entidad debe tener:

## Identificador único

Permite localizarla sin ambigüedad.

---

## Nombre

Representación humana.

---

## Tipo

Categoría de entidad.

---

## Estado

Situación actual.

Ejemplo:

- Activo.
- Pausado.
- Cerrado.
- Archivado.

---

## Fecha

Información temporal.

---

## Relaciones

Conexiones con otras entidades.

---

## Historial

Cambios realizados a lo largo del tiempo.

---

# Entidades principales

---

# Usuario

Representa al propietario de JARVIS.

Contiene:

- Objetivos.
- Preferencias.
- Principios.
- Restricciones.
- Recursos.
- Estado.

---

# Objetivo

Representa algo que el usuario quiere conseguir.

Ejemplos:

- Mejorar carrera profesional.
- Crear negocio.
- Aprender programación.

Puede tener:

- Prioridad.
- Fecha objetivo.
- Estado.
- Métricas.

---

# Proyecto

Representa un conjunto de acciones orientadas a conseguir un resultado.

Ejemplos:

- Crear una aplicación.
- Construir JARVIS.
- Preparar una certificación.

Relaciones:

Proyecto → Objetivo.

Proyecto → Recursos.

Proyecto → Tareas.

---

# Tarea

Representa una acción concreta.

Debe tener:

- Descripción.
- Prioridad.
- Estado.
- Tiempo estimado.
- Dependencias.

---

# Conocimiento

Representa información procesada y útil.

Ejemplos:

- Conceptos técnicos.
- Aprendizajes.
- Reglas.
- Conclusiones.

---

# Recurso

Representa una fuente de información.

Ejemplos:

- PDF.
- Vídeo.
- Web.
- Libro.
- Curso.

---

# Decisión

Representa una elección tomada.

Debe guardar:

- Contexto.
- Alternativas consideradas.
- Motivo.
- Resultado.

---

# Regla

Representa una condición que guía el comportamiento.

Tipos:

- Constitución.
- Sistema.
- Personal.
- Temporal.

---

# Insight

Representa una conclusión obtenida mediante observación.

Ejemplo:

"El usuario aprende mejor mediante proyectos prácticos."

Debe incluir:

- Evidencia.
- Confianza.
- Estado de validación.

---

# Evento

Representa algo que ocurre en el tiempo.

Ejemplos:

- Reunión.
- Compra.
- Cambio profesional.
- Finalización de tarea.

---

# Relación entre entidades

Las relaciones son fundamentales.

Ejemplos:

Usuario

↓

tiene

↓

Objetivos


Proyecto

↓

pertenece a

↓

Objetivo


Conocimiento

↓

apoya

↓

Decisión


Decisión

↓

modifica

↓

Proyecto

---

# Versionado

Todas las entidades importantes deben poder evolucionar.

Nunca se pierde el histórico.

Ejemplo:

Objetivo versión 1

↓

Cambio

↓

Objetivo versión 2

---

# Estados

Las entidades pueden tener ciclos de vida.

Ejemplo:

Idea

↓

Evaluación

↓

Proyecto

↓

Activo

↓

Finalizado

↓

Archivado

---

# Integridad

El modelo debe evitar:

- Duplicados.
- Información aislada.
- Pérdida de contexto.
- Contradicciones.

---

# Extensibilidad

El modelo debe permitir añadir nuevas entidades en el futuro sin reconstruir el sistema.

Ejemplos futuros:

- Negocio.
- Cliente.
- Inversión.
- Agente.
- Automatización.

---

# Objetivo final

Crear una representación digital coherente del mundo del usuario donde toda información pueda relacionarse, evolucionar y aportar valor para la toma de decisiones.