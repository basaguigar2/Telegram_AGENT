"""
Knowledge Engine — versión mínima (Roadmap Fase 2)

Responsabilidad en esta fase: convertir un texto sin procesar en los campos
que el Memory Engine necesita para guardarlo como Conocimiento
(Modules/KnowledgeEngine.md — "transformar información sin procesar en
conocimiento estructurado").

Usa el modelo local Nivel 1 (llama3.2:3b, ver TechStack.md) para clasificar.
No usa Claude: esta es exactamente la tarea de baja complejidad y alto
volumen que ModelRouter.md reserva para modelo local.
"""

import json
import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).parent.parent / "model_router"))
import model_router  # noqa: E402

MODEL_NIVEL_1 = model_router.modelo(1)

PROMPT_CLASIFICACION = """Eres el Knowledge Engine de un sistema personal llamado JARVIS.
Tu única tarea es clasificar una nota que el usuario acaba de capturar.

Nota del usuario:
---
{texto}
---

Responde EXCLUSIVAMENTE con un JSON válido, sin explicaciones ni texto adicional,
con esta forma exacta:

{{
  "topic": "tema corto en 2-5 palabras, en español",
  "reliability": "alta" o "media" o "baja",
  "summary": "resumen de una frase de la nota, en español"
}}

Criterio para reliability: "alta" si es un hecho verificable o una decisión ya tomada,
"media" si es una opinión, idea o intención razonable, "baja" si es especulativo o
incompleto.
"""


def classify(texto: str) -> dict:
    """
    Llama al modelo local para clasificar una nota.
    Devuelve dict con: topic, reliability, summary.
    Si el modelo falla en devolver JSON válido, aplica un fallback conservador
    en vez de inventar (principio de MemoryEngine.md: nunca decidir sin evidencia).
    """
    response = ollama.chat(
        model=MODEL_NIVEL_1,
        messages=[{"role": "user", "content": PROMPT_CLASIFICACION.format(texto=texto)}],
        format="json",
    )
    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
        topic = str(data.get("topic", "")).strip() or "sin clasificar"
        reliability = data.get("reliability", "media")
        if reliability not in ("alta", "media", "baja"):
            reliability = "media"
        summary = str(data.get("summary", "")).strip() or texto[:100]
        return {"topic": topic, "reliability": reliability, "summary": summary}
    except (json.JSONDecodeError, AttributeError):
        # Fallback: no inventamos, marcamos baja confianza y seguimos
        return {"topic": "sin clasificar", "reliability": "baja", "summary": texto[:100]}
