"""
Policy Engine — versión revisada (PropuestaArquitecturaCEO.md)

Responsabilidad: decidir si una acción propuesta por un agente puede ejecutarse,
usando la escala única de autonomía de Schemas/Permissions.md (0-4).
No decide QUÉ hacer (eso es Decision Engine) -- decide QUÉ ESTÁ PERMITIDO hacer
(Modules/PolicyEngine.md).

Revisión de arquitectura CEO (decisión explícita del usuario): la confirmación
puntual deja de aplicarse a "cualquier cosa de nivel 2 o 3" -- eso generaba
fricción constante (un sí/no por guardar una nota, generar código, integrar
un agente...). Ahora solo hay una lista cerrada de tres acciones que siguen
pidiendo confirmación siempre: ejecutar código generado, eliminar, desplegar
a producción (Constitution Art. 2 y 10). Todo lo demás -- niveles 0 a 3,
incluido guardar/generar/sobrescribir/integrar -- es autónomo, sin preguntar.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
import memory_engine as me  # noqa: E402

# Escala única de autonomía (Schemas/Permissions.md, revisada):
#   0 Consulta/Manual        -> permitido
#   1 Asistido                -> permitido
#   2 Supervisado             -> permitido (guardar, generar, sobrescribir, integrar)
#   3 Autónomo limitado       -> permitido
#   4 Autónomo estratégico    -> requiere_aprobación SIEMPRE, sin excepción
#                                 (lista cerrada: ejecutar, eliminar, desplegar --
#                                 Constitution Art. 2 y 10). Nunca "bloqueado" del
#                                 todo -- el usuario decidió mantener el sí/no, no
#                                 un bloqueo absoluto sin salida.
NIVEL_REQUIERE_APROBACION_SIEMPRE = 4


def evaluate(agent_name: str, action: str, autonomy_level: int) -> str:
    """
    Devuelve 'permitido' o 'requiere_aprobación'. Ya no existe 'bloqueado' --
    la única categoría que antes bloqueaba sin excepción ahora pide
    confirmación puntual siempre (decisión explícita del usuario, revisión
    de arquitectura CEO). Toda evaluación se registra como Evento
    (auditoría — Schemas/Permissions.md).
    """
    if autonomy_level >= NIVEL_REQUIERE_APROBACION_SIEMPRE:
        result = "requiere_aprobación"
    else:
        result = "permitido"

    me.create_event(
        event_type="policy.evaluated",
        origin_module="policy_engine",
        context={
            "agent": agent_name,
            "action": action,
            "autonomy_level_required": autonomy_level,
            "result": result,
        },
        requires_approval=(result == "requiere_aprobación"),
    )
    return result
