import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from email.message import EmailMessage
from fpdf import FPDF, FPDFException
import os
import re
import sqlite3
import smtplib
from zoneinfo import ZoneInfo
from psycopg2 import Error as PsycopgError

from database_adapter import conectar_db, ensure_database_file, crear_respaldo_db, sincronizar_supabase, ensure_remote_restore, inicializar_db, has_remote_db, IS_CLOUD

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Gestión de Taller", layout="wide")

st.markdown("""
<style>
    :root {
        --taller-ink: #e8f0f2;
        --taller-muted: #b7c8cf;
        --taller-teal: #147d83;
        --taller-orange: #e76f32;
        --taller-line: #2d4b5d;
        --taller-surface: #173246;
    }

    .stApp {
        background: #0f1f2e;
    }

    [data-testid="stHeader"] {
        background: rgba(15, 31, 46, 0.92);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #18324b 0%, #214d61 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.12);
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #eaf3f5;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #ffffff;
        letter-spacing: 0;
    }

    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 0.28rem;
    }

    [data-testid="stSidebar"] [role="radio"] {
        border-radius: 8px;
        padding: 0.42rem 0.55rem;
        transition: background 160ms ease, transform 160ms ease;
    }

    [data-testid="stSidebar"] [role="radio"] p,
    [data-testid="stSidebar"] [role="radio"] span,
    [data-testid="stSidebar"] [role="radio"] label {
        color: #eaf3f5 !important;
    }

    [data-testid="stSidebar"] [role="radio"]:hover {
        background: rgba(255, 255, 255, 0.10);
        transform: translateX(2px);
    }

    [data-testid="stSidebar"] [role="radio"][aria-checked="true"] {
        background: var(--taller-orange);
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.16);
    }

    [data-testid="stSidebar"] .stButton > button {
        justify-content: flex-start;
        text-align: left;
        background: transparent;
        border-color: transparent;
        color: #eaf3f5;
        box-shadow: none;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.10);
        border-color: transparent;
        color: #ffffff;
        transform: translateX(2px);
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--taller-orange);
        border-color: var(--taller-orange);
        color: #ffffff;
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.16);
    }

    .block-container {
        max-width: 1420px;
        padding-top: 2.2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: var(--taller-ink);
        letter-spacing: 0;
    }

    h1 {
        font-weight: 750;
        font-size: 2rem;
        line-height: 1.15;
        margin-bottom: 0.35rem;
    }

    h2, h3 {
        font-weight: 680;
    }

    section.main [data-testid="stMarkdownContainer"] p,
    section.main [data-testid="stMarkdownContainer"] span,
    section.main [data-testid="stCaptionContainer"] p {
        color: var(--taller-ink) !important;
    }

    section.main [data-baseweb="tab"] {
        color: var(--taller-ink) !important;
    }

    section.main [data-baseweb="tab"][aria-selected="true"] {
        color: var(--taller-orange) !important;
    }

    [data-testid="stCaptionContainer"] {
        color: var(--taller-muted);
    }

    [data-testid="stForm"],
    [data-testid="stExpander"] {
        background: var(--taller-surface);
        border: 1px solid var(--taller-line);
        border-radius: 10px;
        box-shadow: 0 5px 18px rgba(24, 50, 75, 0.055);
    }

    [data-testid="stForm"] {
        padding: 0.85rem 1rem 0.55rem;
    }

    [data-testid="stExpander"] details summary {
        color: var(--taller-ink);
        font-weight: 650;
    }

    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        border-radius: 7px;
        border: 1px solid #c8d5dc;
        font-weight: 650;
        min-height: 2.55rem;
        transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover {
        border-color: var(--taller-teal);
        box-shadow: 0 4px 12px rgba(20, 125, 131, 0.18);
        transform: translateY(-1px);
    }

    [data-testid="stFormSubmitButton"] > button,
    .stButton > button[kind="primary"] {
        background: var(--taller-teal);
        border-color: var(--taller-teal);
        color: #ffffff;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    [data-baseweb="select"] > div {
        border-radius: 7px;
        border-color: #c8d5dc;
    }

    [data-testid="stMetric"] {
        background: var(--taller-surface);
        border: 1px solid var(--taller-line);
        border-radius: 10px;
        padding: 0.8rem 1rem;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--taller-line);
        border-radius: 10px;
        overflow: hidden;
    }

    hr {
        border-color: var(--taller-line);
    }

    .agenda-title {
        font-size: 1.45rem;
        line-height: 1.2;
        margin: 0 0 0.45rem;
    }

    .agenda-day-heading {
        font-size: 1rem;
        line-height: 1.25;
        margin: 0.2rem 0 0.35rem;
    }

    .agenda-day-heading.agenda-today {
        color: #ff9a68;
    }

    .agenda-day-count {
        color: var(--taller-muted);
        font-size: 0.78rem;
        font-weight: 400;
    }

    .st-key-agenda-desktop,
    .st-key-agenda-tablet,
    .st-key-agenda-mobile {
        display: none !important;
    }

    .st-key-agenda-desktop [data-testid="stVerticalBlock"],
    .st-key-agenda-tablet [data-testid="stVerticalBlock"],
    .st-key-agenda-mobile [data-testid="stVerticalBlock"] {
        gap: 0.45rem;
    }

    .st-key-agenda-desktop [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-agenda-tablet [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-agenda-mobile [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.55rem 0.65rem;
    }

    @media (min-width: 1200px) {
        .st-key-agenda-desktop {
            display: block !important;
        }
    }

    @media (min-width: 701px) and (max-width: 1199px) {
        .st-key-agenda-tablet {
            display: block !important;
        }
    }

    @media (max-width: 700px) {
        .st-key-agenda-mobile {
            display: block !important;
        }

        .st-key-agenda-mobile .stButton button {
            min-height: 2.75rem;
        }

        .st-key-ingreso-checklist [data-testid="stHorizontalBlock"],
        .st-key-salida-checklist [data-testid="stHorizontalBlock"] {
            flex-direction: column;
            align-items: stretch;
            gap: 0.25rem;
        }

        .st-key-ingreso-checklist [data-testid="stColumn"],
        .st-key-salida-checklist [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        .st-key-ingreso-checklist input[type="checkbox"],
        .st-key-salida-checklist input[type="checkbox"] {
            transform: scale(1.2);
        }

        .st-key-ingreso-checklist [data-testid="stCheckbox"] label,
        .st-key-salida-checklist [data-testid="stCheckbox"] label {
            min-height: 2.75rem;
            align-items: center;
        }
    }

    .st-key-ingreso-checklist [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-salida-checklist [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.35rem 0.55rem;
    }

    .st-key-ingreso-checklist [data-testid="stVerticalBlock"],
    .st-key-salida-checklist [data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS Y ESTRUCTURA ---
# En Streamlit Cloud el filesystem es efímero: requerimos DATABASE_URL para
# persistencia. Si estamos en Cloud y no hay DB remota, bloqueamos para evitar
# pérdida de datos hasta que el secreto `DATABASE_URL` sea configurado.
if IS_CLOUD and not has_remote_db():
    st.error("La app está desplegada en Streamlit Cloud y no hay base remota configurada. Configure 'DATABASE_URL' en los Secrets de la app para evitar pérdida de datos. Mientras tanto, las operaciones de escritura están deshabilitadas.")
    st.stop()

DB_PATH = ensure_database_file()
if not IS_CLOUD:
    ensure_remote_restore(DB_PATH)
conn_inicial = conectar_db()
inicializar_db(conn_inicial)
conn_inicial.close()


def persistir_y_sync():
    """Genera respaldo local y sincroniza con Supabase tras cambios importantes."""
    if IS_CLOUD:
        return
    try:
        crear_respaldo_db(DB_PATH)
    except Exception:
        pass
    try:
        sincronizar_supabase(DB_PATH)
    except Exception:
        pass

# --- FUNCIONES GENERADORAS DE PDF ---

PDF_MAX_RECORDS_PER_SECTION = 250
PDF_MAX_SECTION_CHARS = 5000


class PdfGenerationError(RuntimeError):
    pass


def _valor_pdf(valor):
    if valor is None or not str(valor).strip():
        return "No informado"
    return str(valor).strip()


def _texto_pdf(valor):
    texto = _valor_pdf(valor)
    if len(texto) > PDF_MAX_SECTION_CHARS:
        texto = texto[:PDF_MAX_SECTION_CHARS] + "\n[Contenido recortado para mantener el reporte manejable]"
    return texto.encode("latin-1", "replace").decode("latin-1")


def _nombre_pdf(prefijo, interno, ingreso_id):
    seguro_id = re.sub(r"[^A-Za-z0-9_-]+", "_", _valor_pdf(ingreso_id)).strip("_") or "ingreso"
    seguro_interno = re.sub(r"[^A-Za-z0-9_-]+", "_", _valor_pdf(interno)).strip("_") or "equipo"
    return f"{prefijo}_{seguro_interno}_{seguro_id}.pdf"


def _guardar_pdf(datos_pdf, nombre_archivo):
    carpeta_pdfs = "comprobantes"
    os.makedirs(carpeta_pdfs, exist_ok=True)
    ruta_pdf = os.path.join(carpeta_pdfs, nombre_archivo)
    with open(ruta_pdf, "wb") as archivo:
        archivo.write(datos_pdf)
    return ruta_pdf


def _guardar_pdf_si_posible(datos_pdf, nombre_archivo):
    try:
        _guardar_pdf(datos_pdf, nombre_archivo)
    except OSError as exc:
        st.warning(
            "El PDF está listo para descargar, pero no se pudo guardar una copia local. "
            f"No quedará disponible en Archivo de PDFs: {exc}"
        )


def _crear_pdf(titulo, filas):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_title(_texto_pdf(titulo))
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, _texto_pdf(titulo), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(
            0,
            8,
            _texto_pdf(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(4)
        for etiqueta, valor in filas:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7, _texto_pdf(f"{etiqueta}:"), wrapmode="CHAR")
            pdf.set_font("Helvetica", "", 10)
            for linea in _texto_pdf(valor).splitlines() or ["No informado"]:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 6, linea or "No informado", wrapmode="CHAR")
            pdf.ln(2)
        contenido = bytes(pdf.output())
        if not contenido.startswith(b"%PDF-"):
            raise PdfGenerationError("La librería no produjo un archivo PDF válido.")
        return contenido
    except (FPDFException, OSError, UnicodeError, ValueError) as exc:
        raise PdfGenerationError(f"No se pudo generar el PDF: {exc}") from exc


def _lineas_registros(registros):
    if not registros:
        return "No informado"
    return "\n".join(
        f"Tarea: {_valor_pdf(registro[0])} | Estado: {_valor_pdf(registro[1])}"
        f"{f' | Tipo: {_valor_pdf(registro[3])}' if len(registro) > 3 else ''} | "
        f"Observaciones: {_valor_pdf(registro[2])}"
        for registro in registros
    )


def _lineas_horas(registros):
    if not registros:
        return "No informado"
    lineas = [
        f"Fecha: {_valor_pdf(registro[0])} | Horas: {_valor_pdf(registro[1])} | "
        f"Mecánico: {_valor_pdf(registro[2])}"
        for registro in registros
    ]
    try:
        total_horas = sum(float(registro[1] or 0) for registro in registros)
    except (TypeError, ValueError):
        total = "No informado"
    else:
        total = f"{total_horas:.2f}".replace(".", ",")
    return f"Total de horas registradas: {total}\n" + "\n".join(lineas)


def _datos_generales_pdf(ingreso):
    return [
        ("Ingreso", ingreso[0]),
        ("Cliente", "No informado (el esquema no registra un cliente asociado al ingreso)"),
        ("Interno", ingreso[1]),
        ("Marca", ingreso[2]),
        ("Modelo", ingreso[3]),
        ("Tipo de equipo", ingreso[4]),
        ("Horómetro al ingreso", ingreso[5]),
        ("Origen / destino", ingreso[6]),
        ("Mecánico asignado", ingreso[7]),
        ("Fecha de ingreso", ingreso[8]),
        ("Hora de inicio", ingreso[9]),
        ("Hora de finalización", ingreso[10]),
        ("Estado del proceso", ingreso[11]),
    ]


def generar_pdf_taller(ingreso_id):
    conn = None
    try:
        conn = conectar_db()
        ingreso = conn.execute("""
            SELECT e.id, e.interno, m.marca, m.modelo, m.tipo, e.horas, e.origen,
                   e.mecanico, e.fecha_ingreso, e.hora_inicio, e.hora_fin,
                   e.estado_proceso
            FROM equipos_ingresados e
            LEFT JOIN maestro_equipos m ON m.interno = e.interno
            WHERE e.id = ?
        """, (ingreso_id,)).fetchone()
        if not ingreso:
            raise PdfGenerationError(f"No existe el ingreso {ingreso_id}.")

        controles = conn.execute(f"""
            SELECT tarea, estado, observaciones
            FROM controles_ingreso WHERE ingreso_id = ? ORDER BY id
            LIMIT {PDF_MAX_RECORDS_PER_SECTION}
        """, (ingreso_id,)).fetchall()
        mantenimiento = conn.execute(f"""
            SELECT tarea, estado, observaciones, tipo_tarea
            FROM controles_mantenimiento WHERE ingreso_id = ? ORDER BY id
            LIMIT {PDF_MAX_RECORDS_PER_SECTION}
        """, (ingreso_id,)).fetchall()
        horas = conn.execute(f"""
            SELECT fecha, horas, mecanico
            FROM registro_horas WHERE ingreso_id = ? ORDER BY id
            LIMIT {PDF_MAX_RECORDS_PER_SECTION}
        """, (ingreso_id,)).fetchall()

        filas = _datos_generales_pdf(ingreso) + [
            ("Inspección de ingreso", _lineas_registros(controles)),
            ("Mantenimiento y reparaciones", _lineas_registros(mantenimiento)),
            ("Horas de trabajo registradas", _lineas_horas(horas)),
        ]
        nombre = _nombre_pdf("Reporte_Taller", ingreso[1], ingreso_id)
        datos = _crear_pdf("Reporte técnico de taller", filas)
        _guardar_pdf_si_posible(datos, nombre)
        return datos, nombre
    except (sqlite3.Error, PsycopgError) as exc:
        raise PdfGenerationError(f"No se pudieron consultar los datos del ingreso: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


def generar_pdf_entrega(ingreso_id):
    conn = None
    try:
        conn = conectar_db()
        ingreso = conn.execute("""
            SELECT e.id, e.interno, m.marca, m.modelo, m.tipo, e.horas, e.origen,
                   e.mecanico, e.fecha_ingreso, e.hora_inicio, e.hora_fin,
                   e.estado_proceso
            FROM equipos_ingresados e
            LEFT JOIN maestro_equipos m ON m.interno = e.interno
            WHERE e.id = ?
        """, (ingreso_id,)).fetchone()
        if not ingreso:
            raise PdfGenerationError(f"No existe el ingreso {ingreso_id}.")

        mantenimiento = conn.execute(f"""
            SELECT tarea, estado, observaciones, tipo_tarea
            FROM controles_mantenimiento WHERE ingreso_id = ? ORDER BY id
            LIMIT {PDF_MAX_RECORDS_PER_SECTION}
        """, (ingreso_id,)).fetchall()
        controles_salida = conn.execute(f"""
            SELECT tarea, estado, observaciones
            FROM controles_salida WHERE ingreso_id = ? ORDER BY id
            LIMIT {PDF_MAX_RECORDS_PER_SECTION}
        """, (ingreso_id,)).fetchall()
        horas = conn.execute(f"""
            SELECT fecha, horas, mecanico
            FROM registro_horas WHERE ingreso_id = ? ORDER BY id
            LIMIT {PDF_MAX_RECORDS_PER_SECTION}
        """, (ingreso_id,)).fetchall()

        filas = _datos_generales_pdf(ingreso) + [
            ("Mantenimiento y reparaciones realizadas", _lineas_registros(mantenimiento)),
            ("Control de salida", _lineas_registros(controles_salida)),
            ("Horas de trabajo registradas", _lineas_horas(horas)),
        ]
        nombre = _nombre_pdf("Certificado_Entrega", ingreso[1], ingreso_id)
        datos = _crear_pdf("Certificado de entrega de equipo", filas)
        _guardar_pdf_si_posible(datos, nombre)
        return datos, nombre
    except (sqlite3.Error, PsycopgError) as exc:
        raise PdfGenerationError(f"No se pudieron consultar los datos del ingreso: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


def enviar_pdf_por_email(datos_pdf, nombre_archivo, asunto):
    """Envía un PDF al destinatario configurado en Streamlit Secrets."""
    try:
        smtp_host = st.secrets.get("SMTP_HOST")
        smtp_port = int(st.secrets.get("SMTP_PORT", 465))
        smtp_user = st.secrets.get("SMTP_USER")
        smtp_password = st.secrets.get("SMTP_PASSWORD")
        destinatario = st.secrets.get("REPORT_EMAIL_TO")
    except Exception:
        smtp_host = smtp_port = smtp_user = smtp_password = destinatario = None

    if not all([smtp_host, smtp_user, smtp_password, destinatario]):
        return False, "Falta configurar SMTP_HOST, SMTP_USER, SMTP_PASSWORD y REPORT_EMAIL_TO en Secrets."

    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = smtp_user
    mensaje["To"] = destinatario
    mensaje.set_content("Adjunto se envía el reporte generado desde Gestión de Taller.")
    mensaje.add_attachment(datos_pdf, maintype="application", subtype="pdf", filename=nombre_archivo)

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as servidor:
                servidor.login(smtp_user, smtp_password)
                servidor.send_message(mensaje)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as servidor:
                servidor.starttls()
                servidor.login(smtp_user, smtp_password)
                servidor.send_message(mensaje)
        return True, destinatario
    except Exception:
        return False, "No se pudo enviar el correo. Verificá la configuración SMTP."

# --- MANEJO SEGURO DE ESTADOS DE SESIÓN ---
if "navegacion" not in st.session_state: st.session_state.navegacion = "🏠 Inicio semanal"
if "paso_ingreso" not in st.session_state: st.session_state.paso_ingreso = "registro_inicial"
if "ultimo_ingreso_id" not in st.session_state: st.session_state.ultimo_ingreso_id = None
if "mant_queue" not in st.session_state: st.session_state.mant_queue = []
if "mant_idx" not in st.session_state: st.session_state.mant_idx = 0
if "mant_ingreso_id" not in st.session_state: st.session_state.mant_ingreso_id = None
if "salida_ingreso_id" not in st.session_state: st.session_state.salida_ingreso_id = None
if "hallazgos_extras_ok" not in st.session_state: st.session_state.hallazgos_extras_ok = False

# --- MENÚ LATERAL ---
lista_opciones_menu = [
    "🏠 Inicio semanal",
    "📊 Tablero Taller", 
    "📊 Tablero de Equipos",
    "💼 Trabajos Clientes",
    "🛒 Lista de Compras",
    "🚜 Ingreso de Equipo (Guiado)",
    "🛠️ Ejecución de Mantenimiento", 
    "✅ Entrega de Equipo (Salida)",
    "🗂️ Archivo de PDFs",
   
    "⚙️ Configuración General",
    "👥 Personal Mecánico",
    "📈 Reportes y Facturación"
]

try:
    idx_defecto = lista_opciones_menu.index(st.session_state.navegacion)
except ValueError:
    idx_defecto = 0

st.sidebar.title("🔧 Sistema Taller")
st.sidebar.caption("Navegación principal")
for opcion_menu in lista_opciones_menu:
    es_seleccionada = st.session_state.navegacion == opcion_menu
    if st.sidebar.button(
        opcion_menu,
        key=f"menu_{opcion_menu}",
        use_container_width=True,
        type="primary" if es_seleccionada else "secondary",
    ):
        st.session_state.navegacion = opcion_menu

menu_elegido = st.session_state.navegacion


def cambiar_pagina(nueva_pagina):
    st.session_state.navegacion = nueva_pagina


_ESTADOS_CHECKLIST = {
    "controles_ingreso": ("OK", "Malo", "No Realizado"),
    "controles_salida": ("OK", "Malo (Avisar a Taller)", "No Aplica"),
}


def _cargar_respuestas_checklist(conn, tabla, ingreso_id):
    if tabla not in _ESTADOS_CHECKLIST:
        raise ValueError(f"Tabla de checklist no válida: {tabla}")
    filas = conn.execute(
        f"SELECT tarea, estado, observaciones FROM {tabla} WHERE ingreso_id = ? ORDER BY id",
        (ingreso_id,),
    ).fetchall()
    return {
        fila[0]: {"estado": fila[1], "observaciones": fila[2] or ""}
        for fila in filas
    }


def _contar_checklist_completados(descripciones, respuestas, tabla):
    estados_validos = _ESTADOS_CHECKLIST.get(tabla)
    if estados_validos is None:
        raise ValueError(f"Tabla de checklist no válida: {tabla}")
    return sum(
        1
        for descripcion in descripciones
        if descripcion in respuestas
        and respuestas[descripcion]["estado"] in estados_validos
    )


def _persistir_respuesta_checklist(
    tabla,
    ingreso_id,
    tarea,
    completado_key,
    estado_key,
    observaciones_key,
    error_key,
):
    estados_validos = _ESTADOS_CHECKLIST.get(tabla)
    if estados_validos is None:
        raise ValueError(f"Tabla de checklist no válida: {tabla}")

    conn = conectar_db()
    try:
        if not st.session_state[completado_key]:
            conn.execute(
                f"DELETE FROM {tabla} WHERE ingreso_id = ? AND tarea = ?",
                (ingreso_id, tarea),
            )
            conn.commit()
            persistir_y_sync()
            st.session_state[estado_key] = None
            st.session_state[observaciones_key] = ""
            st.session_state.checklist_guardado = (
                "success",
                "Paso desmarcado y guardado.",
            )
            st.session_state.pop(error_key, None)
            return

        estado = st.session_state.get(estado_key)
        if estado not in estados_validos:
            st.session_state[error_key] = (
                "Seleccioná una condición antes de marcar el paso como completo."
            )
            return

        observaciones = (st.session_state.get(observaciones_key) or "").strip()
        respuesta = conn.execute(
            f"SELECT id FROM {tabla} WHERE ingreso_id = ? AND tarea = ? ORDER BY id DESC LIMIT 1",
            (ingreso_id, tarea),
        ).fetchone()
        if respuesta:
            conn.execute(
                f"UPDATE {tabla} SET estado = ?, observaciones = ? "
                "WHERE ingreso_id = ? AND tarea = ?",
                (estado, observaciones, ingreso_id, tarea),
            )
        else:
            conn.execute(
                f"INSERT INTO {tabla} (ingreso_id, tarea, estado, observaciones) "
                "VALUES (?, ?, ?, ?)",
                (ingreso_id, tarea, estado, observaciones),
            )
        conn.commit()
        persistir_y_sync()
        st.session_state.checklist_guardado = (
            "success",
            "Cambios guardados automáticamente.",
        )
        st.session_state.pop(error_key, None)
    finally:
        conn.close()


def _guardar_estado_checklist(
    tabla,
    ingreso_id,
    tarea,
    completado_key,
    estado_key,
    observaciones_key,
    error_key,
):
    st.session_state[completado_key] = True
    _persistir_respuesta_checklist(
        tabla,
        ingreso_id,
        tarea,
        completado_key,
        estado_key,
        observaciones_key,
        error_key,
    )


def _guardar_observaciones_checklist(
    tabla,
    ingreso_id,
    tarea,
    completado_key,
    estado_key,
    observaciones_key,
    error_key,
):
    if st.session_state[completado_key]:
        _persistir_respuesta_checklist(
            tabla,
            ingreso_id,
            tarea,
            completado_key,
            estado_key,
            observaciones_key,
            error_key,
        )


def _mostrar_checklist_planilla(tipo, ingreso_id, controles, respuestas):
    tabla = {
        "ingreso": "controles_ingreso",
        "salida": "controles_salida",
    }[tipo]
    estados = _ESTADOS_CHECKLIST[tabla]
    progreso = _contar_checklist_completados(
        [tarea for _, tarea, _ in controles],
        respuestas,
        tabla,
    )
    total = len(controles)
    titulo = "Checklist de ingreso" if tipo == "ingreso" else "Checklist de salida"

    with st.container(key=f"{tipo}-checklist"):
        st.subheader(titulo)
        st.caption(
            "Los controles están en el orden configurado. Cada respuesta y observación "
            "se guarda automáticamente."
        )
        st.write(f"**{progreso} de {total} pasos completados**")
        st.progress(progreso / total if total else 0)
        mensaje_guardado = st.session_state.pop("checklist_guardado", None)
        if mensaje_guardado:
            nivel, mensaje = mensaje_guardado
            (st.success if nivel == "success" else st.warning)(mensaje)

        for indice, (control_id, tarea, _) in enumerate(controles, start=1):
            respuesta = respuestas.get(tarea)
            prefijo = f"checklist_{tipo}_{ingreso_id}_{control_id}"
            completado_key = f"{prefijo}_completado"
            estado_key = f"{prefijo}_estado"
            observaciones_key = f"{prefijo}_observaciones"
            error_key = f"{prefijo}_error"
            if completado_key not in st.session_state:
                st.session_state[completado_key] = bool(respuesta)
            if estado_key not in st.session_state:
                estado_guardado = respuesta["estado"] if respuesta else None
                st.session_state[estado_key] = (
                    estado_guardado if estado_guardado in estados else None
                )
            if observaciones_key not in st.session_state:
                st.session_state[observaciones_key] = (
                    respuesta["observaciones"] if respuesta else ""
                )

            argumentos = (
                tabla,
                ingreso_id,
                tarea,
                completado_key,
                estado_key,
                observaciones_key,
                error_key,
            )
            with st.container(border=True):
                col_estado, col_tarea, col_respuesta, col_observaciones = st.columns(
                    [0.85, 3.2, 1.5, 2.4],
                    gap="small",
                )
                with col_estado:
                    st.checkbox(
                        "Completo",
                        key=completado_key,
                        on_change=_persistir_respuesta_checklist,
                        args=argumentos,
                    )
                with col_tarea:
                    st.markdown(f"**{indice}. {tarea}**")
                with col_respuesta:
                    indice_estado = (
                        estados.index(st.session_state[estado_key])
                        if st.session_state[estado_key] in estados
                        else None
                    )
                    st.selectbox(
                        "Condición",
                        estados,
                        index=indice_estado,
                        key=estado_key,
                        on_change=_guardar_estado_checklist,
                        args=argumentos,
                        label_visibility="collapsed",
                        placeholder="Elegí condición",
                    )
                with col_observaciones:
                    if (
                        st.session_state[completado_key]
                        and st.session_state[estado_key] in estados
                    ):
                        st.text_area(
                            "Observaciones",
                            key=observaciones_key,
                            height=68,
                            on_change=_guardar_observaciones_checklist,
                            args=argumentos,
                            label_visibility="collapsed",
                            placeholder="Observaciones (opcional)",
                        )
                    elif st.session_state[completado_key]:
                        st.caption("Elegí una condición para guardar este paso.")
                    else:
                        st.caption("Respuesta y observaciones al marcar el paso.")

            error = st.session_state.get(error_key)
            if error:
                st.warning(error)

    return progreso, total


def _fecha_agenda(valor):
    if valor is None or pd.isna(valor):
        return None
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _desplazamiento_semana_por_defecto(hoy):
    return 1 if hoy.weekday() >= 5 else 0


def _cargar_trabajos_agenda(conn):
    trabajos = []
    fechas_invalidas = 0

    internos = pd.read_sql_query("""
        SELECT id, titulo, descripcion, fecha_entrega, prioridad, mecanico, estado
        FROM pendientes_taller
        WHERE estado = 'Pendiente'
        ORDER BY fecha_entrega, id
    """, conn)
    for _, fila in internos.iterrows():
        fecha = _fecha_agenda(fila["fecha_entrega"])
        if fecha is None:
            fechas_invalidas += 1
            continue
        trabajos.append({
            "tipo": "interno",
            "id": int(fila["id"]),
            "fecha": fecha,
            "fecha_rotulo": "Entrega estimada",
            "titulo": fila["titulo"],
            "descripcion": fila["descripcion"],
            "cliente": "Taller propio",
            "equipo": None,
            "responsable": fila["mecanico"],
            "estado": fila["estado"],
            "prioridad": fila["prioridad"],
        })

    clientes = pd.read_sql_query("""
        SELECT id, cliente, tarea, estado, fecha_programada
        FROM trabajos_clientes
        WHERE estado = 'Pendiente'
        ORDER BY fecha_programada, id
    """, conn)
    for _, fila in clientes.iterrows():
        fecha = _fecha_agenda(fila["fecha_programada"])
        if fecha is None:
            fechas_invalidas += 1
            continue
        trabajos.append({
            "tipo": "cliente",
            "id": int(fila["id"]),
            "fecha": fecha,
            "fecha_rotulo": "Programado",
            "titulo": fila["tarea"],
            "descripcion": None,
            "cliente": fila["cliente"],
            "equipo": None,
            "responsable": None,
            "estado": fila["estado"],
            "prioridad": None,
        })

    mantenimientos = pd.read_sql_query("""
        SELECT e.id, e.interno, e.origen, e.mecanico, e.fecha_ingreso,
               e.estado_proceso, m.marca, m.modelo,
               (SELECT cm.tarea FROM controles_mantenimiento cm
                WHERE cm.ingreso_id = e.id ORDER BY cm.id DESC LIMIT 1) AS ultima_tarea,
               (SELECT cm.estado FROM controles_mantenimiento cm
                WHERE cm.ingreso_id = e.id ORDER BY cm.id DESC LIMIT 1) AS estado_ultima_tarea
        FROM equipos_ingresados e
        LEFT JOIN maestro_equipos m ON m.interno = e.interno
        WHERE e.estado_proceso IN (
            'En Proceso de Inspección',
            'Inspección Inicial Completada',
            'Mantenimiento en Proceso',
            'Checklist Salida en Proceso'
        )
        ORDER BY e.fecha_ingreso, e.id
    """, conn)
    for _, fila in mantenimientos.iterrows():
        fecha = _fecha_agenda(fila["fecha_ingreso"])
        if fecha is None:
            fechas_invalidas += 1
            continue
        trabajos.append({
            "tipo": "mantenimiento",
            "id": int(fila["id"]),
            "fecha": fecha,
            "fecha_rotulo": "Fecha de ingreso (sin turno programado)",
            "titulo": f"Unidad {fila['interno']}",
            "descripcion": f"{fila['estado_proceso']}",
            "ultima_tarea": fila["ultima_tarea"],
            "estado_ultima_tarea": fila["estado_ultima_tarea"],
            "cliente": fila["origen"],
            "equipo": " ".join(str(parte) for parte in (fila["marca"], fila["modelo"]) if pd.notna(parte)),
            "responsable": fila["mecanico"],
            "estado": fila["estado_proceso"],
            "prioridad": None,
        })

    trabajos.sort(key=lambda trabajo: (trabajo["fecha"], trabajo["tipo"], trabajo["id"]))
    return trabajos, fechas_invalidas


def _nombre_dia(fecha):
    dias = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
    return dias[fecha.weekday()].capitalize()


def _nombre_mes(fecha):
    meses = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    )
    return meses[fecha.month - 1]


def _fecha_legible(fecha):
    return f"{fecha.day} de {_nombre_mes(fecha)} de {fecha.year}"


def _ir_a_detalle_agenda(tipo, trabajo_id):
    destino = {
        "interno": "📊 Tablero Taller",
        "cliente": "💼 Trabajos Clientes",
        "mantenimiento": "📊 Tablero de Equipos",
    }[tipo]
    st.session_state.detalle_agenda = (tipo, trabajo_id)
    st.session_state.navegacion = destino


def _volver_a_agenda():
    st.session_state.pop("detalle_agenda", None)
    st.session_state.navegacion = "🏠 Inicio semanal"


def _mostrar_volver_a_agenda(tipo):
    detalle = st.session_state.get("detalle_agenda")
    if detalle and detalle[0] == tipo:
        st.caption("Abriste este trabajo desde la agenda semanal.")
        st.button(
            "← Volver a la semana consultada",
            key=f"volver_agenda_{tipo}",
            on_click=_volver_a_agenda,
        )


def _texto_agenda(valor):
    if valor is None or pd.isna(valor):
        return ""
    texto = str(valor).strip()
    return texto if texto else ""


def _mostrar_tarjeta_agenda(trabajo, vista, hoy, atrasada=False, ancho_completo=False):
    etiquetas = {
        "interno": "🛠️ Interno",
        "cliente": "📍 Cliente",
        "mantenimiento": "🔧 Mantenimiento",
    }
    etiqueta = etiquetas[trabajo["tipo"]]
    etiquetas_ubicacion = {
        "interno": "Ubicación",
        "cliente": "Cliente",
        "mantenimiento": "Origen / destino",
    }
    with st.container(border=True):
        titulo = _texto_agenda(trabajo["titulo"]) or "Trabajo sin título"
        st.markdown(f"**{etiqueta} · {titulo}**")
        ubicacion = _texto_agenda(trabajo["cliente"])
        equipo = _texto_agenda(trabajo["equipo"])
        descripcion = _texto_agenda(trabajo["descripcion"])
        contexto = []
        if ubicacion:
            contexto.append(f"{etiquetas_ubicacion[trabajo['tipo']]}: {ubicacion}")
        if equipo:
            contexto.append(f"Equipo: {equipo}")
        if contexto:
            st.caption(" · ".join(contexto))
        if descripcion:
            st.write(descripcion)
        ultima_tarea = _texto_agenda(trabajo.get("ultima_tarea"))
        if ultima_tarea:
            estado_ultima_tarea = (
                _texto_agenda(trabajo.get("estado_ultima_tarea")) or "estado no informado"
            )
            st.caption(f"Última tarea: {ultima_tarea} ({estado_ultima_tarea})")
        detalles = [
            f"{trabajo['fecha_rotulo']}: {trabajo['fecha'].strftime('%d/%m/%Y')}",
            f"Estado: {_texto_agenda(trabajo['estado']) or 'No informado'}",
        ]
        responsable = _texto_agenda(trabajo["responsable"])
        prioridad = _texto_agenda(trabajo["prioridad"])
        if responsable:
            detalles.append(f"Responsable: {responsable}")
        if prioridad:
            detalles.append(f"Prioridad: {prioridad}")
        if atrasada:
            dias_atraso = (hoy - trabajo["fecha"]).days
            detalles.append(f"Atraso: {dias_atraso} día(s)")
        st.caption(" · ".join(detalles))
        st.button(
            "Abrir detalle →",
            key=(
                f"agenda_{vista}_{trabajo['tipo']}_{trabajo['id']}_"
                f"{'atraso' if atrasada else 'semana'}"
            ),
            on_click=_ir_a_detalle_agenda,
            args=(trabajo["tipo"], trabajo["id"]),
            use_container_width=ancho_completo,
        )


def _cambiar_semana(delta):
    st.session_state.agenda_semana_offset += delta


def _mostrar_controles_semana(lunes, viernes, hoy, vista):
    col_anterior, col_rango, col_siguiente = st.columns([1.2, 3, 1.2], gap="small")
    etiqueta_anterior = "← Ant." if vista == "mobile" else "← Semana anterior"
    etiqueta_siguiente = "Sig. →" if vista == "mobile" else "Semana siguiente →"
    with col_anterior:
        st.button(
            etiqueta_anterior,
            key=f"agenda_anterior_{vista}",
            on_click=_cambiar_semana,
            args=(-1,),
            use_container_width=True,
        )
    with col_rango:
        if lunes.year == viernes.year and lunes.month == viernes.month:
            rango = f"{lunes.day}–{viernes.day} de {_nombre_mes(viernes)} de {viernes.year}"
        elif lunes.year == viernes.year:
            rango = (
                f"{lunes.day} de {_nombre_mes(lunes)} – "
                f"{viernes.day} de {_nombre_mes(viernes)} de {viernes.year}"
            )
        else:
            rango = (
                f"{lunes.day} de {_nombre_mes(lunes)} de {lunes.year} – "
                f"{viernes.day} de {_nombre_mes(viernes)} de {viernes.year}"
            )
        st.markdown(f"**{rango}**")
        st.caption(f"Lunes a viernes · hoy: {_fecha_legible(hoy)}")
    with col_siguiente:
        st.button(
            etiqueta_siguiente,
            key=f"agenda_siguiente_{vista}",
            on_click=_cambiar_semana,
            args=(1,),
            use_container_width=True,
        )


def _mostrar_dia_agenda(fecha, trabajos_dia, hoy, vista):
    es_hoy = fecha == hoy
    marcador_hoy = " · HOY" if es_hoy else ""
    clases = "agenda-day-heading agenda-today" if es_hoy else "agenda-day-heading"
    st.markdown(
        f"<div class='{clases}'><strong>{_nombre_dia(fecha)} "
        f"{fecha.strftime('%d/%m')}{marcador_hoy}</strong> "
        f"<span class='agenda-day-count'>· {len(trabajos_dia)} pendientes</span></div>",
        unsafe_allow_html=True,
    )
    if trabajos_dia:
        for trabajo in trabajos_dia:
            _mostrar_tarjeta_agenda(
                trabajo,
                vista,
                hoy,
                ancho_completo=(vista == "mobile"),
            )
    else:
        st.caption("Sin trabajos pendientes.")


def _mostrar_fin_de_semana(trabajos_fin_semana, lunes, hoy, vista):
    nombre = "Fuera de la semana laboral"
    with st.expander(
        f"{nombre} · sábado y domingo ({len(trabajos_fin_semana)})",
        expanded=bool(trabajos_fin_semana),
    ):
        if not trabajos_fin_semana:
            st.caption("No hay trabajos pendientes programados para el fin de semana.")
            return
        sabado = lunes + timedelta(days=5)
        domingo = lunes + timedelta(days=6)
        for fecha_dia in (sabado, domingo):
            trabajos_dia = [
                trabajo for trabajo in trabajos_fin_semana if trabajo["fecha"] == fecha_dia
            ]
            _mostrar_dia_agenda(fecha_dia, trabajos_dia, hoy, vista)


def _mostrar_atrasados(trabajos_atrasados, hoy, vista, ancho_completo=False):
    st.subheader(f"⚠️ Atrasados · {len(trabajos_atrasados)}")
    st.caption("Solo trabajos internos y de clientes en estado Pendiente.")
    if trabajos_atrasados:
        for trabajo in trabajos_atrasados:
            _mostrar_tarjeta_agenda(
                trabajo,
                vista,
                hoy,
                atrasada=True,
                ancho_completo=ancho_completo,
            )
    else:
        st.success("No hay trabajos internos o de clientes atrasados.")


def generar_reportes(ingreso_id, incluir_entrega=False):
    pdfs_generados = []
    try:
        pdfs_generados.append(generar_pdf_taller(ingreso_id))
        if incluir_entrega:
            pdfs_generados.append(generar_pdf_entrega(ingreso_id))
    except PdfGenerationError as exc:
        st.session_state[f"pdfs_generados_{ingreso_id}"] = pdfs_generados
        st.session_state.mensaje_pdf = (
            "error",
            f"No se pudieron generar los PDF: {exc}",
        )
    else:
        st.session_state[f"pdfs_generados_{ingreso_id}"] = pdfs_generados
        st.session_state.mensaje_pdf = (
            "success",
            "Los PDF están listos para descargar.",
        )


def mostrar_descargas_pdf(ingreso_id):
    for indice, (datos_pdf, nombre_archivo) in enumerate(
        st.session_state.get(f"pdfs_generados_{ingreso_id}", [])
    ):
        tipo = "Reporte de Taller" if nombre_archivo.startswith("Reporte_Taller") else "Certificado de Entrega"
        st.download_button(
            label=f"📥 Descargar {tipo}",
            data=datos_pdf,
            file_name=nombre_archivo,
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_pdf_{ingreso_id}_{indice}",
        )


def preparar_mantenimiento(ingreso_id, reabrir=False):
    conn = conectar_db()
    try:
        tareas_df = pd.read_sql_query(
            "SELECT descripcion FROM maestro_tareas_mantenimiento ORDER BY orden ASC",
            conn,
        )
        cola_completa = [
            {"tipo": "mantenimiento", "tarea": tarea}
            for tarea in tareas_df["descripcion"].tolist()
        ]
        fallas_df = pd.read_sql_query(
            "SELECT tarea, observaciones FROM controles_ingreso WHERE ingreso_id = ? AND estado = 'Malo'",
            conn,
            params=(ingreso_id,),
        )
        for _, falla in fallas_df.iterrows():
            cola_completa.append({
                "tipo": "reparacion",
                "tarea": f"[{falla['tarea']}] {falla['observaciones'] or ''}",
            })

        hechas_df = pd.read_sql_query(
            "SELECT tarea FROM controles_mantenimiento WHERE ingreso_id = ?",
            conn,
            params=(ingreso_id,),
        )
        hechas = set(hechas_df["tarea"].tolist())
        pendientes = [item for item in cola_completa if item["tarea"] not in hechas]

        if pendientes:
            st.session_state.mant_queue = pendientes
            st.session_state.mant_idx = 0
        else:
            st.session_state.mant_queue = cola_completa or [{"tipo": "mantenimiento", "tarea": "Sin tareas pendientes"}]
            st.session_state.mant_idx = len(st.session_state.mant_queue)

        st.session_state.mant_ingreso_id = ingreso_id
        st.session_state.hallazgos_extras_ok = False
        conn.execute(
            "UPDATE equipos_ingresados SET estado_proceso = 'Mantenimiento en Proceso' WHERE id = ?",
            (ingreso_id,),
        )
        conn.commit()
        cambiar_pagina("🛠️ Ejecución de Mantenimiento")
    finally:
        conn.close()


def continuar_mantenimiento_desde_inspeccion(ingreso_id):
    conn = conectar_db()
    try:
        controles_hechos = conn.execute(
            "SELECT COUNT(DISTINCT tarea) FROM controles_ingreso WHERE ingreso_id = ? AND tarea != 'Falla Adicional Detectada'",
            (ingreso_id,),
        ).fetchone()[0]
        total_controles = conn.execute(
            "SELECT COUNT(*) FROM maestro_controles_ingreso"
        ).fetchone()[0]
        if controles_hechos < total_controles:
            st.session_state.mensaje_reanudacion = (
                f"La inspección tiene {controles_hechos} de {total_controles} controles; completala antes de iniciar mantenimiento."
            )
            return
        conn.execute(
            "UPDATE equipos_ingresados SET estado_proceso = 'Inspección Inicial Completada', hora_fin = ? WHERE id = ?",
            (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), ingreso_id),
        )
        conn.commit()
    finally:
        conn.close()

    st.session_state.mensaje_reanudacion = ""
    preparar_mantenimiento(ingreso_id)


def iniciar_checklist_salida(ingreso_id):
    conn = conectar_db()
    try:
        conn.execute(
            "UPDATE equipos_ingresados SET estado_proceso = 'Checklist Salida en Proceso' "
            "WHERE id = ? AND estado_proceso = 'Mantenimiento Completado'",
            (ingreso_id,),
        )
        conn.commit()
        persistir_y_sync()
    finally:
        conn.close()
    st.session_state.salida_ingreso_id = ingreso_id
    cambiar_pagina("✅ Entrega de Equipo (Salida)")


def retomar_checklist_salida(ingreso_id):
    st.session_state.salida_ingreso_id = ingreso_id
    cambiar_pagina("✅ Entrega de Equipo (Salida)")


def finalizar_checklist_salida(ingreso_id):
    conn = conectar_db()
    try:
        ingreso = conn.execute(
            "SELECT estado_proceso FROM equipos_ingresados WHERE id = ?",
            (ingreso_id,),
        ).fetchone()
        controles = conn.execute(
            "SELECT descripcion FROM maestro_controles_salida ORDER BY orden, id"
        ).fetchall()
        respuestas = _cargar_respuestas_checklist(
            conn,
            "controles_salida",
            ingreso_id,
        )
        total = len(controles)
        completados = _contar_checklist_completados(
            [fila[0] for fila in controles],
            respuestas,
            "controles_salida",
        )
        if not ingreso:
            st.session_state[f"error_salida_{ingreso_id}"] = (
                "No se encontró el ingreso seleccionado."
            )
            return
        if ingreso[0] != "Checklist Salida en Proceso":
            st.session_state[f"error_salida_{ingreso_id}"] = (
                "El equipo ya no está en un checklist de salida activo."
            )
            return
        if total == 0 or completados < total:
            st.session_state[f"error_salida_{ingreso_id}"] = (
                f"Completá todos los controles antes de finalizar "
                f"({completados} de {total})."
            )
            return

        actualizacion = conn.execute(
            "UPDATE equipos_ingresados SET estado_proceso = 'Equipo Entregado' "
            "WHERE id = ? AND estado_proceso = 'Checklist Salida en Proceso'",
            (ingreso_id,),
        )
        if actualizacion.rowcount != 1:
            st.session_state[f"error_salida_{ingreso_id}"] = (
                "No se pudo finalizar porque el estado del equipo cambió. Actualizá la pantalla."
            )
            return
        conn.commit()
        persistir_y_sync()
        st.session_state.pop(f"error_salida_{ingreso_id}", None)
    finally:
        conn.close()

    try:
        st.session_state[f"certificado_salida_{ingreso_id}"] = generar_pdf_entrega(
            ingreso_id
        )
        st.session_state.pop(f"error_certificado_salida_{ingreso_id}", None)
    except PdfGenerationError as exc:
        st.session_state[f"error_certificado_salida_{ingreso_id}"] = str(exc)


def volver_desde_checklist_salida():
    st.session_state.salida_ingreso_id = None
    cambiar_pagina("📊 Tablero de Equipos")


def pausar_mantenimiento():
    st.session_state.mant_queue = []
    st.session_state.hallazgos_extras_ok = False
    cambiar_pagina("📊 Tablero de Equipos")


def guardar_paso_mantenimiento():
    ingreso_id = st.session_state.mant_ingreso_id
    cola = st.session_state.mant_queue
    indice = st.session_state.mant_idx
    st.session_state.mensaje_mantenimiento = ""
    conn = conectar_db()
    try:
        estado_actual = conn.execute(
            "SELECT estado_proceso FROM equipos_ingresados WHERE id = ?",
            (ingreso_id,),
        ).fetchone()
        if not estado_actual or estado_actual[0] == "Mantenimiento Completado":
            return

        if indice < len(cola):
            item = cola[indice]
            accion = st.session_state.get(f"resultado_mantenimiento_{ingreso_id}")
            notas = st.session_state.get(f"notas_mantenimiento_{ingreso_id}", "")
            resultados_validos = (
                {"Realizado", "No Necesario", "Postergado"}
                if item["tipo"] == "mantenimiento"
                else {"Reparado", "No Reparado"}
            )
            if accion not in resultados_validos:
                st.session_state.mensaje_mantenimiento = "Seleccioná un resultado válido para esta operación."
                return
            if accion == "Postergado":
                cola.append(item)
            else:
                conn.execute(
                    "INSERT INTO controles_mantenimiento (ingreso_id, tarea, estado, observaciones, tipo_tarea) VALUES (?, ?, ?, ?, ?)",
                    (ingreso_id, item["tarea"], accion, notas.strip(), item["tipo"]),
                )
                conn.commit()
            st.session_state.mant_idx = indice + 1
        else:
            notas = st.session_state.get(f"notas_mantenimiento_{ingreso_id}", "")
            if notas.strip():
                conn.execute(
                    "INSERT INTO controles_mantenimiento (ingreso_id, tarea, estado, observaciones, tipo_tarea) VALUES (?, ?, ?, ?, ?)",
                    (ingreso_id, "Reparación Adicional en proceso", "Reparado", notas.strip(), "reparacion"),
                )
            conn.execute(
                "UPDATE equipos_ingresados SET estado_proceso = 'Mantenimiento Completado' WHERE id = ?",
                (ingreso_id,),
            )
            conn.commit()
            st.session_state.hallazgos_extras_ok = True
            try:
                st.session_state[f"pdfs_generados_{ingreso_id}"] = [
                    generar_pdf_taller(ingreso_id)
                ]
            except PdfGenerationError as exc:
                st.session_state[f"pdfs_generados_{ingreso_id}"] = []
                st.session_state.mensaje_mantenimiento = (
                    f"Mantenimiento completado, pero no se pudo generar el PDF: {exc}"
                )

        st.session_state[f"resultado_mantenimiento_{ingreso_id}"] = None
        st.session_state[f"notas_mantenimiento_{ingreso_id}"] = ""
    finally:
        conn.close()


def avanzar_paso_ingreso(nuevo_paso):
    st.session_state.paso_ingreso = nuevo_paso


def colorear_estados(val):
    if val in ['Inspección Inicial Completada', 'Mantenimiento Completado']: return 'color: #17a2b8; font-weight: bold;'
    if val in ['En Proceso de Inspección', 'Mantenimiento en Proceso', 'Checklist Salida en Proceso']: return 'color: #fd7e14; font-weight: bold;'
    if val == 'Equipo Entregado': return 'color: #28a745; font-weight: bold;'
    return ''

# ==========================================
# 1. PANTALLA: AGENDA SEMANAL
# ==========================================
if menu_elegido == "🏠 Inicio semanal":
    st.markdown("<h2 class='agenda-title'>🏠 Agenda semanal del taller</h2>", unsafe_allow_html=True)
    conn = conectar_db()
    try:
        trabajos_agenda, fechas_invalidas = _cargar_trabajos_agenda(conn)
    finally:
        conn.close()

    hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    if st.session_state.get("agenda_semana_fecha_referencia") != hoy:
        st.session_state.agenda_semana_offset = _desplazamiento_semana_por_defecto(hoy)
        st.session_state.agenda_semana_fecha_referencia = hoy
    lunes_actual = hoy - timedelta(days=hoy.weekday())
    lunes = lunes_actual + timedelta(weeks=st.session_state.agenda_semana_offset)
    viernes = lunes + timedelta(days=4)
    domingo = lunes + timedelta(days=6)

    trabajos_semana = [trabajo for trabajo in trabajos_agenda if lunes <= trabajo["fecha"] <= viernes]
    trabajos_fin_semana = [trabajo for trabajo in trabajos_agenda if viernes < trabajo["fecha"] <= domingo]
    trabajos_atrasados = [
        trabajo for trabajo in trabajos_agenda
        if trabajo["tipo"] in {"interno", "cliente"} and trabajo["fecha"] < hoy
    ]

    dias_semana = [
        (
            lunes + timedelta(days=numero_dia),
            [
                trabajo for trabajo in trabajos_semana
                if trabajo["fecha"] == lunes + timedelta(days=numero_dia)
            ],
        )
        for numero_dia in range(5)
    ]

    with st.container(key="agenda-desktop"):
        _mostrar_controles_semana(lunes, viernes, hoy, "desktop")
        col_agenda, col_atrasados = st.columns([5, 1.6], gap="small")
        with col_agenda:
            st.caption("Agenda de lunes a viernes")
            columnas_dias = st.columns(5, gap="small")
            for columna, (fecha_dia, trabajos_dia) in zip(columnas_dias, dias_semana):
                with columna:
                    _mostrar_dia_agenda(fecha_dia, trabajos_dia, hoy, "desktop")
            _mostrar_fin_de_semana(trabajos_fin_semana, lunes, hoy, "desktop")
        with col_atrasados:
            _mostrar_atrasados(trabajos_atrasados, hoy, "desktop")

    with st.container(key="agenda-tablet"):
        _mostrar_controles_semana(lunes, viernes, hoy, "tablet")
        col_agenda, col_atrasados = st.columns([3, 1.35], gap="small")
        with col_agenda:
            st.caption("Agenda de lunes a viernes")
            for indice in range(0, 5, 2):
                columnas_dias = st.columns(2, gap="small")
                for columna, numero_dia in zip(columnas_dias, (indice, indice + 1)):
                    if numero_dia < len(dias_semana):
                        with columna:
                            fecha_dia, trabajos_dia = dias_semana[numero_dia]
                            _mostrar_dia_agenda(fecha_dia, trabajos_dia, hoy, "tablet")
            _mostrar_fin_de_semana(trabajos_fin_semana, lunes, hoy, "tablet")
        with col_atrasados:
            _mostrar_atrasados(trabajos_atrasados, hoy, "tablet")

    with st.container(key="agenda-mobile"):
        _mostrar_controles_semana(lunes, viernes, hoy, "mobile")
        with st.expander(f"⚠️ Ver atrasados · {len(trabajos_atrasados)}", expanded=False):
            st.caption("Los ingresos técnicos no se clasifican como atrasados: solo tienen fecha de ingreso, no turno programado.")
            _mostrar_atrasados(trabajos_atrasados, hoy, "mobile", ancho_completo=True)

        opciones_dia = list(range(5))
        indice_dia = st.selectbox(
            "Día de la semana",
            opciones_dia,
            format_func=lambda indice: (
                f"{_nombre_dia(dias_semana[indice][0])} · "
                f"{len(dias_semana[indice][1])} pendientes"
            ),
            key="agenda_dia_movil",
            label_visibility="collapsed",
        )
        fecha_dia, trabajos_dia = dias_semana[indice_dia]
        _mostrar_dia_agenda(fecha_dia, trabajos_dia, hoy, "mobile")
        _mostrar_fin_de_semana(trabajos_fin_semana, lunes, hoy, "mobile")

    if fechas_invalidas:
        st.info(
            f"Se omitieron {fechas_invalidas} registros activos cuya fecha no se pudo interpretar. "
            "No se muestran tareas sin una fecha válida."
        )
    ingresos_tecnicos = sum(
        trabajo["tipo"] == "mantenimiento" for trabajo in trabajos_agenda
    )
    st.caption(
        f"Pendientes incluidos: {sum(trabajo['tipo'] == 'interno' for trabajo in trabajos_agenda)} internos, "
        f"{sum(trabajo['tipo'] == 'cliente' for trabajo in trabajos_agenda)} de clientes y "
        f"{ingresos_tecnicos} ingresos activos del flujo técnico. "
        "Los ingresos técnicos se ubican por fecha de ingreso porque la base no registra un turno programado."
    )

# ==========================================
# 2. PANTALLA: TABLERO TALLER (TRABAJOS INTERNOS)
# ==========================================
elif menu_elegido == "📊 Tablero Taller":
    st.title("📊 Tablero Taller: Gestión de Trabajos Internos")
    _mostrar_volver_a_agenda("interno")
    conn = conectar_db()
    cursor = conn.cursor()
    
    tab_panel, tab_cargar = st.tabs(["📋 Tablero de Trabajos", "➕ Cargar Nuevo Trabajo"])
    
    with tab_cargar:
        st.subheader("Registrar nuevo trabajo interno en el taller")
        df_mec = pd.read_sql_query("SELECT nombre FROM mecanicos", conn)
        
        with st.form("form_nuevo_trabajo_taller"):
            titulo = st.text_input("Título del Trabajo / Tarea:")
            descripcion = st.text_area("Descripción detallada del trabajo:")
            prioridad = st.selectbox("Prioridad:", ["Media", "Alta", "Baja"])
            mecanico = st.selectbox("Mecánico Asignado:", df_mec['nombre'].tolist() if not df_mec.empty else ["Sin asignar"])
            fecha_carga = st.date_input("Fecha de Carga:", value=datetime.today())
            fecha_entrega = st.date_input("Fecha Estimada de Entrega:", value=datetime.today())
            observaciones = st.text_area("Observaciones o Comentarios Iniciales:")
            
            if st.form_submit_button("Guardar Trabajo en Taller"):
                if titulo.strip():
                    cursor.execute("""
                        INSERT INTO pendientes_taller (titulo, descripcion, fecha_carga, fecha_entrega, prioridad, mecanico, estado, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (titulo.strip(), descripcion.strip(), str(fecha_carga), str(fecha_entrega), prioridad, mecanico, "Pendiente", observaciones.strip()))
                    conn.commit()
                    persistir_y_sync()
                    st.success("Trabajo de taller registrado correctamente.")
                    pass
                else:
                    st.error("⚠️ El campo 'Título del Trabajo' es obligatorio.")
                    
    with tab_panel:
        st.subheader("Panel de visualización y edición (Terminados al fondo)")
        df_trabajos = pd.read_sql_query("""
            SELECT * FROM pendientes_taller 
            ORDER BY CASE WHEN estado IN ('Realizado', 'Terminado') THEN 1 ELSE 0 END ASC, id DESC
        """, conn)
        
        if df_trabajos.empty:
            st.info("No hay trabajos registrados en el taller.")
        else:
            df_mec = pd.read_sql_query("SELECT nombre FROM mecanicos", conn)
            lista_mecanicos = df_mec['nombre'].tolist() if not df_mec.empty else []
            
            for _, row in df_trabajos.iterrows():
                es_finalizado = row['estado'] in ['Realizado', 'Terminado']
                icono = "✅" if es_finalizado else "🛠️"
                
                with st.expander(
                    f"{icono} {row['titulo']} — Mecánico: {row['mecanico']} [{row['estado']}]",
                    expanded=st.session_state.get("detalle_agenda") == ("interno", int(row["id"])),
                ):
                    with st.form(f"form_edit_taller_{row['id']}"):
                        edit_titulo = st.text_input("Título:", value=row['titulo'])
                        edit_desc = st.text_area("Descripción:", value=row['descripcion'] if row['descripcion'] else "")
                        edit_prioridad = st.selectbox("Prioridad:", ["Media", "Alta", "Baja"], index=["Media", "Alta", "Baja"].index(row['prioridad']) if row['prioridad'] in ["Media", "Alta", "Baja"] else 0)
                        
                        idx_mec = 0
                        if row['mecanico'] in lista_mecanicos:
                            idx_mec = lista_mecanicos.index(row['mecanico'])
                        edit_mecanico = st.selectbox("Mecánico Asignado:", lista_mecanicos if lista_mecanicos else ["Sin asignar"], index=idx_mec)
                        
                        edit_fcarga = st.text_input("Fecha Carga (AAAA-MM-DD):", value=row['fecha_carga'] if row['fecha_carga'] else "")
                        edit_fentrega = st.text_input("Fecha Entrega Estimada (AAAA-MM-DD):", value=row['fecha_entrega'] if row['fecha_entrega'] else "")
                        edit_estado = st.selectbox("Estado:", ["Pendiente", "Realizado", "Terminado"], index=["Pendiente", "Realizado", "Terminado"].index(row['estado']) if row['estado'] in ["Pendiente", "Realizado", "Terminado"] else 0)
                        edit_obs = st.text_area("Observaciones:", value=row['observaciones'] if row['observaciones'] else "")
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            cursor.execute("""
                                UPDATE pendientes_taller 
                                SET titulo = ?, descripcion = ?, prioridad = ?, mecanico = ?, fecha_carga = ?, fecha_entrega = ?, estado = ?, observaciones = ? 
                                WHERE id = ?
                            """, (edit_titulo.strip(), edit_desc.strip(), edit_prioridad, edit_mecanico, edit_fcarga.strip(), edit_fentrega.strip(), edit_estado, edit_obs.strip(), row['id']))
                            conn.commit()
                            persistir_y_sync()
                            st.success("Trabajo modificado correctamente.")
                            pass
                    
                    c_status, c_del = st.columns(2)
                    with c_status:
                        if not es_finalizado:
                            if st.button("✅ Marcar como Realizado", key=f"ok_taller_{row['id']}", use_container_width=True):
                                cursor.execute("UPDATE pendientes_taller SET estado = 'Realizado' WHERE id = ?", (row['id'],))
                                conn.commit()
                                persistir_y_sync()
                                pass
                    with c_del:
                        if st.button("🗑️ Eliminar Trabajo", key=f"del_taller_{row['id']}", use_container_width=True):
                            cursor.execute("DELETE FROM pendientes_taller WHERE id = ?", (row['id'],))
                            conn.commit()
                            pass
    conn.close()

# ==========================================
# 2. PANTALLA: TABLERO DE EQUIPOS
# ==========================================
elif menu_elegido == "📊 Tablero de Equipos":
    st.title("🚜 Estado General y Flujo Técnico")
    _mostrar_volver_a_agenda("mantenimiento")
    conn = conectar_db()
    
    df_incompletos = pd.read_sql_query("SELECT id, interno, mecanico, estado_proceso FROM equipos_ingresados WHERE estado_proceso IN ('En Proceso de Inspección', 'Mantenimiento en Proceso', 'Checklist Salida en Proceso')", conn)
    if not df_incompletos.empty:
        st.warning("⚠️ Alerta: Existen Checklists guardados por la mitad")
        opciones_inc = {f"[{r['estado_proceso']}] {r['interno']} (ID: {r['id']})": r['id'] for _, r in df_incompletos.iterrows()}
        detalle_agenda = st.session_state.get("detalle_agenda")
        ingreso_incompleto_agenda = (
            detalle_agenda[1]
            if detalle_agenda and detalle_agenda[0] == "mantenimiento"
            else None
        )
        indice_incompleto_agenda = next(
            (i for i, ingreso_id in enumerate(opciones_inc.values()) if ingreso_id == ingreso_incompleto_agenda),
            0,
        )
        seleccion_inc = st.selectbox(
            "Seleccione la tarea para retomarla:",
            list(opciones_inc.keys()),
            index=indice_incompleto_agenda,
        )
        
        id_retomar = opciones_inc[seleccion_inc]
        estado_inc = df_incompletos[df_incompletos["id"] == id_retomar].iloc[0]["estado_proceso"]
        if estado_inc == "En Proceso de Inspección":
            def retomar_inspeccion(ingreso_id):
                db = conectar_db()
                try:
                    controles_hechos = db.execute(
                        "SELECT COUNT(DISTINCT tarea) FROM controles_ingreso "
                        "WHERE ingreso_id = ? AND tarea != 'Falla Adicional Detectada'",
                        (ingreso_id,),
                    ).fetchone()[0]
                    total_controles = db.execute("SELECT COUNT(*) FROM maestro_controles_ingreso").fetchone()[0]
                finally:
                    db.close()
                st.session_state.ultimo_ingreso_id = ingreso_id
                st.session_state.paso_ingreso = "fallas_adicionales" if controles_hechos >= total_controles else "checklist"
                cambiar_pagina("🚜 Ingreso de Equipo (Guiado)")

            st.button(
                "➡️ Retomar Tarea Seleccionada",
                key="retomar_tarea_incompleta",
                use_container_width=True,
                on_click=retomar_inspeccion,
                args=(id_retomar,),
            )
            db = conectar_db()
            try:
                controles_hechos = db.execute(
                    "SELECT COUNT(DISTINCT tarea) FROM controles_ingreso WHERE ingreso_id = ? AND tarea != 'Falla Adicional Detectada'",
                    (id_retomar,),
                ).fetchone()[0]
                total_controles = db.execute(
                    "SELECT COUNT(*) FROM maestro_controles_ingreso"
                ).fetchone()[0]
            finally:
                db.close()
            if total_controles > 0 and controles_hechos >= total_controles:
                st.caption("El checklist está completo aunque el ingreso aún figure como inspección en proceso.")
                st.button(
                    "🛠️ Continuar a mantenimiento",
                    key=f"continuar_mantenimiento_inspeccion_{id_retomar}",
                    use_container_width=True,
                    on_click=continuar_mantenimiento_desde_inspeccion,
                    args=(id_retomar,),
                )
            mensaje_reanudacion = st.session_state.get("mensaje_reanudacion")
            if mensaje_reanudacion:
                st.warning(mensaje_reanudacion)
        elif estado_inc == "Mantenimiento en Proceso":
            st.button(
                "➡️ Retomar Tarea Seleccionada",
                key="retomar_tarea_incompleta",
                use_container_width=True,
                on_click=preparar_mantenimiento,
                args=(id_retomar,),
            )
        else:
            st.button(
                "➡️ Retomar Tarea Seleccionada",
                key="retomar_tarea_incompleta",
                use_container_width=True,
                on_click=retomar_checklist_salida,
                args=(id_retomar,),
            )

    with st.expander("➕ Crear equipo nuevo"):
        st.caption("Registrá el equipo antes de generar un ingreso o para corregir un ingreso existente.")
        with st.form("form_crear_equipo_tablero"):
            col_equipo_1, col_equipo_2 = st.columns(2)
            with col_equipo_1:
                nuevo_interno = st.text_input("Número de interno:")
                nueva_marca = st.text_input("Marca:")
            with col_equipo_2:
                nuevo_modelo = st.text_input("Modelo:")
                nuevo_tipo = st.text_input("Tipo de equipo:")

            if st.form_submit_button("💾 Guardar equipo"):
                datos_equipo = [nuevo_interno.strip(), nueva_marca.strip(), nuevo_modelo.strip(), nuevo_tipo.strip()]
                if not all(datos_equipo):
                    st.error("Completá todos los datos del equipo.")
                elif conn.execute("SELECT 1 FROM maestro_equipos WHERE interno = ?", (datos_equipo[0],)).fetchone():
                    st.error("Ya existe un equipo con ese número de interno.")
                else:
                    conn.execute(
                        "INSERT INTO maestro_equipos (interno, marca, modelo, tipo) VALUES (?, ?, ?, ?)",
                        tuple(datos_equipo),
                    )
                    conn.commit()
                    persistir_y_sync()
                    st.success("Equipo creado correctamente. Ya podés seleccionarlo al editar un ingreso.")
            
    st.markdown("---")
    
    df_ingresos = pd.read_sql_query("SELECT e.id, e.interno, m.marca, m.modelo, e.horas, e.origen, e.mecanico, e.fecha_ingreso, e.hora_inicio, e.estado_proceso FROM equipos_ingresados e JOIN maestro_equipos m ON e.interno = m.interno ORDER BY e.id DESC", conn)
    if df_ingresos.empty:
        st.info("No hay equipos ingresados en el sistema.")
    else:
        st.dataframe(df_ingresos.style.map(colorear_estados, subset=['estado_proceso']), use_container_width=True, hide_index=True)
        opciones_select = {f"{r['interno']} - {r['marca']} {r['modelo']} (ID: {r['id']}) - {r['estado_proceso']}": r['id'] for _, r in df_ingresos.iterrows()}
        detalle_agenda = st.session_state.get("detalle_agenda")
        ingreso_agenda = detalle_agenda[1] if detalle_agenda and detalle_agenda[0] == "mantenimiento" else None
        indice_ingreso_agenda = next(
            (i for i, ingreso_id in enumerate(opciones_select.values()) if ingreso_id == ingreso_agenda),
            0,
        )
        seleccion_mante = st.selectbox(
            "Seleccionar Unidad para ver acciones:",
            list(opciones_select.keys()),
            index=indice_ingreso_agenda,
        )
        
        if seleccion_mante:
            id_buscado = opciones_select[seleccion_mante]
            ingreso_actual = df_ingresos[df_ingresos['id'] == id_buscado].iloc[0]

            with st.expander("✏️ Editar datos del ingreso seleccionado"):
                df_equipos_edicion = pd.read_sql_query("SELECT interno, marca, modelo, tipo FROM maestro_equipos ORDER BY interno", conn)
                df_mecanicos_edicion = pd.read_sql_query("SELECT nombre FROM mecanicos ORDER BY nombre", conn)
                opciones_equipos_edicion = {
                    f"{row['interno']} - {row['marca']} {row['modelo']}": row['interno']
                    for _, row in df_equipos_edicion.iterrows()
                }
                etiquetas_equipos = list(opciones_equipos_edicion.keys())
                etiqueta_actual = next(
                    (etiqueta for etiqueta, interno in opciones_equipos_edicion.items() if interno == ingreso_actual['interno']),
                    etiquetas_equipos[0] if etiquetas_equipos else None,
                )
                lista_mecanicos_edicion = df_mecanicos_edicion['nombre'].tolist()
                mecanico_actual = ingreso_actual['mecanico'] if ingreso_actual['mecanico'] in lista_mecanicos_edicion else (lista_mecanicos_edicion[0] if lista_mecanicos_edicion else "Sin asignar")

                with st.form(f"form_editar_ingreso_{id_buscado}"):
                    col_edicion_1, col_edicion_2 = st.columns(2)
                    with col_edicion_1:
                        equipo_editado = st.selectbox(
                            "Equipo / Interno:",
                            etiquetas_equipos if etiquetas_equipos else ["Sin equipos configurados"],
                            index=etiquetas_equipos.index(etiqueta_actual) if etiqueta_actual in etiquetas_equipos else 0,
                        )
                        horas_editadas = st.number_input("Horómetro:", min_value=0, value=int(ingreso_actual['horas'] or 0), step=1)
                        origen_editado = st.selectbox("Origen / Destino:", ["Cliente", "Unidad de Alquiler", "Flota Propia"], index=["Cliente", "Unidad de Alquiler", "Flota Propia"].index(ingreso_actual['origen']) if ingreso_actual['origen'] in ["Cliente", "Unidad de Alquiler", "Flota Propia"] else 0)
                    with col_edicion_2:
                        mecanico_editado = st.selectbox("Mecánico:", lista_mecanicos_edicion if lista_mecanicos_edicion else ["Sin asignar"], index=lista_mecanicos_edicion.index(mecanico_actual) if mecanico_actual in lista_mecanicos_edicion else 0)
                        fecha_editada = st.text_input("Fecha de ingreso:", value=ingreso_actual['fecha_ingreso'] or "")
                        hora_inicio_editada = st.text_input("Hora de inicio:", value=ingreso_actual.get('hora_inicio', '') if hasattr(ingreso_actual, 'get') else "")

                    if st.form_submit_button("💾 Guardar correcciones"):
                        if not etiquetas_equipos:
                            st.error("No hay equipos configurados para asignar al ingreso.")
                        else:
                            conn.execute(
                                "UPDATE equipos_ingresados SET interno = ?, horas = ?, origen = ?, mecanico = ?, fecha_ingreso = ?, hora_inicio = ? WHERE id = ?",
                                (opciones_equipos_edicion[equipo_editado], horas_editadas, origen_editado, mecanico_editado, fecha_editada.strip(), hora_inicio_editada.strip(), id_buscado),
                            )
                            conn.commit()
                            persistir_y_sync()
                            st.success("Datos del ingreso corregidos correctamente.")

            estado_actual = df_ingresos[df_ingresos['id'] == id_buscado].iloc[0]['estado_proceso']
            
            if estado_actual == 'Inspección Inicial Completada':
                st.info("💡 Inspección completa. Iniciar Mantenimiento.")
                st.button(
                    "🛠️ Iniciar Mantenimiento",
                    use_container_width=True,
                    key=f"iniciar_mantenimiento_{id_buscado}",
                    on_click=preparar_mantenimiento,
                    args=(id_buscado,),
                )

            elif estado_actual == 'Mantenimiento Completado':
                st.info("✅ Mantenimiento finalizado. Generá el reporte técnico para descargarlo.")

                st.button(
                    "🔄 Reabrir mantenimiento para corregir",
                    use_container_width=True,
                    key=f"reabrir_mantenimiento_{id_buscado}",
                    on_click=preparar_mantenimiento,
                    args=(id_buscado,),
                )

                st.button(
                    "📄 Generar y guardar reporte PDF",
                    key=f"generar_archivar_reporte_{id_buscado}",
                    use_container_width=True,
                    on_click=generar_reportes,
                    args=(id_buscado,),
                )
                mensaje_pdf = st.session_state.pop("mensaje_pdf", None)
                if mensaje_pdf:
                    nivel, mensaje = mensaje_pdf
                    (st.error if nivel == "error" else st.success)(mensaje)
                mostrar_descargas_pdf(id_buscado)
                st.caption(
                    "Al generarlo, el PDF estará disponible para descarga. Si se guarda una copia local, "
                    "en Streamlit Cloud no será permanente."
                )
                
                st.write("---")
                st.button(
                    "📋 Iniciar Checklist de Salida / Entrega",
                    use_container_width=True,
                    key=f"iniciar_salida_{id_buscado}",
                    on_click=iniciar_checklist_salida,
                    args=(id_buscado,),
                )

            elif estado_actual == 'Equipo Entregado':
                st.success("🎉 Equipo entregado. Proceso finalizado en su totalidad.")
                st.button(
                    "📄 Generar y guardar reportes PDF",
                    key=f"generar_archivar_reportes_entrega_{id_buscado}",
                    use_container_width=True,
                    on_click=generar_reportes,
                    args=(id_buscado, True),
                )
                mensaje_pdf = st.session_state.pop("mensaje_pdf", None)
                if mensaje_pdf:
                    nivel, mensaje = mensaje_pdf
                    (st.error if nivel == "error" else st.success)(mensaje)
                mostrar_descargas_pdf(id_buscado)
    conn.close()

# ==========================================
# 3. PANTALLA: INGRESO DE EQUIPO
# ==========================================
elif menu_elegido == "🚜 Ingreso de Equipo (Guiado)":
    st.title("🚜 Recepción de Equipos y Diagnóstico")
    conn = conectar_db()
    controles_ingreso = pd.read_sql_query(
        "SELECT id, descripcion, orden FROM maestro_controles_ingreso ORDER BY orden, id",
        conn,
    )
    lista_ingreso = controles_ingreso["descripcion"].tolist()
    
    if st.session_state.paso_ingreso == "registro_inicial":
        st.subheader("Paso 1: Datos de Recepción")
        df_maestro = pd.read_sql_query("SELECT * FROM maestro_equipos ORDER BY interno", conn)
        df_mec = pd.read_sql_query("SELECT nombre FROM mecanicos", conn)
        if df_mec.empty:
            st.error("Por favor cargue mecánicos primero.")
        else:
            crear_equipo_nuevo = df_maestro.empty
            if not df_maestro.empty:
                opcion_equipo = st.radio(
                    "¿Qué desea cargar?",
                    ["Seleccionar equipo existente", "Crear nuevo equipo"],
                    index=0
                )
                crear_equipo_nuevo = opcion_equipo == "Crear nuevo equipo"

            with st.form("alta_ingreso"):
                if crear_equipo_nuevo:
                    interno = st.text_input("Nuevo Número de Interno:")
                    marca = st.text_input("Marca del Equipo:")
                    modelo = st.text_input("Modelo del Equipo:")
                    tipo = st.text_input("Tipo de Equipo:")
                else:
                    interno = st.selectbox("Seleccione Número de Interno:", df_maestro['interno'].tolist())
                    marca = None
                    modelo = None
                    tipo = None

                horas = st.number_input("Horómetro:", min_value=0, step=1)
                origen = st.selectbox("Origen / Destino:", ["Cliente", "Unidad de Alquiler", "Flota Propia"])
                mecanico = st.selectbox("Mecánico:", df_mec['nombre'].tolist())

                if st.form_submit_button("Comenzar Inspección ➡️"):
                    if crear_equipo_nuevo:
                        if not interno.strip() or not marca.strip() or not modelo.strip() or not tipo.strip():
                            st.error("Todos los datos del equipo son obligatorios para crear un nuevo equipo.")
                        else:
                            existe_equipo = conn.execute("SELECT 1 FROM maestro_equipos WHERE interno = ?", (interno.strip(),)).fetchone()
                            if existe_equipo:
                                st.error("Ya existe un equipo con ese interno. Use otro número o seleccione un equipo existente.")
                            else:
                                conn.execute(
                                    "INSERT INTO maestro_equipos (interno, marca, modelo, tipo) VALUES (?, ?, ?, ?)",
                                    (interno.strip(), marca.strip(), modelo.strip(), tipo.strip())
                                )
                                conn.commit()
                                persistir_y_sync()
                    if not lista_ingreso:
                        st.error("No hay ítems configurados en el Checklist de Ingreso.")
                    else:
                        ahora_txt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                        resultado_ingreso = conn.execute(
                            "INSERT INTO equipos_ingresados (interno, horas, origen, mecanico, fecha_ingreso, hora_inicio, estado_proceso) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id",
                            (interno.strip(), horas, origen, mecanico, fecha_hoy, ahora_txt, "En Proceso de Inspección")
                        )
                        st.session_state.ultimo_ingreso_id = resultado_ingreso.fetchone()[0]
                        conn.commit()
                        persistir_y_sync()
                        st.session_state.salida_ingreso_id = None
                        avanzar_paso_ingreso("checklist")
                        conn.close()
                        st.rerun()
                    
    elif st.session_state.paso_ingreso == "checklist":
        ingreso_id = st.session_state.ultimo_ingreso_id
        if not ingreso_id:
            st.error("No hay un ingreso activo. Retomalo desde el Tablero de Equipos.")
        elif not controles_ingreso.empty:
            respuestas = _cargar_respuestas_checklist(
                conn,
                "controles_ingreso",
                ingreso_id,
            )
            progreso, total_controles = _mostrar_checklist_planilla(
                "ingreso",
                ingreso_id,
                list(controles_ingreso.itertuples(index=False, name=None)),
                respuestas,
            )
            st.button(
                "Continuar a fallas adicionales →",
                key=f"continuar_fallas_{ingreso_id}",
                use_container_width=True,
                on_click=avanzar_paso_ingreso,
                args=("fallas_adicionales",),
                disabled=progreso < total_controles,
            )
        else:
            st.error("No hay ítems configurados en el Checklist de Ingreso.")
            
    elif st.session_state.paso_ingreso == "fallas_adicionales":
        st.subheader("⚠️ Fallas o Roturas Adicionales")
        st.write("Si detectaste algún problema extra en la máquina que no estaba en el checklist, detallalo acá (opcional):")
        
        with st.form("form_fallas_extra"):
            col1, col2 = st.columns(2)
            with col1:
                f1 = st.text_input("Problema adicional 1:")
                f2 = st.text_input("Problema adicional 2:")
                f3 = st.text_input("Problema adicional 3:")
            with col2:
                f4 = st.text_input("Problema adicional 4:")
                f5 = st.text_input("Problema adicional 5:")
                
            if st.form_submit_button("✅ Finalizar Inspección Completa"):
                fallas_extra = [f for f in [f1, f2, f3, f4, f5] if f.strip() != ""]
                ingreso_id = st.session_state.ultimo_ingreso_id
                respuestas = _cargar_respuestas_checklist(
                    conn,
                    "controles_ingreso",
                    ingreso_id,
                )
                controles_hechos = _contar_checklist_completados(
                    lista_ingreso,
                    respuestas,
                    "controles_ingreso",
                )
                if not lista_ingreso:
                    st.error("No hay controles configurados; no se puede finalizar el ingreso.")
                elif controles_hechos < len(lista_ingreso):
                    st.error(
                        f"Completá todos los controles antes de finalizar "
                        f"({controles_hechos} de {len(lista_ingreso)})."
                    )
                else:
                    estado_ingreso = conn.execute(
                        "SELECT estado_proceso FROM equipos_ingresados WHERE id = ?",
                        (ingreso_id,),
                    ).fetchone()
                    if not estado_ingreso or estado_ingreso[0] != "En Proceso de Inspección":
                        st.error("El ingreso ya no está en estado de inspección activa.")
                    else:
                        for falla in fallas_extra:
                            conn.execute(
                                "INSERT INTO controles_ingreso "
                                "(ingreso_id, tarea, estado, observaciones) VALUES (?, ?, ?, ?)",
                                (ingreso_id, "Falla Adicional Detectada", "Malo", falla.strip()),
                            )

                        conn.execute(
                            "UPDATE equipos_ingresados SET estado_proceso = "
                            "'Inspección Inicial Completada', hora_fin = ? WHERE id = ?",
                            (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), ingreso_id),
                        )
                        conn.commit()
                        persistir_y_sync()
                        st.session_state.paso_ingreso = "registro_inicial"
                        st.session_state.ultimo_ingreso_id = None
                        cambiar_pagina("📊 Tablero de Equipos")
                        conn.close()
                        st.rerun()

    conn.close()

