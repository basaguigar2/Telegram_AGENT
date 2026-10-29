"""
Prueba del criterio de salida de la Fase 1:
"puedes capturar una nota, que quede guardada como Conocimiento versionado,
y recuperarla."

Ejecutar desde la carpeta memory_engine/:
    python probar_captura.py
"""

import memory_engine as me

print("--- Fase 1: prueba del Memory Engine ---\n")

nota = input("Escribe una nota o idea para guardar como Conocimiento: ")
tema = input("¿Con qué tema se relaciona? (ej. JARVIS, trabajo, personal): ")

kid = me.create_knowledge(content=nota, topic=tema, reliability="media", source="usuario")
print(f"\nGuardado con id: {kid}")

recuperado = me.get_knowledge(kid)
print(f"Recuperado -> tema: '{recuperado['topic']}', estado: {recuperado['status']}, versión: {recuperado['version']}")
print(f"Contenido: {recuperado['content']}")

print("\nListado de todo el Conocimiento activo guardado hasta ahora:")
for item in me.list_knowledge():
    print(f"  - [{item['status']}] {item['topic']}: {item['content'][:60]}")

print("\nSi ves tu nota en la lista de arriba, la Fase 1 está funcionando.")
