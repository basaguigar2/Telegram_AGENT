"""
Automation Engine — Briefing diario (primera automatización real de JARVIS)

Responsabilidad: ejecutarse SOLO, sin que el usuario abra nada, y dejar un
briefing legible (Modules/AutomationEngine.md — "Briefing diario",
Modules/ExecutiveDashboard.md — "Vista diaria").

No usa input() en ningún punto -- si lo tuviera, un Task Scheduler que lo
lanza a las 8:00 se quedaría colgado esperando una respuesta que nunca llega.
Los valores de tiempo/energía salen de config.json, editable a mano.

Reutiliza el mismo camino auditado que ya existe (Orchestrator -> Policy
Engine -> Advisor Agent) en vez de llamar a Decision Engine directamente,
para que esta automatización quede registrada igual que cualquier otra
acción del sistema (Schemas/Permissions.md — auditoría).
"""

import json
import sys
import datetime
from pathlib import Path

import requests

BASE = Path(__file__).parent.parent
sys.path.append(str(BASE / "orchestrator"))
sys.path.append(str(BASE / "memory_engine"))
sys.path.append(str(BASE / "agents"))

import orchestrator as orch          # noqa: E402
import memory_engine as me           # noqa: E402
import supervisor_agent as sup       # noqa: E402

CONFIG_PATH = Path(__file__).parent / "config.json"
TELEGRAM_CONFIG_PATH = BASE / "telegram_bot" / "config.json"
OUTPUT_PATH = BASE.parent / "03_Documentation" / "BriefingDiario.md"
LOG_PATH = Path(__file__).parent / "briefing_errores.log"


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def _log_error(mensaje: str) -> None:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()} — {mensaje}\n")


def _texto_para_telegram(lineas: list[str]) -> str:
    """Versión sin sintaxis Markdown -- Telegram sin parse_mode la mostraría literal."""
    texto = "\n".join(lineas)
    for marca in ("**", "## ", "# ", "_"):
        texto = texto.replace(marca, "")
    return texto[:4000]  # límite de Telegram por mensaje


def _enviar_telegram(lineas: list[str]) -> None:
    """
    Reutiliza el mismo bot_token/allowed_chat_id que ya configuraste para
    el bot conversacional -- no hace falta montar nada nuevo. Si el bot
    todavía no está configurado, se limita a registrar el motivo en el log
    y sigue (el .md ya se guardó igualmente, no se pierde el briefing).
    """
    try:
        with open(TELEGRAM_CONFIG_PATH, encoding="utf-8") as f:
            tg_config = json.load(f)
    except FileNotFoundError:
        _log_error("No se envió por Telegram: falta telegram_bot/config.json")
        return

    token = tg_config.get("bot_token")
    chat_id = tg_config.get("allowed_chat_id")
    if not token or token == "PON_AQUI_TU_TOKEN_DE_BOTFATHER" or not chat_id:
        _log_error("No se envió por Telegram: bot_token o allowed_chat_id sin configurar")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": _texto_para_telegram(lineas)},
            timeout=15,
        )
    except requests.RequestException as e:
        _log_error(f"Fallo al enviar el briefing por Telegram: {e}")


def generar_briefing() -> None:
    config = _load_config()
    hoy = datetime.date.today().isoformat()

    try:
        estado, resultado = orch.dispatch(
            "recomendar",
            question=config["question"],
            available_time_hours=config["available_time_hours"],
            energy=config["energy"],
        )
    except Exception as e:  # noqa: BLE001 - una automatización no debe morir en silencio
        _log_error(f"Fallo al generar recomendación: {e}")
        estado, resultado = "error", None

    objetivos = me.active_goals()
    conocimiento = me.recent_knowledge(limit=5)

    lineas = [
        f"# Briefing diario — {hoy}",
        "",
        "## Objetivos activos",
        "",
    ]
    if objetivos:
        for g in objetivos:
            lineas.append(f"- **{g['name']}** ({g['priority']})")
    else:
        lineas.append("- (ninguno registrado todavía)")

    lineas += ["", "## Conocimiento reciente", ""]
    if conocimiento:
        for k in conocimiento:
            lineas.append(f"- [{k['reliability']}] {k['topic']}: {k['content'][:100]}")
    else:
        lineas.append("- (ninguno registrado todavía)")

    lineas += ["", "## Recomendación de JARVIS", ""]
    if estado == "error":
        lineas.append("No se pudo generar la recomendación hoy (Ollama no respondió o falló). "
                       "Revisa `briefing_errores.log`.")
    elif estado == "permitido_ejecutado" and resultado:
        lineas.append(f"**Acción:** {resultado['recommended_action']}")
        lineas.append("")
        lineas.append(f"**Motivo:** {resultado['reason']}")
        lineas.append("")
        lineas.append(f"**Alternativas:** {', '.join(resultado['alternatives']) or '—'}")
        lineas.append("")
        lineas.append(f"**Confianza:** {resultado['confidence']}")
        if resultado["confidence"] == "baja":
            lineas.append("")
            lineas.append("_Confianza baja — hay poco contexto todavía o la pregunta era ambigua._")
    else:
        lineas.append(f"Estado inesperado: {estado}")

    para_claude = me.pending_for_claude()
    lineas += ["", "## Pendiente para Claude", ""]
    if para_claude:
        for d in para_claude:
            lineas.append(f"- {d['reason']} (desde {d['created_at'][:10]})")
    else:
        lineas.append("- Nada pendiente para Claude ahora mismo.")

    revision = sup.run()
    lineas += ["", "## Revisión del Supervisor", ""]
    lineas.append(sup.formatear(revision))

    lineas += ["", "---", f"_Generado automáticamente. Config usada: {config}_"]

    OUTPUT_PATH.write_text("\n".join(lineas), encoding="utf-8")
    _enviar_telegram(lineas)


if __name__ == "__main__":
    generar_briefing()
