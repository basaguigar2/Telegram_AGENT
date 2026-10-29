"""
Advisor Agent v1.0 (AgentFramework.md — contrato de agente)

Misión: generar una recomendación a partir del contexto actual.
Responsabilidades: construir contexto (Context Engine) y proponer (Decision Engine).
Límites: nunca ejecuta la recomendación, nunca decide sin exponer alternativas.
Nivel de autonomía: 1 (Asistido) -- solo prepara información, el usuario decide
(AgentFramework.md, Nivel 1).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "context_engine"))
sys.path.append(str(Path(__file__).parent.parent / "decision_engine"))
import context_engine as ce   # noqa: E402
import decision_engine as de  # noqa: E402

AUTONOMY_LEVEL = 1


def run(question: str, available_time_hours: float, energy: str) -> dict:
    contexto = ce.build_context(available_time_hours, energy, question)
    resultado, decision_id = de.recommend_and_log(contexto)
    return {"decision_id": decision_id, **resultado}
