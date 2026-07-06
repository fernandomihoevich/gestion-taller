import streamlit as st
import sqlite3
import boto3
import os
from io import BytesIO
import shutil

# --- CONFIGURACIÓN AWS S3 ---
AWS_ACCESS_KEY = st.secrets.get("AWS_ACCESS_KEY", os.environ.get("AWS_ACCESS_KEY"))
AWS_SECRET_KEY = st.secrets.get("AWS_SECRET_KEY", os.environ.get("AWS_SECRET_KEY"))
S3_BUCKET = st.secrets.get("S3_BUCKET", os.environ.get("S3_BUCKET"))
DB_FILE = "taller_gestion.db"

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def descargar_db_desde_s3():
    """Descarga la BD de S3 al inicio"""
    try:
        s3_client.download_file(S3_BUCKET, DB_FILE, DB_FILE)
        print(f"✓ BD descargada desde S3")
    except:
        print(f"⚠ Primera ejecución: creando nueva BD")
        pass

def guardar_db_en_s3():
    """Guarda la BD a S3 después de cambios"""
    try:
        s3_client.upload_file(DB_FILE, S3_BUCKET, DB_FILE)
        print(f"✓ BD sincronizada con S3")
    except Exception as e:
        print(f"❌ Error sincronizando BD: {e}")

# Descargar BD al iniciar la app
if not os.path.exists(DB_FILE):
    descargar_db_desde_s3()

# --- EL RESTO DE TU CÓDIGO SIGUE IGUAL ---
# Solo agregamos esta línea al final de cada operación que modifique la BD:
# guardar_db_en_s3()
