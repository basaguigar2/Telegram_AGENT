"""
Capture Agent v1.0 (AgentFramework.md — contrato de agente)

Misión: capturar una nota y guardarla como Conocimiento clasificado.
Responsabilidades: clasificar (Knowledge Engine) y persistir (Memory Engine).
Límites: nunca decide prioridades ni ejecuta automatizaciones.
Nivel de autonomía: 1 (Asistido, auto-permitido) -- guardar una nota no es
una acción destructiva ni estratégica (Constitution.md Art. 10 protege
decisiones/ejecuciones, no capturar información): el Conocimiento se
versiona y nunca se sobrescribe ni se borra, solo se archiva, así que
pedir confirmación en cada nota no aporta seguridad real, solo fricción.
Si el usuario quiere revisar lo guardado, puede pedir el historial
(get_history) o el conocimiento reciente en cualquier momento.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "knowledge_engine"))
sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
import knowledge_engine as ke  # noqa: E402
import memory_engine as me     # noqa: E402

AUTONOMY_LEVEL = 1


def propose(texto: str) -> dict:
    """Clasifica sin guardar -- para poder mostrar la propuesta antes de confirmar."""
    return ke.classify(texto)


def save(texto: str, clasificacion: dict) -> str:
    """Guarda una clasificación ya aceptada. Devuelve el id creado."""
    return me.create_knowledge(
        content=texto,
        topic=clasificacion["topic"],
        reliability=clasificacion["reliability"],
        source="capture_agent",
    )


def run(texto: str) -> dict:
    """Uso desde CLI: la confirmación ya la hizo el Orchestrator antes de llamar aquí."""
    clasificacion = propose(texto)
    kid = save(texto, clasificacion)
    return {"knowledge_id": kid, **clasificacion}
