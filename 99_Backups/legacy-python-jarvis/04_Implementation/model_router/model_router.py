"""
Model Router v1.0 (Modules/ModelRouter.md)

Responsabilidad: ser el único lugar del código donde se nombra un modelo
de Ollama en concreto. Antes de esto, cada agente tenía escrito a mano
"llama3.2:3b" o "llama3.1:8b" repetido en cuatro archivos distintos --
justo lo contrario de lo que pedía ModelRouter.md desde el principio del
proyecto ("independiente del modelo dominante del momento") y de la
Constitution Art. 6 ("ningún modelo de IA es imprescindible").

Con esto, cambiar de modelo es una línea aquí, no una edición en cada
agente. Los agentes piden "el modelo de nivel 1" o "el de nivel 2", nunca
un nombre concreto.
"""

# Único lugar del repo donde deberían aparecer nombres de modelo de Ollama.
MODELOS = {
    1: "llama3.2:3b",   # rápido, barato -- clasificar, enrutar, tareas simples
    2: "llama3.1:8b",   # más capaz -- generar código/agentes, redactar, narrar
}


def modelo(nivel: int) -> str:
    """
    Devuelve el nombre del modelo de Ollama asignado a un nivel del
    ModelRouter (Modules/ModelRouter.md). Si el nivel no está configurado,
    falla con un error claro en vez de devolver un modelo al azar --
    mejor un fallo visible que una llamada silenciosa al modelo equivocado.
    """
    if nivel not in MODELOS:
        raise ValueError(f"No hay modelo configurado para el nivel {nivel}. "
                          f"Niveles disponibles: {sorted(MODELOS)}.")
    return MODELOS[nivel]
