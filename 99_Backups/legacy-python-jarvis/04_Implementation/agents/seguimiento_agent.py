"""
Seguimiento Agent v1.0 (AgentFramework.md -- contrato de agente)

Misión: revisar el tablero de tareas de negocio (tabla `task`, campo
`business_line` -- ver RelacionConAGENTE.md) y avisar de tarjetas que llevan
varios días sin moverse de fase, igual que describe AGENTE ("Agente
Seguimiento", Fase 3.1 de la hoja de ruta original).

Responsabilidades: leer `task` filtrando por línea de negocio, agrupar por
`business_phase`, y detectar tareas cuyo `updated_at` lleva más de N días sin
cambiar.

Límites: NUNCA mueve ni cierra una tarea por su cuenta -- solo informa. NUNCA
usa un modelo de IA para decidir qué está estancado: es una regla determinista
sobre fechas reales (mismo principio que Supervisor Agent, que ya evita
juzgar con un modelo lo que puede resolverse con datos).

Nivel de autonomía: 1 (Asistido) -- solo informa, nunca actúa.
"""

import sys
import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
import memory_engine as me  # noqa: E402

AUTONOMY_LEVEL = 1
DIAS_ESTANCADO_DEFECTO = 3


def _dias_sin_mover(tarea: dict) -> int:
    actualizada = datetime.datetime.fromisoformat(tarea["updated_at"])
    return (datetime.datetime.now() - actualizada).days


def run(business_line: str | None = None, dias_estancado: int = DIAS_ESTANCADO_DEFECTO) -> dict:
    """
    Revisa las tareas de `business_line` (todas las líneas si es None, salvo
    las que no tienen ninguna asignada -- ver nota abajo) y devuelve:
        {'total_activas': int, 'por_fase': {fase: [tareas]}, 'estancadas': [tareas]}
    Una tarea se considera estancada si lleva >= dias_estancado días sin
    actualizarse y no está en un estado terminal (completada/fallida/archivada).
    """
    tareas = me.list_tasks(business_line=business_line)
    # list_tasks(business_line=None) no filtra por línea -- para Seguimiento de
    # negocio interesa solo lo que sí pertenece a alguna línea, nunca las
    # tareas internas de JARVIS (business_line NULL), que no son su ámbito.
    tareas = [t for t in tareas if t.get("business_line")]

    por_fase: dict[str, list[dict]] = {}
    for t in tareas:
        fase = t.get("business_phase") or "(sin fase)"
        por_fase.setdefault(fase, []).append(t)

    estancadas = [
        t for t in tareas
        if t["status"] not in ("completada", "fallida", "archivada")
        and _dias_sin_mover(t) >= dias_estancado
    ]

    me.create_event(
        event_type="seguimiento.review",
        origin_module="seguimiento_agent",
        context={"business_line": business_line, "total_activas": len(tareas),
                  "estancadas": len(estancadas)},
    )

    return {"total_activas": len(tareas), "por_fase": por_fase, "estancadas": estancadas}


def formatear(resultado: dict) -> str:
    """Convierte el resultado de run() en texto legible, sin modelo de IA."""
    if resultado["total_activas"] == 0:
        return "Seguimiento: no hay tareas de negocio activas todavía."

    lineas = [f"Seguimiento: {resultado['total_activas']} tarea(s) de negocio activa(s)."]

    lineas.append("\nPor fase:")
    for fase, tareas in resultado["por_fase"].items():
        lineas.append(f"  - {fase}: {len(tareas)}")

    if resultado["estancadas"]:
        lineas.append(f"\n{len(resultado['estancadas'])} estancada(s):")
        for t in resultado["estancadas"]:
            lineas.append(f"  - [{t.get('business_line')}] {t['name']} "
                           f"(fase: {t.get('business_phase') or '(sin fase)'}, "
                           f"sin moverse desde {t['updated_at'][:10]})")
    else:
        lineas.append("\nNinguna estancada.")

    return "\n".join(lineas)
