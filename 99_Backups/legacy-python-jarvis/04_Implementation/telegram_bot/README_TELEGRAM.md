# Interfaz de Telegram — puesta en marcha

## 1. Crear el bot

En Telegram, busca **@BotFather** y escríbele `/newbot`. Te pedirá un nombre
y un usuario (debe terminar en "bot", ej. `jarvis_basi_bot`). Al terminar te
da un **token** (algo como `123456789:AAExxxxxxxxxxxxxxxxxxxxxxx`).

## 2. Instalar la dependencia que falta

Desde una terminal:
```
pip install requests
```
(Muy probablemente ya la tengas instalada por otras librerías, pero por si acaso.)

## 3. Configurar el token

Abre `04_Implementation/telegram_bot/config.json` y sustituye
`PON_AQUI_TU_TOKEN_DE_BOTFATHER` por el token real, entre comillas.

## 4. Primer arranque — obtener tu chat_id

Ejecuta:
```
python 04_Implementation\telegram_bot\bot.py
```
Abre Telegram, busca tu bot por el usuario que le pusiste, y mándale
cualquier mensaje (ej. "hola"). El bot te responderá con tu `chat_id`.
Copia ese número, ciérralo (Ctrl+C), y pégalo en `config.json`:
```json
{
  "bot_token": "tu_token_real",
  "allowed_chat_id": 123456789
}
```
Este paso es el único control de acceso que tiene el sistema — sin esto
configurado, el bot no te deja hacer nada (y con otro chat_id, tampoco).

## 5. Arrancar de verdad

```
python 04_Implementation\telegram_bot\bot.py
```
Déjalo corriendo. Desde el móvil, escríbele:

- Cualquier texto normal → lo guarda como nota, te pide confirmación.
- `/pregunta 3|media|¿qué hago esta tarde?` → recomendación directa.
- `/codigo función que sume dos números|scripts/suma.py` → te enseña el código propuesto y pide confirmación antes de guardar.
- `/help` → recuerda los comandos.

## 6. Dejarlo corriendo solo, incluso tras reiniciar Windows

A diferencia del briefing diario (que se dispara una vez y termina), el bot
tiene que quedarse corriendo todo el rato. Para eso:

1. Abre PowerShell (no hace falta administrador, pero si Windows pide permiso, acéptalo).
2. Ve a la carpeta del bot:
   ```
   cd "C:\Users\basag\OneDrive\Documentos\JARVIS\04_Implementation\telegram_bot"
   ```
3. Ejecuta el script de instalación:
   ```
   .\instalar_tarea_inicio.ps1
   ```
   Si PowerShell se queja de que no permite ejecutar scripts, ejecuta antes
   (una sola vez): `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Esto registra una tarea llamada "JARVIS Telegram Bot" que arranca sola cada
vez que inicias sesión en Windows, sin ventana visible, sin límite de tiempo
de ejecución, y que se reinicia sola hasta 5 veces si se cae por algún error.

Para arrancarla ya mismo sin reiniciar el PC:
```
Start-ScheduledTask -TaskName "JARVIS Telegram Bot"
```

Si algo falla, revisa `04_Implementation/telegram_bot/bot.log` — ahí queda
todo lo que antes veías por consola.

Para pararla: `Stop-ScheduledTask -TaskName "JARVIS Telegram Bot"`.
Para quitarla del todo: `Unregister-ScheduledTask -TaskName "JARVIS Telegram Bot" -Confirm:$false`.

Recuerda: **el bot solo responde si tu Victus está encendido, conectado a
internet, y con Ollama corriendo.** Si el portátil está apagado o dormido,
no vas a recibir respuesta hasta que vuelva a estar activo.

## Seguridad — no lo olvides

No compartas el token del bot ni el `allowed_chat_id` con nadie. Si el
token se filtra, cualquiera con ese token puede intentar hablarle al bot
(aunque el `allowed_chat_id` los bloquea, es mejor no depender solo de esa
capa). Si sospechas que el token se ha filtrado, en @BotFather puedes
regenerarlo con `/token`.
