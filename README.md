# Gestión de Taller - Aplicación Deployable

Aplicación web para gestionar operaciones de taller mecánico usando Streamlit.

## 📋 Requisitos Previos

- **Python 3.9 o superior** instalado en la máquina

## 🚀 Instalación Rápida (Windows)

### Opción 1: Automática (Recomendado)

1. Descarga o clona esta carpeta
2. Haz doble clic en `setup.bat` - instala automáticamente todas las dependencias
3. Luego haz doble clic en `run.bat` - ejecuta la aplicación

### Opción 2: Manual

1. Abre una terminal (cmd, PowerShell)
2. Navega a la carpeta del proyecto:
   ```bash
   cd ruta/a/Gestion_taller
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Ejecuta la aplicación:
   ```bash
   streamlit run app.py
   ```

## 📱 Usar la Aplicación

Una vez ejecutada, la aplicación se abrirá automáticamente en tu navegador en:
```
http://localhost:8501
```

## 📁 Estructura del Proyecto

```
Gestion_taller/
├── app.py                      # Código principal de la aplicación
├── taller_gestion.db          # Base de datos (se crea automáticamente)
├── comprobantes/              # Carpeta donde se guardan los PDFs generados
├── requirements.txt           # Dependencias del proyecto
├── setup.bat                  # Script de instalación (Windows)
├── run.bat                    # Script para ejecutar (Windows)
└── README.md                  # Este archivo
```

## 🔧 Para Compartir la Aplicación

Para distribuir esta aplicación a otras computadoras:

1. **Empaqueta la carpeta completa** (`Gestion_taller/`)
2. Envía por correo o comparte por USB/OneDrive
3. En la otra computadora:
   - Extrae la carpeta
   - Si es la primera vez: ejecuta `setup.bat`
   - Para usar: ejecuta `run.bat`

## ⚙️ Solución de Problemas

### "Python no está instalado o no está en PATH"
- Descarga Python desde https://www.python.org/downloads/
- **Importante**: Marca la opción "Add Python to PATH" durante la instalación
- Reinicia la computadora después de instalar

### Streamlit no se abre
- Abre una terminal manualmente
- Navega a la carpeta del proyecto
- Ejecuta: `streamlit run app.py`

### Error: "ModuleNotFoundError"
- Ejecuta nuevamente `setup.bat`
- O manualmente: `pip install -r requirements.txt`

## 📦 Dependencias

- **Streamlit** - Framework web para Python
- **Pandas** - Procesamiento de datos
- **FPDF2** - Generación de reportes en PDF

## 💾 Datos Persistentes

La aplicación usa una base de datos SQLite local (`taller_gestion.db`) que se guarda en la misma carpeta. Los datos se conservan entre ejecuciones.

## 📞 Soporte

Para problemas o sugerencias, revisa los logs de Streamlit en la terminal donde ejecutaste la aplicación.
