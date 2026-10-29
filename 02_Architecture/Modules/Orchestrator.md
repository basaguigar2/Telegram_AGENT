# Orchestrator

Estado: Diseño

---

# Objetivo

El Orchestrator es el módulo encargado de coordinar los diferentes agentes, herramientas y procesos de JARVIS.

Su función es transformar una decisión aprobada en un flujo de trabajo ejecutable.

No decide qué debe hacerse.

Decide quién debe hacerlo y cómo coordinarlo.

---

# Misión

Responder a una única pregunta:

> ¿Qué agente, herramienta o proceso es más adecuado para ejecutar esta acción?

---

# Principio fundamental

Los agentes son trabajadores especializados.

El Orchestrator es el coordinador.

Ningún agente debe tener conocimiento completo del sistema.

El Orchestrator proporciona únicamente el contexto necesario.

---

# Responsabilidades

- Recibir tareas aprobadas.
- Seleccionar agentes adecuados.
- Crear flujos de trabajo.
- Coordinar agentes.
- Gestionar dependencias.
- Controlar estados.
- Supervisar resultados.
- Gestionar errores.
- Solicitar intervención humana cuando sea necesario.
- Registrar ejecución.

---

# Lo que NO hace

El Orchestrator nunca:

- Decide objetivos.
- Cambia prioridades.
- Modifica la memoria directamente.
- Define reglas.
- Sustituye al usuario.
- Ejecuta decisiones estratégicas.
- Tiene conocimiento completo de todas las áreas.

---

# Flujo general

Actualizado tras la revisión de arquitectura CEO (PropuestaArquitecturaCEO.md) -- el diagrama anterior no incluía ningún punto de entrada/salida hacia el usuario ni mencionaba al CEO, porque se escribió antes de que ese módulo existiera. El Orchestrator sigue sin decidir nada (eso no cambia) -- lo que cambia es quién le entrega el trabajo y quién recibe el resultado.

Usuario

↓

CEO (Modules/CEO.md) -- comprende, recupera memoria/contexto, consulta Constitución/Capability Registry, elabora el plan

↓

Orchestrator -- coordina

↓

Agente especializado

↓

Orchestrator

↓

CEO -- integra el resultado, genera la respuesta

↓

Usuario

El Orchestrator nunca recibe una petición directamente del usuario ni le responde directamente -- siempre entra y sale por el CEO.

---

# Entrada

El Orchestrator recibe:

## Acción aprobada

Ejemplo:

"Preparar análisis de mercado."

---

## Contexto necesario

Ejemplo:

- Objetivo.
- Restricciones.
- Recursos.
- Formato esperado.

---

## Políticas aplicables

Ejemplo:

- Qué puede hacer.
- Qué necesita aprobación.

---

# Selección de agentes

El Orchestrator selecciona agentes según:

- Capacidad.
- Especialización.
- Coste.
- Disponibilidad.
- Nivel de autonomía permitido.

---

# Ejemplo

Solicitud:

"Analiza una idea de negocio."

El Decision Engine determina:

Acción recomendada:

"Realizar estudio inicial."

El Orchestrator crea el flujo:

Investigador Agent

↓

Analista Financiero Agent

↓

Marketing Agent

↓

Gestor Documental Agent

↓

Informe final

---

# Agentes

Los agentes son módulos especializados.

Ejemplos:

## Builder Agent

Responsable:

- Programación.
- Arquitectura técnica.
- Desarrollo.

---

## Tester Agent

Responsable:

- Validación.
- Pruebas.
- Calidad.

---

## Research Agent

Responsable:

- Investigación.
- Recopilación de información.

---

## Marketing Agent

Responsable:

- SEO.
- Estrategia.
- Análisis mercado.

---

## Financial Agent

Responsable:

- Análisis financiero.
- Modelos económicos.

---

## Learning Agent

Responsable:

- Formación.
- Planes de aprendizaje.

---

# Contrato de los agentes

Todo agente debe definir:

- Objetivo.
- Responsabilidades.
- Límites.
- Entradas.
- Salidas.
- Herramientas disponibles.
- Nivel de autonomía.
- Métricas.

---

# Estados de ejecución

Cada trabajo tiene un estado.

## Pendiente

Esperando ejecución.

---

## En ejecución

Proceso activo.

---

## Bloqueado

Necesita información o aprobación.

---

## Completado

Trabajo finalizado.

---

## Fallido

Error durante ejecución.

---

# Gestión de errores

Cuando un agente falla:

1. Registrar error.
2. Analizar causa.
3. Intentar recuperación si está permitido.
4. Solicitar intervención humana si es necesario.

---

# Paralelización

El Orchestrator puede ejecutar agentes simultáneamente cuando:

- Las tareas sean independientes.
- No exista conflicto.
- Mejore el tiempo total.

---

# Límites

El Orchestrator debe evitar:

- Crear agentes innecesarios.
- Dividir tareas simples excesivamente.
- Generar complejidad sin beneficio.
- Ejecutar procesos sin objetivo claro.

---

# Coste y eficiencia

Antes de asignar una tarea debe considerar:

- ¿Necesita IA?
- ¿Puede hacerlo un script?
- ¿Puede hacerlo un modelo local?
- ¿Necesita un modelo premium?

El objetivo es maximizar valor y minimizar coste.

---

# Aprendizaje

El Orchestrator aprende de:

- Resultados de agentes.
- Tiempo empleado.
- Errores.
- Calidad obtenida.

Puede proponer mejoras en los flujos.

---

# Eventos

## Escucha

- Nueva tarea aprobada.
- Cambio de prioridad.
- Resultado de agentes.
- Errores.

---

## Genera

- Trabajo asignado.
- Estado de ejecución.
- Resultados.
- Alertas.

---

# Objetivo final

Crear una organización digital formada por especialistas coordinados, donde cada tarea llegue al agente adecuado con el contexto correcto y siempre bajo las reglas de JARVIS.

El Orchestrator convierte un conjunto de agentes independientes en una organización coherente.