# ==========================================
# 4. PANTALLA: EJECUCIÓN DE MANTENIMIENTO
# ==========================================
elif menu_elegido == "🛠️ Ejecución de Mantenimiento":
    st.title("🛠️ Orden de Trabajo y Reparaciones")
    if not st.session_state.mant_queue:
        st.info("No hay rutina activa. Iníciala desde el Tablero de Equipos.")
    else:
        conn = conectar_db()
        idx = st.session_state.mant_idx
        cola = st.session_state.mant_queue
        total = len(cola)
        ingreso_id = st.session_state.mant_ingreso_id
        
        with st.sidebar:
            st.markdown("### ⏱️ Control de Tiempos")
            total_horas = conn.execute("SELECT SUM(horas) FROM registro_horas WHERE ingreso_id = ?", (ingreso_id,)).fetchone()[0]
            st.metric("Total Horas Invertidas", f"{total_horas or 0} hs")
            with st.expander("Cargar Horas (Mecánicos)"):
                with st.form("form_horas"):
                    df_mec = pd.read_sql_query("SELECT nombre FROM mecanicos", conn)
                    mec_horas = st.selectbox("Técnico:", df_mec['nombre'].tolist())
                    h_input = st.number_input("Horas dedicadas hoy:", min_value=0.5, step=0.5, value=1.0)
                    if st.form_submit_button("💾 Guardar Horas"):
                        conn.execute("INSERT INTO registro_horas (ingreso_id, fecha, horas, mecanico) VALUES (?, ?, ?, ?)", (ingreso_id, datetime.today().strftime("%d/%m/%Y"), h_input, mec_horas))
                        conn.commit()
                        pass
            st.markdown("---")
            st.button(
                "⏸️ Pausar Tareas",
                use_container_width=True,
                key=f"btn_pausar_tareas_{ingreso_id}",
                on_click=pausar_mantenimiento,
            )

        paso_en_curso = idx < total
        item = cola[idx] if paso_en_curso else None
        estado_mantenimiento = conn.execute(
            "SELECT estado_proceso FROM equipos_ingresados WHERE id = ?",
            (ingreso_id,),
        ).fetchone()[0]
        mantenimiento_cerrado = estado_mantenimiento == "Mantenimiento Completado"

        if paso_en_curso:
            st.progress(idx / max(total, 1))
            st.info(f"Operación {idx + 1} de {total}: {item['tarea']}")
        else:
            st.progress(1.0)
            st.info("Etapa final: verificá hallazgos adicionales y cerrá el mantenimiento.")

        st.radio(
            "Resultado:",
            ["Realizado", "No Necesario", "Postergado", "Reparado", "No Reparado"],
            horizontal=True,
            index=None,
            key=f"resultado_mantenimiento_{ingreso_id}",
        )
        st.text_area(
            "Notas, insumos o hallazgos adicionales (opcional):",
            key=f"notas_mantenimiento_{ingreso_id}",
        )
        st.button(
            "Guardar / continuar",
            key=f"guardar_mantenimiento_{ingreso_id}",
            on_click=guardar_paso_mantenimiento,
        )
        mensaje_mantenimiento = st.session_state.get("mensaje_mantenimiento")
        if mensaje_mantenimiento:
            st.warning(mensaje_mantenimiento)
        mostrar_descargas_pdf(ingreso_id)

        if not mensaje_mantenimiento:
            st.info(
                "Al cerrar el mantenimiento, el PDF queda disponible para descarga. También se intenta guardar "
                "una copia en la carpeta local; en Streamlit Cloud, ese archivo no queda archivado permanentemente."
            )
        st.button(
            "Volver al Tablero de Equipos",
            use_container_width=True,
            key=f"btn_volver_tablero_equipos_{ingreso_id}",
            on_click=pausar_mantenimiento,
        )
        conn.close()

