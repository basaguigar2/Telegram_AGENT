"""
Builder Agent v1.0 (AgentFramework.md — contrato de agente)

Misión: proponer código para una tarea concreta usando el modelo local.
Responsabilidades: generar una propuesta, mostrártela, escribir el archivo
SOLO si confirmas explícitamente, y opcionalmente ejecutarlo si lo confirmas
por separado Y el escaneo de seguridad no detecta patrones peligrosos.
Límites: nunca escribe sobre un archivo sin mostrarte antes el contenido
completo. Nunca ejecuta sin una segunda confirmación explícita, distinta de
la de guardado. Nunca ejecuta código que el escáner marque como sospechoso
(borrado de archivos, red, ejecución de comandos del sistema). No borra
archivos por sí mismo.
Nivel de autonomía: 2 (Supervisado) -- coincide con Schemas/Permissions.md:
"confirmación puntual antes de ejecutar".

Nota sobre calidad: usa el modelo local Nivel 2 (llama3.1:8b, 8B parámetros).
Para tareas de código es notablemente peor que un modelo premium -- espera
revisar y corregir lo que proponga, no lo trates como código final.
Si más adelante quieres mejor calidad sin subir de nivel de modelo, puedes
probar un modelo especializado en código (ej. `ollama pull qwen2.5-coder:7b`)
y cambiar MODEL_NIVEL_2 abajo.
"""

import re
import subprocess
import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).parent.parent / "model_router"))
import model_router  # noqa: E402

MODEL_NIVEL_2 = model_router.modelo(2)
AUTONOMY_LEVEL = 2
TIMEOUT_EJECUCION_SEGUNDOS = 30

# Patrones que bloquean la ejecución automática (no la escritura -- eso ya
# está controlado por la confirmación de guardado). Es un escaneo por texto,
# no un sandbox real: reduce el riesgo obvio, no lo elimina. Si el código
# hace algo peligroso de forma disimulada, esto no lo va a pillar.
PATRONES_PELIGROSOS = {
    "borrado de archivos": [
        r"os\.remove\(", r"os\.rmdir\(", r"shutil\.rmtree\(",
        r"\.unlink\(", r"send2trash",
    ],
    "ejecución de comandos del sistema": [
        r"os\.system\(", r"subprocess\.", r"os\.popen\(", r"\beval\(", r"\bexec\(",
    ],
    "acceso de red": [
        r"\brequests\.", r"urllib\.", r"\bsocket\.", r"http\.client",
        r"ftplib\.", r"smtplib\.",
    ],
}

# Referencia real del sistema para que el modelo deje de inventarse tablas o
# funciones que no existen (esto es justo lo que falló con el primer script
# de decisiones pendientes -- se inventó una tabla "decisiones" que no
# existía). Si el script necesita tocar memoria, base de datos o agentes,
# esto le da la forma real a la que debe ajustarse.
CONTEXTO_JARVIS = """
Referencia real de JARVIS (no inventes nombres distintos a estos):

Base de datos: SQLite en 04_Implementation/db/jarvis.db.
Tablas reales (Schemas/Entities.md, db/schema.sql): user, goal, project, task,
resource, knowledge, decision, rule, insight, event, relationship.
NUNCA uses nombres de tabla distintos a estos (ej. nunca "decisiones", usa "decision").

Si la tarea necesita leer o guardar información, usa SIEMPRE memory_engine
en vez de tocar SQLite directamente. Para importarlo desde un script en
04_Implementation/scripts/:

    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
    import memory_engine as me

Funciones ya disponibles en memory_engine (no las reinventes):
    me.create_knowledge(content, topic, reliability, source) -> id
    me.get_knowledge(id) -> dict | None
    me.list_knowledge(topic=None, status=None) -> list[dict]
    me.validate_knowledge(id)
    me.update_knowledge(id, **cambios) -> nuevo_id
    me.archive_knowledge(id)
    me.get_history(id) -> list[dict]
    me.create_decision(context, reason, alternatives=None, related_goal_id=None, source=...) -> id
    me.resolve_decision(id, result)  # result: 'aceptada' | 'rechazada'
    me.pending_decisions() -> list[dict]
    me.active_goals() -> list[dict]
    me.recent_knowledge(limit=10) -> list[dict]
    me.create_event(event_type, origin_module, context, outcome=None, requires_approval=False) -> id
"""

PROMPT_BUILDER = """Eres el Builder Agent de JARVIS, un sistema personal.
Tu única tarea es escribir el código para lo que se te pide a continuación.

{contexto_jarvis}

Tarea: {task_description}

Archivo destino: {target_file}

Contenido actual del archivo (vacío si es nuevo):
---
{existing_content}
---

Responde EXCLUSIVAMENTE con el contenido completo y final que debería tener
el archivo después del cambio. No incluyas explicaciones, no incluyas
markdown de bloque de código (```), no incluyas nada antes ni después --
solo el contenido del archivo tal cual debe quedar guardado.
"""


def _limpiar_bloque_markdown(texto: str) -> str:
    """El modelo a veces envuelve la respuesta en ```...``` pese a que se le pide que no lo haga."""
    if texto.strip().startswith("```"):
        lineas = texto.strip().splitlines()
        if lineas[-1].strip() == "```":
            lineas = lineas[1:-1]
        else:
            lineas = lineas[1:]
        return "\n".join(lineas)
    return texto


def propose(task_description: str, target_file: str) -> str:
    """Pide al modelo local el contenido propuesto para target_file. No escribe nada."""
    target_path = Path(target_file)
    existing = target_path.read_text(encoding="utf-8") if target_path.exists() else ""

    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{
            "role": "user",
            "content": PROMPT_BUILDER.format(
                contexto_jarvis=CONTEXTO_JARVIS,
                task_description=task_description,
                target_file=target_file,
                existing_content=existing or "(archivo nuevo, no existe todavía)",
            ),
        }],
    )
    return _limpiar_bloque_markdown(response["message"]["content"])


