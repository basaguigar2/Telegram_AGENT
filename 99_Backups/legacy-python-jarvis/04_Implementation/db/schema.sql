-- JARVIS — Esquema SQLite
-- Generado a partir de Schemas/Entities.md, Schemas/Relationships.md,
-- Schemas/Events.md y Schemas/Lifecycle.md
-- Motor: SQLite (ver TechStack.md)

PRAGMA foreign_keys = ON;

-- ============================================================
-- Núcleo común: todas las tablas de entidad comparten estas columnas
-- (Schemas/Entities.md — "Núcleo común")
-- ============================================================

-- id            TEXT PRIMARY KEY (uuid)
-- name          TEXT NOT NULL
-- status        TEXT NOT NULL
-- created_at    TEXT NOT NULL   (ISO8601)
-- updated_at    TEXT NOT NULL   (ISO8601)
-- version       INTEGER NOT NULL DEFAULT 1
-- previous_version_id  TEXT REFERENCES <misma tabla>(id)
-- source        TEXT NOT NULL
-- confidence    TEXT            ('alta' | 'media' | 'baja')

-- ============================================================
-- Usuario (instancia única por despliegue)
-- ============================================================
CREATE TABLE IF NOT EXISTS user (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'activo',
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES user(id),
    source              TEXT NOT NULL,
    energy              TEXT,          -- estado estimado, no exacto (UserModelEngine.md)
    mental_load         TEXT,
    available_time      TEXT,
    motivation          TEXT
);

CREATE TABLE IF NOT EXISTS user_preference (
    id      TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user(id),
    label   TEXT NOT NULL,
    value   TEXT
);

CREATE TABLE IF NOT EXISTS user_principle (
    id      TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user(id),
    body    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_constraint (
    id      TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user(id),
    kind    TEXT NOT NULL,   -- tiempo | presupuesto | disponibilidad | limite_autoimpuesto
    body    TEXT NOT NULL
);

-- ============================================================
-- Objetivo
-- ============================================================
CREATE TABLE IF NOT EXISTS goal (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('propuesto','activo','pausado','conseguido','abandonado','archivado')),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES goal(id),
    source              TEXT NOT NULL,
    priority            TEXT NOT NULL CHECK (priority IN ('estrategico','importante','operativo','prescindible')),
    target_date         TEXT,
    parent_goal_id      TEXT REFERENCES goal(id)
);

-- ============================================================
-- Proyecto
-- ============================================================
CREATE TABLE IF NOT EXISTS project (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('evaluacion','creado','activo','pausado','finalizado','archivado')),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES project(id),
    source              TEXT NOT NULL,
    goal_id             TEXT NOT NULL REFERENCES goal(id)
);

-- ============================================================
-- Tarea
-- Activada para uso real por Agente Seguimiento / Agente Generador
-- (línea de negocio "contenido_afiliados", RelacionConAGENTE.md) --
-- hasta entonces quedaba definida pero sin ningún agente que la usara.
-- ============================================================
CREATE TABLE IF NOT EXISTS task (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('pendiente','en_progreso','bloqueada','completada','fallida','archivada')),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES task(id),
    source              TEXT NOT NULL,
    description         TEXT NOT NULL,
    priority            TEXT NOT NULL,
    estimated_effort    TEXT,
    project_id          TEXT REFERENCES project(id),
    assigned_agent_id   TEXT,
    -- Campos de tablero multi-negocio (AGENTE, tablero_tareas) modelados como
    -- extensión de Tarea en vez de una tabla/base de datos nueva (decisión
    -- explícita del usuario: SQLite local, no Supabase, mientras no haga
    -- falta acceso remoto real -- RelacionConAGENTE.md).
    business_line        TEXT,    -- slug estable, ej. 'contenido_afiliados'. NULL = tarea interna de JARVIS.
    business_phase        TEXT,   -- vocabulario libre por línea (ej. 'idea'|'produccion'|'borrador_listo'|'publicado'
                                   -- para contenido); sin CHECK a propósito, cada línea define el suyo sin migrar el esquema.
    related_knowledge_id  TEXT REFERENCES knowledge(id)  -- ej. el artículo que esta tarea rastrea
);

CREATE TABLE IF NOT EXISTS task_dependency (
    task_id            TEXT NOT NULL REFERENCES task(id),
    depends_on_task_id TEXT NOT NULL REFERENCES task(id),
    PRIMARY KEY (task_id, depends_on_task_id),
    CHECK (task_id != depends_on_task_id)
);

-- ============================================================
-- Recurso
-- ============================================================
CREATE TABLE IF NOT EXISTS resource (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('capturado','procesado','archivado')),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES resource(id),
    source              TEXT NOT NULL,
    resource_type       TEXT NOT NULL CHECK (resource_type IN ('pdf','video','web','curso','libro','otro')),
    origin_url_or_path  TEXT,
    retrieved_at        TEXT NOT NULL
);