# ==========================================
# 5. PANTALLA: CHECKLIST DE SALIDA
# ==========================================
elif menu_elegido == "✅ Entrega de Equipo (Salida)":
    st.title("✅ Control de Calidad y Entrega")
    conn = conectar_db()
    controles_salida = pd.read_sql_query(
        "SELECT id, descripcion, orden FROM maestro_controles_salida ORDER BY orden, id",
        conn,
    )
    lista_salida = controles_salida["descripcion"].tolist()
    ingreso_id = st.session_state.salida_ingreso_id
    
    if not ingreso_id:
        st.info("No hay Checklist de Salida activo. Inicialo desde el Tablero de Equipos.")
    else:
        estado_ingreso = conn.execute(
            "SELECT estado_proceso FROM equipos_ingresados WHERE id = ?",
            (ingreso_id,),
        ).fetchone()
        if not estado_ingreso:
            st.error("No se encontró el ingreso seleccionado.")
        elif estado_ingreso[0] == "Equipo Entregado":
            st.success("🎉 Checklist de salida completado. El equipo quedó habilitado para ser retirado.")
            certificado = st.session_state.get(f"certificado_salida_{ingreso_id}")
            error_certificado = st.session_state.get(
                f"error_certificado_salida_{ingreso_id}"
            )
            if certificado:
                bytes_entrega, nombre_entrega = certificado
                st.download_button(
                    label="📄 Descargar Certificado de Entrega (PDF)",
                    data=bytes_entrega,
                    file_name=nombre_entrega,
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"dl_entrega_checklist_{ingreso_id}",
                )
                if st.button(
                    "✉️ Enviar Certificado por email",
                    key=f"mail_entrega_activa_{ingreso_id}",
                    use_container_width=True,
                ):
                    enviado, detalle = enviar_pdf_por_email(
                        bytes_entrega,
                        nombre_entrega,
                        "Certificado de entrega",
                    )
                    (st.success if enviado else st.warning)(
                        f"Certificado enviado a {detalle}." if enviado else detalle
                    )
                st.caption(
                    "El certificado se descarga en tu dispositivo. La copia local no queda archivada "
                    "permanentemente en Streamlit Cloud."
                )
            else:
                if error_certificado:
                    st.error(f"No se pudo generar el Certificado de Entrega: {error_certificado}")
                else:
                    st.info("El checklist quedó completo; el certificado puede generarse desde el Tablero de Equipos.")
            st.button(
                "Volver al Tablero",
                use_container_width=True,
                key=f"btn_volver_tablero_entrega_{ingreso_id}",
                on_click=volver_desde_checklist_salida,
            )
        elif estado_ingreso[0] != "Checklist Salida en Proceso":
            st.info("No hay un Checklist de Salida activo para este equipo. Iniciálo desde el Tablero de Equipos.")
        elif controles_salida.empty:
            st.error("No hay ítems configurados en el Checklist de Salida.")
        else:
            respuestas = _cargar_respuestas_checklist(
                conn,
                "controles_salida",
                ingreso_id,
            )
            progreso, total_controles = _mostrar_checklist_planilla(
                "salida",
                ingreso_id,
                list(controles_salida.itertuples(index=False, name=None)),
                respuestas,
            )
            st.button(
                "✅ Finalizar entrega",
                key=f"finalizar_salida_{ingreso_id}",
                use_container_width=True,
                disabled=progreso < total_controles,
                on_click=finalizar_checklist_salida,
                args=(ingreso_id,),
            )
            mensaje_error = st.session_state.get(f"error_salida_{ingreso_id}")
            if mensaje_error:
                st.error(mensaje_error)
    conn.close()

