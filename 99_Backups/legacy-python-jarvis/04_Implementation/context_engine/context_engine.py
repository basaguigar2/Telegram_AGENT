"""
Context Engine — versión mínima (Roadmap Fase 3)

Responsabilidad: construir el contexto necesario para que el Decision Engine
pueda recomendar algo con sentido, sin cargar toda la memoria
(Modules/ContextEngine.md — "gestión del ruido").

En esta fase el "estado del usuario" es básico y se pide directamente
(no existe todavía un User Model Engine completo con aprendizaje continuo
— eso no está en el alcance del Roadmap hasta más adelante).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
import memory_engine as me  # noqa: E402


def build_context(available_time_hours: float, energy: str, question: str) -> dict:
    """
    Reúne: objetivos activos, conocimiento reciente, estado básico y la
    pregunta del usuario. Devuelve un dict listo para pasar al Decision Engine.
    """
    if energy not in ("alta", "media", "baja"):
        raise ValueError("energy debe ser 'alta', 'media' o 'baja'")

    goals = me.active_goals()
    knowledge = me.recent_knowledge(limit=8)

    return {
        "question": question,
        "available_time_hours": available_time_hours,
        "energy": energy,
        "active_goals": [{"name": g["name"], "priority": g["priority"]} for g in goals],
        "recent_knowledge": [{"topic": k["topic"], "content": k["content"]} for k in knowledge],
    }
