@echo off
chcp 65001 > nul
title Compilador de YouTube Downloader Pro a .EXE
echo ======================================================================
echo           COMPILADOR DE YOUTUBE DOWNLOADER PRO A .EXE
echo ======================================================================
echo.

:: Crear carpeta temporal local en esta unidad para evitar fallos de espacio en C:
if not exist "tmp_build" mkdir "tmp_build"
set "TEMP=%~dp0tmp_build"
set "TMP=%~dp0tmp_build"
set "KIVY_HOME=%~dp0tmp_build\kivy"

echo Comprobando PyInstaller...
python -m pip show pyinstaller > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Instalando PyInstaller...
    python -m pip install pyinstaller
)

echo.
echo Iniciando proceso de compilación con PyInstaller...
echo (Este proceso puede tardar unos minutos...)
echo.

python -m PyInstaller --noconfirm --clean youtube_downloader.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo  ¡COMPILACIÓN EXITOSA!
    echo ======================================================================
    echo  El ejecutable portable se encuentra en la carpeta:
    echo  dist\YouTubeDownloaderPro\YouTubeDownloaderPro.exe
    echo ======================================================================
    echo.
) else (
    echo.
    echo ======================================================================
    echo  [ERROR] Ocurrió un fallo durante la compilación.
    echo ======================================================================
    echo.
)

pause
