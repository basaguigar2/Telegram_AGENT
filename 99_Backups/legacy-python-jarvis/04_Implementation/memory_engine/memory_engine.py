"""
Memory Engine — versión mínima (Roadmap Fase 1)

Responsabilidad única en esta fase: CRUD versionado sobre Conocimiento.
Nada de razonamiento, nada de prioridades — eso llega en fases posteriores
(Decision Engine, Fase 3).

Reglas que respeta este código, heredadas de Modules/MemoryEngine.md y
Schemas/Lifecycle.md:
- Nunca se sobrescribe una fila: todo cambio crea una nueva versión.
- Nunca se elimina físicamente: el estado 'archivado' es el único retiro.
- Toda entidad guarda de dónde viene (`source`).
"""

import sqlite3
import uuid
import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "db" / "jarvis.db"


def _now() -> str:
    return datetime.datetime.now().isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_knowledge(content: str, topic: str, reliability: str = "media",
                      source: str = "usuario", source_resource_id: str | None = None) -> str:
    """Captura conocimiento nuevo. Devuelve el id creado."""
    if reliability not in ("alta", "media", "baja"):
        raise ValueError("reliability debe ser 'alta', 'media' o 'baja'")

    new_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO knowledge
                (id, name, status, created_at, updated_at, version,
                 previous_version_id, source, content, topic, reliability, source_resource_id)
            VALUES (?, ?, 'propuesto', ?, ?, 1, NULL, ?, ?, ?, ?, ?)
            """,
            (new_id, topic[:80], now, now, source, content, topic, reliability, source_resource_id),
        )
    return new_id


def get_knowledge(knowledge_id: str) -> dict | None:
    """Recupera la versión indicada (o la que se le pase) de un Conocimiento."""
    with _connect() as conn:
        row = conn.execute("SELECT * FROM knowledge WHERE id = ?", (knowledge_id,)).fetchone()
    return dict(row) if row else None


def list_knowledge(topic: str | None = None, status: str | None = None) -> list[dict]:
    """Lista Conocimiento, opcionalmente filtrado por tema o estado."""
    query = "SELECT * FROM knowledge WHERE 1=1"
    params = []
    if topic:
        query += " AND topic = ?"
        params.append(topic)
    if status:
        query += " AND status = ?"
        params.append(status)
    else:
        query += " AND status != 'archivado'"
    query += " ORDER BY created_at DESC"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def validate_knowledge(knowledge_id: str) -> None:
    """Pasa un Conocimiento de 'propuesto' a 'validado' (MemoryEngine.md — calidad del conocimiento)."""
    with _connect() as conn:
        conn.execute(
            "UPDATE knowledge SET status = 'validado', updated_at = ? WHERE id = ?",
            (_now(), knowledge_id),
        )


def update_knowledge(knowledge_id: str, **changes) -> str:
    """
    Actualiza Conocimiento SIN sobrescribir: crea una nueva fila versionada,
    marca la anterior como 'desactualizado' y devuelve el id de la nueva versión.
    """
    current = get_knowledge(knowledge_id)
    if current is None:
        raise ValueError(f"No existe Conocimiento con id {knowledge_id}")

    new_id = str(uuid.uuid4())
    now = _now()
    merged = {
        "content": changes.get("content", current["content"]),
        "topic": changes.get("topic", current["topic"]),
        "reliability": changes.get("reliability", current["reliability"]),
        "source_resource_id": changes.get("source_resource_id", current["source_resource_id"]),
    }

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO knowledge
                (id, name, status, created_at, updated_at, version,
                 previous_version_id, source, content, topic, reliability, source_resource_id)
            VALUES (?, ?, 'propuesto', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (new_id, merged["topic"][:80], now, now, current["version"] + 1,
             knowledge_id, changes.get("source", "usuario"),
             merged["content"], merged["topic"], merged["reliability"], merged["source_resource_id"]),
        )
        conn.execute(
            "UPDATE knowledge SET status = 'desactualizado', updated_at = ? WHERE id = ?",
            (now, knowledge_id),
        )
    return new_id


def archive_knowledge(knowledge_id: str) -> None:
    """Retira Conocimiento de circulación sin borrarlo nunca."""
    with _connect() as conn:
        conn.execute(
            "UPDATE knowledge SET status = 'archivado', updated_at = ? WHERE id = ?",
            (_now(), knowledge_id),
        )


def create_decision(context: str, reason: str, alternatives: list[str] | None = None,
                     related_goal_id: str | None = None, source: str = "decision_engine") -> str:
    """
    Registra una Decisión propuesta por el Decision Engine.
    result queda en 'pendiente' hasta que el usuario la acepte o rechace
    (Constitution Art. 10 — nunca se ejecuta nada sin aprobación explícita).
    """
    new_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO decision
                (id, name, status, created_at, updated_at, version,
                 previous_version_id, source, context, reason, result, related_goal_id)
            VALUES (?, ?, 'propuesta', ?, ?, 1, NULL, ?, ?, ?, 'pendiente', ?)
            """,
            (new_id, reason[:80], now, now, source, context, reason, related_goal_id),
        )
        for alt in (alternatives or []):
            conn.execute(
                "INSERT INTO decision_alternative (id, decision_id, body) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), new_id, alt),
            )
    return new_id


