"""
CEO Agent v1.0 (AgentFramework.md -- contrato de agente)

Misión: ser el único punto de entrada natural de JARVIS. El usuario le
habla a este agente y nada más -- el CEO decide a qué agente le toca
atender el mensaje, leyendo el catálogo vivo de agentes disponibles
(orchestrator.AGENTES_CEO) en vez de tener la lista de intenciones
incrustada a mano en un prompt (eso era intent_router.py -- este agente
lo sustituye como punto de entrada; añadir un agente nuevo al sistema
pasa a ser una línea en el catálogo, no un prompt nuevo).

Responsabilidades: leer el mensaje del usuario, decidir cuál de los
agentes del catálogo debe atenderlo, y pasarle el texto (reformulado con
claridad si hace falta).

Límites: el CEO nunca ejecuta nada él mismo y nunca se salta la
confirmación de cada agente -- solo decide "a quién". Todo lo que pase
después sigue el mismo camino de siempre (Policy Engine, confirmaciones
en Telegram, registro de eventos). Esto es a propósito: dar más poder de
decisión al enrutador no debe traducirse en menos control humano sobre
lo que se ejecuta (Constitution.md Art. 10).

Nivel de autonomía: 1 (Asistido) -- solo decide a quién delegar, nunca actúa.
"""

import json
import re
import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).parent.parent / "orchestrator"))
sys.path.append(str(Path(__file__).parent.parent / "model_router"))
sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
import orchestrator as orch  # noqa: E402
import model_router  # noqa: E402
import memory_engine as me  # noqa: E402

MODEL_NIVEL_2 = model_router.modelo(2)  # el enrutado se beneficia del modelo más grande según crezca el catálogo
AUTONOMY_LEVEL = 1

# Respaldo determinista para el eje que más se ha equivocado el modelo local
# hasta ahora (agente confundido con "codigo" o "estrategico"). En vez de
# fiarlo todo al prompt, si el mensaje pide explícitamente crear un agente
# (verbo de creación + la palabra "agente"), se decide aquí mismo sin pasar
# por el modelo -- ni más rápido ni más caro, y no hay margen de error en
# este caso concreto (mismo principio que is_safe_to_execute en Builder
# Agent: una regla de texto fiable donde el modelo ya ha fallado dos veces).
_VERBOS_CREACION = r"(?:genera|gener[ae]me|cr[eé]a(?:me)?|haz(?:me)?|mont[ae](?:me)?|quiero|necesito|constru(?:ye|yeme))"
_PATRON_AGENTE_EXPLICITO = re.compile(rf"{_VERBOS_CREACION}\w*\s+(?:un\s+)?agente\b", re.IGNORECASE)

# Segundo eje donde el modelo local se ha equivocado en pruebas reales:
# confunde "investigar" (temas de CONTENIDO para el blog) con "ideas" (ideas
# de AGENTES de software), incluso variando la respuesta entre ejecuciones
# idénticas -- el prompt (reglas 1-3 arriba) no basta de forma fiable con un
# modelo de 8B. Mismo remedio que _PATRON_AGENTE_EXPLICITO: una regla de
# texto determinista en vez de confiar el eje entero al modelo.
_PATRON_INVESTIGAR_CONTENIDO = re.compile(
    r"investig(?:a|ame|ar)\w*|"
    r"(?:tema|temas).*(?:blog|art[ií]culo|contenido|escribir)|"
    r"(?:blog|art[ií]culo|contenido).*(?:tema|temas|idea|ideas)|"
    r"qu[eé]\s+(?:podr[ií]a\s+)?escribir|"
    r"qu[eé]\s+tema",
    re.IGNORECASE,
)

# Tercer eje: "buscar" (búsqueda real en internet vía Brave) se confundiría
# con "investigar" (brainstorm sin verificar) porque ambos comparten la
# palabra "investigar" -- se distingue por llevar además una señal
# explícita de que se quiere algo real ("internet", "de verdad", "real").
# Se comprueba ANTES que _PATRON_INVESTIGAR_CONTENIDO en decide().
_PATRON_BUSQUEDA_REAL = re.compile(
    r"busc(?:a|ame|ar)\w*.*(?:internet|real|de verdad)|"
    r"(?:internet|real|de verdad).*busc(?:a|ame|ar)?\w*|"
    r"investig(?:a|ame|ar)\w*.*(?:de verdad|real)|(?:de verdad|real).*investig",
    re.IGNORECASE,
)

