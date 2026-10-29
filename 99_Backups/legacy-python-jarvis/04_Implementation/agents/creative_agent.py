"""
Creative Agent v1.0 (AgentFramework.md -- contrato de agente)

Misión: ayudar a pensar qué agentes construir (brainstorming) y convertir
una idea elegida en un encargo detallado y claro para el Builder Agent --
mucho mejor que la frase suelta que se escribe de pasada en el móvil.

Responsabilidades: generar ideas de agentes acotadas a lo que un modelo
local puede ejecutar bien; elaborar una idea en un encargo completo
(entradas, proceso, salidas, límites) listo para Builder Agent.

Límites: nunca genera código él mismo (eso es Builder Agent). Nunca decide
qué agente construir -- solo propone opciones, el usuario elige.

Nivel de autonomía: 1 (Asistido) -- solo genera texto, nunca actúa.
"""

import json
import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).parent.parent / "model_router"))
import model_router  # noqa: E402

MODEL_NIVEL_2 = model_router.modelo(2)  # la creatividad se beneficia del modelo más grande
AUTONOMY_LEVEL = 1

PROMPT_BRAINSTORM = """Eres el Creative Agent de JARVIS, un sistema personal que ya
tiene construido: Memory Engine, Capture Agent, Advisor Agent, Builder Agent,
Supervisor Agent, CEO Agent (enrutado), Process Narrator Agent, y una
interfaz de Telegram.

El usuario quiere ideas de agentes nuevos sobre este tema: {tema}

Genera {n} ideas de agentes concretos y útiles, no genéricos. Cada uno debe:
- Tener un nombre corto y claro.
- Resolver un problema real dentro de ese tema.
- Ser algo que un modelo local de 3-8B pueda ejecutar razonablemente bien
  (tareas acotadas: clasificar, resumir, redactar borradores, calcular,
  consultar información guardada) -- evita ideas que requieran juicio
  estratégico complejo, eso ya tiene su propio camino hacia Claude.

Responde EXCLUSIVAMENTE con un JSON válido, sin texto adicional:

{{
  "ideas": [
    {{"nombre": "nombre corto", "mision": "una frase", "justificacion": "por qué aporta valor"}}
  ]
}}
"""

PROMPT_BRIEF = """Eres el Creative Agent de JARVIS. Vas a convertir una idea de
agente en un encargo claro y completo para el Builder Agent, que va a
generar el código a partir de lo que escribas aquí.

Idea: {nombre} -- {mision}

Escribe un encargo detallado que incluya:
- Qué debe hacer exactamente el agente (entrada, proceso, salida).
- Qué NUNCA debe hacer (límites de seguridad y de alcance).
- Qué funciones de memory_engine debería usar si necesita guardar o leer información.

Responde SOLO con el texto del encargo, sin JSON, sin explicaciones extra,
listo para pasárselo directamente al Builder Agent.
"""


def brainstorm(tema: str, n_ideas: int = 4) -> list[dict]:
    """
    Genera ideas de agentes sobre un tema. Devuelve lista de dicts con
    'nombre', 'mision', 'justificacion'. Lista vacía si el modelo falla --
    nunca se inventan ideas de relleno ante una respuesta rara.
    """
    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{"role": "user", "content": PROMPT_BRAINSTORM.format(tema=tema, n=n_ideas)}],
        format="json",
    )
    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
        ideas = data.get("ideas", [])
        return [
            {
                "nombre": str(i.get("nombre", "")).strip(),
                "mision": str(i.get("mision", "")).strip(),
                "justificacion": str(i.get("justificacion", "")).strip(),
            }
            for i in ideas
            if i.get("nombre") and i.get("mision")
        ]
    except (json.JSONDecodeError, AttributeError):
        return []


def elaborar_brief(nombre: str, mision: str) -> str:
    """
    Convierte una idea elegida en un encargo detallado para Builder Agent.
    Si el modelo falla, cae en un encargo mínimo pero honesto en vez de
    inventar contenido -- mejor un brief simple que uno con datos falsos.
    """
    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{"role": "user", "content": PROMPT_BRIEF.format(nombre=nombre, mision=mision)}],
    )
    brief = response["message"]["content"].strip()
    return brief or f"Crear un agente llamado {nombre} cuya misión es: {mision}"
