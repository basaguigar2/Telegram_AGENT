"""
Interfaz de Telegram para JARVIS -- primera interfaz "constante" desde el móvil.

Arquitectura: esto es solo una nueva forma de hablar con el mismo sistema.
No sustituye a Policy Engine ni a Memory Engine -- cada acción sigue pasando
por policy_engine.evaluate() igual que en la terminal (Schemas/Permissions.md),
así que el historial de auditoría es el mismo, escribas desde la terminal o
desde el móvil.

Seguridad: el bot SOLO responde al chat_id guardado en config.json.
Cualquier mensaje de otro chat_id se ignora en silencio -- es el único
control de acceso de este sistema, no lo desactives ni lo compartas.

Requiere: tu Victus encendido, Ollama corriendo, y este script en ejecución
(ver README_TELEGRAM.md para dejarlo corriendo en segundo plano).
"""

import importlib
import json
import msvcrt
import re
import sys
import threading
import time
from pathlib import Path

import requests

_LOCK_PATH = Path(__file__).parent / "bot.lock"


def _adquirir_instancia_unica():
    """
    Impide que dos instancias del bot corran a la vez -- la causa real de los
    409 Conflict de Telegram (dos procesos pidiendo getUpdates con el mismo
    token) cuando Stop-ScheduledTask no mata un python.exe huérfano y luego
    Start-ScheduledTask lanza uno nuevo encima. El lock es un file lock de
    Windows (msvcrt) que el propio sistema operativo libera al morir el
    proceso, incluso con Ctrl+C o un crash -- no hace falta limpieza manual
    ni riesgo de lock "atascado" de una ejecución anterior.
    """
    fh = open(_LOCK_PATH, "w")
    try:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        print("Ya hay una instancia del bot corriendo (bot.lock ocupado) -- saliendo sin arrancar otra.")
        sys.exit(1)
    return fh  # mantener la referencia viva mientras el proceso corra -- si se recolecta, se libera el lock

BASE = Path(__file__).parent.parent
sys.path.append(str(BASE / "memory_engine"))
sys.path.append(str(BASE / "policy_engine"))
sys.path.append(str(BASE / "agents"))
sys.path.append(str(BASE / "context_engine"))
sys.path.append(str(BASE / "decision_engine"))
sys.path.append(str(BASE / "intent_router"))
sys.path.append(str(BASE / "orchestrator"))

import memory_engine as me     # noqa: E402
import policy_engine as pe     # noqa: E402
import capture_agent           # noqa: E402
import advisor_agent           # noqa: E402
import builder_agent           # noqa: E402
import supervisor_agent as sup # noqa: E402
import creative_agent          # noqa: E402
import process_narrator_agent as narrador  # noqa: E402
import generador_agent         # noqa: E402
import seguimiento_agent       # noqa: E402
import investigador_agent      # noqa: E402
import conversador_agent       # noqa: E402
import ceo_agent as ceo        # noqa: E402
import orchestrator_integrator as oi  # noqa: E402
import intent_router as ir     # noqa: E402 -- se sigue usando por sus utilidades (_slug, carpetas seguras)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


class _MientrasEscribe:
    """
    Mantiene visible el indicador nativo de Telegram ("escribiendo...") durante
    una operación de fondo lenta (llamada a Ollama), en vez de mandar un
    mensaje de texto que enseña la mecánica interna del sistema (ej. "Pensando
    a quién le toca esto..."). El objetivo es que hablar con JARVIS se sienta
    como un chat normal, no como interactuar con un router. El indicador nativo
    de Telegram desaparece solo a los ~5s, así que se reenvía en bucle mientras
    dure el bloque `with`.
    """
    def __init__(self, bot: "JarvisTelegramBot", chat_id: int):
        self._bot = bot
        self._chat_id = chat_id
        self._parar = threading.Event()
        self._hilo = threading.Thread(target=self._bucle, daemon=True)

    def _bucle(self) -> None:
        while not self._parar.is_set():
            self._bot._accion_escribiendo(self._chat_id)
            self._parar.wait(4)

    def __enter__(self) -> "_MientrasEscribe":
        self._hilo.start()
        return self

    def __exit__(self, *exc) -> None:
        self._parar.set()
        self._hilo.join(timeout=1)


