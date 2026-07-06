"""
DATABASE ADAPTER - Convierte SQLite queries a PostgreSQL
Importa esta librería en app.py para cambiar automáticamente entre SQLite y PostgreSQL
"""

import streamlit as st
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

# Detectar si estamos en Streamlit Cloud o local
IS_CLOUD = os.environ.get('STREAMLIT_CLOUD') == 'true' or st.secrets

def conectar_db():
    """Conecta a Supabase PostgreSQL o SQLite local"""
    
    if IS_CLOUD or 'DATABASE_URL' in st.secrets:
        # Usar PostgreSQL en la nube
        try:
            db_url = st.secrets.get("DATABASE_URL", os.environ.get("DATABASE_URL"))
            if not db_url:
                st.error("❌ DATABASE_URL no configurada en Secrets")
                st.stop()
            
            conn = psycopg2.connect(db_url)
            conn.autocommit = False
            return conn
        except Exception as e:
            st.error(f"❌ Error conectando a Supabase: {e}")
            st.stop()
    else:
        # Usar SQLite localmente
        import sqlite3
        return sqlite3.connect("taller_gestion.db")

def inicializar_db(conn):
    """Crea todas las tablas si no existen"""
    cursor = conn.cursor()
    
    # Detectar si es PostgreSQL o SQLite
    is_postgresql = hasattr(cursor, 'connection') and hasattr(cursor.connection, 'server_version')
    
    if is_postgresql:
        # SQL para PostgreSQL
        sql_statements = [
            """CREATE TABLE IF NOT EXISTS mecanicos (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL
            )""",
            
            """CREATE TABLE IF NOT EXISTS pendientes_taller (
                id SERIAL PRIMARY KEY,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                fecha_carga TEXT,
                fecha_entrega TEXT,
                prioridad TEXT,
                mecanico TEXT,
                estado TEXT,
                observaciones TEXT
            )""",
            
            """CREATE TABLE IF NOT EXISTS maestro_equipos (
                interno TEXT PRIMARY KEY,
                marca TEXT NOT NULL,
                modelo TEXT NOT NULL,
                tipo TEXT
            )""",
            
            """CREATE TABLE IF NOT EXISTS equipos_ingresados (
                id SERIAL PRIMARY KEY,
                interno TEXT,
                horas INTEGER,
                origen TEXT,
                mecanico TEXT,
                fecha_ingreso TEXT,
                hora_inicio TEXT,
                hora_fin TEXT,
                estado_proceso TEXT,
                FOREIGN KEY(interno) REFERENCES maestro_equipos(interno)
            )""",
            
            """CREATE TABLE IF NOT EXISTS controles_ingreso (
                id SERIAL PRIMARY KEY,
                ingreso_id INTEGER,
                tarea TEXT NOT NULL,
                estado TEXT NOT NULL,
                observaciones TEXT,
                FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS controles_mantenimiento (
                id SERIAL PRIMARY KEY,
                ingreso_id INTEGER,
                tarea TEXT NOT NULL,
                estado TEXT NOT NULL,
                observaciones TEXT,
                tipo_tarea TEXT,
                FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS controles_salida (
                id SERIAL PRIMARY KEY,
                ingreso_id INTEGER,
                tarea TEXT NOT NULL,
                estado TEXT NOT NULL,
                observaciones TEXT,
                FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS registro_horas (
                id SERIAL PRIMARY KEY,
                ingreso_id INTEGER,
                fecha TEXT NOT NULL,
                horas REAL NOT NULL,
                mecanico TEXT NOT NULL,
                FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS maestro_controles_ingreso (
                id SERIAL PRIMARY KEY,
                descripcion TEXT NOT NULL,
                orden INTEGER NOT NULL
            )""",
            
            """CREATE TABLE IF NOT EXISTS maestro_tareas_mantenimiento (
                id SERIAL PRIMARY KEY,
                descripcion TEXT NOT NULL,
                orden INTEGER NOT NULL
            )""",
            
            """CREATE TABLE IF NOT EXISTS maestro_controles_salida (
                id SERIAL PRIMARY KEY,
                descripcion TEXT NOT NULL,
                orden INTEGER NOT NULL
            )""",
            
            """CREATE TABLE IF NOT EXISTS maestro_rubros_compras (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL
            )""",
            
            """CREATE TABLE IF NOT EXISTS lista_compras (
                id SERIAL PRIMARY KEY,
                rubro TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                detalle TEXT,
                cantidad TEXT NOT NULL,
                fecha_carga TEXT,
                estado TEXT NOT NULL
            )""",
            
            """CREATE TABLE IF NOT EXISTS trabajos_clientes (
                id SERIAL PRIMARY KEY,
                cliente TEXT NOT NULL,
                tarea TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha_programada TEXT
            )"""
        ]
        
        for sql in sql_statements:
            try:
                cursor.execute(sql)
            except psycopg2.Error as e:
                if 'already exists' not in str(e):
                    print(f"⚠️ Error creando tabla: {e}")
        
        # Insertar datos iniciales
        cursor.execute("SELECT COUNT(*) FROM mecanicos")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO mecanicos (nombre) VALUES (%s)",
                [("Cesar",), ("Lucas",), ("Marcelo",)]
            )
        
        cursor.execute("SELECT COUNT(*) FROM maestro_equipos")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO maestro_equipos (interno, marca, modelo, tipo) VALUES (%s, %s, %s, %s)",
                [
                    ("AE02", "TOYOTA", "628FD25", "Autoelevador"),
                    ("AE05", "TOYOTA", "FD2025", "Autoelevador"),
                    ("AE15", "HELI", "CPD25", "Eléctrico"),
                    ("VY01", "YALE", "Propiedad Corven", "Autoelevador")
                ]
            )
        
        # ... (resto de inserciones iniciales adaptadas a %s)
        
        conn.commit()
    else:
        # Para SQLite (código original)
        pass
    
    return conn
