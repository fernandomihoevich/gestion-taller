@echo off
REM Script para ejecutar la aplicación Streamlit
cd /d "%~dp0"
python -m streamlit run app.py
pause