# =========================================================
# 6. PANTALLA: ARCHIVO DE COMPROBANTES 
# =========================================================
elif menu_elegido == "🗂️ Archivo de PDFs":
    st.title("🗂️ Archivo de Comprobantes")
    st.write("Desde acá podés descargar los PDF que estén disponibles en la carpeta local `comprobantes`.")
    st.info("En Streamlit Cloud, esta carpeta es temporal: los archivos no quedan archivados permanentemente.")
    
    carpeta_pdfs = "comprobantes" 
    
    if not os.path.exists(carpeta_pdfs):
        os.makedirs(carpeta_pdfs)
        
    archivos = os.listdir(carpeta_pdfs)
    archivos_pdf = [f for f in archivos if f.endswith(".pdf")]
    
    if archivos_pdf:
        st.write("---")
        busqueda = st.text_input("🔍 Buscar comprobante por nombre, reporte o equipo:", "")
        archivos_filtrados = [f for f in archivos_pdf if busqueda.lower() in f.lower()]
        
        if archivos_filtrados:
            for archivo in archivos_filtrados:
                col1, col2 = st.columns([3, 1])
                if "Reporte_Taller" in archivo:
                    col1.write(f"🛠️ **[Reporte Taller]** `{archivo}`")
                else:
                    col1.write(f"📦 **[Entrega]** `{archivo}`")
                    
                with open(os.path.join(carpeta_pdfs, archivo), "rb") as f:
                    datos_archivo = f.read()
                    col2.download_button(
                        label="📥 Descargar",
                        data=datos_archivo,
                        file_name=archivo,
                        mime="application/pdf",
                        key=f"btn_{archivo}"
                    )
                    if col2.button("✉️ Enviar", key=f"mail_archivo_{archivo}"):
                        enviado, detalle = enviar_pdf_por_email(datos_archivo, archivo, f"Comprobante {archivo}")
                        (st.success if enviado else st.warning)(f"PDF enviado a {detalle}." if enviado else detalle)
        else:
            st.info("No se encontraron comprobantes que coincidan con la búsqueda.")
    else:
        st.info("Todavía no hay archivos PDF guardados.")

