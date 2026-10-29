"""
Supervisor Agent v1.0 (AgentFramework.md -- contrato de agente)

Misión: revisar lo que el resto del sistema ha hecho recientemente y avisar
de lo que no salió bien, sin esperar a que el usuario lo descubra por su
cuenta. Cubre tanto JARVIS mismo como cualquier línea de negocio con
tareas en el tablero (RelacionConAGENTE.md, "Auditoría Interna
transversal") -- no es un agente nuevo por línea, es el mismo Supervisor
ampliado, siguiendo AgentFrameWork.md ("no busca crear muchos agentes,
busca crear una organización eficiente").

Responsabilidades: leer eventos, decisiones y conocimiento recientes, y
detectar patrones de fallo (ejecuciones que fallaron, código bloqueado por
el escáner de seguridad, decisiones que llevan mucho tiempo sin resolverse,
conocimiento de baja confianza que nadie ha validado) -- y, para negocio,
reglas mecánicas simples como pedía AGENTE ("que todo dato citado tenga
fuente"): artículos con enlaces o precios que no deberían estar ahí,
ideas marcadas como investigación real sin la fuente que lo demuestre, y
tareas que apuntan a un Conocimiento que ya no existe.

Límites: NUNCA corrige nada por su cuenta. NUNCA usa el modelo local para
decidir si algo salió bien -- eso sería el mismo tipo de modelo que comete
errores juzgándose a sí mismo, poco fiable. Todas sus comprobaciones son
reglas deterministas sobre datos reales de Memory Engine.

Nivel de autonomía: 1 (Asistido) -- solo informa, nunca actúa.
"""

import re
import sys
import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
sys.path.append(str(Path(__file__).parent.parent / "agents"))
import memory_engine as me  # noqa: E402
import generador_agent      # noqa: E402 -- solo para PLACEHOLDER_ENLACE, ver _articulos_con_datos_sin_verificar

AUTONOMY_LEVEL = 1

# Umbrales de las reglas -- ajustables sin tocar la lógica
VENTANA_HORAS = 24
DIAS_DECISION_ESTANCADA = 3


def _ejecuciones_fallidas(eventos: list[dict]) -> list[str]:
    hallazgos = []
    for e in eventos:
        if e["event_type"] != "code.executed":
            continue
        import json
        try:
            ctx = json.loads(e["context"])
        except (ValueError, TypeError):
            continue
        if ctx.get("timeout"):
            hallazgos.append(f"Ejecución cancelada por timeout: {ctx.get('target_file', '?')}")
        elif ctx.get("returncode") not in (0, None):
            hallazgos.append(f"Ejecución con error (código {ctx.get('returncode')}): "
                              f"{ctx.get('target_file', '?')}")
    return hallazgos


def _codigo_bloqueado_por_seguridad(eventos: list[dict]) -> list[str]:
    hallazgos = []
    for e in eventos:
        if e["event_type"] != "code.safety_scan":
            continue
        import json
        try:
            ctx = json.loads(e["context"])
        except (ValueError, TypeError):
            continue
        if not ctx.get("es_seguro", True):
            motivos = ", ".join(ctx.get("motivos", []))
            hallazgos.append(f"Código guardado pero bloqueado para ejecutar "
                              f"({motivos}): {ctx.get('target_file', '?')}")
    return hallazgos


def _acciones_bloqueadas_por_politica(eventos: list[dict]) -> list[str]:
    hallazgos = []
    for e in eventos:
        if e["event_type"] != "policy.evaluated":
            continue
        import json
        try:
            ctx = json.loads(e["context"])
        except (ValueError, TypeError):
            continue
        if ctx.get("result") == "bloqueado":
            hallazgos.append(f"Acción bloqueada por Policy Engine: "
                              f"{ctx.get('agent', '?')} / {ctx.get('action', '?')}")
    return hallazgos


def _decisiones_estancadas() -> list[str]:
    hallazgos = []
    limite = datetime.datetime.now() - datetime.timedelta(days=DIAS_DECISION_ESTANCADA)
    for d in me.pending_decisions():
        try:
            creada = datetime.datetime.fromisoformat(d["created_at"])
        except ValueError:
            continue
        if creada < limite:
            dias = (datetime.datetime.now() - creada).days
            hallazgos.append(f"Decisión pendiente desde hace {dias} días sin resolver: {d['reason']}")
    return hallazgos


_PATRON_PRECIO = re.compile(r"[\$€]\s?\d+[.,]?\d*")


def _articulos_con_datos_sin_verificar() -> list[str]:
    """
    Regla mecánica de negocio (AGENTE -- "que todo dato citado tenga
    fuente"), aplicada al revés: revisa los artículos de Generador Agent en
    busca de un enlace de afiliado que NO sea el placeholder oficial, o de
    un precio con cifra concreta -- ambos prohibidos explícitamente en su
    prompt (nunca inventar URLs ni precios reales). Ninguna comprobación
    usa un modelo, son patrones de texto sobre lo que ya se escribió.
    """
    hallazgos = []
    for k in me.list_knowledge():
        if k.get("source") != "generador_agent":
            continue
        contenido = k["content"]
        urls_reales = [
            u.rstrip(").,;") for u in re.findall(r"https?://\S+", contenido)
            if u.rstrip(").,;") != generador_agent.PLACEHOLDER_ENLACE
        ]
        if urls_reales:
            hallazgos.append(f"Enlace que no es el placeholder en \"{k['topic']}\": {urls_reales[0]}")
        if _PATRON_PRECIO.search(contenido):
            hallazgos.append(f"Precio con cifra concreta en \"{k['topic']}\" -- revisar si está inventado")
    return hallazgos


