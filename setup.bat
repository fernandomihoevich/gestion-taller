@echo off
REM Script para instalar dependencias
echo ===================================
echo Instalando dependencias...
echo ===================================
cd /d "%~dp0"

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en PATH
    echo Descarga Python desde https://www.python.org/downloads/
    echo Asegúrate de marcar "Add Python to PATH" durante la instalación
    pause
    exit /b 1
)

REM Instalar dependencias
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ===================================
echo Instalación completada!
echo ===================================
echo.
echo Ahora puedes ejecutar: run.bat
pause