def resolve_decision(decision_id: str, result: str) -> None:
    """El usuario acepta o rechaza una decisión propuesta. Nunca se auto-resuelve."""
    if result not in ("aceptada", "rechazada"):
        raise ValueError("result debe ser 'aceptada' o 'rechazada'")
    with _connect() as conn:
        conn.execute(
            "UPDATE decision SET result = ?, status = ?, updated_at = ? WHERE id = ?",
            (result, result, _now(), decision_id),
        )


def flag_for_claude(topic: str, detail: str, source: str = "sistema") -> str:
    """
    Marca algo como 'esto le toca a Claude'. No llama a ninguna API -- solo
    deja constancia persistente en memoria para que el usuario lo traiga él
    mismo al chat con Claude cuando quiera (nunca automático, decisión
    explícita del usuario de cuándo y cómo activar a Claude).
    Reutiliza la entidad Decisión con un marcador en el contexto, en vez de
    inventar una tabla nueva.
    """
    import json as _json
    context = _json.dumps({"requiere_claude": True, "topic": topic}, ensure_ascii=False)
    return create_decision(context=context, reason=detail, source=source)


def pending_for_claude() -> list[dict]:
    """Decisiones pendientes marcadas específicamente como 'requiere Claude'."""
    import json as _json
    resultado = []
    for d in pending_decisions():
        try:
            ctx = _json.loads(d["context"])
        except (ValueError, TypeError):
            continue
        if ctx.get("requiere_claude"):
            resultado.append(d)
    return resultado


def create_insight(pattern: str, source: str = "sistema", nombre: str | None = None) -> str:
    """
    Registra una limitación o patrón detectado por el propio sistema
    (Modules/SelfEvolution.md) -- backlog de autoevolución. Nunca se
    auto-aplica: queda con validated=0 hasta que el usuario lo revise
    (mismo principio que resolve_decision -- nada se ejecuta solo).

    `nombre` es un identificador corto y estable para poder deduplicar
    (ej. "patron_repetido:ejecuciones_fallidas") -- si no se da, se usa
    el propio texto del patrón truncado, que es más difícil de reconocer
    como "el mismo insight" en llamadas futuras.
    """
    new_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO insight
                (id, name, status, created_at, updated_at, version,
                 previous_version_id, source, pattern, validated)
            VALUES (?, ?, 'detectado', ?, ?, 1, NULL, ?, ?, 0)
            """,
            (new_id, (nombre or pattern)[:80], now, now, source, pattern),
        )
    return new_id


def pending_insights() -> list[dict]:
    """Backlog de autoevolución: insights detectados que el usuario no ha validado ni descartado."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM insight WHERE validated = 0 AND status != 'descartado' "
            "ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def validate_insight(insight_id: str) -> None:
    """El usuario confirma que el patrón detectado es real y vale la pena actuar sobre él."""
    with _connect() as conn:
        conn.execute(
            "UPDATE insight SET validated = 1, status = 'validado', updated_at = ? WHERE id = ?",
            (_now(), insight_id),
        )


def discard_insight(insight_id: str) -> None:
    """El usuario decide que el patrón detectado no vale la pena o es un falso positivo."""
    with _connect() as conn:
        conn.execute(
            "UPDATE insight SET status = 'descartado', updated_at = ? WHERE id = ?",
            (_now(), insight_id),
        )


