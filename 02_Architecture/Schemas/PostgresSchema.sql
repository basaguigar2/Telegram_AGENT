-- JARVIS v2 -- esquema Postgres para el flujo nuevo (Telegram -> n8n -> Llama/Jev -> permisos -> Postgres).
-- Traduce 1:1 el modelo conceptual ya existente en Schemas/Entities.md, Schemas/Events.md y
-- Schemas/Permissions.md -- no se reescribe el modelo, se reimplementa en otro motor (TechStack.md
-- ya anticipaba esta migracion: "el esquema conceptual no cambia").
--
-- Nombres en espanol y prefijo mayordomo_ para quedar consistentes con la tabla que ya existe en
-- produccion (mayordomo_memoria, usada por "JARVIS - Guardar Recuerdo" / "JARVIS - Memoria
-- Persistente"). Estas tablas son nuevas y complementarias -- no tocan mayordomo_memoria.
--
-- Diseno: una tabla `mayordomo_entidades` generica (nucleo comun + JSONB para campos propios de
-- cada tipo) en vez de una tabla por tipo. Motivo: n8n inserta/lee con nodos genericos de Postgres:
-- con 9 tipos de entidad (Usuario, Objetivo, Proyecto, Tarea, Conocimiento, Recurso, Decision,
-- Regla, Insight) una tabla por tipo obliga a 9 ramas distintas en cada workflow. Con una tabla +
-- JSONB, un unico nodo "Insert entity" sirve para las 9, y el tipo decide que campos lleva `atributos`.

create extension if not exists pgcrypto; -- gen_random_uuid()

create table mayordomo_entidades (
    id                  uuid primary key default gen_random_uuid(),
    usuario_id          text not null,          -- mismo criterio que mayordomo_memoria
    tipo                text not null,          -- usuario | objetivo | proyecto | tarea | conocimiento | recurso | decision | regla | insight
    nombre              text not null,
    estado              text not null,          -- ver Schemas/Lifecycle.md (activo | archivado | ...)
    creado_en           timestamptz not null default now(),
    actualizado_en      timestamptz not null default now(),
    version             integer not null default 1,
    version_anterior_id uuid references mayordomo_entidades(id),
    -- Entities.md no define un id estable de "familia" (cada version es un id nuevo encadenado por
    -- version_anterior_id) -- eso obliga a recorrer la cadena hacia atras para saber si una fila es
    -- la version vigente. Anadido aqui como mejora practica al migrar a Postgres: raiz_id es el id
    -- de la primera version y nunca cambia, asi "dame la version activa de X" es una query directa
    -- (raiz_id = X and estado = 'activo') en vez de recorrer version_anterior_id.
    raiz_id             uuid not null,
    origen              text not null,          -- agente, modulo o 'usuario'
    confianza           text,                   -- alta | media | baja (solo decision / insight)
    atributos           jsonb not null default '{}'::jsonb
);

-- Regla de integridad #2 de Entities.md: ninguna entidad puede tener dos versiones activas a la vez.
create unique index mayordomo_entidades_una_version_activa
    on mayordomo_entidades (raiz_id)
    where estado = 'activo';

create index mayordomo_entidades_tipo_estado_idx on mayordomo_entidades (tipo, estado);
create index mayordomo_entidades_atributos_gin on mayordomo_entidades using gin (atributos);

create table mayordomo_relaciones (
    id                  uuid primary key default gen_random_uuid(),
    entidad_origen_id   uuid not null references mayordomo_entidades(id),
    tipo_relacion       text not null,
    entidad_destino_id  uuid not null references mayordomo_entidades(id),
    creado_en           timestamptz not null default now()
);

create index mayordomo_relaciones_origen_idx on mayordomo_relaciones (entidad_origen_id);
create index mayordomo_relaciones_destino_idx on mayordomo_relaciones (entidad_destino_id);

-- Schemas/Events.md -- el evento es su propia estructura (no una entidad generica), incluye los
-- campos "criticos" (requiere_aprobacion / aprobado_por) siempre presentes y nulos cuando no aplican.
create table mayordomo_eventos (
    id                      uuid primary key default gen_random_uuid(),
    usuario_id              text not null,
    tipo                    text not null,          -- catalogo cerrado, ver Schemas/Events.md
    ocurrido_en             timestamptz not null,
    modulo_origen           text not null,
    contexto                jsonb not null default '{}'::jsonb,
    entidades_relacionadas  uuid[] default '{}',
    resultado               text,
    estado                  text not null default 'emitido', -- emitido | procesado | fallido
    requiere_aprobacion     boolean not null default false,
    aprobado_por            text
);

create index mayordomo_eventos_tipo_idx on mayordomo_eventos (tipo);
create index mayordomo_eventos_ocurrido_en_idx on mayordomo_eventos (ocurrido_en desc);
create index mayordomo_eventos_pendientes_idx on mayordomo_eventos (requiere_aprobacion)
    where requiere_aprobacion = true and aprobado_por is null;

-- Permissions.md: cada evaluacion de Policy Engine (aqui, el Switch de autonomia en n8n) se
-- persiste como evento policy.evaluated con contexto = {accion, modulo_solicitante,
-- nivel_autonomia_requerido, nivel_autonomia_concedido, resultado}. No hace falta tabla aparte:
-- es un insert en mayordomo_eventos.

-- raiz_id es NOT NULL pero nunca hace falta rellenarlo a mano: este trigger lo copia de id en
-- cualquier INSERT que lo deje en null (la primera version de una entidad siempre es su propia
-- raiz). Evita el patron fragil de "INSERT + UPDATE en el mismo WITH" -- el INSERT por si solo ya
-- viola el NOT NULL antes de que el UPDATE llegue a correr.
create or replace function mayordomo_fijar_raiz_id() returns trigger as $$
begin
  if new.raiz_id is null then
    new.raiz_id := new.id;
  end if;
  return new;
end;
$$ language plpgsql;

create trigger mayordomo_entidades_raiz_id_trigger
  before insert on mayordomo_entidades
  for each row execute function mayordomo_fijar_raiz_id();

-- Router Jev: cada fila es una "ruta" (categoria de mensaje) que Jev puede elegir. Anadir una
-- ruta nueva es una fila nueva aqui + su sub-workflow en n8n -- nunca hay que tocar el prompt de
-- un clasificador ni recablear el principal. `descripcion` es literalmente lo que se le pasa a
-- Jev como criterio con nombre (su `choice` elige una de estas claves, ver conversacion 2026-10-23).
create table mayordomo_rutas (
    ruta_id     text primary key,
    descripcion text not null,
    activa      boolean not null default true,
    creado_en   timestamptz not null default now()
);

insert into mayordomo_rutas (ruta_id, descripcion) values
('agendar', 'el mensaje pide o informa de algo con fecha Y hora concretas (cita, reunion, evento)'),
('recordatorio_sin_hora', 'el mensaje menciona una fecha concreta pero sin hora (cumpleanos, plazo, aniversario)'),
('consulta_proyecto', 'el mensaje PREGUNTA por el estado de uno de los proyectos del usuario (Levstamp, Tu Home Office, Wedding Planner Pro, JARVIS) -- es una pregunta, no informa de nada nuevo'),
('actualizar_proyecto', 'el mensaje INFORMA de un avance ya ocurrido, O de algo nuevo que queda pendiente/falta hacer, en uno de los 4 proyectos (Levstamp, Tu Home Office, Wedding Planner Pro, JARVIS) -- no es una pregunta, es una noticia de que algo paso o de algo que falta'),
('memoria_general', 'cualquier otra cosa: preferencias, objetivos, tareas sueltas, decisiones, estado del dia, confirmaciones de tareas completadas, o charla sin informacion que guardar');

comment on table mayordomo_rutas is 'Catalogo de rutas del router Jev. Nueva categoria = nueva fila + su sub-workflow, sin tocar el principal.';

-- Banco de preguntas personales para el briefing diario. Cada mañana se eligen 2-3 sin preguntar
-- todavia; al elegirlas se marcan preguntada=true para no repetirlas. Anadir mas preguntas aqui
-- en cualquier momento, sin tocar ningun workflow.
create table mayordomo_preguntas_personales (
    id               uuid primary key default gen_random_uuid(),
    pregunta         text not null,
    preguntada       boolean not null default false,
    fecha_preguntada timestamptz
);

insert into mayordomo_preguntas_personales (pregunta) values
('¿Haces ejercicio o actividad física de forma regular? ¿Cuál?'),
('¿Tienes alguna afición o hobby fuera del trabajo que te relaje de verdad?'),
('¿Cómo sueles dormir — horas, calidad? ¿Te preocupa algo de tu descanso?'),
('¿Tienes hermanos? ¿Mantienes relación cercana con tu familia?'),
('¿Qué tipo de música, podcasts o contenido consumes para desconectar?'),
('¿Tienes alguna meta personal (no de proyecto ni trabajo) para este año?'),
('¿Cómo te gusta celebrar cuando consigues algo importante?'),
('¿Hay algo que te estrese de forma recurrente que no hayamos hablado todavía?'),
('¿Sigues alguna rutina de alimentación en particular?'),
('¿Tienes mascotas?'),
('¿En qué ciudad/zona vives? ¿Te gustaría quedarte ahí a largo plazo?'),
('¿Hay alguna app o herramienta que uses a diario y que no hayamos mencionado?');

comment on table mayordomo_entidades is 'Nucleo comun de Schemas/Entities.md. atributos guarda los campos propios de cada tipo.';
comment on table mayordomo_eventos is 'Estructura de Schemas/Events.md. Un evento con estado=fallido nunca se borra (Constitution Art. 5).';