PROMPT_CEO = """Eres el CEO Agent de JARVIS, un sistema personal. Tu único trabajo es
decidir qué agente del equipo debe atender el mensaje del usuario -- nunca
respondes tú directamente ni ejecutas nada.

Agentes disponibles ahora mismo:
{catalogo}

Contexto reciente del usuario (Memory Engine -- úsalo para desambiguar si
ayuda, ignóralo si no es relevante para este mensaje en concreto):
{contexto}

Reglas importantes para no confundirte:

1. Si el usuario pide CONSTRUIR o GENERAR algo (un agente, un script), eso
   siempre gana sobre cualquier otra lectura, incluso si el tema de lo que
   pide construir es el propio JARVIS o su funcionamiento interno. "créame
   un agente que explique cómo funciona JARVIS" sigue siendo "quiero que
   construyas un agente", no una pregunta sobre el rumbo del proyecto.

2. Si la palabra "agente" aparece en el mensaje pidiendo crearlo/generarlo
   (con cualquier verbo: genera, créame, hazme, quiero, necesito, monta...),
   la categoría es SIEMPRE "agente", nunca "codigo". No lo trates como un
   script suelto solo porque la tarea suene a algo automatizable -- si dice
   "agente", es "agente".

3. "ideas" es SOLO para ideas de AGENTES nuevos de JARVIS (software que
   construir, ej. "un agente que...", "qué agentes podría crear"). Si el
   mensaje pregunta qué ESCRIBIR, qué TEMA tratar, o menciona "artículo",
   "contenido" o "blog" de cualquier forma (ej. "dame ideas de temas para
   el blog", "qué podría escribir después", "qué tema toco ahora"), es
   SIEMPRE "investigar", nunca "ideas" -- la señal es si se trata de temas
   de contenido para escribir, no de software para construir.

4. "buscar" es para cuando el usuario pide explícitamente una búsqueda REAL
   en internet (menciona "internet", "buscar/búscame", "de verdad" o
   "real" junto a la petición). "investigar" sin esa señal es solo
   brainstorm del modelo, sin verificar nada -- no confundas ambas.

5. "nota" es SOLO cuando el usuario pide explícitamente guardar/recordar/
   apuntar algo. Cualquier charla, pregunta abierta u opinión que no pida
   guardar nada ni encaje en otra categoría de la lista es "conversar" --
   nunca la trates como "nota" solo por no saber clasificarla.

Mensaje del usuario: {mensaje}

Responde EXCLUSIVAMENTE con un JSON válido, sin texto adicional:

{{
  "agente": "clave exacta de uno de los agentes de la lista de arriba",
  "texto": "el mensaje del usuario, reformulado con claridad si hace falta -- esto es lo que recibirá ese agente"
}}

Si dudas entre varios, o el mensaje no encaja claramente en ninguno, usa "conversar"
-- nunca inventes una clave que no esté en la lista de arriba.
"""


def _catalogo_texto() -> str:
    # AGENTES_CEO es un Capability Registry estructurado (Schemas/CapabilityRegistry.md)
    # -- el CEO solo necesita la descripción para decidir, el resto (entradas,
    # salidas, herramientas, autonomy_level) es para auditoría y para
    # orchestrator_integrator.py, no para este prompt.
    return "\n".join(f"- \"{clave}\": {info['descripcion']}" for clave, info in orch.AGENTES_CEO.items())


def _contexto_texto() -> str:
    """
    Recupera memoria relevante (Modules/CEO.md -- "recuperar memoria
    relevante" es responsabilidad del CEO, no algo que se le pida a cada
    agente por separado). Deliberadamente ligero: solo objetivos activos y
    conocimiento reciente, sin todo el histórico -- esto es contexto para
    desambiguar un mensaje corto, no una base de conocimiento completa.
    Si algo falla al leer memoria, el CEO sigue funcionando sin contexto en
    vez de romperse -- el enrutado no debe depender de que esto no falle.
    """
    try:
        objetivos = me.active_goals()
        conocimiento = me.recent_knowledge(limit=3)
    except Exception:  # noqa: BLE001 -- el enrutado no debe caerse por esto
        return "(sin contexto disponible)"

    lineas = []
    if objetivos:
        lineas.append("Objetivos activos: " + ", ".join(g["name"] for g in objetivos[:5]))
    if conocimiento:
        lineas.append("Conocimiento reciente: " + "; ".join(
            f"{k['topic']}" for k in conocimiento))
    return "\n".join(lineas) if lineas else "(sin contexto todavía)"


def decide(mensaje: str) -> dict:
    """
    Decide a qué agente del catálogo le toca el mensaje. Devuelve
    {'agente': clave, 'texto': texto}. Si el modelo falla o inventa una
    clave que no existe, cae en 'conversar' con el mensaje tal cual --
    fallback seguro sin efectos en memoria (nunca se asume 'codigo',
    'agente' ni 'estrategico' por defecto ante una respuesta rara).
    """
    if "agente" in orch.AGENTES_CEO and _PATRON_AGENTE_EXPLICITO.search(mensaje):
        return {"agente": "agente", "texto": mensaje}

    if "buscar" in orch.AGENTES_CEO and _PATRON_BUSQUEDA_REAL.search(mensaje):
        return {"agente": "buscar", "texto": mensaje}

    if "investigar" in orch.AGENTES_CEO and _PATRON_INVESTIGAR_CONTENIDO.search(mensaje):
        return {"agente": "investigar", "texto": mensaje}

    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{"role": "user", "content": PROMPT_CEO.format(
            catalogo=_catalogo_texto(), contexto=_contexto_texto(), mensaje=mensaje)}],
        format="json",
    )
    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
        agente = data.get("agente")
        if agente not in orch.AGENTES_CEO:
            raise ValueError("agente no reconocido")
        texto = str(data.get("texto") or mensaje).strip()
        return {"agente": agente, "texto": texto or mensaje}
    except (json.JSONDecodeError, ValueError, AttributeError):
        return {"agente": "conversar", "texto": mensaje}