# ==========================================
# 7. PANTALLA: LISTA DE COMPRAS
# ==========================================
elif menu_elegido == "🛒 Lista de Compras":
    st.title("🛒 Gestión de Insumos y Repuestos")
    conn = conectar_db()
    
    tab_pendientes, tab_cargar, tab_rubros = st.tabs(["📋 Lista de Pendientes", "📝 Cargar Necesidad", "⚙️ Configurar Rubros"])
    
    with tab_cargar:
        st.subheader("Cargar nuevo ítem a comprar")
        df_rubros_carga = pd.read_sql_query("SELECT nombre FROM maestro_rubros_compras ORDER BY nombre", conn)
        
        if df_rubros_carga.empty:
            st.warning("⚠️ Primero tenés que configurar al menos un rubro en la solapa 'Configurar Rubros'.")
        else:
            with st.form("form_compras"):
                rubro_sel = st.selectbox("Seleccionar Rubro / Proveedor:", df_rubros_carga['nombre'].tolist())
                desc_input = st.text_input("Descripción (Ej: Filtro de aceite, Electrodos, Lija):")
                det_input = st.text_area("Detalle Técnico / Código / Marca preferida (Opcional):")
                cant_input = st.text_input("Cantidad necesaria (Ej: 2 unidades, 5 litros):")
                
                if st.form_submit_button("➕ Agregar a la lista"):
                    if desc_input.strip() and cant_input.strip():
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                        conn.execute("INSERT INTO lista_compras (rubro, descripcion, detalle, cantidad, fecha_carga, estado) VALUES (?, ?, ?, ?, ?, ?)", 
                                     (rubro_sel, desc_input.strip(), det_input.strip(), cant_input.strip(), fecha_hoy, "Pendiente"))
                        conn.commit()
                        st.success("¡Agregado exitosamente a la lista de pendientes!")
                        pass
                    else:
                        st.error("⚠️ Los campos 'Descripción' y 'Cantidad' son obligatorios.")

    with tab_pendientes:
        st.subheader("Pendientes de Compra por Rubro")
        df_pendientes = pd.read_sql_query("SELECT * FROM lista_compras WHERE estado = 'Pendiente' ORDER BY rubro", conn)
        
        if df_pendientes.empty:
            st.success("🎉 ¡No hay compras pendientes! El taller está completamente abastecido.")
        else:
            rubros_activos = df_pendientes['rubro'].unique()
            for rubro in rubros_activos:
                st.markdown(f"### 📦 {rubro}")
                df_filtrado = df_pendientes[df_pendientes['rubro'] == rubro]
                
                for _, fila in df_filtrado.iterrows():
                    c1, c2, c3, c4 = st.columns([0.3, 0.4, 0.15, 0.15])
                    c1.write(f"**{fila['descripcion']}**")
                    c2.caption(fila['detalle'] if fila['detalle'] else "-")
                    c3.write(f"Cant: **{fila['cantidad']}**")
                    if c4.button("✅ Ya lo compré", key=f"btn_compra_{fila['id']}"):
                        conn.execute("UPDATE lista_compras SET estado = 'Comprado' WHERE id = ?", (fila['id'],))
                        conn.commit()
                        pass
                st.markdown("---")

    with tab_rubros:
        st.subheader("Administrar Categorías (Rubros)")
        with st.form("form_add_rubro"):
            nuevo_rubro = st.text_input("Nombre del nuevo Rubro (Ej: Bulonería, Repuestos Hidráulica):")
            if st.form_submit_button("Guardar Rubro"):
                if nuevo_rubro.strip():
                    conn.execute("INSERT INTO maestro_rubros_compras (nombre) VALUES (?)", (nuevo_rubro.strip(),))
                    conn.commit()
                    st.success("Rubro agregado correctamente.")
                    pass
                    
        st.markdown("**Rubros Actuales:**")
        df_rubros_lista = pd.read_sql_query("SELECT * FROM maestro_rubros_compras ORDER BY nombre", conn)
        for _, fila in df_rubros_lista.iterrows():
            c1, c2 = st.columns([0.8, 0.2])
            c1.write(f"🔹 {fila['nombre']}")
            if c2.button("🗑️ Eliminar", key=f"btn_delrub_{fila['id']}"):
                conn.execute("DELETE FROM maestro_rubros_compras WHERE id = ?", (fila['id'],))
                conn.commit()
                pass

    conn.close()

