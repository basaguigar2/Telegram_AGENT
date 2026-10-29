@echo off
REM Lanzador del briefing diario de JARVIS.
REM Redirige toda la salida (incluidos errores) a briefing_run.log para
REM poder diagnosticar si algo falla cuando lo lanza el Programador de Tareas.

cd /d "%~dp0"
python daily_briefing.py >> briefing_run.log 2>&1
