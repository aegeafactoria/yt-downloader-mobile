@echo off
chcp 65001 > nul
setlocal

title YouTube Downloader Pro - Lanzador
echo ========================================================
echo   Iniciando YouTube Downloader Pro...
echo ========================================================
echo.

rem Detectar el mejor intérprete de Python (preferir 3.13 / 3.12 / 3.11 sobre 3.14 preview)
set "PY_CMD=python"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    py -3.13 -c "import sys" >nul 2>&1 && set "PY_CMD=py -3.13" && goto :RUN
    py -3.12 -c "import sys" >nul 2>&1 && set "PY_CMD=py -3.12" && goto :RUN
    py -3.11 -c "import sys" >nul 2>&1 && set "PY_CMD=py -3.11" && goto :RUN
    py -3 -c "import sys" >nul 2>&1 && set "PY_CMD=py -3" && goto :RUN
)

:RUN
%PY_CMD% main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================================
    echo   [AVISO] La aplicación se cerró con código: %ERRORLEVEL%
    echo   Revisa el archivo 'startup.log' para ver los detalles.
    echo ========================================================
    echo.
    pause
)
