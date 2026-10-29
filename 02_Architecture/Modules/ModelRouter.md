# Model Router

Estado: Diseño

---

# Objetivo

El Model Router es el módulo encargado de seleccionar el modelo de inteligencia artificial más adecuado para cada tarea dentro de JARVIS.

Su objetivo es maximizar la relación entre coste, velocidad, privacidad y calidad.

---

# Misión

Responder a una única pregunta:

> ¿Cuál es el modelo adecuado para resolver esta tarea con el mínimo coste posible manteniendo la calidad necesaria?

---

# Principio fundamental

JARVIS no utiliza el modelo más potente.

JARVIS utiliza el modelo adecuado.

La inteligencia premium debe reservarse para problemas donde aporte una diferencia real.

---

# Responsabilidades

- Analizar requisitos de una tarea.
- Clasificar complejidad.
- Seleccionar modelo.
- Evaluar coste.
- Evaluar privacidad.
- Gestionar fallback.
- Comparar rendimiento.
- Aprender del histórico.

---

# Lo que NO hace

El Model Router nunca:

- Decide qué tarea debe realizarse.
- Cambia prioridades.
- Ejecuta acciones.
- Guarda conocimiento.
- Sustituye al usuario.
- Sustituye al Decision Engine.

---

# Factores de decisión

Cada tarea será evaluada según:

## Complejidad

¿Necesita razonamiento avanzado?

---

## Coste

¿Merece utilizar un modelo premium?

---

## Privacidad

¿Puede salir información del entorno local?

---

## Velocidad

¿Debe responder inmediatamente?

---

## Calidad necesaria

¿Qué nivel de precisión requiere?

---

# Clasificación de tareas

## Nivel 1 - Automatización simple

Características:

- Repetitiva.
- Baja complejidad.
- Alto volumen.

Ejemplos:

- Clasificar documentos.
- Crear etiquetas.
- Resumir textos.

Modelo recomendado:

Modelo local.

---

## Nivel 2 - Trabajo intelectual medio

Características:

- Necesita comprensión.
- Requiere cierta creatividad.

Ejemplos:

- Preparar informes.
- Investigación inicial.
- Brainstorming.

Modelo recomendado:

Modelo local avanzado o modelo económico.

---

## Nivel 3 - Trabajo crítico

Características:

- Alto impacto.
- Requiere razonamiento profundo.

Ejemplos:

- Arquitectura.
- Estrategia.
- Decisiones empresariales.
- Revisiones importantes.

Modelo recomendado:

Modelo premium.

---

# Reglas iniciales

## Regla 1

Primero intentar resolver localmente.

---

## Regla 2

Escalar únicamente si existe una razón.

---

## Regla 3

Claude u otros modelos premium son recursos estratégicos.

No herramientas diarias.

---

## Regla 4

La calidad obtenida debe justificar el coste.

---

# Fallback

Si un modelo falla:

Modelo principal

↓

Modelo alternativo

↓

Aviso al usuario si cambia la calidad esperada

---

# Aprendizaje

El Model Router aprende mediante:

- Resultados obtenidos.
- Evaluaciones del usuario.
- Coste generado.
- Tiempo empleado.

Ejemplo:

Si un modelo local resuelve correctamente una tarea durante 100 ocasiones:

La tarea puede quedar asignada por defecto a ese modelo.

---

# Registro

Cada llamada debe guardar:

- Tarea.
- Modelo utilizado.
- Tiempo.
- Coste.
- Resultado.
- Valoración.

---

# Integración

## IA Gateway

Proporciona acceso a modelos.

---

## Decision Engine

Define importancia de la tarea.

---

## Orchestrator

Solicita ejecución.

---

## Memory Engine

Guarda métricas e histórico.

---

# Objetivo final

Crear una inteligencia híbrida donde JARVIS utilice recursos locales siempre que sea posible y reserve modelos avanzados únicamente para situaciones donde generen una ventaja real.

La arquitectura debe ser independiente del modelo dominante del momento.