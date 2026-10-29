"""
Orchestrator — versión mínima (Roadmap Fase 4)

Responsabilidad: recibir una tarea, pedirle a Policy Engine que la evalúe,
y si procede, delegarla al agente adecuado (Modules/Orchestrator.md).
No decide QUÉ hacer, ni valida reglas -- solo coordina.

Los agentes nunca se llaman entre sí: todo pasa por aquí.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "policy_engine"))
sys.path.append(str(Path(__file__).parent.parent / "agents"))
import policy_engine as pe     # noqa: E402
import capture_agent           # noqa: E402
import advisor_agent           # noqa: E402
import builder_agent           # noqa: E402
import process_narrator_agent  # noqa: E402
import generador_agent         # noqa: E402
import seguimiento_agent       # noqa: E402
import investigador_agent      # noqa: E402

REGISTRY = {
    "capturar": (capture_agent.run, capture_agent.AUTONOMY_LEVEL),
    "recomendar": (advisor_agent.run, advisor_agent.AUTONOMY_LEVEL),
    "programar": (builder_agent.run, builder_agent.AUTONOMY_LEVEL),
    "narrar": (process_narrator_agent.narrar, process_narrator_agent.AUTONOMY_LEVEL),
    "generar_articulo": (generador_agent.run, generador_agent.AUTONOMY_LEVEL),
    "revisar_negocio": (seguimiento_agent.run, seguimiento_agent.AUTONOMY_LEVEL),
    "investigar_temas": (investigador_agent.run, investigador_agent.AUTONOMY_LEVEL),
    "buscar_real": (investigador_agent.run_busqueda_real, investigador_agent.AUTONOMY_LEVEL),
}

# Capability Registry (Schemas/CapabilityRegistry.md) -- catálogo único de
# "a quién le puede tocar un mensaje" que usa el CEO Agent (agents/ceo_agent.py)
# para decidir sin conocer la implementación de ningún agente. Añadir un
# agente nuevo al sistema es, en lo que toca al enrutado natural, añadir una
# entrada aquí: el CEO lee este diccionario, no hace falta tocar ningún
# prompt a mano. La clave debe coincidir con la que espera bot.py para
# llamar al flujo correspondiente.
#
# Cada entrada declara: descripcion (para que el CEO decida), entradas,
# salidas, herramientas (informativo, para auditar) y autonomy_level
# (Schemas/Permissions.md -- determina si Policy Engine pide confirmación;
# hoy solo nivel 4 la pide, reservado a ejecutar/eliminar/desplegar).
AGENTES_CEO = {
    "nota": {
        "descripcion": "Guardar información, una idea o un dato que el usuario pide "
                        "explícitamente recordar o apuntar (ej. 'apunta que...', 'recuérdame "
                        "que...', 'tengo que comprar pilas'). NO es la categoría por defecto -- "
                        "si el mensaje es una charla, pregunta u opinión sin pedir guardar nada, "
                        "es 'conversar'.",
        "entradas": "texto libre",
        "salidas": "id del Conocimiento creado",
        "herramientas": ["knowledge_engine.classify", "memory_engine.create_knowledge"],
        "autonomy_level": 1,
    },
    "conversar": {
        "descripcion": "Charla libre, pregunta general u opinión que no pide ninguna acción "
                        "concreta del catálogo ni pide guardar algo explícitamente (ej. 'qué "
                        "opinas de...', 'cómo funciona X', cualquier pregunta abierta). Es la "
                        "categoría por defecto si el mensaje no encaja claramente en ninguna "
                        "otra -- responde con razonamiento libre usando el contexto de memoria, "
                        "nunca ejecuta ni guarda nada.",
        "entradas": "texto libre",
        "salidas": "respuesta en texto, sin efectos en memoria",
        "herramientas": ["conversador_agent.run"],
        "autonomy_level": 0,
    },
    "pregunta": {
        "descripcion": "Pedir una recomendación o consejo sobre qué hacer con el tiempo o la "
                        "energía del usuario ahora mismo.",
        "entradas": "pregunta, horas disponibles, energía",
        "salidas": "recomendación + alternativas + confianza",
        "herramientas": ["decision_engine.recommend_and_log"],
        "autonomy_level": 1,
    },
    "codigo": {
        "descripcion": "Pedir un script o utilidad puntual y concreta -- SOLO si el mensaje NO "
                        "usa la palabra 'agente' en ningún momento (ej. 'hazme un script que liste "
                        "mis tareas'). Si el mensaje menciona la palabra 'agente' pidiendo "
                        "crearlo/generarlo, NUNCA es esta categoría, es 'agente', sin importar el "
                        "verbo (genera, créame, hazme, quiero, necesito, monta...).",
        "entradas": "descripción de la tarea",
        "salidas": "archivo .py guardado en 04_Implementation/scripts/",
        "herramientas": ["builder_agent.propose", "builder_agent.write", "builder_agent.execute"],
        "autonomy_level": 2,
    },
    "agente": {
        "descripcion": "Pedir crear un agente nuevo y permanente para JARVIS. Regla simple y sin "
                        "excepciones: si la palabra 'agente' aparece en el mensaje junto a un verbo "
                        "de crear/generar/hacer (genera un agente que..., créame un agente que..., "
                        "hazme un agente que..., quiero un agente que..., necesito un agente que..., "
                        "monta un agente que...), es SIEMPRE esta categoría -- nunca 'codigo' (eso "
                        "sería tratar un agente como si fuera un script suelto, y no lo es: un "
                        "agente sigue un contrato distinto, con AUTONOMY_LEVEL y función run()) y "
                        "nunca 'estrategico' (aunque el tema del agente sea el propio JARVIS o su "
                        "funcionamiento, el usuario pide construir algo, no opinar sobre el rumbo).",
        "entradas": "descripción de la tarea del agente",
        "salidas": "archivo .py del agente, integrado en REGISTRY y AGENTES_CEO",
        "herramientas": ["builder_agent.propose_agent", "builder_agent.write", "orchestrator_integrator"],
        "autonomy_level": 2,
    },
    "ideas": {
        "descripcion": "Pedir ideas de qué agentes crear sobre un tema, sin tener todavía una "
                        "idea concreta (ej. 'dame ideas de agentes para mi carrera').",
        "entradas": "tema",
        "salidas": "lista de ideas (nombre, misión, justificación)",
        "herramientas": ["creative_agent.brainstorm", "creative_agent.elaborar_brief"],
        "autonomy_level": 1,
    },
    "estrategico": {
        "descripcion": "El usuario pregunta DIRECTAMENTE sobre el rumbo, la arquitectura o el "
                        "roadmap de JARVIS, SIN pedir construir nada concreto (ej. 'qué debería "
                        "mejorar de mi arquitectura', 'cuál es el siguiente paso del proyecto'). "
                        "Si el mensaje pide crear/generar un agente o script, NUNCA es esta "
                        "categoría aunque el tema tratado sea el propio JARVIS -- eso es 'agente' "
                        "o 'codigo'.",
        "entradas": "pregunta",
        "salidas": "decisión pendiente marcada para Claude",
        "herramientas": ["memory_engine.flag_for_claude"],
        "autonomy_level": 1,
    },
    "estado": {
        "descripcion": "Preguntar qué tiene pendiente el usuario, cómo va todo, o pedir un resumen.",
        "entradas": "ninguna",
        "salidas": "lista de decisiones pendientes",
        "herramientas": ["memory_engine.pending_decisions", "memory_engine.pending_for_claude"],
        "autonomy_level": 0,
    },
    "supervisar": {
        "descripcion": "Preguntar si algo ha fallado, si todo funciona bien, o pedir una "
                        "revisión del sistema -- cubre JARVIS mismo Y las líneas de negocio "
                        "(ej. artículos con datos inventados, ideas sin fuente real).",
        "entradas": "ninguna",
        "salidas": "hallazgos por categoría",
        "herramientas": ["supervisor_agent.run"],
        "autonomy_level": 1,
    },
    "relato": {
        "descripcion": "Preguntar qué ha pasado o qué proceso se ha seguido para completar (o "
                        "intentar) una tarea concreta ya realizada -- se apoya en el registro de "
                        "eventos real, nunca inventa pasos (ej. 'cuéntame qué pasos seguiste para "
                        "crear el agente X').",
        "entradas": "consulta",
        "salidas": "relato basado en eventos reales",
        "herramientas": ["process_narrator_agent.narrar"],
        "autonomy_level": 1,
    },
    "ayuda": {
        "descripcion": "Preguntar qué puede hacer JARVIS o cómo funciona este chat.",
        "entradas": "ninguna",
        "salidas": "texto de ayuda",
        "herramientas": [],
        "autonomy_level": 0,
    },
    "articulo": {
        "descripcion": "Pedir un artículo de afiliados sobre un tema del nicho de "
                        "home office para la línea de negocio de contenido (ej. 'escribe un "
                        "artículo sobre sillas ergonómicas', 'genera un artículo de afiliados "
                        "sobre monitores para trabajar desde casa').",
        "entradas": "tema del artículo",
        "salidas": "artículo en Markdown guardado como Conocimiento + Tarea de negocio en fase 'borrador_listo'",
        "herramientas": ["generador_agent.propose", "generador_agent.save"],
        "autonomy_level": 1,
    },
    "negocio": {
        "descripcion": "Preguntar cómo va el tablero de una línea de negocio, qué tareas "
                        "están paradas, o pedir un resumen de contenido/negocio (ej. 'cómo va "
                        "el tablero de contenido', 'qué artículos están pendientes de revisar', "
                        "'hay algo estancado en el negocio'). Distinto de 'estado' y 'supervisar', "
                        "que hablan de JARVIS mismo, no de líneas de negocio externas.",
        "entradas": "línea de negocio opcional (ej. 'contenido_afiliados')",
        "salidas": "resumen por fase + tareas estancadas",
        "herramientas": ["seguimiento_agent.run"],
        "autonomy_level": 1,
    },
    "investigar": {
        "descripcion": "Pedir ideas de TEMAS nuevos de artículo para el blog de home office, "
                        "sin tener un tema concreto todavía (ej. 'dame ideas de temas para el "
                        "blog', 'qué podría escribir después', 'investígame temas nuevos'). "
                        "Distinto de 'ideas' (eso es para agentes nuevos de JARVIS, no temas de "
                        "contenido) y de 'articulo' (eso es para escribir un tema YA elegido).",
        "entradas": "ninguna, o número de temas deseado",
        "salidas": "lista de temas propuestos (tema, ángulo, justificación) -- sin verificar "
                    "contra datos de mercado reales, Ollama no tiene acceso a internet",
        "herramientas": ["investigador_agent.investigar", "investigador_agent.crear_tarea_idea"],
        "autonomy_level": 1,
    },
    "buscar": {
        "descripcion": "Pedir una investigación con búsqueda REAL en internet (Brave Search) "
                        "sobre un tema concreto, para fundamentar contenido con datos reales en "
                        "vez de lo que el modelo local se imagina (ej. 'busca en internet sobre "
                        "monitores para home office', 'investiga de verdad qué se vende de sillas "
                        "ergonómicas'). Requiere una clave de Brave Search API configurada -- si "
                        "no lo está, avisa de cómo configurarla en vez de inventar resultados. "
                        "Distinto de 'investigar', que solo hace brainstorm sin verificar.",
        "entradas": "tema o consulta concreta a buscar",
        "salidas": "lista de temas anclados a resultados reales (con URL de origen)",
        "herramientas": ["investigador_agent.buscar_web", "investigador_agent.investigar_con_busqueda_real"],
        "autonomy_level": 1,
    },
}


def dispatch(action: str, **payload):
    """
    Punto único de entrada. action debe ser una clave de REGISTRY.
    Devuelve (estado, resultado_o_None):
        estado en {'permitido_ejecutado', 'requiere_aprobación', 'bloqueado', 'accion_desconocida'}
    """
    if action not in REGISTRY:
        return "accion_desconocida", None

    agent_fn, autonomy_level = REGISTRY[action]
    evaluacion = pe.evaluate(agent_name=agent_fn.__module__, action=action, autonomy_level=autonomy_level)

    if evaluacion == "bloqueado":
        return "bloqueado", None

    if evaluacion == "requiere_aprobación":
        respuesta = input(f"[Orchestrator] La acción '{action}' requiere tu aprobación. ¿Continuar? (s/n): ")
        if respuesta.strip().lower() != "s":
            return "requiere_aprobación", None

    resultado = agent_fn(**payload)
    return "permitido_ejecutado", resultado
