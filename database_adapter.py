"""
DATABASE ADAPTER - Convierte SQLite queries a PostgreSQL
Importa esta librería en app.py para cambiar automáticamente entre SQLite y PostgreSQL
"""

import os
import shutil
import sqlite3
import time
from datetime import datetime

import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover - entorno no Streamlit
    st = None

psycopg2 = None
RealDictCursor = None


def _import_psycopg2():
    """Importa psycopg2 solo cuando se necesita."""
    global psycopg2, RealDictCursor
    if psycopg2 is not None:
        return psycopg2

    try:
        import psycopg2 as _psycopg2
        from psycopg2.extras import RealDictCursor as _RealDictCursor
        psycopg2 = _psycopg2
        RealDictCursor = _RealDictCursor
    except ImportError:
        psycopg2 = None
        RealDictCursor = None
    return psycopg2


def _is_cloud_environment():
    """Detecta si la app está corriendo en un entorno con secretos de Streamlit."""
    if os.environ.get('STREAMLIT_CLOUD') == 'true' or os.environ.get('DATABASE_URL'):
        return True
    if st is None:
        return False
    try:
        return bool(st.secrets)
    except Exception:
        return False


# Detectar si estamos en Streamlit Cloud o local
IS_CLOUD = _is_cloud_environment()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_USER_DATA_DIR = os.path.join(os.path.expanduser("~"), ".taller_gestion")
DATA_DIR = os.path.join(BASE_DIR, "data") if IS_CLOUD else DEFAULT_USER_DATA_DIR
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
LEGACY_DB_PATH = os.path.join(BASE_DIR, "taller_gestion.db")
BACKUP_RETENTION = int(os.environ.get("TALLER_BACKUP_RETENTION", "5"))
SYNC_INTERVAL_SECONDS = int(os.environ.get("TALLER_SYNC_INTERVAL_SECONDS", "300"))
LAST_SYNC_TS = None


def get_database_path():
    """Devuelve una ruta persistente para la base de datos local."""
    override = os.environ.get("TALLER_DB_PATH") or os.environ.get("DB_PATH")
    if override:
        candidate = override if os.path.dirname(override) else os.path.join(DATA_DIR, override)
        path = os.path.abspath(candidate)
    else:
        path = os.path.join(DATA_DIR, "taller_gestion.db")

    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def ensure_database_file():
    """Migra la base de datos antigua al nuevo path si corresponde."""
    db_path = get_database_path()
    if os.path.exists(LEGACY_DB_PATH) and not os.path.exists(db_path):
        try:
            shutil.copy2(LEGACY_DB_PATH, db_path)
            print(f"✅ Base de datos migrada a {db_path}")
        except Exception as exc:
            print(f"⚠️ No se pudo migrar la base de datos: {exc}")
    return db_path


def crear_respaldo_db(db_path=None):
    """Crea un respaldo timestampado de la base SQLite."""
    db_path = db_path or get_database_path()
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"taller_gestion_{stamp}.db")
    try:
        shutil.copy2(db_path, backup_path)
    except Exception as exc:
        print(f"⚠️ No se pudo crear el respaldo: {exc}")
        return None

    # Si está configurado S3, intentar subir el respaldo automáticamente
    s3_cfg = _get_s3_config()
    if s3_cfg and os.path.exists(backup_path):
        key = backup_path.replace("\\", "/")
        # Use prefix si está definido
        prefix = s3_cfg.get("S3_PREFIX") or ""
        if prefix:
            key = f"{prefix.rstrip('/')}/{os.path.basename(backup_path)}"
        else:
            key = os.path.basename(backup_path)

        try:
            uploaded = upload_file_to_s3(backup_path, s3_cfg.get("S3_BUCKET"), key,
                                         aws_access_key_id=s3_cfg.get("AWS_ACCESS_KEY_ID"),
                                         aws_secret_access_key=s3_cfg.get("AWS_SECRET_ACCESS_KEY"),
                                         region=s3_cfg.get("AWS_REGION"))
            if uploaded:
                print(f"✅ Respaldo subido a S3: {s3_cfg.get('S3_BUCKET')}/{key}")
            else:
                print("⚠️ No se pudo subir el respaldo a S3")
        except Exception as exc:
            print(f"⚠️ Error subiendo respaldo a S3: {exc}")

    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("taller_gestion_") and f.endswith(".db")])
    while len(backups) > BACKUP_RETENTION:
        os.remove(os.path.join(BACKUP_DIR, backups[0]))
        backups = backups[1:]
    return backup_path