-- ============================================================
-- Conocimiento
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    status              TEXT NOT NULL CHECK (status IN ('propuesto','validado','activo','desactualizado','archivado')),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES knowledge(id),
    source              TEXT NOT NULL,
    confidence          TEXT CHECK (confidence IN ('alta','media','baja')),
    content              TEXT NOT NULL,
    topic                TEXT NOT NULL,
    reliability           TEXT NOT NULL CHECK (reliability IN ('alta','media','baja')),
    source_resource_id    TEXT REFERENCES resource(id),
    -- embedding para búsqueda semántica (sqlite-vec, ver TechStack.md)
    embedding             BLOB
);

-- ============================================================
-- Decisión
-- ============================================================
CREATE TABLE IF NOT EXISTS decision (
    id                  TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'propuesta' CHECK (status IN ('propuesta','pendiente_aprobacion','aceptada','rechazada')),
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES decision(id),
    source              TEXT NOT NULL,
    confidence          TEXT CHECK (confidence IN ('alta','media','baja')),
    context              TEXT NOT NULL,
    reason               TEXT NOT NULL,
    result               TEXT NOT NULL DEFAULT 'pendiente' CHECK (result IN ('aceptada','rechazada','pendiente')),
    related_goal_id      TEXT REFERENCES goal(id)
);

CREATE TABLE IF NOT EXISTS decision_alternative (
    id          TEXT PRIMARY KEY,
    decision_id TEXT NOT NULL REFERENCES decision(id),
    body        TEXT NOT NULL
);

-- ============================================================
-- Regla
-- ============================================================
CREATE TABLE IF NOT EXISTS rule (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'activa' CHECK (status IN ('activa','derogada')),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES rule(id),
    source      TEXT NOT NULL,
    rule_level  TEXT NOT NULL CHECK (rule_level IN ('constitucion','sistema','personal','temporal')),
    expires_at  TEXT,       -- obligatorio si rule_level = 'temporal', validado en aplicación
    body        TEXT NOT NULL
);

-- ============================================================
-- Insight
-- ============================================================
CREATE TABLE IF NOT EXISTS insight (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'detectado' CHECK (status IN ('detectado','validado','descartado')),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    previous_version_id TEXT REFERENCES insight(id),
    source      TEXT NOT NULL,
    pattern     TEXT NOT NULL,
    validated   INTEGER NOT NULL DEFAULT 0 CHECK (validated IN (0,1))
);

CREATE TABLE IF NOT EXISTS insight_evidence (
    id         TEXT PRIMARY KEY,
    insight_id TEXT NOT NULL REFERENCES insight(id),
    ref_type   TEXT NOT NULL,   -- 'event' | 'decision'
    ref_id     TEXT NOT NULL
);

-- ============================================================
-- Evento (Schemas/Events.md — inmutable, no usa el lifecycle genérico)
-- ============================================================
CREATE TABLE IF NOT EXISTS event (
    id                  TEXT PRIMARY KEY,
    event_type          TEXT NOT NULL,
    occurred_at         TEXT NOT NULL,
    origin_module       TEXT NOT NULL,
    context              TEXT NOT NULL,   -- JSON serializado
    outcome              TEXT,
    status                TEXT NOT NULL DEFAULT 'emitido' CHECK (status IN ('emitido','procesado','fallido')),
    requires_approval     INTEGER NOT NULL DEFAULT 0 CHECK (requires_approval IN (0,1)),
    approved_by           TEXT
);

CREATE TABLE IF NOT EXISTS event_related_entity (
    event_id  TEXT NOT NULL REFERENCES event(id),
    entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    PRIMARY KEY (event_id, entity_id)
);

-- ============================================================
-- Relaciones genéricas (Schemas/Relationships.md)
-- Para relaciones que no encajan como columna FK directa arriba
-- (supports, derived_from, evidence_for, governed_by, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS relationship (
    id           TEXT PRIMARY KEY,
    type         TEXT NOT NULL CHECK (type IN (
                     'has_goal','belongs_to','has_task','depends_on','uses_resource',
                     'supports','modifies','derived_from','evidence_for',
                     'governed_by','assigned_to'
                 )),
    source_id    TEXT NOT NULL,
    source_type  TEXT NOT NULL,
    target_id    TEXT NOT NULL,
    target_type  TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    created_by   TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'activa' CHECK (status IN ('activa','archivada'))
);

CREATE INDEX IF NOT EXISTS idx_relationship_source ON relationship(source_id, source_type);
CREATE INDEX IF NOT EXISTS idx_relationship_target ON relationship(target_id, target_type);
CREATE INDEX IF NOT EXISTS idx_event_type ON event(event_type);
CREATE INDEX IF NOT EXISTS idx_event_occurred ON event(occurred_at);
