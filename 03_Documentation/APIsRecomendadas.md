# APIs recomendadas para JARVIS

Fuente: [github.com/public-apis/public-apis](https://github.com/public-apis/public-apis).

Nota sobre el origen de cada entrada: el fetch del README se truncó a mitad
de contenido (el repo es enorme), así que pude leer completas las categorías
Business, Calendar, Currency Exchange, Data Validation, Development,
Dictionaries, Documents & Productivity, Email, Entertainment, Environment,
Events, Finance y Food & Drink. Las marco como **(repo)**. Para categorías
del mismo repo que no llegué a leer completas por el corte (Weather, News,
Machine Learning, Jobs, Science & Math, Text Analysis, Open Data, entre
otras) incluyo APIs conocidas que sé que están listadas ahí, marcadas como
**(conocimiento general, no verificado línea a línea en esta sesión)** --
antes de integrar cualquiera de estas conviene confirmar el link exacto en
el repo.

Organizado por qué le aportaría a JARVIS, no por el orden alfabético del repo.

## Clima (contexto para Decision Engine / recomendaciones de energía-tiempo)

- **Open-Meteo** -- pronóstico y clima histórico, sin API key, gratuito sin
  límites agresivos. La opción más simple para JARVIS: nada de auth que
  gestionar. (conocimiento general)
- **OpenWeatherMap** -- clima actual, pronóstico y alertas, apiKey gratuita
  con cuota razonable. Muy usada como referencia. (conocimiento general)

## Noticias y contexto del mundo (para Context Engine)

- **NewsAPI.org** -- headlines y búsqueda de noticias por tema/fuente/idioma,
  apiKey. (conocimiento general)
- **GNews** -- alternativa a NewsAPI, cuota gratuita más generosa.
  (conocimiento general)

## Productividad y documentos (para Capture Agent / Builder Agent)

- **Notion API** -- OAuth, leer/escribir páginas y bases de datos. Encaja si
  en algún momento JARVIS sincroniza Knowledge Engine con Notion. **(repo)**
- **Todoist API** -- OAuth, listas de tareas. Relevante si el sistema de
  tareas (`task` table, hoy fuera de alcance) se retoma más adelante. **(repo)**
- **Google Sheets / Google Docs / Google Keep API** -- OAuth, leer/escribir.
  Útil si se quiere exportar Memory Engine o Backlog a algo que el usuario
  pueda editar fuera del bot. **(repo)**
- **OCR.Space** -- OCR de imágenes/PDF con capa gratuita, apiKey. Útil si
  Capture Agent alguna vez recibe fotos de notas manuscritas por Telegram.
  **(repo)**
- **iLovePDF API** -- convertir/combinar/dividir PDFs, apiKey, gratis hasta
  250 documentos/mes. **(repo)**

## Calendario y tiempo (para Decision Engine)

- **Nager.Date** -- festivos públicos de más de 90 países, sin auth, HTTPS.
  Útil para que el motor de decisión sepa si hoy es festivo antes de
  recomendar algo. **(repo)**
- **Google Calendar API** -- OAuth, leer/crear/modificar eventos. Si JARVIS
  algún día gestiona la agenda real del usuario, esta es la integración
  natural. **(repo)**

## Finanzas personales (si el proyecto crece hacia gestión financiera)

- **Frankfurter** -- tipos de cambio y series históricas, sin auth, HTTPS,
  CORS. La más simple para convertir divisas sin gestionar apiKey. **(repo)**
- **Exchangerate.host** -- tipos de cambio y cripto, gratis, sin auth.
  **(repo)**
- **FRED (Federal Reserve Bank of St. Louis)** -- series macroeconómicas
  (inflación, tipos de interés, etc.), apiKey gratuita. Útil si algún agente
  analiza contexto económico. **(repo)**
- **Plaid** -- conectar con cuentas bancarias reales y leer transacciones,
  apiKey. Es el estándar del sector para esto, pero implica dar acceso a
  datos bancarios reales -- valorar con calma antes de integrar. **(repo)**

## Machine Learning / IA complementaria (si algún agente necesita algo que Ollama local no cubre bien)

- **Hugging Face Inference API** -- modelos alojados (visión, audio, NLP
  especializado) vía apiKey, para tareas puntuales que un modelo local
  pequeño no resuelve bien. (conocimiento general)
- **IBM Text to Speech** -- texto a voz, apiKey. Relevante si el bot alguna
  vez responde con audio en Telegram. **(repo)**

## Datos abiertos y ciencia (para Knowledge Engine / Research futuro)

- **Wikipedia/Wikidata API** -- sin auth, consulta de conocimiento
  enciclopédico y datos estructurados. Buen respaldo cuando Knowledge Engine
  necesita verificar un hecho. (conocimiento general)
- **SEC EDGAR** -- informes anuales de empresas públicas de EE.UU., sin
  auth. **(repo)**

## Desarrollo / infraestructura del propio JARVIS

- **GitHub API** -- OAuth, gestionar repos, issues, commits
  programáticamente. Relevante si Builder Agent alguna vez sincroniza
  agentes generados con un repo real (versión de las agent .py que hoy solo
  viven en el filesystem local). **(repo)**
- **IPinfo / IPify** -- IP y geolocalización básica, sin auth. Útil si algún
  agente necesita saber ubicación aproximada sin pedir nada al usuario.
  **(repo)**
- **QuickChart** -- generar gráficos e imágenes de charts desde datos, sin
  auth, HTTPS, CORS. Podría usarlo Process Narrator Agent o un futuro
  reporting agent para mandar gráficos por Telegram en vez de solo texto.
  **(repo)**

## Email (si JARVIS necesita notificar o leer fuera de Telegram)

- **Sendgrid** -- envío de emails transaccionales, apiKey. **(repo)**
- **Hunter** -- búsqueda/verificación de emails, apiKey. Menos prioritario,
  más orientado a prospección que a uso personal. **(repo)**

## Ocio / respaldo para Creative Agent

- **chucknorris.io**, **Bored API** (actividades random contra el
  aburrimiento) -- sin auth. Baja prioridad, pero triviales de integrar si
  Creative Agent alguna vez necesita un input aleatorio como semilla de
  brainstorm. **(repo)**

---

## Recomendación de prioridad

Para el estado actual de JARVIS (Memory/Knowledge/Context/Decision/Policy
Engine + agentes locales), lo que más aportaría primero, en este orden:

1. **Open-Meteo** (clima) -- gratis, sin auth, cero fricción, alimenta
   directamente a Decision Engine.
2. **Nager.Date** (festivos) -- mismo motivo, sin auth.
3. **Frankfurter** (tipos de cambio) -- solo si hay un caso de uso financiero
   real ya identificado, si no, esperar.
4. **Google Calendar API** -- el salto de mayor valor, pero requiere OAuth y
   pedir permisos reales del usuario, así que conviene decidirlo
   deliberadamente y no meterlo "porque está en la lista".

El resto son candidatas razonables pero no urgentes -- las dejo apuntadas
para cuando surja el caso de uso concreto en vez de integrar por integrar.
