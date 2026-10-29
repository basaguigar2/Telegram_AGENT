"""
Investigador Agent v1.0 (AgentFramework.md -- contrato de agente)

Misión: proponer temas de artículos nuevos para la línea de negocio de
contenido de afiliados (AGENTE, segunda vía -- "mismos 3 agentes:
Investigador, Generador, Seguimiento, sin el filtro de marca/moat").
Completa el trío junto a generador_agent.py y seguimiento_agent.py.

Limitación real y deliberada: Ollama corre sin conexión a internet, así
que este agente NUNCA puede confirmar qué se vende de verdad ahora mismo
ni qué palabras clave tienen búsquedas reales -- solo propone ideas a
partir de lo que el modelo ya sabe (mismo principio que Creative Agent al
proponer ideas de agentes). Toda idea generada así queda marcada
`source="investigador_agent"` y con una nota explícita de que no está
verificada contra datos de mercado reales, para que Seguimiento y el
usuario nunca la confundan con una investigación real. Cuando la
investigación sí viene de una fuente real (ej. una búsqueda web hecha por
Claude en el chat de arquitectura), se registra con `source` distinto
-- ver `crear_tarea_idea(..., source=...)`.

Responsabilidades: generar ideas de tema + ángulo + justificación;
convertir una idea (propia o externa) en una Tarea en fase 'idea' del
tablero de negocio.

Búsqueda real (opcional): si `config/config.json` tiene una clave de Brave
Search API, `investigar_con_busqueda_real()` complementa el brainstorm de
Ollama con resultados de búsqueda web reales -- Ollama sigue sin tener
internet, pero JARVIS (este módulo, en Python) sí puede llamar a una API
externa con `requests`, exactamente igual que ya hace `telegram_bot/bot.py`
con la API de Telegram. Cada idea nacida así lleva su `fuente_url` real y
`source='investigador_agent_busqueda_real'`, para no confundirla nunca con
una idea sin verificar.

Límites: nunca escribe el artículo (eso es Generador Agent). Nunca decide
qué tema es "el mejor" -- solo propone, el usuario elige qué pasa a
producción. `investigar_con_busqueda_real` nunca inventa un tema que no
esté anclado a un resultado de búsqueda real concreto -- si Brave no
devuelve nada útil, devuelve menos temas en vez de rellenar con invención.

Nivel de autonomía: 1 (Asistido) -- solo genera texto, nunca actúa.
"""

import json
import sys
from pathlib import Path

import ollama
import requests

sys.path.append(str(Path(__file__).parent.parent / "model_router"))
sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
import model_router  # noqa: E402
import memory_engine as me  # noqa: E402

MODEL_NIVEL_2 = model_router.modelo(2)
AUTONOMY_LEVEL = 1
BUSINESS_LINE = "contenido_afiliados"
NICHO = "home office (mobiliario, ergonomía y equipamiento para trabajar desde casa)"

CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.json"
BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

PROMPT_INVESTIGADOR = f"""Eres el Investigador Agent de JARVIS para un blog de {NICHO}.

Propón {{n}} temas de artículo NUEVOS y distintos entre sí, evitando genéricos
ya muy trillados salvo que le des un ángulo concreto. Para cada uno da:
- "tema": título de trabajo, corto y claro.
- "angulo": qué lo hace específico (ej. "para espacios pequeños", "para
  quienes teletrabajan con videollamadas todo el día"), no genérico.
- "justificacion": una frase de por qué un lector de este nicho lo buscaría.

No inventes cifras de ventas, tendencias "virales" ni datos de mercado --
no tienes acceso a esa información. Basa cada idea solo en necesidades
razonables y conocidas del nicho, dicho como tal (una hipótesis razonable,
no un hecho verificado).

Responde EXCLUSIVAMENTE con un JSON válido, sin texto adicional:

{{{{
  "temas": [
    {{{{"tema": "...", "angulo": "...", "justificacion": "..."}}}}
  ]
}}}}
"""


def investigar(n_temas: int = 5) -> list[dict]:
    """
    Genera n_temas ideas de artículo. Devuelve lista de dicts con 'tema',
    'angulo', 'justificacion'. Lista vacía si el modelo falla -- nunca se
    inventan ideas de relleno ante una respuesta rara (mismo principio que
    creative_agent.brainstorm).
    """
    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{"role": "user", "content": PROMPT_INVESTIGADOR.format(n=n_temas)}],
        format="json",
    )
    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
        temas = data.get("temas", [])
        return [
            {
                "tema": str(t.get("tema", "")).strip(),
                "angulo": str(t.get("angulo", "")).strip(),
                "justificacion": str(t.get("justificacion", "")).strip(),
            }
            for t in temas
            if t.get("tema")
        ]
    except (json.JSONDecodeError, AttributeError):
        return []


