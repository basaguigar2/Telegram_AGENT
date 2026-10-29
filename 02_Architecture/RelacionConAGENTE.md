# Relación con AGENTE

Estado: Análisis v0.1 — decisión estratégica pendiente del usuario
Depende de: Roadmap.md, TechStack.md, Constitution.md
Origen: auditoría exhaustiva de la carpeta JARVIS solicitada el 2026-08-31, contrastada
contra `AGENTE — Guía de Construcción Detallada` (documento externo, COO multi-negocio
sobre n8n + Docker + Supabase).

---

# Por qué existe este documento

AGENTE describe, en sus Fases 0 y 1, construir desde cero: un bot de Telegram de pruebas,
n8n en Docker, una llamada HTTP a Ollama con un "prompt maestro", y confirmar que Ollama
responde. Eso es exactamente lo que JARVIS ya tiene construido y en producción — con más
capacidad (enrutado por intención vía CEO Agent, memoria versionada, motor de políticas,
generación de agentes nuevos, auditoría por eventos) de lo que un flujo de nodos en n8n
ofrece hoy. Sin este documento, ese solapamiento se habría descubierto tarde, reconstruyendo
en n8n algo que ya funciona en Python.

---

# Lo que AGENTE no aporta que JARVIS no tenga ya

- Un bot de Telegram con CEO Agent, memoria SQLite versionada, Policy Engine, y siete
  agentes especializados (Capture, Advisor, Builder, Supervisor, Creative, Process
  Narrator, CEO) — todo en `04_Implementation/`, corriendo como tarea programada de
  Windows en el Victus del usuario.
- Model Router centralizado (`model_router.py`) — cambiar de modelo Ollama es una línea,
  no una edición en cuatro archivos.
- Escala única de autonomía (Schemas/Permissions.md) con solo tres acciones que piden
  confirmación puntual (ejecutar, eliminar, desplegar) — más permisiva y más auditada que
  la revisión manual de cada acción que describe la Fase 4 de AGENTE.
- Backlog de autoevolución (Modules/SelfEvolution.md, `memory_engine.pending_insights`).

# Lo que AGENTE aporta que JARVIS no tiene

- Líneas de negocio nuevas: Trading, Scouter, contenido de afiliados (WordPress, KDP,
  POD) — ninguna existe hoy en JARVIS ni está en su Roadmap.
- Un tablero multi-negocio (`tablero_tareas`) pensado para varias líneas a la vez, no
  para un único usuario y su vida personal.
- Infraestructura 24/7 fuera del portátil: Raspberry Pi, Wake-on-LAN, UptimeRobot.
- Auditoría Interna como equipo transversal a *varias* líneas de negocio (Supervisor
  Agent de JARVIS hoy solo audita al propio JARVIS).

---

# Decisión (tomada el 2026-08-31)

AGENTE se construye como una capa nueva por encima de JARVIS: se reutilizan el CEO Agent,
Memory Engine y Telegram bot ya existentes para orquestar las líneas de negocio nuevas, y
n8n queda reservado solo para lo que de verdad requiere integrarse con APIs de terceros
con poco código (publicar en WordPress, por ejemplo) — no para reconstruir lo que ya
funciona en Python. Migrar JARVIS entero hacia n8n + Supabase queda descartado: implicaría
tirar meses de arquitectura ya coherente y en producción para recuperar, con más esfuerzo,
capacidades que ya existen.

