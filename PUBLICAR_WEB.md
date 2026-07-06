# PUBLICAR EN LA WEB - GUÍA COMPLETA

## 🚀 OPCIÓN 1: Streamlit Cloud (Gratis - Recomendado para Comenzar)

### Ventajas:
- Completamente gratis
- Deploy automático desde GitHub
- Actualización instantánea con cada push

### Desventajas:
- Sin base de datos persistente (se pierde cada deploy)
- Límite de 1GB RAM

### Pasos:

1. **Sube el código a GitHub:**
   - Crea cuenta en https://github.com
   - Crea repo: `gestion-taller`
   - Sube tu carpeta completa

2. **Conecta a Streamlit Cloud:**
   - Ve a https://share.streamlit.io
   - Login con GitHub
   - Selecciona repo: `gestion-taller`
   - File path: `app.py`
   - Click "Deploy"

3. **URL Final:**
   ```
   https://[tu-usuario]-gestion-taller.streamlit.app
   ```

---

## 💾 OPCIÓN 2: Con Base de Datos Persistente (PostgreSQL + Render)

### Ventajas:
- Datos persisten entre actualizaciones
- Mejor para producción

### Pasos:

1. **Crear base de datos en Render:**
   - Ve a https://render.com
   - New Database → PostgreSQL
   - Copia la connection string

2. **Crear archivo `database.py`:**
   ```python
   import psycopg2
   import os
   
   def conectar_db():
       DATABASE_URL = os.environ.get('DATABASE_URL')
       conn = psycopg2.connect(DATABASE_URL)
       # Replicar las tablas que tienes en SQLite
       return conn
   ```

3. **Actualizar `app.py`:**
   - Cambiar de SQLite a PostgreSQL
   - Importar `database.py`

4. **Deploy a Render:**
   - New → Web Service
   - Conectar repo GitHub
   - Environment: `DATABASE_URL` = tu connection string
   - Publish

---

## 🔧 OPCIÓN 3: Con SQLite Sincronizado (Más Fácil)

Usar **Streamlit Cloud + AWS S3** para guardar la BD en la nube:

```python
import boto3
import sqlite3

s3_client = boto3.client('s3')

def guardar_db_en_s3():
    s3_client.upload_file('taller_gestion.db', 'mi-bucket', 'taller_gestion.db')

def cargar_db_desde_s3():
    s3_client.download_file('mi-bucket', 'taller_gestion.db', 'taller_gestion.db')
```

---

## 📊 Recomendación Según Tu Uso

### Si es **Prueba/Demo:**
→ Streamlit Cloud (gratis, sin BD)

### Si necesitas **Datos Persistentes:**
→ Render + PostgreSQL (~$12/mes)

### Si es **Aplicación Crítica:**
→ AWS/Azure/Google Cloud (~$20-100/mes)

---

## 🎯 PRIMER PASO: GitHub

Para cualquier opción, primero necesitas GitHub:

```bash
# Instala Git desde https://git-scm.com

# En tu carpeta Gestion_taller:
git init
git add .
git commit -m "Primera versión"
git remote add origin https://github.com/tu-usuario/gestion-taller.git
git branch -M main
git push -u origin main
```

¿Cuál opción prefieres? Puedo ayudarte a configurarla paso a paso.