# ==========================================
# 8. PANTALLA: TRABAJOS CLIENTES
# ==========================================
elif menu_elegido == "💼 Trabajos Clientes":
    st.title("💼 Gestión de Trabajos en Clientes")
    _mostrar_volver_a_agenda("cliente")
    conn = conectar_db()
    cursor = conn.cursor()

    tab_panel, tab_cargar = st.tabs(["📋 Panel de Trabajos", "➕ Cargar Nuevo Trabajo"])
    
    with tab_cargar:
        st.subheader("Registrar nuevo trabajo externo")
        with st.form("form_nuevo_trabajo"):
            cliente = st.text_input("Nombre del Cliente:")
            tarea = st.text_area("Descripción de la tarea / Servicio técnico a realizar:")
            fecha = st.date_input("Fecha estimada:", value=datetime.today())
            if st.form_submit_button("Guardar Trabajo"):
                if cliente.strip() and tarea.strip():
                    cursor.execute("INSERT INTO trabajos_clientes (cliente, tarea, estado, fecha_programada) VALUES (?, ?, ?, ?)", 
                                   (cliente.strip(), tarea.strip(), "Pendiente", str(fecha)))
                    conn.commit()
                    persistir_y_sync()
                    st.success("Trabajo registrado correctamente.")
                    pass
                else:
                    st.error("⚠️ Todos los campos son obligatorios.")

    with tab_panel:
        st.subheader("Panel de visualización y edición")
        df_t = pd.read_sql_query("SELECT * FROM trabajos_clientes WHERE estado = 'Pendiente' ORDER BY fecha_programada", conn)
        
        if df_t.empty:
            st.info("No hay trabajos en clientes pendientes.")
        else:
            for _, row in df_t.iterrows():
                with st.expander(
                    f"📍 {row['cliente']} — Programado: {row['fecha_programada']}",
                    expanded=st.session_state.get("detalle_agenda") == ("cliente", int(row["id"])),
                ):
                    with st.form(f"form_edit_cliente_{row['id']}"):
                        edit_cliente = st.text_input("Nombre del Cliente:", value=row['cliente'])
                        edit_tarea = st.text_area("Detalle de la tarea:", value=row['tarea'])
                        edit_fecha = st.text_input("Fecha Programada (AAAA-MM-DD):", value=row['fecha_programada'])
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            cursor.execute("UPDATE trabajos_clientes SET cliente = ?, tarea = ?, fecha_programada = ? WHERE id = ?", 
                                           (edit_cliente.strip(), edit_tarea.strip(), edit_fecha.strip(), row['id']))
                            conn.commit()
                            persistir_y_sync()
                            st.success("Registro modificado correctamente.")
                            pass
                    
                    c_status, c_del = st.columns(2)
                    with c_status:
                        if st.button("✅ Marcar como Realizado", key=f"ok_{row['id']}", use_container_width=True):
                            cursor.execute("UPDATE trabajos_clientes SET estado = 'Realizado' WHERE id = ?", (row['id'],))
                            conn.commit()
                            pass
                    with c_del:
                        if st.button("🗑️ Eliminar Registro", key=f"del_{row['id']}", use_container_width=True):
                            cursor.execute("DELETE FROM trabajos_clientes WHERE id = ?", (row['id'],))
                            conn.commit()
                            pass

    conn.close()