Pendiente: diseñar Scouter, Trading y Auditoría multi-negocio como agentes/equipos
dentro del Capability Registry de JARVIS, cuando toque (Trading explícitamente "nunca
antes" de tener base de conocimiento lista, por regla del propio documento AGENTE).

---

# Primera línea construida: contenido de afiliados (2026-08-31)

Se activó `db/schema.sql` → tabla `task` (definida desde el inicio del proyecto, sin usar
hasta ahora) con tres columnas nuevas para modelar el tablero multi-negocio como extensión
del esquema existente, sin introducir Supabase ni ninguna base de datos nueva (decisión del
usuario): `business_line` (slug de línea de negocio, NULL = tarea interna de JARVIS),
`business_phase` (vocabulario libre por línea, sin CHECK — cada línea define el suyo sin
migrar esquema) y `related_knowledge_id` (FK directa a `knowledge`, mismo patrón que
`decision.related_goal_id`).

Dos agentes nuevos, siguiendo el contrato de AgentFrameWork.md e integrados en
`orchestrator.REGISTRY` / `orchestrator.AGENTES_CEO` igual que los siete ya existentes:

- **Generador Agent** (`agents/generador_agent.py`, nivel 1) — nicho "home office", programa
  de afiliados Amazon Afiliados (España). Genera un artículo SEO en Markdown con tabla
  comparativa, usando siempre un enlace placeholder explícito (nunca inventa URLs ni precios
  reales), lo guarda como Conocimiento y crea una Tarea en fase `borrador_listo`. No publica
  en ningún sitio — no existe WordPress real todavía (decisión del usuario); conectar la API
  de WordPress queda para cuando el sitio exista.
- **Seguimiento Agent** (`agents/seguimiento_agent.py`, nivel 1) — determinista, sin modelo
  de IA (mismo principio que Supervisor Agent). Revisa `task` por `business_line`, agrupa por
  `business_phase` y avisa de tareas sin moverse ≥3 días.

Enrutables por lenguaje natural vía CEO Agent bajo las claves `articulo` y `negocio` — no
requirió tocar `PROMPT_CEO`, porque el catálogo se lee dinámicamente de
`orchestrator.AGENTES_CEO` (justo el diseño que motivó sustituir el antiguo intent_router).
Probado end-to-end contra una copia de `jarvis.db` (nunca contra la base real) y con
llamadas reales a Ollama antes de integrarlo.

---

# Investigador Agent y el "Scouter" del organigrama principal (2026-08-31)

El documento AGENTE usa "Scouter" en dos sentidos distintos: en el organigrama principal
filtra oportunidades con "un criterio de cribado ya definido" (de marca/moat) que no existe
en ningún documento disponible aquí; en la segunda vía (contenido, sin marca) el mismo papel
lo hace el **Investigador**, sin ese filtro. Se decidió construir el Investigador -- completa
el trío de la línea de contenido -- y aparcar el Scouter principal hasta que ese criterio de
marca se defina explícitamente.

`agents/investigador_agent.py` (nivel 1) propone temas de artículo con Ollama, siempre
marcados como no verificados contra datos de mercado reales (Ollama no tiene acceso a
internet -- misma limitación que Creative Agent). El usuario elige cuáles pasan al tablero
como Tarea en fase `idea`.

Para no depender solo de ideas sin verificar, Claude hizo una investigación real (búsqueda
web, en esta misma conversación de arquitectura) sobre el nicho de home office y sembró el
tablero con 8 temas concretos, cada uno con `source='claude_websearch_2026-08-31'` -- esa
distinción de `source` es la que permite diferenciar en el tablero una idea investigada de
verdad de una simplemente generada por el modelo local.

Se corrigió además un problema real detectado en pruebas: el modelo local (llama3.1:8b)
confundía "investigar" (temas de contenido) con "ideas" (agentes de software nuevos) de
forma inconsistente entre ejecuciones idénticas. Se resolvió con el mismo patrón ya usado
para agente/código: una regla de texto determinista (`_PATRON_INVESTIGAR_CONTENIDO` en
`ceo_agent.py`) que decide sin pasar por el modelo cuando el mensaje es inequívoco.
Verificado con 10 frases × 3 repeticiones, 0 fallos.

---

# Búsqueda real vía Brave Search API (2026-08-31)

Aclaración importante que motivó esto: Ollama nunca va a tener acceso a internet -- es una
limitación del modelo en sí, no de configuración. Pero JARVIS (el código Python alrededor de
Ollama) sí puede llamar a cualquier API externa con `requests`, exactamente igual que
`telegram_bot/bot.py` ya llama a la API de Telegram. Conectar una búsqueda real no necesitaba
n8n -- habría añadido Docker y un problema nuevo (cómo recibe JARVIS los datos de n8n, que
hoy no sabe hacer) para algo que en Python son ~20 líneas con el mismo patrón que ya existe
en el proyecto.

Se eligió **Brave Search API** (alta inmediata, nivel gratuito) sobre SerpApi (cuota gratis
menor) y sobre Amazon PA-API (exige ventas de afiliado reales en los últimos 180 días, no
sirve para empezar). La clave vive en `04_Implementation/config/config.json` (nuevo,
cubierto por el `.gitignore` existente `**/config.json`), con `config.example.json` como
plantilla — pendiente de que el usuario cree la cuenta y pegue su clave real, algo que
Claude no puede hacer en su lugar.

`investigador_agent.buscar_web()` llama a Brave con `requests` y devuelve resultados reales
(título, URL, descripción). `investigar_con_busqueda_real()` nunca deja que Ollama "invente"
temas nuevos a partir de la búsqueda -- le pide únicamente que redacte un título de artículo
y un ángulo por CADA resultado real, indexado 1:1, de modo que la URL de origen (`fuente_url`)
siempre corresponde exactamente al resultado que la originó, sin riesgo de que el modelo
atribuya un dato a la fuente equivocada.

Nuevo intent de CEO Agent: `buscar` (distinto de `investigar`, que sigue siendo brainstorm
sin verificar). Igual que con agente/código e ideas/investigar, el modelo local confundía
"buscar ... real" con "investigar" sin la señal de búsqueda real -- se añadió un tercer
patrón determinista (`_PATRON_BUSQUEDA_REAL`) verificado antes de `_PATRON_INVESTIGAR_CONTENIDO`.
Verificado con 12 frases × 3 repeticiones, 0 fallos, incluyendo regresión de todos los ejes
anteriores (agente/código, ideas/investigar).

**Configurado y verificado (2026-08-31)**: el usuario creó la cuenta (plan "Search Postpaid",
$5 de crédito gratis al mes = ~1000 búsquedas gratis, más que suficiente para este uso) y
pegó la clave real -- por descuido, primero en `config.example.json` (que sí está en git).
Corregido de inmediato: la clave se movió a `config.json` (ignorado) y `config.example.json`
se restauró al placeholder antes de cualquier commit -- confirmado con
`git log --all -p -- config.example.json | grep <clave>` que nunca entró al historial.
Probado end-to-end contra la API real: `buscar_web()` devuelve resultados reales de Google/Bing
sobre sillas ergonómicas, e `investigar_con_busqueda_real()` los convierte en temas de artículo
con su URL de origen intacta.

---

# Auditoría multi-negocio: se amplía Supervisor Agent, no se crea uno nuevo (2026-08-31)

Decisión del usuario: en vez de un "Auditoría Agent" nuevo, se amplía `supervisor_agent.py`
(AgentFrameWork.md -- "no busca crear muchos agentes, busca crear una organización
eficiente"). Tres reglas mecánicas nuevas, todas deterministas (sin modelo, mismo principio
que el resto de Supervisor):

- **Artículos con datos sin verificar**: escanea el contenido de los artículos de Generador
  Agent en busca de un enlace que no sea el placeholder oficial, o un precio con cifra
  concreta -- ambos prohibidos en su prompt. Aplica literalmente la regla que pedía AGENTE
  ("que todo dato citado tenga fuente"), pero al revés: verificar que no se cuele un dato
  fabricado presentado como real.
- **Ideas de negocio sin fuente trazable**: tareas en fase 'idea' marcadas como investigación
  real (`source` de búsqueda real o de Claude) pero sin la marca `[fuente real: URL]` en su
  descripción.
- **Tareas huérfanas**: tareas que referencian un `related_knowledge_id` que ya no existe o
  está archivado.

Probado contra una copia de la base real (nunca la real directamente) y encontró dos cosas
genuinas: 9 decisiones pendientes de hace 35-36 días sin resolver (de antes de esta sesión,
nunca detectadas hasta ahora porque nadie había preguntado), y que los 8 temas sembrados hoy
por investigación real (sección anterior) no llevaban la marca `[fuente real:]` -- un
descuido al crearlos a mano sin pasar `fuente_url`. Corregido en la base real añadiendo la
URL exacta que originó cada tema (las mismas fuentes de la investigación de hoy). Verificado
de nuevo: el hallazgo desaparece, solo queda el genuino (las 9 decisiones estancadas, que
siguen pendientes de que el usuario las resuelva).

---

# Limpieza identificada, no destructiva por sí sola

- Carpeta JARVIS sin control de versiones hasta esta auditoría — corregido: primer commit
  del árbol completo, con `.gitignore` para credenciales, `*.db` y `*.log`.
- 12 carpetas raíz vacías (00_Core, 01_SecondBrain, 04_Logs, 05_Templates, 06_Standards,
  07_Research, 08_Experiments, 09_Sandbox, 11_Assets, 12_Tools, 13_AI, 99_Backups) y 27
  documentos `.md` vacíos — coherente con Roadmap.md ("fuera de alcance por ahora"). Se
  conservan a propósito como esqueleto de la taxonomía prevista (decisión del usuario).
- `flujo_completo.py`, `flujo_decision.py`, `flujo_orchestrator.py` (04_Implementation/)
  estaban supersedidos por `telegram_bot/bot.py`, que cubre el mismo flujo por lenguaje
  natural — retirados el 2026-08-31.

---

# Trading: arranque explícito del usuario (2026-08-31)

Contradice, a propósito y por decisión directa del usuario, la regla anterior de este
mismo documento ("Trading, sin empezar, deliberado -- va el último"). Esa regla existía
para que JARVIS nunca empezara Trading por su cuenta sin que el usuario lo pidiera --
el usuario lo pidió explícitamente hoy, con una especificación técnica completa propia
(backtesting.py, ccxt, Binance spot, criterios de eliminación fijados de antemano), así
que deja de aplicar el "todavía no". Sigue aplicando el resto de la Constitución: nada de
esto ejecuta operaciones ni toca capital real, es investigación offline sobre histórico.

Ver `04_Implementation/trading/README.md` para el plan completo (7 pasos), la estructura
de carpetas, y el hallazgo real del paso 1: un bug de `backtesting.py` (no soporta
unidades fraccionarias de BTC/ETH) que rompía silenciosamente los backtests con poco
capital de referencia, corregido antes de seguir. Vive fuera del patrón CEO
Agent/Orchestrator/Telegram del resto de JARVIS -- es un pipeline de investigación por
CLI, no algo que tenga sentido operar por lenguaje natural desde el móvil todavía; se
reconsiderará cuando exista algo que de verdad convenga exponer así (ej. "cómo va el
cribado", paper trading en marcha).

También detectado y resuelto en este paso: el entorno de Windows tiene **Smart App
Control** activo, que bloqueaba pandas 3.0.3 por falta de reputación (no un fallo de
compatibilidad) -- solucionado fijando `pandas==2.2.3` en `requirements.txt`, sin tocar
ninguna configuración de seguridad del sistema.

---

# Trading: cribado completo cerrado, pasos 1-5 (2026-08-31)

En la misma sesión se completaron los pasos 2-5 del plan de `trading/README.md`:
catálogo completo de 5 estrategias (trend-following ×2, mean-reversion ×2,
volatility breakout ×1), walk-forward multi-ventana, cribado completo con los 5
criterios de eliminación aplicados a escala real (30 combinaciones, 75s), y matriz
de correlación + selección de baja correlación.

Segundo bug real encontrado durante la construcción (el primero fue el capital de
referencia insuficiente, paso 1): `backtesting.py` devuelve Sharpe Ratio = NaN
cuando una ventana tiene 0-1 operaciones, y `nan < umbral` es `False` en Python --
sin corregirlo, una estrategia sin evidencia suficiente habría pasado el criterio
de Sharpe por accidente en vez de fallarlo. Corregido en `engine/validation.py`
(ignora NaN al promediar entre ventanas) y `engine/screening.py` (`math.isnan()`
explícito, siempre tratado como fallo).

Resultado real del primer cribado completo: **0 de 30 combinaciones sobreviven**
con los parámetros por defecto de cada estrategia (sin barrido de parámetros
todavía) -- resultado válido de investigación, no un pipeline roto. Detalle
completo en `trading/README.md` y `trading/results/cribado.csv`.

Decisión pendiente, no tomada en esta sesión: si se amplía el cribado con un
barrido de parámetros por estrategia antes de aceptar "0 supervivientes", o se
prueban familias de estrategia distintas. Pasos 6 (paper trading) y 7 (capital
real) no se han empezado -- son de una naturaleza distinta (procesos
persistentes, claves de API con permiso de trading) y requieren esa decisión
primero.

---

# Trading: barrido de parámetros, hallazgo estructural (2026-08-31)

A petición del usuario ("habrá que buscar más alternativas") se construyó
`config/param_grids.py` (rejillas de ~3 valores por parámetro por estrategia) y se
amplió `engine/screening.py` con `barrer_parametros=True`. Corrido a escala real:
204 combinaciones, 63 segundos. Siguen sin sobrevivir 0 de 204, pero el barrido
reveló POR QUÉ, cosa que el cribado sin parámetros no dejaba ver: hay una tensión
estructural real entre dos criterios, no un fallo del pipeline.

Timeframes bajos (diario, 4h) alcanzan Sharpe OOS > 1.0 en varias combinaciones
(hasta 1.41), pero ninguna genera las 30 operaciones OOS mínimas -- muy pocas
señales caben dentro del 30% out-of-sample de solo 4 ventanas. Timeframes altos
(1h) generan operaciones de sobra, pero el Sharpe cae por debajo de 1.0 -- más
operaciones significa más coste acumulado (comisión+spread+slippage) y más ruido.
Ninguna combinación resuelve ambos a la vez con el histórico y las ventanas
actuales. Detalle completo en `trading/results/cribado_barrido_parametros.csv`.

No se ha relajado ningún criterio para "arreglar" esto -- seguiría violando la
regla de fijarlos antes de ver resultados. Pendiente de decidir con el usuario:
ampliar el histórico hacia atrás de 2020 (más operaciones OOS sin bajar de
timeframe), probar timeframes intermedios (15m/30m, fuera del alcance original
de 1h/4h/1d), o directamente nuevas familias de estrategia.

---

# Trading: cierre de la sesión -- 490 combinaciones, dos casi-aciertos (2026-08-31)

Última tarea del día, a petición explícita del usuario: probar el punto 2 (timeframes
15m/30m) y luego el punto 3 (familias de estrategia nuevas) de las alternativas
anteriores, buscando llegar a varias estrategias reales para paper trading de 3-4
semanas. Se añadieron 15m/30m a `config/settings.py` y dos estrategias nuevas:
`macd_momentum` (familia momentum) y `pullback_consecutivo` (mean-reversion por
patrón de velas, no por indicador) -- ambas en `04_Implementation/trading/`.

Un intento inicial de correr el barrido completo en segundo plano se perdió por un
reinicio de sesión ("agent teardown", sin registro de finalización) -- relanzado en
primer plano con los datos ya cacheados para evitar depender de un proceso que
sobreviva entre turnos.

Tercer bug real encontrado (los dos anteriores fueron el capital de referencia
insuficiente y el Sharpe NaN, sesión anterior): `PullbackConsecutivo` no definía
`init()` -- `backtesting.Strategy` es abstracta y exige el método aunque no haga
nada; sin él, ni se podía instanciar la estrategia.

Total acumulado del día: 490 combinaciones evaluadas (30 + 204 + 184 + 72).
**Siguen sin sobrevivir 0 de 490 los 5 criterios a rajatabla**, pero aparecieron dos
casi-aciertos genuinos, cada uno fallando por un único criterio y por poco margen:

- `BTC/USDT 30m atr_breakout (periodo_atr=20, multiplicador=2.0)`: 144 operaciones
  OOS, drawdown -17.3%, rentabilidad OOS muy por encima de la IS -- solo falla
  Sharpe (0.94 frente a 1.0).
- `BTC/USDT 1d pullback_consecutivo (n_velas_bajistas=4)`: Sharpe 1.01 (SÍ pasa),
  drawdown -5.9%, rentabilidad OOS muy por encima de la IS -- solo fallan las
  operaciones (22 de las 30 mínimas).

No se ha relajado ningún criterio ni se ha declarado superviviente a ninguna de las
dos -- serían un sesgo de selección clásico ("la mejor de 490 pruebas"). Se han
dejado marcadas como candidatas razonables para paper trading (paso 6, todavía sin
diseñar ni empezar): el propio paper trading es la forma honesta de resolver esa
ambigüedad con datos nuevos que el proceso de búsqueda no vio. Detalle completo en
`trading/README.md`, sección "Resultado final del barrido ampliado".

---

# Trading: búsqueda iterativa, 3 supervivientes reales (2026-08-31, cierre definitivo)

El usuario pidió explícitamente una tarea iterativa: buscar entre 40-50 sistemas
reales de la práctica del trading (no inventados), probarlos por tandas contra
Binance real, guardar los que pasen los 5 criterios y seguir buscando si no,
hasta llegar a 3. Se hizo así: 3 tandas de 5 estrategias reales y documentadas
cada una (Turtle Trading, Parabolic SAR, Aroon, Vortex, CCI, Chaikin Money Flow,
On-Balance Volume, Williams %R, Stochastic RSI, "Double 7's" de Larry Connors,
Canal de Keltner, y variantes con filtro ADX de varias estrategias ya existentes),
15 estrategias nuevas sobre las 7 del cribado anterior -- 22 en total, 1.100+
combinaciones evaluadas en toda la sesión de Trading.

**Resultado: 3 de 3 -- objetivo cumplido.** Las tres pasan los 5 criterios de
forma limpia. Las tres resultaron ser la misma familia (`cruce_medias_adx`: cruce
de medias filtrado por ADX, la técnica real de "solo tradear el cruce cuando hay
tendencia confirmada") con distinto activo/timeframe/parámetros -- al ver que esa
familia daba el primer superviviente, se amplió SU rejilla de parámetros en vez de
seguir añadiendo familias sin evidencia, y de ahí salieron los otros dos. Baja
correlación entre ellas (0.13-0.27, sobre curvas de retornos reales) pese a
compartir familia.

Candidatas para paper trading (paso 6, README.md para el detalle numérico
completo):
1. ETH/USDT, 1h, rápida=20/lenta=50, ADX>25 -- Sharpe 1.19, drawdown -16.4%.
2. BTC/USDT, 1h, rápida=30/lenta=150, ADX>25 -- Sharpe 1.11, drawdown -13.7%.
3. BTC/USDT, 4h, rápida=10/lenta=50, ADX>20 -- Sharpe 1.02, drawdown -14.1%,
   pero con exactamente 30 operaciones OOS (el mínimo exacto, sin margen) --
   la más frágil de las tres por construcción del criterio, no por su Sharpe.

Bug real adicional (el cuarto de la sesión de Trading): `_cci` usaba
`rolling().apply(raw=False)`, 6-7x más lento que `raw=True` en el mismo backtest
por reconstruir una Series de pandas en cada ventana -- corregido antes de
escalar el cribado.

---

# Trading: corrección -- el usuario quería independencia real, no la misma técnica 3 veces (2026-08-31)

El usuario señaló, correctamente, que los 3 supervivientes anteriores no cumplían
lo pedido: eran los tres `cruce_medias_adx` (misma receta, distinto
activo/timeframe/parámetros), no tres formas independientes de leer el mercado.
Decisión del usuario: conservar el mejor de los tres (ETH/USDT 1h) como la
primera, y buscar 2 más de familias con lógica de señal genuinamente distinta.

Antes de seguir, se explicó Sharpe (rentabilidad ajustada al riesgo -- mismo
resultado final con menos sustos por el camino es mejor) y Drawdown (la peor
caída de pico a valle que sufre la cuenta en algún momento, no el resultado
final) en lenguaje llano, a petición del usuario.

Se retomó la búsqueda aplicando la MISMA idea real que ya había funcionado
(usar ADX para distinguir régimen de mercado) en su forma completa y
documentada: ADX alto confirma tendencia (ya usado), ADX bajo confirma rango
-- la contraparte estándar para mean-reversion. Aroon y Vortex (sin filtro)
se ampliaron primero pero mostraron un techo real en Sharpe ~0.86-0.97 que ni
un barrido más fino ni un stop-loss por ATR consiguieron superar (probado y
descartado explícitamente, no abandonado sin evidencia). El filtro de rango
sí funcionó: `bollinger_reversion_rango` (Bollinger + ADX<20) fue la segunda
superviviente real. Aplicando el mismo filtro de tendencia (ADX alto) que ya
funcionaba, pero sobre On-Balance Volume en vez de precio, salió la tercera:
`obv_tendencia_adx` -- primera superviviente basada en volumen de toda la
sesión.

Quinto bug real de la sesión de Trading: `engine/runner.py` solo importaba
`strategies.trend_following` desde el paso 1 -- `reporting/correlation.py`
(que depende de él) llevaba roto para cualquier estrategia de mean-reversion,
volatility-breakout o momentum desde que se creó, sin detectarse porque el
cribado (que sí importa las 4 familias) nunca pasa por `runner.py`. Corregido.

**Los 3 supervivientes finales, independientes de verdad**, correlación
0.01-0.11 entre ellos (más baja que los 0.13-0.27 de la ronda anterior, pese
a compartir menos técnica):
1. ETH/USDT 1h, cruce de medias + ADX alto (tendencia, precio) -- Sharpe 1.19.
2. BTC/USDT 4h, Bollinger + ADX bajo (reversión, precio) -- Sharpe 1.09,
   drawdown -5.7% (el mejor de las tres).
3. BTC/USDT 4h, OBV + ADX alto (tendencia, volumen) -- Sharpe 1.24 (el mejor).

Aviso honesto sobre la #2 y la #3: ambas tienen IS negativo y OOS positivo.
En la #3 esto es consistente en las 4 ventanas por separado (no un promedio
que esconde una mala), señal de robustez real, no de suerte de una sola
ventana -- pero es un patrón distinto al de la #1 y merece más atención en
paper trading. Detalle completo, incluida la explicación de Sharpe/Drawdown en
lenguaje llano, en `trading/README.md`.

---

# Trading: paper trading construido y en marcha (2026-09-01)

Paso 6 del plan. Antes de construir, se explicó qué es el paper trading en
lenguaje llano (simular en vivo con dinero falso, para validar lo que un
backtest no puede: que el sistema decide bien con datos que nunca vio la
búsqueda) y se aclaró si "el agente" (JARVIS/CEO Agent) interviene: el motor
en sí es un proceso programado que corre solo (mismo patrón que
`daily_briefing.py`), no una conversación -- pero sí reutiliza el bot de
Telegram existente para avisar de cada operación simulada y un resumen
diario, y no necesita Ollama porque las 3 estrategias son reglas
deterministas, no llamadas a IA.

Decisiones del usuario: 1.000€ virtuales por estrategia (no relacionado con
los 300€ reales), y avisos tanto por operación como resumen diario.

`04_Implementation/trading/paper/motor.py` reutiliza `engine.runner.
ejecutar_backtest()` sin duplicar lógica de señal -- cada revisión corre el
backtest completo hasta la vela más reciente y compara la posición actual
contra el estado guardado. Se añadió `data.fetch.actualizar_ohlcv()` para
traer solo las velas nuevas en cada revisión, en vez de re-descargar años
de histórico cada hora. Dos tareas programadas de Windows (mismo patrón que
el bot de Telegram): revisión horaria y resumen diario a las 09:00,
instalables con `scripts/instalar_tareas_paper_trading.ps1`.

Un detalle de diseño importante para no falsear el historial: la primera
vez que se revisa cada estrategia, si ya está en posición, se sincroniza el
estado real (fecha/precio de entrada reales de `_trades`) sin notificar --
de lo contrario se habría registrado una entrada falsa "ahora mismo" para
una posición que en realidad podría llevar abierta días.

Probado contra datos reales de Binance antes de dejarlo en marcha: primera
revisión sincroniza sin avisar, segunda revisión inmediata no genera ruido,
`actualizar_ohlcv` confirmado trayendo solo la vela nueva. Pendiente:
esperar los 3-4 semanas acordados y revisar qué estrategia(s) sobreviven de
verdad antes de tocar el paso 7 (capital real).

# Bot de Telegram: fallo de instancia duplicada, y charla libre con límites (2026-09-01)

**Fallo real encontrado y corregido**: el 409 Conflict de Telegram no era un
problema de Ollama, era `Stop-ScheduledTask` dejando vivo el proceso
`python.exe` real (confirmado en vivo dos veces: la tarea se paraba y el
proceso seguía respondiendo). Dos arreglos en `bot.py`: (1) un fallo
procesando un mensaje ya no tira el proceso entero (antes solo se
capturaban errores de red en `get_updates`, no excepciones en `handle`);
(2) un lock de instancia única (`msvcrt`, se libera solo al morir el
proceso) que hace que una segunda instancia se niegue a arrancar en vez de
competir por el mismo canal. También se sustituyeron los mensajes tipo
"Pensando a quién le toca esto..." por el indicador nativo de Telegram
(`sendChatAction`) -- exponer la mecánica interna del enrutado rompía la
sensación de estar hablando con alguien.

**Decisión de producto**: el usuario preguntó por qué el bot no puede
razonar libre "como Claude" en vez de depender de un catálogo de
categorías. Se explicaron las dos razones reales (el modelo local de 8B es
mucho más limitado para razonamiento abierto que uno en la nube, y el
catálogo fijo es lo que hace funcionar el control de Policy Engine sobre
acciones reales) y se propuso una opción intermedia, que el usuario
aceptó: charla/preguntas/opiniones se responden con razonamiento libre,
pero cualquier acción real (crear un agente, publicar, ejecutar algo)
sigue pasando por el catálogo fijo con Policy Engine de por medio -- no se
elimina el control, solo se relaja para lo que no tiene efectos.

Implementado como un agente nuevo, `agents/conversador_agent.py`
(autonomy_level 0, solo lee contexto de memoria y devuelve texto, nunca
escribe nada). Se añadió `"conversar"` al catálogo de `AGENTES_CEO`
(`orchestrator.py`) como la nueva categoría por defecto, sustituyendo a
`"nota"` en ese rol (`"nota"` ahora es solo para guardar algo que el
usuario pide explícitamente recordar). El prompt del CEO Agent
(`ceo_agent.py`) se actualizó con la regla de distinción y el fallback
seguro pasó de `"nota"` a `"conversar"` -- más seguro porque no escribe
nada en memoria ante una respuesta rara del modelo.

**Bug encontrado durante la prueba**: el campo `"texto"` que devuelve el
CEO Agent (pensado para "reformular con claridad" el mensaje) no es fiable
para charla libre -- el modelo de 8B a veces lo sustituye por su propio
razonamiento de clasificación o por una pregunta distinta a la del
usuario, en vez de la reformulación esperada (probado con varios mensajes,
comportamiento consistente, no un caso aislado). Arreglado en `bot.py`
pasándole a `conversador_agent` el mensaje original del usuario en vez de
`decision["texto"]`, solo para la rama `"conversar"` -- las demás
categorías conservan la reformulación, que sí les sirve.

# Trading: descartado por completo (2026-09-01)

Decisión del usuario tras ver el sistema funcionando de verdad, no antes:
con el paper trading ya corriendo en vivo y varias tandas de análisis
(rentabilidad real con 300€ a 6 meses/1 año/2 años, frecuencia real de
operaciones, y una búsqueda explícita de si aceptar más drawdown abría
paso a más rédito -- comprobado con los 1.743 resultados del cribado
completo: **ninguna** de las 175 combinaciones que superaban el 60% de
drawdown tenía Sharpe positivo, todas perdían dinero de forma consistente,
así que más riesgo no daba más rédito en este espacio de búsqueda), la
conclusión fue que el rédito esperado con 300€ no compensaba ni el esfuerzo
ni el riesgo real de perder el capital. Se exploró también una vía de
"apuesta" de alta frecuencia sin la validación estricta (walk-forward,
mínimo de operaciones) -- muestra más rédito potencial en el backtest, pero
también reconocido como más ruido que ventaja real.

**Acción tomada**: eliminación completa, no solo pausa.
- Carpeta `04_Implementation/trading/` borrada entera (backtesting, las 24
  estrategias, motor de paper trading, dashboard de resultados) -- recuperable
  del historial de git si hiciera falta consultar la metodología en el futuro.
- Tareas programadas de Windows `JARVIS Paper Trading - Revision` y
  `JARVIS Paper Trading - Resumen` detenidas; pendiente que el usuario las
  desinstale (`Unregister-ScheduledTask`) desde una PowerShell como
  Administrador -- Claude Code no tiene permisos para eso desde esta sesión.
- Sección "Paper trading" quitada de `dashboard/generar_dashboard.py` y de
  `pendientes.md`; la decisión pendiente `[Trading]` en Memory Engine
  resuelta como rechazada.

**Lo que se lleva de esta línea, aunque se descarte**: el pipeline entero
(backtesting.py, walk-forward sin fuga temporal, cribado con 5 criterios,
matriz de correlación) quedó construido, probado y documentado con rigor --
si en el futuro se retoma Trading con más capital o mejor tolerancia al
drawdown, no se empieza de cero, se empieza releyendo este documento y el
historial de git de la carpeta borrada.

**Siguiente paso, según el propio usuario**: buscar otras ideas de negocio
que sí den dinero, o replicar modelos de negocio que ya sean rentables
para otros -- sin definir todavía cuáles. Pendiente de conversación futura,
no de código.
