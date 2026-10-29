# Agent Framework

Estado: Diseño

---

# Objetivo

El Agent Framework define cómo se diseñan, crean, gestionan y evolucionan los agentes dentro de JARVIS.

Su función es establecer una arquitectura común para todos los agentes especializados.

---

# Misión

Responder a una única pregunta:

> ¿Cómo debe funcionar un trabajador digital dentro de JARVIS?

---

# Principio fundamental

Un agente no es un modelo de IA.

Un agente es una unidad especializada de trabajo con:

- Objetivo.
- Responsabilidades.
- Límites.
- Herramientas.
- Contexto.
- Permisos.
- Métricas.

---

# Filosofía

JARVIS no busca crear muchos agentes.

Busca crear una organización eficiente.

Cada agente debe existir porque aporta un valor claro.

Si una tarea puede resolverse sin un agente, no debe crearse uno.

---

# Anatomía de un agente

Todo agente debe tener:

---

## Identidad

Define quién es.

Incluye:

- Nombre.
- Propósito.
- Área.
- Versión.

Ejemplo:

Builder Agent v1.0

---

## Misión

Describe su objetivo principal.

Ejemplo:

"Crear soluciones software siguiendo los estándares técnicos definidos."

---

## Responsabilidades

Define qué debe hacer.

Ejemplo:

- Analizar código.
- Crear propuestas técnicas.
- Implementar funcionalidades.

---

## Límites

Define qué nunca debe hacer.

Ejemplo:

- No publicar en producción.
- No cambiar arquitectura sin aprobación.

---

## Herramientas

Define qué puede utilizar.

Ejemplo:

- Editor.
- Terminal.
- APIs.
- Bases de datos.

---

## Modelo de IA

Define qué inteligencia utiliza.

Puede cambiar mediante:

- IA Gateway.
- Model Router.

---

## Permisos

Define su nivel de autonomía.

---

# Niveles de autonomía

Escala única, definida en `Schemas/Permissions.md` (0 Consulta/Manual, 1 Asistido, 2 Supervisado, 3 Autónomo limitado, 4 Autónomo estratégico). No se repite aquí para no tener dos fuentes de verdad sobre lo mismo -- este documento tenía su propia copia casi idéntica hasta esta revisión, y `Permissions.md` ya se escribió específicamente para unificarla.

Desde la revisión de arquitectura CEO (`PropuestaArquitecturaCEO.md`), el nivel 4 / bloqueo por Constitución se limita a tres acciones nombradas explícitamente (ejecutar código, eliminar, desplegar) -- no a una categoría abierta de "estratégico".

---

# Contrato de agente

Todos los agentes deben seguir un contrato común:

Entrada:

- Objetivo.
- Contexto.
- Restricciones.
- Recursos disponibles.

Proceso:

- Análisis.
- Ejecución.
- Validación.

Salida:

- Resultado.
- Evidencias.
- Cambios realizados.
- Nivel de confianza.

---

# Comunicación entre agentes

Los agentes no deben comunicarse libremente.

Toda comunicación debe pasar por:

Orchestrator

↓

Agente receptor

---

Motivo:

Evitar:

- Dependencias ocultas.
- Caos.
- Información contradictoria.

---

# Agentes iniciales previstos

---

# Builder Agent

Área:

Desarrollo software.

Responsabilidades:

- Programación.
- Arquitectura técnica.
- Integración.

Límites:

- No publicar.
- No desplegar sin aprobación.

---

# Research Agent

Área:

Investigación.

Responsabilidades:

- Buscar información.
- Comparar fuentes.
- Extraer conocimiento.

---

# Knowledge Agent

Área:

Gestión del conocimiento.

Responsabilidades:

- Clasificar información.
- Crear relaciones.
- Preparar memoria.

---

# Financial Agent

Área:

Finanzas.

Responsabilidades:

- Analizar gastos.
- Crear informes.
- Detectar oportunidades.

Límites:

- No realizar movimientos financieros.

---

# Learning Agent

Área:

Formación.

Responsabilidades:

- Crear planes de aprendizaje.
- Recomendar recursos.
- Medir progreso.

---

# Marketing Agent

Área:

Negocios.

Responsabilidades:

- SEO.
- Investigación mercado.
- Estrategia contenido.

---

# Personal Assistant Agent

Área:

Vida personal.

Responsabilidades:

- Organización personal.
- Recordatorios.
- Recomendaciones.

Límites:

- No imponer decisiones.

---

# Creación de nuevos agentes

Antes de crear un agente debe responderse:

1. ¿Qué problema resuelve?
2. ¿Por qué no puede hacerlo otro agente?
3. ¿Qué valor aporta?
4. ¿Qué permisos necesita?
5. ¿Cómo mediremos su éxito?

---

# Eliminación de agentes

Un agente debe revisarse si:

- No aporta valor.
- Duplica funciones.
- Aumenta complejidad.
- Tiene bajo uso.

---

# Evaluación de agentes

Cada agente debe medirse mediante:

- Calidad del resultado.
- Tiempo ahorrado.
- Coste generado.
- Errores cometidos.
- Utilidad percibida.

---

# Evolución

Los agentes tienen versiones.

Ejemplo:

Builder Agent v1

↓

Mejoras

↓

Builder Agent v2

---

# Seguridad

Todo agente debe:

- Respetar Policy Engine.
- Usar memoria oficial.
- Registrar acciones.
- Mantener trazabilidad.

---

# Objetivo final

Crear una organización digital formada por especialistas capaces de colaborar, aprender y mejorar continuamente, manteniendo siempre el control del usuario.

Los agentes son los trabajadores.

La arquitectura es la empresa.

El usuario es el director.