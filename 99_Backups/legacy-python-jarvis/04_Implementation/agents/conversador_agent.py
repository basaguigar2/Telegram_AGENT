"""
Conversador Agent v1.0 (AgentFramework.md -- contrato de agente)

Misión: responder con razonamiento libre a todo lo que sea charla, pregunta
general u opinión -- lo que el CEO Agent no reconoce como una acción concreta
del catálogo. Es la opción intermedia que el usuario eligió explícitamente
frente a "todo router" o "todo libre" (RelacionConAGENTE.md): las acciones
reales (crear un agente, publicar, ejecutar algo) siguen pasando por el
catálogo fijo y Policy Engine -- esto es solo para hablar.

Responsabilidades: reunir contexto relevante de memoria (objetivos activos,
conocimiento reciente, decisiones pendientes) y responder con el modelo
local, dejando claro cuando no tiene información en vez de inventarla.

Límites: nunca ejecuta nada, nunca crea ni modifica ninguna entidad de
memoria -- solo lee contexto y devuelve texto. Por eso no pasa por Policy
Engine (no hay nada que autorizar).

Nivel de autonomía: 0 (Informativo puro) -- ver AgentFramework.md.
"""

import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
sys.path.append(str(Path(__file__).parent.parent / "model_router"))
import memory_engine as me   # noqa: E402
import model_router          # noqa: E402

MODEL_NIVEL_2 = model_router.modelo(2)  # conversar bien se beneficia del modelo más capaz
AUTONOMY_LEVEL = 0

PROMPT_CONVERSAR = """Eres JARVIS, el asistente personal del usuario. Esto es una
charla libre -- no una acción del sistema -- así que responde con tu propio
razonamiento, en español, de forma natural y directa, como si hablaras con
alguien que conoces.

Contexto real disponible sobre el usuario y su sistema (úsalo si ayuda a la
respuesta, ignóralo si no es relevante para este mensaje en concreto):
{contexto}

Reglas:
- Si el contexto no tiene la información que hace falta para responder bien,
  dilo abiertamente en vez de inventarte datos, cifras o hechos.
- No prometas ejecutar ninguna acción real (crear algo, publicar, modificar
  el sistema) -- si el usuario quiere eso, dile que te lo pida de forma más
  directa para que se enrute a la acción correcta.
- Responde en pocas frases, sin relleno.

Mensaje del usuario: {mensaje}
"""


def _contexto_texto() -> str:
    try:
        objetivos = me.active_goals()
        conocimiento = me.recent_knowledge(limit=5)
        pendientes = me.pending_decisions()
    except Exception:  # noqa: BLE001 -- conversar no debe romperse por un fallo de memoria
        return "(sin contexto disponible)"

    lineas = []
    if objetivos:
        lineas.append("Objetivos activos: " + ", ".join(g["name"] for g in objetivos[:5]))
    if conocimiento:
        lineas.append("Conocimiento reciente: " + "; ".join(
            f"{k['name']} ({k['topic']})" for k in conocimiento))
    if pendientes:
        lineas.append(f"Decisiones pendientes sin resolver: {len(pendientes)}")
    return "\n".join(lineas) if lineas else "(sin contexto todavía)"


def run(mensaje: str) -> dict:
    """Responde en lenguaje libre a partir del mensaje y el contexto de memoria.
    Nunca ejecuta nada ni escribe en memoria -- solo lee y devuelve texto."""
    prompt = PROMPT_CONVERSAR.format(contexto=_contexto_texto(), mensaje=mensaje)
    try:
        response = ollama.chat(model=MODEL_NIVEL_2, messages=[{"role": "user", "content": prompt}])
        respuesta = response["message"]["content"].strip()
    except Exception as e:  # noqa: BLE001 -- un fallo del modelo no debe tirar el bot
        respuesta = f"No he podido pensar una respuesta ahora mismo ({e})."
    return {"respuesta": respuesta or "No se me ha ocurrido nada -- prueba a reformularlo."}
