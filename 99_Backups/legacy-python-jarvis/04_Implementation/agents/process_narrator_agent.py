"""
Process Narrator Agent v1.0 (AgentFramework.md -- contrato de agente)

Misión: reconstruir y contar, en lenguaje claro, qué pasos ha seguido
JARVIS para completar (o intentar) una tarea concreta -- leyendo el
propio rastro de auditoría (tabla event, Schemas/Events.md) en vez de
inventar un relato plausible.

Responsabilidades: buscar en memory_engine.recent_events() los eventos
que coincidan con la consulta del usuario, ordenarlos cronológicamente,
y redactar un relato fiel a lo realmente ocurrido.

Límites: nunca actúa ni modifica nada -- solo lee y redacta. Si no
encuentra eventos relacionados, lo dice tal cual en vez de rellenar
huecos con una historia inventada (mismo principio que MemoryEngine.md
-- nunca decidir/afirmar sin evidencia suficiente).

Nivel de autonomía: 1 (Asistido) -- solo informa, nunca actúa.
"""

import json
import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
sys.path.append(str(Path(__file__).parent.parent / "model_router"))
import memory_engine as me  # noqa: E402
import model_router  # noqa: E402

MODEL_NIVEL_2 = model_router.modelo(2)  # redactar un relato coherente se beneficia del modelo más grande
AUTONOMY_LEVEL = 1
VENTANA_HORAS_DEFECTO = 24 * 7  # una semana -- una tarea puede abarcar varios días

PROMPT_NARRACION = """Eres el Process Narrator de JARVIS. Vas a contarle al usuario, en
lenguaje claro y en orden cronológico, qué ha pasado con una tarea suya --
basándote EXCLUSIVAMENTE en esta lista de eventos reales registrados por
el sistema. No inventes ningún paso que no esté en la lista. Si la lista
es corta o parece incompleta, dilo tal cual en vez de rellenar huecos.

Consulta del usuario: {consulta}

Eventos encontrados (orden cronológico, el primero es el más antiguo):
{eventos}

Escribe un relato breve y claro de qué ha pasado, en 3-6 frases.
"""


def _coincide(evento: dict, consulta: str) -> bool:
    """Coincidencia simple por palabra clave -- determinista, sin modelo."""
    contexto = evento.get("context") or ""
    campos = " ".join([
        evento.get("event_type") or "",
        evento.get("origin_module") or "",
        contexto,
        evento.get("outcome") or "",
    ]).lower()
    palabras = [p for p in consulta.lower().split() if len(p) > 3]
    return any(p in campos for p in palabras) if palabras else False


def buscar_eventos(consulta: str, since_hours: int = VENTANA_HORAS_DEFECTO) -> list[dict]:
    """
    Devuelve los eventos de memory_engine.recent_events() cuyo contenido
    coincide con alguna palabra significativa de la consulta, ordenados
    del más antiguo al más reciente (para poder contarlos como secuencia).
    """
    eventos = me.recent_events(since_hours=since_hours)
    coincidentes = [e for e in eventos if _coincide(e, consulta)]
    return sorted(coincidentes, key=lambda e: e["occurred_at"])


def _formatear_eventos(eventos: list[dict]) -> str:
    lineas = []
    for e in eventos:
        try:
            ctx = json.loads(e["context"])
        except (TypeError, ValueError):
            ctx = e.get("context")
        lineas.append(f"- [{e['occurred_at']}] {e['event_type']} (origen: {e['origin_module']}): "
                       f"contexto={ctx}, resultado={e.get('outcome') or '(sin resultado registrado)'}")
    return "\n".join(lineas)


def narrar(consulta: str, since_hours: int = VENTANA_HORAS_DEFECTO) -> dict:
    """
    Devuelve {'encontrado': bool, 'relato': str, 'n_eventos': int}.
    Si no hay eventos relacionados, no se llama al modelo -- se dice
    directamente que no hay rastro, nunca se inventa un relato.
    """
    eventos = buscar_eventos(consulta, since_hours)
    if not eventos:
        return {
            "encontrado": False,
            "relato": (f"No he encontrado eventos relacionados con \"{consulta}\" "
                       f"en los últimos {since_hours} horas de registro. O no ha pasado "
                       f"todavía, o pasó antes de esa ventana, o no coincide con las "
                       f"palabras clave del registro."),
            "n_eventos": 0,
        }

    eventos_texto = _formatear_eventos(eventos)
    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{"role": "user", "content": PROMPT_NARRACION.format(
            consulta=consulta, eventos=eventos_texto)}],
    )
    relato = response["message"]["content"].strip()
    if not relato:
        relato = f"Encontré {len(eventos)} eventos relacionados, pero no pude redactar el relato:\n\n{eventos_texto}"

    return {"encontrado": True, "relato": relato, "n_eventos": len(eventos)}