def recent_events(since_hours: int = 24, event_type: str | None = None) -> list[dict]:
    """
    Eventos ocurridos en las últimas `since_hours` horas, opcionalmente
    filtrados por tipo. Base del Supervisor Agent -- revisa lo ya ocurrido
    a partir del registro de auditoría real, no de lo que un modelo "cree"
    que pasó.
    """
    cutoff = (datetime.datetime.now() - datetime.timedelta(hours=since_hours)).isoformat()
    query = "SELECT * FROM event WHERE occurred_at >= ?"
    params = [cutoff]
    if event_type:
        query += " AND event_type = ?"
        params.append(event_type)
    query += " ORDER BY occurred_at DESC"
    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def active_goals() -> list[dict]:
    """Objetivos activos, para que el Context Engine los use como contexto."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM goal WHERE status = 'activo' ORDER BY priority").fetchall()
    return [dict(r) for r in rows]


def recent_knowledge(limit: int = 10) -> list[dict]:
    """Conocimiento activo más reciente, para que el Context Engine lo use como contexto."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM knowledge WHERE status IN ('validado','propuesto') "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def pending_decisions() -> list[dict]:
    """Decisiones propuestas todavía sin aceptar/rechazar (result = 'pendiente')."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM decision WHERE result = 'pendiente' ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def create_event(event_type: str, origin_module: str, context: dict,
                  outcome: str | None = None, requires_approval: bool = False) -> str:
    """Registra un Evento (Schemas/Events.md). Inmutable desde que se emite."""
    import json as _json
    new_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO event
                (id, event_type, occurred_at, origin_module, context, outcome, status, requires_approval)
            VALUES (?, ?, ?, ?, ?, ?, 'procesado', ?)
            """,
            (new_id, event_type, _now(), origin_module, _json.dumps(context, ensure_ascii=False),
             outcome, 1 if requires_approval else 0),
        )
    return new_id


def create_task(name: str, description: str, business_line: str | None = None,
                 priority: str = "operativo", business_phase: str | None = None,
                 related_knowledge_id: str | None = None, source: str = "sistema") -> str:
    """
    Crea una Tarea (Schemas/Entities.md). `business_line` identifica a qué línea
    de negocio pertenece (ej. 'contenido_afiliados'); NULL significa tarea
    interna de JARVIS. `business_phase` es el vocabulario propio de esa línea
    (ver db/schema.sql -- sin CHECK a propósito, cada línea define el suyo).
    """
    new_id = str(uuid.uuid4())
    now = _now()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO task
                (id, name, status, created_at, updated_at, version,
                 previous_version_id, source, description, priority,
                 business_line, business_phase, related_knowledge_id)
            VALUES (?, ?, 'pendiente', ?, ?, 1, NULL, ?, ?, ?, ?, ?, ?)
            """,
            (new_id, name[:80], now, now, source, description, priority,
             business_line, business_phase, related_knowledge_id),
        )
    return new_id


def get_task(task_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def list_tasks(business_line: str | None = None, status: str | None = None) -> list[dict]:
    """Lista Tareas, opcionalmente filtradas por línea de negocio o estado (excluye 'archivada' por defecto)."""
    query = "SELECT * FROM task WHERE 1=1"
    params = []
    if business_line:
        query += " AND business_line = ?"
        params.append(business_line)
    if status:
        query += " AND status = ?"
        params.append(status)
    else:
        query += " AND status != 'archivada'"
    query += " ORDER BY updated_at DESC"

    with _connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def update_task(task_id: str, status: str | None = None, business_phase: str | None = None) -> None:
    """
    Actualiza estado y/o fase de negocio de una Tarea. Transición directa, sin
    versionar -- igual que resolve_decision/validate_knowledge, porque esto es
    un cambio de estado de ciclo de vida (Schemas/Lifecycle.md), no un cambio
    de contenido (eso sí exigiría update_knowledge-style versionado).
    """
    if status is not None and status not in (
        "pendiente", "en_progreso", "bloqueada", "completada", "fallida", "archivada"
    ):
        raise ValueError("status no reconocido para task")

    campos, valores = [], []
    if status is not None:
        campos.append("status = ?")
        valores.append(status)
    if business_phase is not None:
        campos.append("business_phase = ?")
        valores.append(business_phase)
    if not campos:
        return

    campos.append("updated_at = ?")
    valores.append(_now())
    valores.append(task_id)
    with _connect() as conn:
        conn.execute(f"UPDATE task SET {', '.join(campos)} WHERE id = ?", valores)


def get_history(knowledge_id: str) -> list[dict]:
    """Recorre previous_version_id hacia atrás y devuelve todo el histórico de versiones."""
    history = []
    current_id = knowledge_id
    with _connect() as conn:
        while current_id:
            row = conn.execute("SELECT * FROM knowledge WHERE id = ?", (current_id,)).fetchone()
            if not row:
                break
            history.append(dict(row))
            current_id = row["previous_version_id"]
    return history
