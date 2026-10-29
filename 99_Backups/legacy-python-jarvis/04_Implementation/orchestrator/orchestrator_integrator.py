"""
Orchestrator Integrator v1.0

Misión: automatizar el paso mecánico de "añadir un agente ya generado al
Orchestrator" -- import + entrada en REGISTRY + entrada en el catálogo del
CEO Agent (AGENTES_CEO) -- que antes había que hacer a mano. No es un
agente que razone: es edición de texto determinista sobre un archivo con
un formato ya conocido y fijo, no pasa por ningún modelo.

Por qué esto SÍ se puede automatizar sin romper Constitution.md Art. 10:
orchestrator.py sigue siendo un archivo central, así que aplicar_integracion()
solo debe llamarse después de que el usuario haya visto exactamente qué se
va a añadir (proponer_integracion()) y lo haya confirmado explícitamente --
el mismo patrón de "propón, muestra, confirma, entonces escribe" que ya usa
Builder Agent para cualquier archivo. La diferencia es que aquí no hace
falta que un modelo se invente el texto: siempre es el mismo patrón fijo.

Límites: si el archivo no tiene el patrón exacto esperado (bloques
"REGISTRY = {...}" y "AGENTES_CEO = {...}"), no intenta adivinar ni edita
nada -- falla con un error claro para que se revise a mano en vez de
arriesgarse a corromper un archivo central.
"""

import re
from pathlib import Path

ORCHESTRATOR_PATH = Path(__file__).parent / "orchestrator.py"


def _insertar_en_dict(contenido: str, nombre_dict: str, nueva_linea: str) -> str:
    """
    Inserta nueva_linea justo antes del '}' que cierra nombre_dict = {...},
    contando llaves para encontrar el cierre correcto -- necesario desde que
    AGENTES_CEO pasó a ser un Capability Registry estructurado (cada valor
    es a su vez un dict con sus propias llaves anidadas). Una búsqueda
    ingenua del primer "\\n}" se pararía en el cierre de la primera entrada
    anidada, no en el del dict completo.
    """
    marcador = re.search(rf"\b{nombre_dict}\s*=\s*\{{", contenido)
    if not marcador:
        raise ValueError(f"No se encontró el bloque '{nombre_dict} = {{...}}' en orchestrator.py "
                          f"-- no se ha tocado nada, edítalo a mano.")

    profundidad = 0
    cierre = None
    for pos in range(marcador.end() - 1, len(contenido)):
        if contenido[pos] == "{":
            profundidad += 1
        elif contenido[pos] == "}":
            profundidad -= 1
            if profundidad == 0:
                cierre = pos
                break
    if cierre is None:
        raise ValueError(f"No se encontró el cierre de '{nombre_dict}' en orchestrator.py "
                          f"-- no se ha tocado nada, edítalo a mano.")

    return contenido[:cierre] + nueva_linea.rstrip() + "\n" + contenido[cierre:]


def proponer_integracion(target_file: str, descripcion: str) -> dict:
    """
    Devuelve el texto exacto que se añadiría a orchestrator.py, para
    enseñárselo al usuario ANTES de escribir nada. No toca el archivo.
    """
    modulo = Path(target_file).stem
    clave = modulo
    descripcion = descripcion.replace('"', "'").strip()[:200]

    import_linea = f"import {modulo}  # noqa: E402"
    registry_linea = f'    "{clave}": ({modulo}.run, {modulo}.AUTONOMY_LEVEL),'
    # Entrada de Capability Registry estructurada (Schemas/CapabilityRegistry.md).
    # entradas/salidas/herramientas quedan genéricas -- en el momento de
    # integrar no se conoce más que la tarea que originó el agente; el
    # usuario puede afinarlas a mano después si quiere ser más preciso.
    catalogo_linea = (
        f'    "{clave}": {{\n'
        f'        "descripcion": "{descripcion}",\n'
        f'        "entradas": "definido por la tarea que generó este agente",\n'
        f'        "salidas": "resultado de run()",\n'
        f'        "herramientas": [],\n'
        f'        "autonomy_level": {modulo}.AUTONOMY_LEVEL,\n'
        f'    }},'
    )

    return {
        "modulo": modulo,
        "clave": clave,
        "import_linea": import_linea,
        "registry_linea": registry_linea,
        "catalogo_linea": catalogo_linea,
        "resumen": (
            f"Esto se añadiría a orchestrator.py:\n\n"
            f"1) {import_linea}\n"
            f"2) En REGISTRY:\n   {registry_linea.strip()}\n"
            f"3) En AGENTES_CEO (para que puedas invocarlo hablando normal):\n   {catalogo_linea.strip()}"
        ),
    }


def aplicar_integracion(target_file: str, descripcion: str) -> str:
    """
    Escribe de verdad los tres cambios en orchestrator.py. Solo se debe
    llamar después de que el usuario haya confirmado explícitamente el
    texto de proponer_integracion(). Devuelve la clave con la que queda
    registrado el agente (REGISTRY y AGENTES_CEO comparten la misma clave).
    """
    propuesta = proponer_integracion(target_file, descripcion)
    modulo = propuesta["modulo"]

    contenido = ORCHESTRATOR_PATH.read_text(encoding="utf-8")

    if re.search(rf"\bimport {re.escape(modulo)}\b", contenido):
        raise ValueError(f"'{modulo}' ya está importado en orchestrator.py -- no se ha vuelto a tocar nada.")

    marcador = "\nREGISTRY = {"
    if marcador not in contenido:
        raise ValueError("No se encontró 'REGISTRY = {' en orchestrator.py -- no se ha tocado nada.")
    contenido = contenido.replace(marcador, f"\n{propuesta['import_linea']}\n{marcador}", 1)

    contenido = _insertar_en_dict(contenido, "REGISTRY", propuesta["registry_linea"])
    contenido = _insertar_en_dict(contenido, "AGENTES_CEO", propuesta["catalogo_linea"])

    ORCHESTRATOR_PATH.write_text(contenido, encoding="utf-8")
    return propuesta["clave"]