def _get_s3_config():
    """Lee configuración de S3 desde variables de entorno o `st.secrets`.
    Devuelve un dict con keys: S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, S3_PREFIX
    """
    cfg = {}
    # Primero desde entorno
    cfg['S3_BUCKET'] = os.environ.get('S3_BUCKET') or os.environ.get('TALLER_S3_BUCKET')
    cfg['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID')
    cfg['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
    cfg['AWS_REGION'] = os.environ.get('AWS_REGION')
    cfg['S3_PREFIX'] = os.environ.get('S3_PREFIX')

    # Si hay streamlit secrets, permiten sobreescribir/alternativa
    if st is not None:
        try:
            secrets = getattr(st, 'secrets', {}) or {}
            cfg['S3_BUCKET'] = cfg['S3_BUCKET'] or secrets.get('S3_BUCKET')
            cfg['AWS_ACCESS_KEY_ID'] = cfg['AWS_ACCESS_KEY_ID'] or secrets.get('AWS_ACCESS_KEY_ID')
            cfg['AWS_SECRET_ACCESS_KEY'] = cfg['AWS_SECRET_ACCESS_KEY'] or secrets.get('AWS_SECRET_ACCESS_KEY')
            cfg['AWS_REGION'] = cfg['AWS_REGION'] or secrets.get('AWS_REGION')
            cfg['S3_PREFIX'] = cfg['S3_PREFIX'] or secrets.get('S3_PREFIX')
        except Exception:
            pass

    # Requerimos al menos el bucket para considerar activa la subida
    if not cfg.get('S3_BUCKET'):
        return None
    return cfg


def upload_file_to_s3(file_path, bucket, key, aws_access_key_id=None, aws_secret_access_key=None, region=None):
    """Sube un archivo a S3 usando boto3. Devuelve True si tuvo éxito."""
    try:
        import boto3
    except Exception:
        print("⚠️ boto3 no está instalado; no se puede subir a S3")
        return False

    session_kwargs = {}
    if aws_access_key_id and aws_secret_access_key:
        session_kwargs['aws_access_key_id'] = aws_access_key_id
        session_kwargs['aws_secret_access_key'] = aws_secret_access_key
    if region:
        session_kwargs['region_name'] = region

    try:
        session = boto3.session.Session(**session_kwargs) if session_kwargs else boto3
        s3 = session.client('s3') if hasattr(session, 'client') else boto3.client('s3')
        s3.upload_file(file_path, bucket, key)
        return True
    except Exception as exc:
        print(f"⚠️ Error subiendo a S3: {exc}")
        return False


def _get_database_url():
    """Devuelve la URL de Supabase/PostgreSQL si está configurada."""
    if os.environ.get("DATABASE_URL"):
        return os.environ.get("DATABASE_URL")
    if st is not None:
        try:
            return st.secrets.get("DATABASE_URL")
        except Exception:
            return None
    return None


def has_remote_db():
    """Indica si hay una base remota configurada y psycopg2 disponible."""
    return _has_remote_db()


def is_persistent_backend_available():
    """Devuelve True si la app tiene un backend persistente disponible.

    En entornos Cloud (Streamlit) esto requiere `DATABASE_URL` configurada.
    Localmente, el filesystem se considera persistente.
    """
    if IS_CLOUD:
        return _has_remote_db()
    return True


def _has_remote_db():
    if _import_psycopg2() is None:
        return False
    return bool(_get_database_url())


def _remote_db_is_empty(db_url=None):
    """Comprueba si la base de datos remota tiene tablas en el schema public."""
    psy = _import_psycopg2()
    if psy is None:
        return True
    db_url = db_url or _get_database_url()
    if not db_url:
        return True
    try:
        conn = psy.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';")
        count = cur.fetchone()[0]
        conn.close()
        return count == 0
    except Exception:
        return True


def _local_db_is_empty(db_path):
    if not os.path.exists(db_path):
        return True
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        count = cursor.fetchone()[0]
        conn.close()
        return count == 0
    except Exception:
        return True


def restaurar_desde_supabase(db_path=None, force=False):
    """Restaura la base local desde Supabase si está disponible."""
    db_path = db_path or get_database_path()
    if not _has_remote_db():
        return False
    if not force and not _local_db_is_empty(db_path):
        return False

    db_url = _get_database_url()
    if not db_url:
        return False

    psycopg2 = _import_psycopg2()
    if psycopg2 is None:
        return False

    try:
        conn_pg = psycopg2.connect(db_url)
        conn_pg.autocommit = False
        conn_sqlite = sqlite3.connect(db_path)
        cursor_sqlite = conn_sqlite.cursor()

        tables = ["mecanicos", "pendientes_taller", "maestro_equipos", "equipos_ingresados", "controles_ingreso", "controles_mantenimiento", "controles_salida", "registro_horas", "maestro_controles_ingreso", "maestro_tareas_mantenimiento", "maestro_controles_salida", "maestro_rubros_compras", "lista_compras", "trabajos_clientes"]

        for table in tables:
            try:
                cursor_sqlite.execute(f"CREATE TABLE IF NOT EXISTS {table} AS SELECT * FROM {table} WHERE 1=0")
            except Exception:
                pass

        for table in tables:
            try:
                cursor = conn_pg.cursor()
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                if not rows:
                    continue

                cursor_sqlite.execute(f"DELETE FROM {table}")
                placeholders = ", ".join(["?"] * len(columns))
                cursor_sqlite.executemany(
                    f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                    [tuple(row) for row in rows]
                )
            except Exception as exc:
                print(f"⚠️ No se pudo restaurar tabla {table}: {exc}")

        conn_sqlite.commit()
        conn_sqlite.close()
        conn_pg.close()
        return True
    except Exception as exc:
        print(f"⚠️ No se pudo restaurar desde Supabase: {exc}")
        return False


def ensure_remote_restore(db_path=None):
    """Restaura la base local desde Supabase si la base local está vacía."""
    db_path = db_path or get_database_path()
    if _has_remote_db() and _local_db_is_empty(db_path):
        return restaurar_desde_supabase(db_path)
    return False


def sincronizar_supabase(db_path=None):
    """Sincroniza la base SQLite local con Supabase si hay DATABASE_URL configurada."""
    global LAST_SYNC_TS
    db_path = db_path or get_database_path()
    if not _has_remote_db():
        return False

    try:
        db_url = _get_database_url()
        if not db_url:
            return False
        if LAST_SYNC_TS is not None and (time.time() - LAST_SYNC_TS) < SYNC_INTERVAL_SECONDS:
            return True

        psycopg2 = _import_psycopg2()
        if psycopg2 is None:
            return False

        conn_pg = psycopg2.connect(db_url)
        conn_sqlite = sqlite3.connect(db_path)
        cur_pg = conn_pg.cursor()
        cur_sql = conn_sqlite.cursor()

        tables = ["mecanicos", "pendientes_taller", "maestro_equipos", "equipos_ingresados", "controles_ingreso", "controles_mantenimiento", "controles_salida", "registro_horas", "maestro_controles_ingreso", "maestro_tareas_mantenimiento", "maestro_controles_salida", "maestro_rubros_compras", "lista_compras", "trabajos_clientes"]

        for table in tables:
            try:
                rows = cur_sql.execute(f"SELECT * FROM {table}").fetchall()
                if rows is None:
                    continue
                columns = [col[1] for col in cur_sql.execute(f"PRAGMA table_info({table})").fetchall()]
                placeholders = ", ".join(["%s"] * len(columns))
                cur_pg.execute(f"DELETE FROM {table}")
                if rows:
                    cur_pg.executemany(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", [tuple(row) for row in rows])
                if "id" in columns:
                    cur_pg.execute("SELECT pg_get_serial_sequence(%s, 'id')", (table,))
                    seq = cur_pg.fetchone()[0]
                    if seq:
                        cur_pg.execute(f"SELECT setval(%s, (SELECT MAX(id) FROM {table}), true)", (seq,))
            except Exception as exc:
                print(f"⚠️ No se pudo sincronizar tabla {table}: {exc}")

        conn_pg.commit()
        conn_pg.close()
        conn_sqlite.close()
        LAST_SYNC_TS = time.time()
        return True
    except Exception as exc:
        print(f"⚠️ No se pudo sincronizar con Supabase: {exc}")
        return False


def _commit_with_backup(self, *args, **kwargs):
    """Commit local + respaldo + sincronización opcional con Supabase."""
    try:
        result = _sqlite_commit(self, *args, **kwargs)
    except Exception:
        raise

    try:
        db_path = get_database_path()
        crear_respaldo_db(db_path)
        sincronizar_supabase(db_path)
    except Exception as exc:
        print(f"⚠️ Error en respaldo/sincronización: {exc}")
    return result


# Hook automático para que cada commit guarde respaldo y sincronice si aplica.
try:
    import sqlite3 as _sqlite3_module
    _sqlite_commit = _sqlite3_module.Connection.commit
    _sqlite3_module.Connection.commit = _commit_with_backup
except Exception:
    pass


def conectar_db():
    """Conecta a Supabase PostgreSQL o SQLite local"""
    db_path = ensure_database_file()

    # Si hay DB remota disponible, evaluar estado y sincronizar según corresponda
    if _has_remote_db():
        try:
            db_url = _get_database_url()
            psy = _import_psycopg2()
            if psy and db_url:
                remote_empty = _remote_db_is_empty(db_url)
                local_empty = _local_db_is_empty(db_path)

                # Caso 1: remoto vacío y local tiene datos -> inicializar y empujar local->remoto
                if remote_empty and not local_empty:
                    try:
                        conn_pg = psy.connect(db_url)
                        conn_pg.autocommit = False
                        inicializar_db(conn_pg)
                        conn_pg.commit()
                        conn_pg.close()
                        sincronizar_supabase(db_path)
                    except Exception as exc:
                        print(f"⚠️ No se pudo inicializar/sincronizar remoto: {exc}")

                # Caso 2: remoto con datos y local vacío -> restaurar remoto->local
                if not remote_empty and local_empty:
                    try:
                        restaurar_desde_supabase(db_path)
                    except Exception:
                        pass
        except Exception:
            pass

    if _has_remote_db() and psycopg2 is not None:
        # Usar PostgreSQL en la nube cuando haya URL remota disponible
        try:
            db_url = _get_database_url()
            if not db_url:
                raise RuntimeError("DATABASE_URL no configurada")

            conn = psycopg2.connect(db_url)
            conn.autocommit = False
            return conn
        except Exception as e:
            if st is not None:
                st.error(f"❌ Error conectando a Supabase: {e}")
                st.stop()
            raise
    else:
        # Usar SQLite localmente en una ruta persistente
        import sqlite3
        try:
            crear_respaldo_db(db_path)
        except Exception:
            pass
        return sqlite3.connect(db_path)

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
        sqlite_sql_statements = [
            """CREATE TABLE IF NOT EXISTS mecanicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS pendientes_taller (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingreso_id INTEGER,
                tarea TEXT NOT NULL,
                estado TEXT NOT NULL,
                observaciones TEXT,
                FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
            )""",
            """CREATE TABLE IF NOT EXISTS controles_mantenimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingreso_id INTEGER,
                tarea TEXT NOT NULL,
                estado TEXT NOT NULL,
                observaciones TEXT,
                tipo_tarea TEXT,
                FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
            )""",
            """CREATE TABLE IF NOT EXISTS controles_salida (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingreso_id INTEGER,
                tarea TEXT NOT NULL,
                estado TEXT NOT NULL,
                observaciones TEXT,
                FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
            )""",
            """CREATE TABLE IF NOT EXISTS registro_horas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingreso_id INTEGER,
                fecha TEXT NOT NULL,
                horas REAL NOT NULL,
                mecanico TEXT NOT NULL,
                FOREIGN KEY(ingreso_id) REFERENCES equipos_ingresados(id)
            )""",
            """CREATE TABLE IF NOT EXISTS maestro_controles_ingreso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                orden INTEGER NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS maestro_tareas_mantenimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                orden INTEGER NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS maestro_controles_salida (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                orden INTEGER NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS maestro_rubros_compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS lista_compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rubro TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                detalle TEXT,
                cantidad TEXT NOT NULL,
                fecha_carga TEXT,
                estado TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS trabajos_clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT NOT NULL,
                tarea TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha_programada TEXT
            )"""
        ]

        for sql in sqlite_sql_statements:
            try:
                cursor.execute(sql)
            except Exception as e:
                print(f"⚠️ Error creando tabla SQLite: {e}")

        cursor.execute("SELECT COUNT(*) FROM mecanicos")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("INSERT INTO mecanicos (nombre) VALUES (?)", [("Cesar",), ("Lucas",), ("Marcelo",)])

        cursor.execute("SELECT COUNT(*) FROM maestro_equipos")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT OR IGNORE INTO maestro_equipos (interno, marca, modelo, tipo) VALUES (?, ?, ?, ?)",
                [
                    ("AE02", "TOYOTA", "628FD25", "Autoelevador"),
                    ("AE05", "TOYOTA", "FD2025", "Autoelevador"),
                    ("AE15", "HELI", "CPD25", "Eléctrico"),
                    ("VY01", "YALE", "Propiedad Corven", "Autoelevador")
                ]
            )

        cursor.execute("SELECT COUNT(*) FROM maestro_controles_ingreso")
        if cursor.fetchone()[0] == 0:
            iniciales = [
                "Visual estado equipo (estetico)", "Visual de perdidas de fluidos o roturas", "Funcionamiento luces delanteras",
                "Funcionamiento Luces traseras", "Luces perimetrales", "Luces freno", "Baliza de techo", "Sirena de retroceso",
                "Sensor hombre muerto", "Nivel aceite motor", "Nivel refrigerante motor", "Nivel aceite transmicion",
                "Nivel aceite hidráulico", "Nivel y estado liquido de frenos", "Estado de las uñas (rajaduras y torceduras)",
                "Estado de butaca", "Estado y funcionamiento HMS", "Estado de cubiertas", "Funcionamiento bocina",
                "Funcionamiento de pedal de acelerador", "Estado de resortes de los pedales", "Prueba frenos de servicio",
                "Prueba Freno de estacionamiento", "Control de pedales", "Funcionamiento de comandos hidráulicos",
                "Chequear instrumentos de tablero", "Chequear estado de mangueras y cadenas"
            ]
            cursor.executemany("INSERT INTO maestro_controles_ingreso (descripcion, orden) VALUES (?, ?)", [(t, i + 1) for i, t in enumerate(iniciales)])

        cursor.execute("SELECT COUNT(*) FROM maestro_tareas_mantenimiento")
        if cursor.fetchone()[0] == 0:
            mant_imagen = [
                "Lavado Completo", "Retiro de uñas y parrilla", "Elevar y colocar tacos parte trasera",
                "Elevar y colocar tacos parte delantera", "Retiro ruedas delanteras", "Retirar aceite diferencial",
                "Retiro y desarme mazas delanteras", "Sopletear Frenos", "Controlar estado de patines de freno",
                "Lubricar regulador de frenos", "Controlar estado de campanas de freno", "Retirar retenes desarmar y lavar rodamientos",
                "Armar de mazas con retenes nuevos", "Colocar mazas delanteras", "Regular de patines de freno",
                "Regular Freno de mano", "Drenar liquido de frenos", "Retirar deposito de liquido de frenos para lavar",
                "Rearmar deposito controlando perdidas", "Controlar estado bulbo de frenos", "Rellenar y purgar frenos",
                "Reemplazar aceite y filtro motor", "Reemplazar filtro de aire", "Engrase general"
            ]
            cursor.executemany("INSERT INTO maestro_tareas_mantenimiento (descripcion, orden) VALUES (?, ?)", [(t, i + 1) for i, t in enumerate(mant_imagen)])

        cursor.execute("SELECT COUNT(*) FROM maestro_controles_salida")
        if cursor.fetchone()[0] == 0:
            salida_imagen = [
                "Visual estado equipo (estetico)", "Visual de perdidas de fluidos o roturas", "Funcionamiento luces delanteras",
                "Funcionamiento Luces Traseras", "Luces perimetrales", "Luces freno", "Baliza de techo",
                "Sirena de retroceso", "Sensor hombre muerto", "Nivel aceite motor", "Nivel refrigerante motor",
                "Nivel aceite transmicion", "Nivel aceite hidráulico", "Nivel y estado liquido de frenos",
                "Estado de butaca", "Estado y funcionamiento HMS", "Estado de cubiertas", "Funcionamiento bocina"
            ]
            cursor.executemany("INSERT INTO maestro_controles_salida (descripcion, orden) VALUES (?, ?)", [(t, i + 1) for i, t in enumerate(salida_imagen)])

        cursor.execute("SELECT COUNT(*) FROM maestro_rubros_compras")
        if cursor.fetchone()[0] == 0:
            rubros_inic = ["Ferretería", "Electricidad", "Pinturería", "Hierros", "Transporte / Logística", "Repuestos Específicos", "Insumos Generales"]
            cursor.executemany("INSERT INTO maestro_rubros_compras (nombre) VALUES (?)", [(r,) for r in rubros_inic])

        conn.commit()
    
    return conn