PROMPT_AGENTE = """Eres el Builder Agent de JARVIS, un sistema personal.
Vas a crear un AGENTE nuevo, no un script suelto. Un agente en JARVIS sigue
siempre el mismo contrato (ver Modules/AgentFramework.md):

{contexto_jarvis}

Todo agente debe tener esta forma exacta:

    \"\"\"
    <Nombre> Agent v1.0 (AgentFramework.md -- contrato de agente)

    Misión: <una frase>.
    Responsabilidades: <lista breve>.
    Límites: <qué NUNCA debe hacer este agente>.
    Nivel de autonomía: 2 (Supervisado) -- requiere confirmación antes de ejecutar
    (Schemas/Permissions.md).
    \"\"\"

    AUTONOMY_LEVEL = 2

    def run(**kwargs) -> dict:
        # la lógica del agente. Debe devolver un dict con el resultado.
        ...

Tarea que debe cumplir este agente: {task_description}

Nombre de archivo: {target_file}

Responde EXCLUSIVAMENTE con el contenido completo del archivo Python del
agente, siguiendo exactamente esa forma. No incluyas explicaciones, no
incluyas markdown de bloque de código (```), no incluyas nada antes ni
después -- solo el contenido del archivo.
"""


def propose_agent(task_description: str, agent_name: str, target_file: str) -> str:
    """Pide al modelo local un agente nuevo siguiendo el contrato de AgentFramework.md."""
    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{
            "role": "user",
            "content": PROMPT_AGENTE.format(
                contexto_jarvis=CONTEXTO_JARVIS,
                task_description=task_description,
                target_file=target_file,
            ),
        }],
    )
    return _limpiar_bloque_markdown(response["message"]["content"])


def checklist_integracion(agent_name: str, target_file: str) -> str:
    """
    Fallback de referencia manual. Desde que existe
    orchestrator/orchestrator_integrator.py, telegram_bot/bot.py ya no llama
    a esto en el flujo normal: la integración (import + REGISTRY +
    AGENTES_CEO) se propone y aplica de forma automática, con tu
    confirmación explícita, en cuanto guardas el agente. Esta función se
    deja aquí solo para el caso en que la integración automática falle
    (ej. orchestrator.py no tiene el patrón esperado) y haga falta hacerlo
    a mano.
    """
    modulo = Path(target_file).stem
    return (
        f"Archivo creado: {target_file}\n\n"
        f"Para que quede integrado de verdad, todavía falta (esto tenéis que "
        f"hacerlo tú y Claude juntos, no yo solo):\n\n"
        f"1. Revisar el código -- el modelo local se equivoca a menudo.\n"
        f"2. En orchestrator.py, añadir:\n"
        f"   import {modulo}\n"
        f"   y una entrada nueva en REGISTRY, ej:\n"
        f'   "accion_nueva": ({modulo}.run, {modulo}.AUTONOMY_LEVEL)\n'
        f"3. Si quieres invocarlo por lenguaje natural, añadir una intención "
        f"nueva en intent_router.py.\n"
        f"4. Probarlo con una tarea real antes de confiar en él.\n\n"
        f"Trae este archivo al chat con Claude para hacer estos pasos con cuidado."
    )


def write(target_file: str, content: str) -> None:
    """Escribe content en target_file. Sin confirmación propia -- quien llama debe haberla obtenido."""
    target_path = Path(target_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(content, encoding="utf-8")


def is_safe_to_execute(code: str) -> tuple[bool, list[str]]:
    """
    Escanea el código en busca de patrones de riesgo evidente antes de
    permitir ejecutarlo. Devuelve (es_seguro, lista_de_motivos_de_bloqueo).
    No es un sandbox -- es una primera barrera, no la única que debería
    existir si esto crece más adelante.
    """
    motivos = []
    for categoria, patrones in PATRONES_PELIGROSOS.items():
        for patron in patrones:
            if re.search(patron, code):
                motivos.append(categoria)
                break
    return (len(motivos) == 0, motivos)


def execute(target_file: str) -> dict:
    """
    Ejecuta target_file con Python, con límite de tiempo, y captura la
    salida. Quien llama debe haber comprobado is_safe_to_execute() y haber
    obtenido confirmación explícita antes de llamar a esto -- esta función
    no vuelve a preguntar.
    """
    try:
        resultado = subprocess.run(
            [sys.executable, target_file],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_EJECUCION_SEGUNDOS,
        )
        return {
            "ejecutado": True,
            "timeout": False,
            "returncode": resultado.returncode,
            "stdout": resultado.stdout,
            "stderr": resultado.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "ejecutado": False,
            "timeout": True,
            "returncode": None,
            "stdout": "",
            "stderr": f"Cancelado tras {TIMEOUT_EJECUCION_SEGUNDOS}s sin terminar (posible bucle infinito).",
        }


def run(task_description: str, target_file: str) -> dict:
    """
    Uso desde CLI: propone código, lo muestra por consola, y solo escribe el
    archivo si el usuario confirma explícitamente ahí mismo.
    """
    propuesto = propose(task_description, target_file)

    print(f"\n--- Propuesta del Builder Agent para: {target_file} ---\n")
    print(propuesto)
    print("\n--- fin de la propuesta ---\n")

    confirmacion = input("¿Guardar este contenido en el archivo? (s/n): ").strip().lower()
    if confirmacion != "s":
        return {"written": False, "target_file": target_file, "proposed_code": propuesto}

    write(target_file, propuesto)
    return {"written": True, "target_file": target_file, "proposed_code": propuesto}