# ==========================================
# 9. PANTALLA: CONFIGURACIÓN GENERAL
# ==========================================
elif menu_elegido == "⚙️ Configuración General":
    st.title("⚙️ Configurador de Listas de Tareas")
    conn = conectar_db()
    
    def gestionar_lista(tabla, titulo_boton):
        with st.form(f"add_{tabla}"):
            nuevo_t = st.text_input("Nuevo ítem para la lista:")
            res_o = conn.execute(f"SELECT MAX(orden) FROM {tabla}").fetchone()[0]
            nuevo_o = (res_o + 1) if res_o else 1
            if st.form_submit_button(titulo_boton):
                if nuevo_t:
                    conn.execute(f"INSERT INTO {tabla} (descripcion, orden) VALUES (?, ?)", (nuevo_t.strip(), nuevo_o))
                    conn.commit(); pass
                    
        df_list = pd.read_sql_query(f"SELECT * FROM {tabla} ORDER BY orden ASC", conn)
        for i, fila in df_list.iterrows():
            c1, c2, c3, c4 = st.columns([0.6, 0.08, 0.08, 0.24])
            c1.write(f"**{fila['orden']}**. {fila['descripcion']}")
            if c2.button("⬆️", key=f"u_{tabla}_{fila['id']}") and i > 0:
                fant = df_list.iloc[i - 1]
                conn.execute(f"UPDATE {tabla} SET orden = ? WHERE id = ?", (fila['orden'], fant['id']))
                conn.execute(f"UPDATE {tabla} SET orden = ? WHERE id = ?", (fant['orden'], fila['id']))
                conn.commit(); pass
            if c3.button("⬇️", key=f"d_{tabla}_{fila['id']}") and i < len(df_list) - 1:
                fsig = df_list.iloc[i + 1]
                conn.execute(f"UPDATE {tabla} SET orden = ? WHERE id = ?", (fila['orden'], fsig['id']))
                conn.execute(f"UPDATE {tabla} SET orden = ? WHERE id = ?", (fsig['orden'], fila['id']))
                conn.commit(); pass
            if c4.button("🗑️ Quitar", key=f"del_{tabla}_{fila['id']}"):
                conn.execute(f"DELETE FROM {tabla} WHERE id = ?", (fila['id'],))
                conn.commit(); pass

    tab1, tab2, tab3 = st.tabs(["1️⃣ Checklist Ingreso", "2️⃣ Rutina Mantenimiento", "3️⃣ Checklist Salida"])
    
    with tab1:
        st.subheader("Configurar Preguntas de Ingreso")
        gestionar_lista("maestro_controles_ingreso", "Agregar a Ingreso")
    with tab2:
        st.subheader("Configurar Tareas de Mantenimiento")
        gestionar_lista("maestro_tareas_mantenimiento", "Agregar a Mantenimiento")
    with tab3:
        st.subheader("Configurar Checklist de Entrega (Salida)")
        gestionar_lista("maestro_controles_salida", "Agregar a Salida")

    conn.close()

