"""
Decision Engine — versión mínima (Roadmap Fase 3)

Responsabilidad: convertir contexto en una recomendación accionable
(Modules/DecisionEngine.md). Usa el modelo local Nivel 2 (llama3.1:8b)
por defecto.

Escalada a Claude (Nivel 3): en esta fase NO se llama a la API de Claude
automáticamente -- no hay credenciales configuradas todavía y, según
ModelRouter.md, escalar "solo si existe una razón" declarada explícitamente.
Si el modelo local devuelve confianza baja, este módulo lo marca en vez de
inventar una respuesta mejor, y te avisa para que decidas si merece la pena
preguntarle a Claude directamente (Constitution Art. 9).
"""

import json
import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
sys.path.append(str(Path(__file__).parent.parent / "model_router"))
import memory_engine as me  # noqa: E402
import model_router  # noqa: E402

MODEL_NIVEL_2 = model_router.modelo(2)

PROMPT_DECISION = """Eres el Decision Engine de JARVIS, un sistema operativo cognitivo personal.
No sustituyes la decisión del usuario. Ayudas a decidir la acción de mayor valor ahora mismo.

Pregunta del usuario: {question}

Contexto disponible:
- Tiempo disponible: {available_time_hours} horas
- Energía actual: {energy}
- Objetivos activos: {goals}
- Conocimiento reciente relevante: {knowledge}

Analiza importancia, urgencia, alineación con objetivos, esfuerzo requerido y momento adecuado
(Modules/DecisionEngine.md). Si el contexto es insuficiente para una recomendación sólida,
dilo con confidence "baja" en vez de inventar.

Responde EXCLUSIVAMENTE con un JSON válido, sin texto adicional:

{{
  "recommended_action": "qué hacer, en una frase concreta",
  "reason": "por qué, en una o dos frases",
  "alternatives": ["otra opción posible", "otra opción posible"],
  "confidence": "alta" o "media" o "baja"
}}
"""


def recommend(context: dict) -> dict:
    """Genera una recomendación a partir del contexto del Context Engine."""
    prompt = PROMPT_DECISION.format(
        question=context["question"],
        available_time_hours=context["available_time_hours"],
        energy=context["energy"],
        goals=context["active_goals"] or "ninguno registrado todavía",
        knowledge=context["recent_knowledge"] or "ninguno registrado todavía",
    )

    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{"role": "user", "content": prompt}],
        format="json",
    )
    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
        confidence = data.get("confidence", "media")
        if confidence not in ("alta", "media", "baja"):
            confidence = "media"
        return {
            "recommended_action": data.get("recommended_action", "").strip(),
            "reason": data.get("reason", "").strip(),
            "alternatives": data.get("alternatives", []),
            "confidence": confidence,
        }
    except (json.JSONDecodeError, AttributeError):
        return {
            "recommended_action": "",
            "reason": "El modelo local no devolvió una respuesta interpretable.",
            "alternatives": [],
            "confidence": "baja",
        }


def recommend_and_log(context: dict) -> tuple[dict, str]:
    """Genera la recomendación Y la registra como Decisión pendiente en memoria."""
    result = recommend(context)
    decision_context = json.dumps(
        {k: v for k, v in context.items() if k != "question"}, ensure_ascii=False
    )
    decision_id = me.create_decision(
        context=decision_context,
        reason=result["reason"] or "(sin motivo devuelto por el modelo)",
        alternatives=result["alternatives"],
        source="decision_engine",
    )
    return result, decision_id
