# Context Engine

Estado: Diseño

---

# Objetivo

El Context Engine es el sistema encargado de construir el contexto adecuado para cada situación.

Su misión es seleccionar, combinar y preparar la información necesaria antes de que cualquier agente, modelo de IA o módulo tome una acción.

El Context Engine evita que JARVIS consulte información innecesaria y garantiza que cada decisión se tome con la información más relevante disponible.

---

# Misión

Responder a una única pregunta:

> ¿Qué información necesita JARVIS en este momento para comprender correctamente la situación?

---

# Principio fundamental

La información existe.

El contexto decide cuál importa.

Tener mucha información no significa tener conocimiento útil.

El valor está en seleccionar correctamente.

---

# Responsabilidades

- Recopilar información relevante.
- Crear contexto dinámico.
- Priorizar información.
- Reducir ruido.
- Preparar instrucciones para modelos de IA.
- Unificar información procedente de diferentes fuentes.
- Mantener contexto temporal.
- Mantener contexto personal.
- Mantener contexto profesional.

---

# Lo que NO hace

El Context Engine nunca:

- Decide objetivos.
- Toma decisiones estratégicas.
- Modifica memoria permanente.
- Ejecuta tareas.
- Crea conocimiento nuevo.
- Sustituye al usuario.

---

# Fuentes de contexto

El Context Engine puede utilizar:

## Memory Engine

Información almacenada.

Ejemplos:

- Proyectos.
- Decisiones.
- Documentos.
- Recursos.

---

## User Model Engine

Información sobre el usuario.

Ejemplos:

- Preferencias.
- Objetivos.
- Estado.
- Restricciones.

---

## Estado actual

Información temporal.

Ejemplos:

- Fecha.
- Hora.
- Calendario.
- Energía disponible.
- Tiempo libre.

---

## Entorno

Información externa.

Ejemplos:

- Noticias.
- Mercado.
- Clima.
- Cambios tecnológicos.

---

# Tipos de contexto

## Contexto personal

Relacionado con la vida del usuario.

Ejemplos:

- Salud.
- Compras.
- Rutinas.
- Relaciones.

---

## Contexto profesional

Relacionado con trabajo y carrera.

Ejemplos:

- Proyectos.
- Formación.
- Objetivos laborales.

---

## Contexto empresarial

Relacionado con negocios.

Ejemplos:

- Clientes.
- Finanzas.
- Operaciones.

---

## Contexto de tarea

Información necesaria para realizar una acción concreta.

Ejemplo:

Para revisar código:

- Lenguaje.
- Arquitectura.
- Errores conocidos.
- Objetivo del proyecto.

---

# Construcción de contexto

El flujo será:

Solicitud

↓

Identificación de intención

↓

Selección de área

↓

Consulta de memoria

↓

Consulta de User Model

↓

Aplicación de reglas

↓

Creación de contexto

↓

Entrega al módulo correspondiente

---

# Contexto dinámico

El contexto no es fijo.

Cambia según:

- Momento del día.
- Prioridades actuales.
- Objetivos activos.
- Estado del usuario.
- Información reciente.

---

# Ejemplo

Usuario:

"¿Qué hago esta tarde?"

El Context Engine recopila:

Objetivos actuales:

- Estudiar APIs.
- Avanzar JARVIS.

Calendario:

- 3 horas libres.

Estado:

- Energía media.

Pendientes:

- Revisar documentación.

Preferencias:

- Aprende mejor haciendo.

Resultado:

Genera un contexto para que el Decision Engine pueda recomendar.

---

# Gestión del ruido

El Context Engine debe evitar:

- Cargar toda la memoria.
- Enviar información irrelevante.
- Saturar modelos de IA.
- Mezclar temas sin relación.

La cantidad de información no debe superar la capacidad de razonamiento.

---

# Relación con modelos de IA

Los modelos nunca reciben acceso directo a toda la memoria.

Siempre reciben:

Memoria seleccionada

↓

Contexto preparado

↓

Petición concreta

---

# Context Window Management

El Context Engine debe optimizar el uso de contexto.

Principios:

- Información relevante primero.
- Información crítica siempre presente.
- Información antigua solo cuando sea necesaria.
- Evitar duplicidades.

---

# Actualización de contexto

El contexto puede cambiar por:

- Nueva información.
- Nuevas decisiones.
- Cambio de prioridades.
- Cambio de estado del usuario.

---

# Eventos

## Escucha

Puede recibir:

- Nueva consulta.
- Nuevo objetivo.
- Nuevo proyecto.
- Cambio de estado.
- Evento externo.

---

## Genera

Puede emitir:

- Contexto preparado.
- Solicitud de información adicional.
- Aviso de falta de contexto.

---

# Calidad del contexto

Un contexto correcto debe ser:

- Relevante.
- Actual.
- Suficiente.
- No excesivo.
- Trazable.

---

# Fallos posibles

## Falta de información

Acción:

Solicitar más datos.

---

## Información contradictoria

Acción:

Consultar fuentes adicionales.

Si persiste:

Solicitar decisión al usuario.

---

## Exceso de información

Acción:

Priorizar y reducir.

---

# Seguridad

El Context Engine nunca debe:

- Inventar información.
- Ocultar información relevante.
- Cambiar datos originales.
- Romper las reglas de JARVIS.

---

# Objetivo final

Crear un sistema capaz de entregar a cada módulo exactamente la información necesaria en el momento adecuado.

El Context Engine convierte una gran base de conocimiento en inteligencia práctica.