# ==========================================
# 10. PANTALLA: PERSONAL MECÁNICO
# ==========================================
elif menu_elegido == "👥 Personal Mecánico":
    st.title("👥 Personal Técnico del Taller")
    conn = conectar_db()
    with st.form("alta_mec"):
        nuevo_m = st.text_input("Nombre del nuevo operario mecánico:")
        if st.form_submit_button("Registrar Técnico"):
            if nuevo_m:
                conn.execute("INSERT INTO mecanicos (nombre) VALUES (?)", (nuevo_m.strip(),))
                conn.commit(); st.success("Técnico dado de alta."); pass
    st.subheader("Nómina Activa")
    st.dataframe(pd.read_sql_query("SELECT * FROM mecanicos", conn), use_container_width=True, hide_index=True)
    conn.close()

# ==========================================
# 11. PANTALLA: REPORTES Y FACTURACIÓN
# ==========================================
elif menu_elegido == "📈 Reportes y Facturación":
    st.title("📈 Reporte Mensual de Trabajos")
    st.write("Acá podés generar el detalle unificado de todos los trabajos terminados (Taller, Externos e Internos) para exportarlos a Excel y facilitar la facturación.")
    
    conn = conectar_db()
    
    st.write("---")
    st.subheader("Seleccionar Período a Exportar")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fecha_desde = st.date_input("Desde:", datetime.today().replace(day=1))
    with col_f2:
        fecha_hasta = st.date_input("Hasta:", datetime.today())
        
    if st.button("🚀 Generar Reporte Completo", use_container_width=True):
        
        # 1. Equipos del Taller
        query_equipos = """
            SELECT 
                e.fecha_ingreso as "Fecha",
                'TALLER: ' || e.origen as "Cliente",
                m.marca || ' ' || m.modelo || ' (Int: ' || e.interno || ')' as "Equipo",
                'Mantenimiento / Reparación de Unidad en Taller' as "Descripcion_Trabajo",
                e.id as "ingreso_id"
            FROM equipos_ingresados e
            JOIN maestro_equipos m ON e.interno = m.interno
            WHERE e.estado_proceso IN ('Mantenimiento Completado', 'Checklist Salida en Proceso', 'Equipo Entregado')
        """
        df_eq = pd.read_sql_query(query_equipos, conn)
        
        if not df_eq.empty:
            df_eq['Horas Mano de Obra'] = 0.0
            df_eq['Repuestos / Insumos'] = ""
            for idx, row in df_eq.iterrows():
                h_total = conn.execute("SELECT sum(horas) FROM registro_horas WHERE ingreso_id = ?", (row['ingreso_id'],)).fetchone()[0]
                df_eq.at[idx, 'Horas Mano de Obra'] = h_total if h_total else 0.0
                
                tareas = conn.execute("SELECT observaciones FROM controles_mantenimiento WHERE ingreso_id = ? AND estado IN ('Realizado', 'Reparado')", (row['ingreso_id'],)).fetchall()
                if tareas:
                    # Filtramos los que tengan nota cargada para que sea más prolijo el reporte
                    insumos_limpios = [t[0] for t in tareas if t[0].strip() != ""]
                    df_eq.at[idx, 'Repuestos / Insumos'] = " - ".join(insumos_limpios) if insumos_limpios else "Sin insumos detallados"
                else:
                    df_eq.at[idx, 'Repuestos / Insumos'] = "Sin detalle"
                    
            df_eq = df_eq.drop(columns=['ingreso_id'])
        
        # 2. Trabajos Externos en Clientes
        query_clientes = """
            SELECT 
                fecha_programada as "Fecha",
                'EXTERNO: ' || cliente as "Cliente",
                'Servicio Técnico en Cliente' as "Equipo",
                tarea as "Descripcion_Trabajo",
                0.0 as "Horas Mano de Obra",
                '' as "Repuestos / Insumos"
            FROM trabajos_clientes
            WHERE estado = 'Realizado'
        """
        df_cli = pd.read_sql_query(query_clientes, conn)
        
        # 3. Trabajos Internos
        query_internos = """
            SELECT 
                fecha_entrega as "Fecha",
                'INTERNO: Taller Propio' as "Cliente",
                titulo as "Equipo",
                descripcion as "Descripcion_Trabajo",
                0.0 as "Horas Mano de Obra",
                observaciones as "Repuestos / Insumos"
            FROM pendientes_taller
            WHERE estado IN ('Realizado', 'Terminado')
        """
        df_int = pd.read_sql_query(query_internos, conn)
        
        frames = [df for df in [df_eq, df_cli, df_int] if not df.empty]
        
        if not frames:
            st.warning("No hay trabajos finalizados en la base de datos.")
        else:
            df_reporte = pd.concat(frames, ignore_index=True)
            df_reporte['Fecha_Parsed'] = pd.to_datetime(df_reporte['Fecha'], format='mixed', dayfirst=True, errors='coerce')
            
            mask = (df_reporte['Fecha_Parsed'].dt.date >= fecha_desde) & (df_reporte['Fecha_Parsed'].dt.date <= fecha_hasta)
            df_filtrado = df_reporte.loc[mask].copy()
            
            if df_filtrado.empty:
                st.info(f"No hay registros terminados entre el {fecha_desde.strftime('%d/%m/%Y')} y el {fecha_hasta.strftime('%d/%m/%Y')}.")
            else:
                df_filtrado = df_filtrado.drop(columns=['Fecha_Parsed'])
                columnas_finales = ['Fecha', 'Cliente', 'Equipo', 'Descripcion_Trabajo', 'Repuestos / Insumos', 'Horas Mano de Obra']
                df_filtrado = df_filtrado[columnas_finales]
                df_filtrado.rename(columns={'Descripcion_Trabajo': 'Descripción del Trabajo'}, inplace=True)
                
                st.success(f"Se encontraron {len(df_filtrado)} trabajos en el período seleccionado.")
                st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
                
                csv = df_filtrado.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                st.download_button(
                    label="📥 Descargar Exportación para Excel (Formato CSV)",
                    data=csv,
                    file_name=f"Reporte_Trabajos_{fecha_desde.strftime('%Y%m%d')}_a_{fecha_hasta.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    conn.close()