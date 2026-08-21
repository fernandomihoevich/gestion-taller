# PUBLICAR EN LA WEB - GUÍA COMPLETA

## 🚀 OPCIÓN 1: Streamlit Cloud (Gratis - Recomendado para Comenzar)

### Ventajas:
- Completamente gratis
- Deploy automático desde GitHub
- Actualización instantánea con cada push

### Desventajas:
- El filesystem local es temporal; no debe usarse para guardar datos
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

## 💾 OPCIÓN 2: Con Base de Datos Persistente (Supabase Free)

### Ventajas:
- Datos persisten entre actualizaciones
- El plan Free de Supabase evita depender del filesystem temporal de Streamlit
- No requiere AWS S3 ni un servidor adicional

### Pasos:

1. En Supabase, abre tu proyecto Free y copia la conexión PostgreSQL.
2. En Streamlit Cloud, abre la app → **Settings → Secrets**.
3. Pega únicamente esta variable, usando la URL del pooler si la conexión directa falla:
   ```toml
   DATABASE_URL = "postgresql://postgres.TU_PROYECTO:TU_CONTRASENA@aws-0-REGION.pooler.supabase.com:6543/postgres"
   ```
4. Guarda y pulsa **Reboot app**.

La app usa PostgreSQL como fuente principal y bloquea el arranque si Streamlit
Cloud no encuentra `DATABASE_URL`, para no escribir datos en almacenamiento temporal.

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
→ Streamlit Cloud + Supabase Free

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