class JarvisTelegramBot:
    def __init__(self, config: dict):
        self.token = config["bot_token"]
        self.allowed_chat_id = config.get("allowed_chat_id")
        self.api = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0
        self.sessions: dict[int, dict] = {}  # chat_id -> {"state": str, "payload": dict}

    # --- Transporte (Telegram) ---

    def get_updates(self) -> list:
        r = requests.get(f"{self.api}/getUpdates",
                          params={"offset": self.offset, "timeout": 30}, timeout=40)
        r.raise_for_status()
        return r.json().get("result", [])

    def send(self, chat_id: int, text: str) -> None:
        requests.post(f"{self.api}/sendMessage", data={"chat_id": chat_id, "text": text})

    def _accion_escribiendo(self, chat_id: int) -> None:
        try:
            requests.post(f"{self.api}/sendChatAction",
                          data={"chat_id": chat_id, "action": "typing"}, timeout=5)
        except requests.RequestException:
            pass  # cosmético -- si falla, simplemente no se ve el indicador esta vez

    def run(self) -> None:
        print("Bot de JARVIS escuchando... (Ctrl+C para parar)")
        while True:
            try:
                updates = self.get_updates()
            except requests.RequestException as e:
                print(f"Error de red, reintentando en 5s: {e}")
                time.sleep(5)
                continue

            for update in updates:
                self.offset = update["update_id"] + 1
                message = update.get("message")
                if not message or "text" not in message:
                    continue
                chat_id = message["chat"]["id"]
                try:
                    self.handle(chat_id, message["text"].strip())
                except Exception as e:  # noqa: BLE001 -- un fallo en un mensaje no debe tirar el bot entero
                    print(f"Error procesando mensaje de {chat_id}: {e}")
                    try:
                        self.send(chat_id, "Algo ha fallado procesando tu mensaje -- ya está registrado, prueba de nuevo.")
                    except requests.RequestException:
                        pass

    # --- Enrutado de mensajes ---

    def handle(self, chat_id: int, text: str) -> None:
        if self.allowed_chat_id is None:
            self.send(chat_id, f"Tu chat_id es: {chat_id}\n\n"
                                f"Ponlo en config.json como \"allowed_chat_id\" (número, sin comillas) "
                                f"y reinicia el bot.")
            return

        if chat_id != self.allowed_chat_id:
            return  # control de acceso: se ignora en silencio

        session = self.sessions.setdefault(chat_id, {"state": None, "payload": {}})

        if session["state"] == "confirmar_nota":
            self._resolver_nota(chat_id, text, session)
        elif session["state"] == "confirmar_codigo_ejecutar":
            self._resolver_codigo_ejecutar(chat_id, text, session)
        elif session["state"] == "eligiendo_idea_creativa":
            self._resolver_eleccion_idea(chat_id, text, session)
        elif session["state"] == "eligiendo_tema_investigado":
            self._resolver_eleccion_tema(chat_id, text, session)
        elif text.startswith("/help"):
            self.send(chat_id, self._help())
        elif text.startswith("/pregunta"):
            # sintaxis manual -- se mantiene como opción avanzada, no hace falta usarla
            self._iniciar_pregunta_manual(chat_id, text)
        elif text.startswith("/codigo"):
            # sintaxis manual -- la única forma de EDITAR un archivo ya existente del
            # sistema (memory_engine.py, orchestrator.py, ...). El modo natural nunca
            # toca archivos existentes por su cuenta, solo crea archivos nuevos.
            self._iniciar_codigo_manual(chat_id, text)
        else:
            self._iniciar_natural(chat_id, text)

    def _help(self) -> str:
        return (
            "JARVIS -- háblame normal, no hace falta sintaxis especial. Todo lo que "
            "escribas pasa primero por el CEO Agent, que decide a qué agente le toca "
            "y lo deriva -- tú no tienes que saber cuál es cuál.\n\n"
            "Ejemplos:\n"
            "  \"tengo que comprar pilas\" -> lo guarda como nota\n"
            "  \"tengo 3 horas libres y energía media, ¿qué hago?\" -> te recomienda algo\n"
            "  \"hazme un script que liste mis decisiones pendientes\" -> lo genera y lo "
            "guarda directo\n"
            "  \"créame un agente que se encargue de X\" -> lo genera, lo guarda y lo "
            "integra en el Orchestrator, todo seguido\n"
            "  \"dame ideas de agentes para mi carrera\" -> te propongo varias, eliges una y "
            "la convierto en encargo para el Builder\n"
            "  \"cuéntame qué pasos seguiste para crear el agente X\" -> te relato lo que "
            "de verdad está registrado, nunca me lo invento\n"
            "  \"escribe un artículo sobre sillas ergonómicas\" -> genera un artículo de "
            "afiliados (home office) y lo guarda como borrador, con enlaces placeholder\n"
            "  \"cómo va el tablero de contenido\" -> resumen de tareas de negocio por fase "
            "y cuáles llevan días paradas\n"
            "  \"dame ideas de temas para el blog\" -> Investigador propone temas nuevos "
            "(sin verificar) para guardar en el tablero\n"
            "  \"qué hago con JARVIS ahora\" -> te digo que eso lo hablamos en el chat con Claude\n\n"
            "Solo te pregunto sí/no para tres cosas (Constitution Art. 2): ejecutar código "
            "generado, eliminar algo, o desplegar a producción. Todo lo demás (guardar, "
            "generar, integrar) lo hago directo, sin pedirte confirmación.\n\n"
            "Avanzado (opcional, para EDITAR un archivo ya existente del sistema):\n"
            "  /pregunta horas|energia|tu pregunta\n"
            "  /codigo descripción de la tarea|ruta/del/archivo.py\n\n"
            "/help -> este mensaje"
        )

    # --- Modo natural: el CEO Agent decide a quién le toca ---

    @staticmethod
    def _extraer_horas_energia(texto: str) -> tuple[float, str]:
        """
        Heurística ligera y determinista (sin modelo) para no perder la
        extracción de horas/energía que antes hacía el Intent Router --
        el CEO solo decide "a quién", no estos detalles. Si no encuentra
        nada, usa los mismos valores por defecto de siempre (3h, media).
        """
        horas = 3.0
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*h", texto.lower())
        if m:
            try:
                horas = float(m.group(1).replace(",", "."))
            except ValueError:
                pass
        energia = "media"
        for candidata in ("alta", "media", "baja"):
            if candidata in texto.lower():
                energia = candidata
                break
        return horas, energia

    def _iniciar_natural(self, chat_id: int, texto: str) -> None:
        if not texto:
            return
        mensaje_original = texto
        with _MientrasEscribe(self, chat_id):
            decision = ceo.decide(texto)
        agente = decision["agente"]
        texto = decision["texto"]

        if agente == "ayuda":
            self.send(chat_id, self._help())
        elif agente == "nota":
            self._iniciar_nota(chat_id, texto)
        elif agente == "pregunta":
            horas, energia = self._extraer_horas_energia(texto)
            self._procesar_pregunta(chat_id, texto, horas, energia)
        elif agente == "codigo":
            nombre = ir._slug(texto)
            target_file = f"{ir.CARPETA_SEGURA_CODIGO}/{nombre}.py"
            self._procesar_codigo(chat_id, texto, target_file)
        elif agente == "agente":
            nombre_agente = ir._slug(texto)
            if not nombre_agente.endswith("_agent"):
                nombre_agente = f"{nombre_agente}_agent"
            target_file = f"{ir.CARPETA_SEGURA_AGENTE}/{nombre_agente}.py"
            self._procesar_agente(chat_id, texto, nombre_agente, target_file)
        elif agente == "estrategico":
            self._flag_estrategico(chat_id, texto)
        elif agente == "estado":
            self._mostrar_estado(chat_id)
        elif agente == "supervisar":
            self.send(chat_id, "Revisando las últimas 24 horas...")
            resultado = sup.run()
            self.send(chat_id, sup.formatear(resultado))
        elif agente == "ideas":
            self._iniciar_brainstorm(chat_id, texto)
        elif agente == "relato":
            self._procesar_relato(chat_id, texto)
        elif agente == "articulo":
            self._procesar_articulo(chat_id, texto)
        elif agente == "negocio":
            self._mostrar_seguimiento_negocio(chat_id)
        elif agente == "investigar":
            self._iniciar_investigacion(chat_id)
        elif agente == "buscar":
            self._iniciar_busqueda_real(chat_id, texto)
        elif agente == "conversar":
            # el mensaje original, no decision["texto"] -- el modelo local reformula mal
            # la charla libre (a veces devuelve una pregunta distinta a la del usuario)
            self._procesar_conversacion(chat_id, mensaje_original)

    def _procesar_conversacion(self, chat_id: int, texto: str) -> None:
        with _MientrasEscribe(self, chat_id):
            resultado = conversador_agent.run(texto)
        self.send(chat_id, resultado["respuesta"])

    def _flag_estrategico(self, chat_id: int, pregunta: str) -> None:
        did = me.flag_for_claude(topic="pregunta estratégica", detail=pregunta, source="telegram_bot")
        self.send(chat_id,
                   "Esto es una decisión de rumbo del propio JARVIS -- no algo que deba "
                   "responder el modelo local (ModelRouter.md reserva esto para Claude).\n\n"
                   f"Lo he guardado como pendiente (id: {did}) para que lo lleves tú al chat "
                   "con Claude cuando quieras -- no se pierde, y te lo recordará el briefing "
                   "de cada noche mientras siga sin resolver.\n\n"
                   "Pregúntame \"qué tengo pendiente\" cuando quieras ver la lista completa.")

    def _mostrar_estado(self, chat_id: int) -> None:
        pendientes = me.pending_decisions()
        para_claude = me.pending_for_claude()
        otras = [d for d in pendientes if d["id"] not in {p["id"] for p in para_claude}]

        if not pendientes:
            self.send(chat_id, "No tienes nada pendiente ahora mismo.")
            return

        lineas = []
        if para_claude:
            lineas.append(f"Pendiente para Claude ({len(para_claude)}):")
            for d in para_claude:
                lineas.append(f"  - {d['reason']}")
            lineas.append("")
        if otras:
            lineas.append(f"Otras decisiones pendientes ({len(otras)}):")
            for d in otras:
                lineas.append(f"  - {d['reason']}")

        self.send(chat_id, "\n".join(lineas))

    @staticmethod
    def _es_si(text: str) -> bool:
        return text.strip().lower() in ("si", "sí", "s", "yes")

    # --- Captura de notas (nivel 1 -> se guarda directo, sin confirmación) ---

    def _iniciar_nota(self, chat_id: int, texto: str) -> None:
        if not texto:
            return
        evaluacion = pe.evaluate("capture_agent", "capturar", capture_agent.AUTONOMY_LEVEL)
        if evaluacion == "bloqueado":
            self.send(chat_id, "Acción bloqueada por Policy Engine.")
            return

        clasificacion = capture_agent.propose(texto)
        session = self.sessions[chat_id]
        session["payload"] = {"texto": texto, "clasificacion": clasificacion}

        if evaluacion == "permitido":
            self._guardar_nota(chat_id, session)
            return

        session["state"] = "confirmar_nota"
        self.send(chat_id,
                   f"Tema detectado: {clasificacion['topic']}\n"
                   f"Confianza: {clasificacion['reliability']}\n\n"
                   f"¿Guardar esta nota? (si/no)")

    def _resolver_nota(self, chat_id: int, text: str, session: dict) -> None:
        if self._es_si(text):
            self._guardar_nota(chat_id, session)
        else:
            self.send(chat_id, "Descartado, no se ha guardado nada.")
        session["state"] = None
        session["payload"] = {}

    def _guardar_nota(self, chat_id: int, session: dict) -> None:
        payload = session["payload"]
        kid = capture_agent.save(payload["texto"], payload["clasificacion"])
        self.send(chat_id, f"Guardado. id: {kid}")
        session["state"] = None
        session["payload"] = {}

    # --- Recomendación (nivel 1 -> permitido directo) ---

    def _iniciar_pregunta_manual(self, chat_id: int, text: str) -> None:
        cuerpo = text[len("/pregunta"):].strip()
        partes = cuerpo.split("|")
        if len(partes) != 3:
            self.send(chat_id, "Formato: /pregunta horas|energia|tu pregunta")
            return
        horas_str, energia, pregunta = (p.strip() for p in partes)

        try:
            horas = float(horas_str)
        except ValueError:
            self.send(chat_id, "Las horas deben ser un número, ej: /pregunta 3|media|¿qué hago?")
            return
        if energia not in ("alta", "media", "baja"):
            self.send(chat_id, "La energía debe ser alta, media o baja.")
            return

        self._procesar_pregunta(chat_id, pregunta, horas, energia)

    def _procesar_pregunta(self, chat_id: int, pregunta: str, horas: float, energia: str) -> None:
        evaluacion = pe.evaluate("advisor_agent", "recomendar", advisor_agent.AUTONOMY_LEVEL)
        if evaluacion == "bloqueado":
            self.send(chat_id, "Acción bloqueada por Policy Engine.")
            return

        with _MientrasEscribe(self, chat_id):
            resultado = advisor_agent.run(question=pregunta, available_time_hours=horas, energy=energia)

        aviso = ""
        if resultado["confidence"] == "baja":
            aviso = "\n\n(Confianza baja -- poco contexto todavía, o pregunta ambigua.)"

        self.send(chat_id,
                   f"Recomendación: {resultado['recommended_action']}\n"
                   f"Motivo: {resultado['reason']}\n"
                   f"Alternativas: {', '.join(resultado['alternatives']) or '—'}\n"
                   f"Confianza: {resultado['confidence']}{aviso}\n\n"
                   f"Queda registrada como decisión pendiente (id: {resultado['decision_id']}).")

    # --- Relato de proceso (nivel 1 -> permitido directo, igual que la recomendación) ---

    def _procesar_relato(self, chat_id: int, consulta: str) -> None:
        evaluacion = pe.evaluate("process_narrator_agent", "narrar", narrador.AUTONOMY_LEVEL)
        if evaluacion == "bloqueado":
            self.send(chat_id, "Acción bloqueada por Policy Engine.")
            return

        self.send(chat_id, "Revisando el registro de eventos...")
        resultado = narrador.narrar(consulta)
        self.send(chat_id, resultado["relato"])

    # --- Negocio: Generador y Seguimiento (nivel 1 -> permitido directo,
    # igual que Capture Agent -- guardar un borrador no es destructivo ni
    # estratégico, así que no pide confirmación) ---

    def _procesar_articulo(self, chat_id: int, tema: str) -> None:
        if not tema:
            self.send(chat_id, "Dime sobre qué tema quieres el artículo, ej. "
                                "\"escribe un artículo sobre sillas ergonómicas\".")
            return

        evaluacion = pe.evaluate("generador_agent", "generar_articulo", generador_agent.AUTONOMY_LEVEL)
        if evaluacion == "bloqueado":
            self.send(chat_id, "Acción bloqueada por Policy Engine.")
            return

        self.send(chat_id, f"Dame un momento, estoy escribiendo el artículo sobre \"{tema}\"...")
        with _MientrasEscribe(self, chat_id):
            resultado = generador_agent.run(tema)

        articulo = resultado["articulo"]
        preview = articulo if len(articulo) < 3500 else articulo[:3500] + "\n... (recortado)"
        self.send(chat_id, preview)
        self.send(chat_id,
                   f"Guardado como borrador (Conocimiento id: {resultado['knowledge_id']}, "
                   f"Tarea id: {resultado['task_id']}, fase: borrador_listo).\n\n"
                   f"Antes de publicar: sustituye los enlaces placeholder por tus enlaces reales "
                   f"de {generador_agent.PROGRAMA_AFILIADO}.")

    def _mostrar_seguimiento_negocio(self, chat_id: int) -> None:
        evaluacion = pe.evaluate("seguimiento_agent", "revisar_negocio", seguimiento_agent.AUTONOMY_LEVEL)
        if evaluacion == "bloqueado":
            self.send(chat_id, "Acción bloqueada por Policy Engine.")
            return

        resultado = seguimiento_agent.run()
        self.send(chat_id, seguimiento_agent.formatear(resultado))

    def _iniciar_investigacion(self, chat_id: int) -> None:
        evaluacion = pe.evaluate("investigador_agent", "investigar_temas", investigador_agent.AUTONOMY_LEVEL)
        if evaluacion == "bloqueado":
            self.send(chat_id, "Acción bloqueada por Policy Engine.")
            return

        self.send(chat_id, "Pensando temas nuevos para el blog (sin verificar contra datos "
                            "de mercado reales -- Ollama no tiene internet)...")
        temas = investigador_agent.investigar()

        if not temas:
            self.send(chat_id, "No me han salido ideas claras esta vez -- prueba a pedírmelo de nuevo.")
            return

        session = self.sessions[chat_id]
        session["payload"] = {"temas": temas, "origen": "investigador_agent"}
        session["state"] = "eligiendo_tema_investigado"

        lineas = ["Temas propuestos (sin verificar):", ""]
        for i, t in enumerate(temas, start=1):
            lineas.append(f"{i}. {t['tema']} -- {t['angulo']}")
            lineas.append(f"   ({t['justificacion']})")
        lineas.append("")
        lineas.append("Responde con el número del que quieras guardar como idea en el tablero "
                       "(fase 'idea'), \"todos\" para guardarlos todos, o \"no\" para descartarlos.")
        self.send(chat_id, "\n".join(lineas))

    def _iniciar_busqueda_real(self, chat_id: int, query: str) -> None:
        if not query:
            self.send(chat_id, "Dime sobre qué quieres que busque, ej. \"busca en internet "
                                "sobre monitores para home office\".")
            return

        evaluacion = pe.evaluate("investigador_agent", "buscar_real", investigador_agent.AUTONOMY_LEVEL)
        if evaluacion == "bloqueado":
            self.send(chat_id, "Acción bloqueada por Policy Engine.")
            return

        self.send(chat_id, f"Buscando de verdad en internet sobre \"{query}\"...")
        try:
            temas = investigador_agent.investigar_con_busqueda_real(query)
        except ValueError as e:
            self.send(chat_id, str(e))
            return
        except Exception as e:  # noqa: BLE001 -- fallo de red/API no debe tirar el bot
            self.send(chat_id, f"La búsqueda falló: {e}")
            return

        if not temas:
            self.send(chat_id, "La búsqueda no dio resultados que pudiera anclar a un tema claro.")
            return

        session = self.sessions[chat_id]
        session["payload"] = {"temas": temas, "origen": "investigador_agent_busqueda_real"}
        session["state"] = "eligiendo_tema_investigado"

        lineas = ["Temas anclados a resultados reales:", ""]
        for i, t in enumerate(temas, start=1):
            lineas.append(f"{i}. {t['tema']} -- {t['angulo']}")
            lineas.append(f"   ({t['justificacion']})")
            lineas.append(f"   fuente: {t['fuente_url']}")
        lineas.append("")
        lineas.append("Responde con el número del que quieras guardar como idea en el tablero "
                       "(fase 'idea'), \"todos\" para guardarlos todos, o \"no\" para descartarlos.")
        self.send(chat_id, "\n".join(lineas))

    def _resolver_eleccion_tema(self, chat_id: int, text: str, session: dict) -> None:
        temas = session["payload"].get("temas", [])
        origen = session["payload"].get("origen", "investigador_agent")
        texto = text.strip().lower()

        if texto in ("no", "cancelar", "ninguno"):
            self.send(chat_id, "Descartado, ningún tema guardado.")
            session["state"] = None
            session["payload"] = {}
            return

        if texto == "todos":
            elegidos = temas
        else:
            try:
                elegidos = [temas[int(texto) - 1]]
            except (ValueError, IndexError):
                self.send(chat_id, "No he entendido cuál -- responde con el número, \"todos\", o \"no\".")
                return

        session["state"] = None
        session["payload"] = {}

        ids = [investigador_agent.crear_tarea_idea(t["tema"], t["justificacion"], t.get("angulo"),
                                                     source=origen, fuente_url=t.get("fuente_url"))
               for t in elegidos]
        self.send(chat_id, f"Guardado(s) {len(ids)} tema(s) en el tablero, fase 'idea'. "
                            f"Cuando quieras que escriba uno, dime \"escribe un artículo sobre <tema>\".")

    # --- Código (revisión de arquitectura CEO: guardar es autónomo, solo
    # EJECUTAR sigue pidiendo confirmación -- Constitution Art. 2 y 10) ---

    def _iniciar_codigo_manual(self, chat_id: int, text: str) -> None:
        cuerpo = text[len("/codigo"):].strip()
        partes = cuerpo.split("|")
        if len(partes) != 2:
            self.send(chat_id, "Formato: /codigo descripción de la tarea|ruta/del/archivo.py")
            return
        tarea, ruta = (p.strip() for p in partes)
        self._procesar_codigo(chat_id, tarea, ruta)

    def _procesar_codigo(self, chat_id: int, tarea: str, ruta: str) -> None:
        # Se registra la evaluación igualmente (auditoría), pero "programar"
        # ya no es una de las tres acciones que piden confirmación -- se
        # genera y se guarda directo.
        pe.evaluate("builder_agent", "programar", builder_agent.AUTONOMY_LEVEL)

        self.send(chat_id, "Generando con el modelo local, un momento...")
        propuesto = builder_agent.propose(tarea, ruta)

        preview = propuesto if len(propuesto) < 3500 else propuesto[:3500] + "\n... (recortado)"
        self.send(chat_id, f"Propuesta para {ruta}:\n\n{preview}")

        builder_agent.write(ruta, propuesto)
        self.send(chat_id, f"Guardado en {ruta}.")

        es_seguro, motivos = builder_agent.is_safe_to_execute(propuesto)
        me.create_event(
            event_type="code.safety_scan",
            origin_module="builder_agent",
            context={"target_file": ruta, "es_seguro": es_seguro, "motivos": motivos},
        )

        if not es_seguro:
            self.send(chat_id,
                       f"No te ofrezco ejecutarlo: el escaneo detectó posible {', '.join(motivos)}. "
                       f"Si quieres correrlo, revísalo tú mismo primero y hazlo a mano.")
            return

        # "ejecutar" es una de las tres acciones de la lista cerrada
        # (Constitution Art. 2) -- esta sigue pidiendo sí/no siempre.
        pe.evaluate("builder_agent", "ejecutar", 4)
        session = self.sessions[chat_id]
        session["payload"] = {"ruta": ruta}
        session["state"] = "confirmar_codigo_ejecutar"
        self.send(chat_id, "El escaneo no encontró nada sospechoso (borrado, red, comandos del sistema). "
                            "¿Ejecutar también? (si/no)")

    def _resolver_codigo_ejecutar(self, chat_id: int, text: str, session: dict) -> None:
        payload = session["payload"]
        if not self._es_si(text):
            self.send(chat_id, "No ejecutado. El archivo se queda guardado tal cual.")
            session["state"] = None
            session["payload"] = {}
            return

        self.send(chat_id, f"Ejecutando {payload['ruta']} (máx. {builder_agent.TIMEOUT_EJECUCION_SEGUNDOS}s)...")
        resultado = builder_agent.execute(payload["ruta"])

        me.create_event(
            event_type="code.executed",
            origin_module="builder_agent",
            context={"target_file": payload["ruta"], "returncode": resultado["returncode"],
                     "timeout": resultado["timeout"]},
            outcome=resultado["stdout"][:500] if resultado["ejecutado"] else resultado["stderr"],
        )

        if resultado["timeout"]:
            self.send(chat_id, resultado["stderr"])
        else:
            salida = resultado["stdout"] or "(sin salida)"
            error = f"\nErrores:\n{resultado['stderr']}" if resultado["stderr"] else ""
            preview = salida if len(salida) < 3000 else salida[:3000] + "\n... (recortado)"
            self.send(chat_id, f"Terminado (código {resultado['returncode']}).\n\nSalida:\n{preview}{error}")

        session["state"] = None
        session["payload"] = {}

    # --- Creative Agent: brainstorm de agentes + encargo elaborado para Builder ---

    def _iniciar_brainstorm(self, chat_id: int, tema: str) -> None:
        tema = tema or "JARVIS en general"
        with _MientrasEscribe(self, chat_id):
            ideas = creative_agent.brainstorm(tema)

        if not ideas:
            self.send(chat_id, "No me han salido ideas claras esta vez -- prueba a "
                                "pedírmelo de nuevo o con el tema más concreto.")
            return

        session = self.sessions[chat_id]
        session["payload"] = {"ideas": ideas}
        session["state"] = "eligiendo_idea_creativa"

        lineas = [f"Ideas para '{tema}':", ""]
        for i, idea in enumerate(ideas, start=1):
            lineas.append(f"{i}. {idea['nombre']} -- {idea['mision']}")
            lineas.append(f"   ({idea['justificacion']})")
        lineas.append("")
        lineas.append("Responde con el número de la que quieras convertir en encargo, "
                       "o \"no\" para descartar todas.")
        self.send(chat_id, "\n".join(lineas))

    def _resolver_eleccion_idea(self, chat_id: int, text: str, session: dict) -> None:
        ideas = session["payload"].get("ideas", [])

        if text.strip().lower() in ("no", "cancelar", "ninguna"):
            self.send(chat_id, "Descartado, ninguna idea elegida.")
            session["state"] = None
            session["payload"] = {}
            return

        try:
            indice = int(text.strip()) - 1
            elegida = ideas[indice]
        except (ValueError, IndexError):
            self.send(chat_id, "No he entendido cuál -- responde solo con el número de la lista, "
                                "o \"no\" para descartar.")
            return

        session["state"] = None
        session["payload"] = {}

        self.send(chat_id, f"Elaborando el encargo para '{elegida['nombre']}'...")
        brief = creative_agent.elaborar_brief(elegida["nombre"], elegida["mision"])

        preview = brief if len(brief) < 3500 else brief[:3500] + "\n... (recortado)"
        self.send(chat_id, f"Encargo para Builder Agent:\n\n{preview}")

        nombre_agente = ir._slug(elegida["nombre"])
        if not nombre_agente.endswith("_agent"):
            nombre_agente = f"{nombre_agente}_agent"
        target_file = f"{ir.CARPETA_SEGURA_AGENTE}/{nombre_agente}.py"

        self._procesar_agente(chat_id, brief, nombre_agente, target_file)

    # --- Generar agente nuevo (revisión de arquitectura CEO: generar,
    # guardar e integrar son autónomos -- ninguna de las tres es "ejecutar,
    # eliminar o desplegar", así que no piden confirmación) ---

    def _procesar_agente(self, chat_id: int, tarea: str, nombre_agente: str, target_file: str) -> None:
        pe.evaluate("builder_agent", "generar_agente", builder_agent.AUTONOMY_LEVEL)

        self.send(chat_id, "Generando el agente con el modelo local, un momento...")
        propuesto = builder_agent.propose_agent(tarea, nombre_agente, target_file)

        preview = propuesto if len(propuesto) < 3500 else propuesto[:3500] + "\n... (recortado)"
        self.send(chat_id, f"Propuesta de agente para {target_file}:\n\n{preview}")

        builder_agent.write(target_file, propuesto)
        me.create_event(
            event_type="agent.generated",
            origin_module="builder_agent",
            context={"target_file": target_file, "nombre_agente": nombre_agente},
        )
        self.send(chat_id, f"Archivo creado: {target_file}")
        # A propósito NO se ofrece ejecutar directamente: un agente no es un
        # script suelto -- lo que sigue es integrarlo en el Orchestrator, no
        # correrlo a pelo. "Integrar" tampoco es de la lista cerrada de
        # acciones que piden confirmación, así que sigue sin preguntar.

        try:
            propuesta = oi.proponer_integracion(target_file, tarea)
        except ValueError as e:
            self.send(chat_id, f"No he podido preparar la integración automática: {e}\n\n"
                                f"Revisa orchestrator.py a mano con Claude para este caso.")
            return

        self.send(chat_id, propuesta["resumen"])

        try:
            clave = oi.aplicar_integracion(target_file, tarea)
        except ValueError as e:
            self.send(chat_id, f"No he podido integrarlo: {e}")
            return

        me.create_event(
            event_type="agent.integrated",
            origin_module="orchestrator_integrator",
            context={"target_file": target_file, "clave": clave},
        )

        # Revisión obligatoria (Modules/AgentFrameWork.md -- "el modelo local
        # se equivoca a menudo"): antes de dar por bueno el cambio, se
        # comprueba que orchestrator.py sigue siendo Python válido.
        try:
            compile(Path(oi.ORCHESTRATOR_PATH).read_text(encoding="utf-8"),
                    str(oi.ORCHESTRATOR_PATH), "exec")
        except SyntaxError as e:
            self.send(chat_id, f"Integrado en el archivo, pero orchestrator.py ha quedado con un "
                                f"error de sintaxis: {e}\n\nRevísalo con Claude antes de reiniciar el bot "
                                f"-- si reinicias ahora, el bot no arrancará.")
            return

        # Recarga en caliente: así no hace falta reiniciar todo el bot para
        # empezar a usar el agente nuevo por lenguaje natural ahora mismo.
        try:
            importlib.reload(ceo.orch)
            self.send(chat_id, f"Integrado como \"{clave}\" y recargado en caliente -- ya puedes "
                                f"pedírselo al CEO hablando normal, sin reiniciar el bot.")
        except Exception as e:  # noqa: BLE001 -- un fallo de recarga no debe tirar el bot
            self.send(chat_id, f"Integrado como \"{clave}\", pero la recarga en caliente falló: {e}\n\n"
                                f"El cambio está guardado en orchestrator.py de todas formas -- "
                                f"reinicia el bot para que quede activo.")


if __name__ == "__main__":
    _lock_handle = _adquirir_instancia_unica()
    cfg = load_config()
    if cfg["bot_token"] == "PON_AQUI_TU_TOKEN_DE_BOTFATHER":
        print("Falta configurar bot_token en config.json -- ver README_TELEGRAM.md")
        sys.exit(1)
    JarvisTelegramBot(cfg).run()