def _ideas_sin_fuente_trazable() -> list[str]:
    """
    Tareas de negocio en fase 'idea' marcadas como investigación real
    (investigador_agent.crear_tarea_idea con source de búsqueda real o de
    Claude) pero cuya descripción no lleva la marca "[fuente real: ...]" --
    se perdió la trazabilidad en algún punto entre investigar y guardar.
    """
    hallazgos = []
    for t in me.list_tasks():
        if t.get("business_phase") != "idea":
            continue
        source = t.get("source") or ""
        es_investigacion_real = (source == "investigador_agent_busqueda_real"
                                  or source.startswith("claude_websearch"))
        if es_investigacion_real and "[fuente real:" not in (t.get("description") or ""):
            hallazgos.append(f"Idea marcada como investigación real sin fuente trazable: {t['name']}")
    return hallazgos


def _tareas_huerfanas() -> list[str]:
    """
    Tareas de negocio con related_knowledge_id que apunta a un Conocimiento
    inexistente o ya archivado -- rompería el enlace entre la tarea del
    tablero y el artículo/nota que se supone que rastrea.
    """
    hallazgos = []
    for t in me.list_tasks():
        rk_id = t.get("related_knowledge_id")
        if not rk_id:
            continue
        conocimiento = me.get_knowledge(rk_id)
        if conocimiento is None:
            hallazgos.append(f"Tarea \"{t['name']}\" referencia un Conocimiento que ya no existe ({rk_id})")
        elif conocimiento["status"] == "archivado":
            hallazgos.append(f"Tarea \"{t['name']}\" referencia un Conocimiento ya archivado ({rk_id})")
    return hallazgos


def _conocimiento_sin_validar() -> list[str]:
    sin_validar = [
        k for k in me.recent_knowledge(limit=50)
        if k["status"] == "propuesto" and k["reliability"] == "baja"
    ]
    if not sin_validar:
        return []
    return [f"{len(sin_validar)} Conocimiento(s) de confianza baja sin validar todavía "
            f"(ej: \"{sin_validar[0]['topic']}\")"]


# Categorías que, si se repiten (>=2 hallazgos en la misma ventana), se
# consideran un patrón y no un incidente puntual -- umbral deliberadamente
# simple (Modules/SelfEvolution.md prefiere esto a un "análisis de impacto"
# automático que hoy no tendría datos suficientes para ser fiable).
UMBRAL_PATRON = 2


def _registrar_insights_si_patron_repetido(hallazgos: dict) -> None:
    """
    Backlog de autoevolución (Modules/SelfEvolution.md): si una categoría de
    hallazgo se repite dentro de la ventana revisada, se registra como
    Insight para que el usuario lo revise -- nunca se actúa sobre ello
    solo. Evita duplicar: no registra un insight nuevo si ya hay uno
    pendiente para la misma categoría.
    """
    pendientes = me.pending_insights()
    categorias_ya_registradas = {p["name"] for p in pendientes}

    for categoria, items in hallazgos.items():
        if len(items) < UMBRAL_PATRON:
            continue
        nombre_patron = f"patron_repetido:{categoria}"[:80]
        if nombre_patron in categorias_ya_registradas:
            continue
        me.create_insight(
            pattern=f"Patrón repetido detectado por Supervisor Agent: {categoria} "
                    f"({len(items)} veces en {VENTANA_HORAS}h). Ejemplo: {items[0]}",
            source="supervisor_agent",
            nombre=nombre_patron,
        )


def run(since_hours: int = VENTANA_HORAS) -> dict:
    """Revisa las últimas `since_hours` horas y devuelve un dict con hallazgos por categoría."""
    eventos = me.recent_events(since_hours=since_hours)

    hallazgos = {
        "ejecuciones_fallidas": _ejecuciones_fallidas(eventos),
        "codigo_bloqueado": _codigo_bloqueado_por_seguridad(eventos),
        "acciones_bloqueadas": _acciones_bloqueadas_por_politica(eventos),
        "decisiones_estancadas": _decisiones_estancadas(),
        "conocimiento_sin_validar": _conocimiento_sin_validar(),
        "articulos_datos_sin_verificar": _articulos_con_datos_sin_verificar(),
        "ideas_sin_fuente": _ideas_sin_fuente_trazable(),
        "tareas_huerfanas": _tareas_huerfanas(),
    }

    total = sum(len(v) for v in hallazgos.values())
    _registrar_insights_si_patron_repetido(hallazgos)

    me.create_event(
        event_type="supervisor.review",
        origin_module="supervisor_agent",
        context={"since_hours": since_hours, "total_hallazgos": total},
    )

    return {"total_hallazgos": total, "hallazgos": hallazgos}


def formatear(resultado: dict) -> str:
    """Convierte el resultado de run() en texto legible, sin depender de ningún modelo de IA."""
    if resultado["total_hallazgos"] == 0:
        return "Supervisor: todo en orden, sin hallazgos en la ventana revisada."

    lineas = [f"Supervisor: {resultado['total_hallazgos']} hallazgo(s):"]
    nombres = {
        "ejecuciones_fallidas": "Ejecuciones fallidas",
        "codigo_bloqueado": "Código bloqueado por seguridad",
        "acciones_bloqueadas": "Acciones bloqueadas por Policy Engine",
        "decisiones_estancadas": "Decisiones estancadas",
        "conocimiento_sin_validar": "Conocimiento sin validar",
        "articulos_datos_sin_verificar": "Artículos de negocio con datos sin verificar",
        "ideas_sin_fuente": "Ideas de negocio sin fuente trazable",
        "tareas_huerfanas": "Tareas de negocio huérfanas",
    }
    for clave, items in resultado["hallazgos"].items():
        if not items:
            continue
        lineas.append(f"\n{nombres[clave]}:")
        for item in items:
            lineas.append(f"  - {item}")
    return "\n".join(lineas)
