"""
Intent Router -- utilidades de nombrado seguro para código y agentes nuevos.

Históricamente este módulo era el punto de entrada que clasificaba cada
mensaje (classify()). Desde que existe agents/ceo_agent.py, esa decisión
("a quién le toca este mensaje") la toma el CEO Agent leyendo el catálogo
vivo de orchestrator.AGENTES_CEO -- añadir un agente nuevo ya no requiere
tocar el prompt de este archivo. classify() se deja aquí sin usar por el
bot (documentado, no borrado) por si algún día hace falta clasificación
fina dentro de un agente concreto; lo que sigue en uso activo es _slug()
y las carpetas seguras, para que "codigo" y "agente" nunca escriban fuera
de una ubicación controlada.

Antes de esto, el bot exigía sintaxis fija ("/pregunta horas|energia|texto",
"/codigo tarea|ruta"). Eso no es realista para hablar desde el móvil.
Este módulo usa el modelo local Nivel 1 (rápido, barato -- ModelRouter.md)
para decidir qué quiere el usuario y extraer los parámetros, sin que tenga
que escribir ninguna sintaxis especial ni pensar en rutas de archivo.

Salvaguarda de seguridad importante: para las intenciones "codigo" y
"agente", este módulo NUNCA deja que el modelo elija un archivo existente
del sistema (memory_engine.py, orchestrator.py, etc.) -- solo genera un
nombre de archivo nuevo dentro de una carpeta segura. Si el usuario quiere
editar un archivo real y ya existente del sistema, tiene que nombrarlo
explícitamente con el comando /codigo de toda la vida (bot.py lo sigue
aceptando) -- eso es intencional, no un descuido.

Intención "estrategico": preguntas sobre el rumbo, la arquitectura o las
decisiones de diseño de JARVIS NUNCA las responde el modelo local -- eso es
trabajo de Nivel 3 (ModelRouter.md), reservado para Claude. Este módulo solo
detecta que la pregunta es de ese tipo; no intenta responderla.
"""

import json
import re
import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).resolve().parent.parent / "model_router"))
import model_router  # noqa: E402

MODEL_NIVEL_1 = model_router.modelo(1)

# Rutas ABSOLUTAS, ancladas a la ubicación real de este archivo -- no
# relativas al directorio de trabajo del proceso. Antes eran texto relativo
# ("04_Implementation/agents"), que solo resolvía bien si el proceso se
# lanzaba con el cwd en la raíz de JARVIS. run_bot.bat hace "cd /d %~dp0"
# (cwd = carpeta telegram_bot), así que en producción esto escribía los
# agentes/scripts nuevos en telegram_bot/04_Implementation/... -- una
# carpeta fantasma fuera de sys.path, invisible para orchestrator.py e
# imposible de integrar. Bug real, no solo cosmético.
CARPETA_SEGURA_CODIGO = str(Path(__file__).resolve().parent.parent / "scripts")
CARPETA_SEGURA_AGENTE = str(Path(__file__).resolve().parent.parent / "agents")

