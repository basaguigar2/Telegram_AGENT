@echo off
REM Lanzador del bot de Telegram de JARVIS.
REM Redirige toda la salida (incluidos errores) a bot.log para poder
REM diagnosticar si algo falla mientras corre oculto en segundo plano.

cd /d "%~dp0"
python bot.py >> bot.log 2>&1