def crear_tarea_idea(tema: str, justificacion: str, angulo: str | None = None,
                      source: str = "investigador_agent", fuente_url: str | None = None) -> str:
    """
    Convierte un tema (propio o de una investigación externa real) en una
    Tarea de negocio en fase 'idea'. `source` distingue una idea sin
    verificar de Ollama (source='investigador_agent', el valor por defecto)
    de una investigación real -- de búsqueda real
    (source='investigador_agent_busqueda_real', con `fuente_url`) o hecha
    por Claude (ej. 'claude_websearch_2026-08-31'). Esa distinción es la
    que permite confiar más en unas ideas que en otras al revisar el tablero.
    """
    descripcion = justificacion
    if angulo:
        descripcion = f"{justificacion} (ángulo: {angulo})"
    if fuente_url:
        descripcion += f" [fuente real: {fuente_url}]"
    elif source == "investigador_agent":
        descripcion += " -- idea sin verificar contra datos de mercado reales."

    return me.create_task(
        name=tema,
        description=descripcion,
        business_line=BUSINESS_LINE,
        business_phase="idea",
        priority="operativo",
        source=source,
    )


def _brave_api_key() -> str | None:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            clave = json.load(f).get("brave_api_key")
    except FileNotFoundError:
        return None
    if not clave or clave == "PON_AQUI_TU_CLAVE_DE_BRAVE_SEARCH_API":
        return None
    return clave


def buscar_web(query: str, n_resultados: int = 5) -> list[dict]:
    """
    Busca en Brave Search API (JARVIS en Python llamando a una API externa
    con requests -- Ollama no interviene aquí, no necesita internet para
    esto). Devuelve lista de {'titulo', 'url', 'descripcion'}.

    Lanza ValueError con un mensaje claro si falta configurar la clave --
    quien llame (ej. bot.py) debe mostrárselo tal cual al usuario en vez de
    fallar en silencio o inventar resultados.
    """
    clave = _brave_api_key()
    if not clave:
        raise ValueError(
            f"Falta configurar 'brave_api_key' en {CONFIG_PATH} -- copia "
            f"config.example.json a config.json en esa misma carpeta y pon "
            f"tu clave real de https://api.search.brave.com/."
        )

    respuesta = requests.get(
        BRAVE_ENDPOINT,
        headers={"Accept": "application/json", "X-Subscription-Token": clave},
        params={"q": query, "count": n_resultados},
        timeout=15,
    )
    respuesta.raise_for_status()
    resultados = respuesta.json().get("web", {}).get("results", [])
    return [
        {
            "titulo": r.get("title", ""),
            "url": r.get("url", ""),
            "descripcion": r.get("description", ""),
        }
        for r in resultados[:n_resultados]
    ]


PROMPT_BUSQUEDA_REAL = f"""Eres el Investigador Agent de JARVIS para un blog de {NICHO}.

Aquí abajo tienes resultados REALES de una búsqueda web sobre "{{query}}",
numerados. Para cada uno, propón un título de artículo de blog y un ángulo
concreto basados ÚNICAMENTE en lo que dice ese resultado -- no añadas
información que no esté en su título o descripción, no inventes cifras
nuevas. Si un resultado no da pie a un buen tema, sáltalo (mejor menos
temas que uno forzado).

Resultados:
{{resultados}}

Responde EXCLUSIVAMENTE con un JSON válido, con esta forma exacta -- un
elemento por CADA índice que sí uses, "indice" debe coincidir con el
número del resultado de arriba:

{{{{
  "temas": [
    {{{{"indice": 0, "tema": "...", "angulo": "..."}}}}
  ]
}}}}
"""


def investigar_con_busqueda_real(query: str, n_temas: int = 5) -> list[dict]:
    """
    Busca de verdad en internet (Brave) y le pide a Ollama que convierta
    cada resultado real en un tema de artículo con su ángulo -- nunca al
    revés (nunca se le pide a Ollama que "busque", solo que redacte a
    partir de datos ya reales). Devuelve lista de {'tema', 'angulo',
    'justificacion', 'fuente_url'}. Lista vacía si Brave no devuelve nada
    o si Ollama no logra anclar ningún tema a un resultado real.
    """
    resultados = buscar_web(query, n_resultados=n_temas)
    if not resultados:
        return []

    resultados_texto = "\n".join(
        f"{i}. {r['titulo']} -- {r['descripcion']} ({r['url']})"
        for i, r in enumerate(resultados)
    )
    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{"role": "user", "content": PROMPT_BUSQUEDA_REAL.format(
            query=query, resultados=resultados_texto)}],
        format="json",
    )
    raw = response["message"]["content"]

    try:
        data = json.loads(raw)
        temas_crudos = data.get("temas", [])
    except (json.JSONDecodeError, AttributeError):
        return []

    temas = []
    for t in temas_crudos:
        try:
            idx = int(t.get("indice"))
            fuente = resultados[idx]
        except (TypeError, ValueError, IndexError):
            continue  # índice inventado o fuera de rango -- se descarta, no se adivina
        tema = str(t.get("tema", "")).strip()
        if not tema:
            continue
        temas.append({
            "tema": tema,
            "angulo": str(t.get("angulo", "")).strip(),
            "justificacion": fuente["descripcion"] or fuente["titulo"],
            "fuente_url": fuente["url"],
        })
    return temas


def run(n_temas: int = 5) -> list[dict]:
    """Uso desde CLI/orchestrator: solo propone (brainstorm), no crea tareas por su cuenta."""
    return investigar(n_temas)


def run_busqueda_real(query: str, n_temas: int = 5) -> list[dict]:
    """Uso desde CLI/orchestrator para la variante con búsqueda real."""
    return investigar_con_busqueda_real(query, n_temas)
