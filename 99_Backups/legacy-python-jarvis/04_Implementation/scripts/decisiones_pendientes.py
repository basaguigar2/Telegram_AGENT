"""
Lista las Decisiones que JARVIS ha propuesto y siguen sin resolver
(result = 'pendiente' -- Constitution Art. 10, nunca se ejecutan solas).

Ejecutar desde cualquier sitio:
    python 04_Implementation/scripts/decisiones_pendientes.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "memory_engine"))
import memory_engine as me  # noqa: E402

pendientes = me.pending_decisions()

if not pendientes:
    print("No hay decisiones pendientes ahora mismo.")
else:
    print(f"{len(pendientes)} decisión(es) pendiente(s):\n")
    for d in pendientes:
        print(f"- [{d['created_at']}] {d['reason']}")
        print(f"  id: {d['id']}")
        print(f"  contexto: {d['context'][:100]}")
        print()

    print("Para resolver una, desde memory_engine/:")
    print("  python -c \"import memory_engine as me; "
          "me.resolve_decision('ID_AQUI', 'aceptada')\"  (o 'rechazada')")
