# Memory Engine

Estado: Diseño

---

# Objetivo

El Memory Engine es el núcleo de JARVIS.

Su responsabilidad es almacenar, proteger, relacionar y versionar todo el conocimiento del sistema, garantizando que exista una única fuente de verdad independiente de cualquier modelo de inteligencia artificial.

La memoria constituye el activo más importante del sistema.

Los modelos de IA son herramientas intercambiables.

La memoria no.

---

# Misión

Responder a una única pregunta.

> ¿Qué sabe actualmente JARVIS?

Y garantizar que esa respuesta sea siempre consistente.

---

# Responsabilidades

- Gestionar la memoria permanente.
- Mantener la integridad de los datos.
- Versionar toda la información relevante.
- Relacionar entidades.
- Permitir búsquedas rápidas.
- Proporcionar información al Context Engine.
- Mantener un historial completo.
- Archivar conocimiento antiguo.
- Garantizar una única fuente de verdad.

---

# Lo que NO hace

El Memory Engine nunca:

- Razona.
- Toma decisiones.
- Prioriza.
- Ejecuta automatizaciones.
- Selecciona modelos de IA.
- Modifica información estratégica por iniciativa propia.

---

# Principios

## 1. La memoria es permanente.

Nada desaparece sin decisión explícita.

---

## 2. Todo conocimiento tiene propietario.

Cada dato existe una única vez.

Nunca habrá duplicados.

---

## 3. Todo es versionable.

Cuando cambia el conocimiento:

Nunca se sobrescribe.

Se crea una nueva versión.

---

## 4. Todo debe poder recuperarse.

Cualquier versión histórica debe poder consultarse.

---

## 5. Toda modificación debe quedar registrada.

Quién.

Cuándo.

Por qué.

Cómo.

---

# Tipos de memoria

## Inbox

Información pendiente de procesar.

---

## Memoria Activa

Conocimiento utilizado habitualmente.

---

## Archivo

Información histórica.

---

## Eliminable

Información sin utilidad futura.

Nunca se elimina automáticamente.

---

# Flujo de conocimiento

Todo sigue el mismo recorrido.

Entrada

↓

Inbox

↓

Clasificación

↓

Extracción de conocimiento

↓

Validación

↓

Relación con entidades

↓

Versionado

↓

Memoria permanente

---

# Qué se almacena

La memoria nunca almacena únicamente documentos.

Almacena conocimiento estructurado.

Ejemplos.

- Objetivos
- Proyectos
- Personas
- Recursos
- Decisiones
- Preferencias
- Necesidades
- Reglas
- Eventos
- Activos
- Insights
- Conocimiento

Los documentos originales se conservan únicamente como evidencia.

---

# Qué NO es conocimiento

Un PDF no es conocimiento.

Un vídeo no es conocimiento.

Una conversación no es conocimiento.

Son recursos.

El conocimiento es la información útil extraída de ellos.

---

# Versionado

Toda información importante será versionada.

Cuando exista un cambio:

Versión anterior

↓

Nueva versión

↓

Relación entre ambas

Nunca se pierde el histórico.

---

# Conflictos

Cuando dos fuentes proporcionen información incompatible:

1. Buscar nuevas fuentes.

2. Intentar resolver automáticamente el conflicto.

3. Si continúa existiendo incertidumbre:

Generar una propuesta para el usuario.

Nunca decidir sin evidencia suficiente.

---

# Calidad del conocimiento

Antes de entrar en memoria permanente el conocimiento deberá cumplir:

- Ser relevante.
- Ser consistente.
- No duplicar información.
- Estar relacionado con otras entidades.
- Poder justificarse.

---

# Búsqueda

Toda entidad debe poder localizarse mediante:

- Nombre.
- Tipo.
- Relación.
- Etiquetas.
- Fecha.
- Contexto.
- Texto libre.

---

# Relación entre entidades

La memoria no funciona mediante carpetas.

Funciona mediante relaciones.

Ejemplo.

Proyecto

↓

Relacionado con

↓

Objetivo

↓

Recursos

↓

Decisiones

↓

Conocimiento

Este ejemplo usa únicamente entidades definidas en Schemas/Entities.md. "Área" y "Persona" se han retirado del ejemplo porque no existen todavía como entidades de primer nivel; si en el futuro se necesitan (por ejemplo, para agrupar objetivos por ámbito de vida o modelar relaciones con terceros), deben añadirse primero a Schemas/Entities.md antes de volver a aparecer aquí.

Las relaciones constituyen el verdadero valor del sistema.

---

# Integridad

La memoria nunca debe:

- Contradecir la Constitución de JARVIS.
- Romper la trazabilidad.
- Perder versiones.
- Crear duplicados.
- Eliminar información crítica.
- Depender de un modelo de IA.

---

# Interfaces

El Memory Engine proporciona información a:

- Context Engine
- User Model Engine
- Decision Engine
- Executive Dashboard
- Orchestrator
- Agentes

Nunca al contrario.

La memoria siempre actúa como fuente de verdad.

---

# Objetivo final

Conseguir que cualquier modelo de IA pueda razonar utilizando exactamente el mismo conocimiento, independientemente del proveedor, garantizando continuidad, consistencia y evolución durante toda la vida del sistema.