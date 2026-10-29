"""
Generador Agent v1.0 (AgentFramework.md -- contrato de agente)

Misión: generar un artículo con estructura SEO y una tabla comparativa de
productos con enlaces de afiliado, para la línea de negocio de contenido
(AGENTE, Fase 3.2 -- "Agente Generador (línea WordPress)"), y dejarlo
guardado como borrador para revisión humana.

Nicho y programa de afiliados son constantes editables aquí abajo -- único
lugar del código donde deberían aparecer, mismo principio que MODEL_NIVEL_2
en model_router.py: cambiar de nicho o de programa de afiliados es una
línea, no una reescritura del prompt.

No publica en ningún sitio: todavía no hay un WordPress real conectado
(RelacionConAGENTE.md). El artículo se guarda como Conocimiento (tipo
'articulo_afiliado') y como Tarea de negocio en fase 'borrador_listo' --
cuando exista un sitio real, publicar pasa a ser una acción nueva y
explícita (probablemente de nivel 4, "desplegar", si se automatiza de punta
a punta), no algo que este agente haga por su cuenta.

Límites: nunca inventa datos de producto que no pueda marcar como tal --
los precios y enlaces de afiliado son siempre placeholders explícitos que
el usuario debe rellenar antes de publicar, nunca cifras inventadas
presentadas como reales.

Nivel de autonomía: 1 (Asistido, auto-permitido) -- igual que Capture Agent,
guardar un borrador no es una acción destructiva ni estratégica: se
versiona como Conocimiento y nunca se sobrescribe ni se publica solo.
"""

import sys
from pathlib import Path

import ollama

sys.path.append(str(Path(__file__).parent.parent / "model_router"))
sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
import model_router  # noqa: E402
import memory_engine as me  # noqa: E402

MODEL_NIVEL_2 = model_router.modelo(2)
AUTONOMY_LEVEL = 1
BUSINESS_LINE = "contenido_afiliados"

# Único lugar donde se fija nicho y programa de afiliados -- cambiar de nicho
# no debería requerir tocar el prompt de abajo.
NICHO = "home office (mobiliario, ergonomía y equipamiento para trabajar desde casa)"
PROGRAMA_AFILIADO = "Amazon Afiliados (España)"
PLACEHOLDER_ENLACE = "https://amzn.to/TU-ENLACE-AQUI"
PLACEHOLDER_ID = "TU_ID_DE_AFILIADO"

PROMPT_GENERADOR = f"""Eres el Generador Agent de JARVIS, escribiendo para un blog de {NICHO}.
Programa de afiliados: {PROGRAMA_AFILIADO}.

Tema del artículo: {{tema}}

Escribe un artículo completo en Markdown con esta estructura exacta:

1. Título SEO (una línea, empieza con "# ").
2. Meta descripción (1-2 frases, máximo 160 caracteres, marcada como
   "**Meta descripción:**").
3. Introducción (2-3 párrafos) enganchando al lector con el problema real
   que resuelve el tema, sin inventar estadísticas ni estudios que no
   puedas citar de verdad.
4. Una tabla comparativa en Markdown con 3-5 productos plausibles para el
   tema (nombre genérico de producto, característica clave, para quién es
   ideal, y una columna "Enlace" que en TODAS las filas debe usar
   exactamente el texto "{PLACEHOLDER_ENLACE}" -- nunca inventes una URL
   real ni un precio exacto, usa "Ver precio actual" en vez de una cifra.
5. 2-4 secciones de desarrollo (## encabezados) explicando cómo elegir
   entre las opciones según necesidad real del lector.
6. Conclusión breve con una llamada a la acción genérica (revisar la tabla
   de arriba), sin URLs nuevas.

Reglas estrictas:
- Nunca inventes cifras de precio, ni reseñas de usuarios, ni marcas reales
  con afirmaciones que no puedas sostener -- describe productos de forma
  genérica ("un monitor de 27 pulgadas con ajuste de altura") en vez de
  nombrar una marca concreta con datos que no tienes.
- Todos los enlaces de afiliado deben ser exactamente "{PLACEHOLDER_ENLACE}"
  -- este es un borrador que el usuario completará a mano con sus propios
  enlaces de {PROGRAMA_AFILIADO} antes de publicar.
- Responde EXCLUSIVAMENTE con el artículo en Markdown, sin explicaciones
  antes ni después, sin envolver la respuesta en un bloque de código.
"""


def _limpiar_bloque_markdown(texto: str) -> str:
    if texto.strip().startswith("```"):
        lineas = texto.strip().splitlines()
        if lineas[-1].strip() == "```":
            lineas = lineas[1:-1]
        else:
            lineas = lineas[1:]
        return "\n".join(lineas)
    return texto


def propose(tema: str) -> str:
    """Genera el artículo en Markdown. No guarda nada todavía."""
    response = ollama.chat(
        model=MODEL_NIVEL_2,
        messages=[{"role": "user", "content": PROMPT_GENERADOR.format(tema=tema)}],
    )
    return _limpiar_bloque_markdown(response["message"]["content"])


def save(tema: str, articulo: str) -> dict:
    """
    Guarda el artículo como Conocimiento y crea la Tarea de negocio que lo
    rastrea en el tablero (business_line='contenido_afiliados',
    business_phase='borrador_listo'). Devuelve {'knowledge_id', 'task_id'}.
    """
    kid = me.create_knowledge(
        content=articulo,
        topic=f"artículo afiliados: {tema}"[:80],
        reliability="media",
        source="generador_agent",
    )
    tid = me.create_task(
        name=tema,
        description=f"Artículo de afiliados sobre '{tema}' generado y listo para revisión "
                     f"antes de publicar (enlaces de {PROGRAMA_AFILIADO} son placeholders).",
        business_line=BUSINESS_LINE,
        business_phase="borrador_listo",
        related_knowledge_id=kid,
        priority="operativo",
        source="generador_agent",
    )
    me.create_event(
        event_type="generador.articulo_creado",
        origin_module="generador_agent",
        context={"tema": tema, "knowledge_id": kid, "task_id": tid},
    )
    return {"knowledge_id": kid, "task_id": tid}


def run(tema: str) -> dict:
    """Genera y guarda de una vez. Devuelve el artículo y los ids creados."""
    articulo = propose(tema)
    resultado = save(tema, articulo)
    return {"articulo": articulo, **resultado}