PROMPT_INTENT = """Eres el enrutador de intención de JARVIS, un sistema personal.
Analiza el mensaje del usuario y decide qué quiere hacer.

Mensaje: {mensaje}

Las intenciones posibles son:
- "nota": el usuario quiere guardar información, una idea, un dato, algo que recordar.
- "pregunta": el usuario pide una recomendación o consejo sobre qué hacer con SU tiempo o vida.
- "codigo": el usuario pide un script o utilidad concreta y puntual (ej. "hazme un script que...").
- "agente": el usuario pide crear un agente/módulo nuevo y permanente para JARVIS
  (ej. "créame un agente que se encargue de...", "quiero un módulo que decida...").
- "estrategico": el usuario pregunta sobre el rumbo, la arquitectura, el roadmap o las
  decisiones de diseño del propio JARVIS (ej. "qué hago con JARVIS ahora", "cuál es el
  siguiente paso del proyecto", "cómo debería mejorar la arquitectura").
- "estado": el usuario pregunta qué tiene pendiente, cómo va todo, o quiere un resumen
  (ej. "qué tengo pendiente", "cómo va todo", "resumen de estado", "qué le toca a Claude").
- "supervisar": el usuario pregunta si algo ha fallado, si todo funciona bien, o pide
  una revisión del sistema (ej. "revisa que todo esté bien", "ha fallado algo",
  "cómo van las últimas acciones").
- "ideas": el usuario pide ideas de agentes nuevos sobre un tema, sin tener una idea
  concreta todavía (ej. "dame ideas de agentes para mi carrera", "qué agentes podría
  crear para X", "ayúdame a pensar qué construir").
- "ayuda": el usuario pregunta qué puede hacer JARVIS o cómo funciona este chat.

Responde EXCLUSIVAMENTE con un JSON válido, sin texto adicional, con esta forma:

{{
  "intent": "nota" o "pregunta" o "codigo" o "agente" o "estrategico" o "estado" o "supervisar" o "ideas" o "ayuda",
  "nota_texto": "el texto completo a guardar, solo si intent es nota, si no null",
  "pregunta_texto": "la pregunta reformulada con claridad, solo si intent es pregunta, si no null",
  "horas_mencionadas": numero de horas si el usuario las menciona, si no null,
  "energia_mencionada": "alta" o "media" o "baja" si el usuario la menciona, si no null,
  "codigo_tarea": "descripción clara de qué debe hacer el script, solo si intent es codigo, si no null",
  "codigo_nombre_sugerido": "nombre_corto_en_snake_case sin extensión, solo si intent es codigo, si no null",
  "agente_tarea": "descripción clara de qué debe hacer el agente, solo si intent es agente, si no null",
  "agente_nombre_sugerido": "nombre_corto_en_snake_case, solo si intent es agente, si no null",
  "ideas_tema": "el tema sobre el que quiere ideas, solo si intent es ideas, si no null"
}}
"""


def _slug(texto: str) -> str:
    """Convierte un texto libre en un nombre de archivo seguro."""
    texto = texto.lower().strip()
    texto = re.sub(r"[^a-z0-9_]+", "_", texto)
    texto = re.sub(r"_+", "_", texto).strip("_")
    return (texto or "script")[:40]


def classify(mensaje: str) -> dict:
    """
    Devuelve un dict con al menos la clave 'intent'.
    Si el modelo no da un JSON interpretable, cae en 'nota' con el mensaje
    tal cual -- es el fallback más seguro (nunca inventa una ejecución de
    código, ni una respuesta estratégica, por una respuesta rara del modelo).
    """
    response = ollama.chat(
        model=MODEL_NIVEL_1,
        messages=[{"role": "user", "content": PROMPT_INTENT.format(mensaje=mensaje)}],
        format="json",
    )
    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
        intent = data.get("intent")
        if intent not in ("nota", "pregunta", "codigo", "agente", "estrategico", "estado",
                           "supervisar", "ideas", "ayuda"):
            raise ValueError("intent no reconocido")

        resultado = {"intent": intent}

        if intent == "nota":
            resultado["texto"] = (data.get("nota_texto") or mensaje).strip()

        elif intent == "pregunta":
            resultado["pregunta"] = (data.get("pregunta_texto") or mensaje).strip()
            resultado["horas"] = data.get("horas_mencionadas") or 3
            energia = data.get("energia_mencionada")
            resultado["energia"] = energia if energia in ("alta", "media", "baja") else "media"

        elif intent == "codigo":
            tarea = data.get("codigo_tarea") or mensaje
            nombre = _slug(data.get("codigo_nombre_sugerido") or tarea)
            resultado["tarea"] = tarea.strip()
            resultado["target_file"] = f"{CARPETA_SEGURA_CODIGO}/{nombre}.py"

        elif intent == "agente":
            tarea = data.get("agente_tarea") or mensaje
            nombre = _slug(data.get("agente_nombre_sugerido") or tarea)
            if not nombre.endswith("_agent"):
                nombre = f"{nombre}_agent"
            resultado["tarea"] = tarea.strip()
            resultado["nombre_agente"] = nombre
            resultado["target_file"] = f"{CARPETA_SEGURA_AGENTE}/{nombre}.py"

        elif intent == "estrategico":
            resultado["pregunta_original"] = mensaje

        elif intent == "ideas":
            resultado["ideas_tema"] = (data.get("ideas_tema") or mensaje).strip()

        return resultado

    except (json.JSONDecodeError, ValueError, AttributeError):
        # Fallback seguro: si no se entiende, se trata como nota. Nunca se
        # asume "codigo", "agente" ni "estrategico" por defecto.
        return {"intent": "nota", "texto": mensaje}
