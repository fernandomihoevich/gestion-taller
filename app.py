import streamlit as st
import pandas as pd
from datetime import datetime
from email.message import EmailMessage
from fpdf import FPDF
import os
import smtplib

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

def _texto_pdf(valor):
    return str(valor or "").encode("latin-1", "replace").decode("latin-1")


def _guardar_pdf(datos_pdf, nombre_archivo):
    carpeta_pdfs = "comprobantes"
    os.makedirs(carpeta_pdfs, exist_ok=True)
    ruta_pdf = os.path.join(carpeta_pdfs, nombre_archivo)
    with open(ruta_pdf, "wb") as archivo:
        archivo.write(datos_pdf)
    return ruta_pdf


def _crear_pdf(titulo, filas):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_title(_texto_pdf(titulo))
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _texto_pdf(titulo), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, _texto_pdf(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    for etiqueta, valor in filas:
        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 7, _texto_pdf(f"{etiqueta}:"), wrapmode="CHAR")
        pdf.set_font("Helvetica", "", 10)
        for linea in _texto_pdf(valor).splitlines() or [" "]:
            pdf.multi_cell(0, 6, linea or " ", wrapmode="CHAR")
        pdf.ln(2)
    return bytes(pdf.output())


def generar_pdf_taller(ingreso_id):
    conn = conectar_db()
    try:
        ingreso = conn.execute("""
            SELECT e.id, e.interno, m.marca, m.modelo, e.horas, e.origen,
                   e.mecanico, e.fecha_ingreso, e.hora_inicio, e.hora_fin,
                   e.estado_proceso
            FROM equipos_ingresados e
            JOIN maestro_equipos m ON m.interno = e.interno
            WHERE e.id = ?
        """, (ingreso_id,)).fetchone()
        if not ingreso:
            raise ValueError(f"No existe el ingreso {ingreso_id}")

        controles = conn.execute("""
            SELECT tarea, estado, observaciones
            FROM controles_ingreso WHERE ingreso_id = ? ORDER BY id
        """, (ingreso_id,)).fetchall()
        mantenimiento = conn.execute("""
            SELECT tarea, estado, observaciones
            FROM controles_mantenimiento WHERE ingreso_id = ? ORDER BY id
        """, (ingreso_id,)).fetchall()
        horas = conn.execute("""
            SELECT fecha, horas, mecanico
            FROM registro_horas WHERE ingreso_id = ? ORDER BY id
        """, (ingreso_id,)).fetchall()

        filas = [
            ("Ingreso", ingreso[0]), ("Equipo", f"{ingreso[1]} - {ingreso[2]} {ingreso[3]}"),
            ("Horometro", ingreso[4]), ("Origen", ingreso[5]), ("Mecanico", ingreso[6]),
            ("Fecha ingreso", ingreso[7]), ("Estado", ingreso[10]),
            ("Controles de ingreso", "\n".join(f"{r[0]}: {r[1]} - {r[2] or ''}" for r in controles) or "Sin controles"),
            ("Mantenimiento", "\n".join(f"{r[0]}: {r[1]} - {r[2] or ''}" for r in mantenimiento) or "Sin tareas registradas"),
            ("Horas registradas", "\n".join(f"{r[0]} - {r[1]} hs - {r[2]}" for r in horas) or "Sin horas registradas"),
        ]
        nombre = f"Reporte_Taller_{ingreso[1]}_{ingreso_id}.pdf"
        datos = _crear_pdf("Reporte tecnico de taller", filas)
        _guardar_pdf(datos, nombre)
        return datos, nombre
    finally:
        conn.close()


def generar_pdf_entrega(ingreso_id):
    conn = conectar_db()
    try:
        ingreso = conn.execute("""
            SELECT e.id, e.interno, m.marca, m.modelo, e.fecha_ingreso,
                   e.mecanico, e.estado_proceso
            FROM equipos_ingresados e
            JOIN maestro_equipos m ON m.interno = e.interno
            WHERE e.id = ?
        """, (ingreso_id,)).fetchone()
        controles = conn.execute("""
            SELECT tarea, estado, observaciones
            FROM controles_salida WHERE ingreso_id = ? ORDER BY id
        """, (ingreso_id,)).fetchall()
        if not ingreso:
            raise ValueError(f"No existe el ingreso {ingreso_id}")

        filas = [
            ("Ingreso", ingreso[0]), ("Equipo", f"{ingreso[1]} - {ingreso[2]} {ingreso[3]}"),
            ("Fecha ingreso", ingreso[4]), ("Mecanico", ingreso[5]), ("Estado", ingreso[6]),
            ("Checklist de salida", "\n".join(f"{r[0]}: {r[1]} - {r[2] or ''}" for r in controles) or "Sin controles"),
        ]
        nombre = f"Certificado_Entrega_{ingreso[1]}_{ingreso_id}.pdf"
        datos = _crear_pdf("Certificado de entrega", filas)
        _guardar_pdf(datos, nombre)
        return datos, nombre
    finally:
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
if "navegacion" not in st.session_state: st.session_state.navegacion = "📊 Tablero Taller"
if "paso_ingreso" not in st.session_state: st.session_state.paso_ingreso = "registro_inicial"
if "ultimo_ingreso_id" not in st.session_state: st.session_state.ultimo_ingreso_id = None
if "idx_control_actual" not in st.session_state: st.session_state.idx_control_actual = 0
if "mant_queue" not in st.session_state: st.session_state.mant_queue = []
if "mant_idx" not in st.session_state: st.session_state.mant_idx = 0
if "mant_ingreso_id" not in st.session_state: st.session_state.mant_ingreso_id = None
if "salida_ingreso_id" not in st.session_state: st.session_state.salida_ingreso_id = None
if "idx_control_salida" not in st.session_state: st.session_state.idx_control_salida = 0
if "hallazgos_extras_ok" not in st.session_state: st.session_state.hallazgos_extras_ok = False

# --- MENÚ LATERAL ---
lista_opciones_menu = [
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


def avanzar_paso_ingreso(nuevo_paso):
    st.session_state.paso_ingreso = nuevo_paso


def colorear_estados(val):
    if val in ['Inspección Inicial Completada', 'Mantenimiento Completado']: return 'color: #17a2b8; font-weight: bold;'
    if val in ['En Proceso de Inspección', 'Mantenimiento en Proceso', 'Checklist Salida en Proceso']: return 'color: #fd7e14; font-weight: bold;'
    if val == 'Equipo Entregado': return 'color: #28a745; font-weight: bold;'
    return ''

# ==========================================
# 1. PANTALLA: TABLERO TALLER (TRABAJOS INTERNOS)
# ==========================================
if menu_elegido == "📊 Tablero Taller":
    st.title("📊 Tablero Taller: Gestión de Trabajos Internos")
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
                
                with st.expander(f"{icono} {row['titulo']} — Mecánico: {row['mecanico']} [{row['estado']}]"):
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
    conn = conectar_db()
    
    df_incompletos = pd.read_sql_query("SELECT id, interno, mecanico, estado_proceso FROM equipos_ingresados WHERE estado_proceso IN ('En Proceso de Inspección', 'Mantenimiento en Proceso', 'Checklist Salida en Proceso')", conn)
    if not df_incompletos.empty:
        st.warning("⚠️ Alerta: Existen Checklists guardados por la mitad")
        opciones_inc = {f"[{r['estado_proceso']}] {r['interno']} (ID: {r['id']})": r['id'] for _, r in df_incompletos.iterrows()}
        seleccion_inc = st.selectbox("Seleccione la tarea para retomarla:", list(opciones_inc.keys()))
        
        if st.button("➡️ Retomar Tarea Seleccionada", use_container_width=True):
            id_retomar = opciones_inc[seleccion_inc]
            estado_inc = df_incompletos[df_incompletos['id'] == id_retomar].iloc[0]['estado_proceso']
            
            if estado_inc == 'En Proceso de Inspección':
                controles_hechos = conn.execute("SELECT COUNT(*) FROM controles_ingreso WHERE ingreso_id = ? AND tarea != 'Falla Adicional Detectada'", (id_retomar,)).fetchone()[0]
                total_lista = conn.execute("SELECT COUNT(*) FROM maestro_controles_ingreso").fetchone()[0]
                st.session_state.ultimo_ingreso_id = id_retomar
                st.session_state.idx_control_actual = controles_hechos
                
                if controles_hechos >= total_lista:
                    st.session_state.paso_ingreso = "fallas_adicionales"
                else:
                    st.session_state.paso_ingreso = "checklist"
                cambiar_pagina("🚜 Ingreso de Equipo (Guiado)")
            elif estado_inc == 'Mantenimiento en Proceso':
                df_tareas_db = pd.read_sql_query("SELECT descripcion FROM maestro_tareas_mantenimiento ORDER BY orden ASC", conn)
                cola_trabajo = [{'tipo': 'mantenimiento', 'tarea': t} for t in df_tareas_db['descripcion'].tolist()]
                df_malos = pd.read_sql_query("SELECT tarea, observaciones FROM controles_ingreso WHERE ingreso_id = ? AND estado = 'Malo'", conn, params=(id_retomar,))
                for _, averia in df_malos.iterrows():
                    cola_trabajo.append({'tipo': 'reparacion', 'tarea': f"[{averia['tarea']}] {averia['observaciones']}"})
                hechas = pd.read_sql_query("SELECT tarea FROM controles_mantenimiento WHERE ingreso_id = ?", conn, params=(id_retomar,))['tarea'].tolist()
                tareas_pendientes = [tarea for tarea in cola_trabajo if tarea['tarea'] not in hechas]
                st.session_state.mant_queue = cola_trabajo
                st.session_state.mant_idx = len(cola_trabajo) if not tareas_pendientes else cola_trabajo.index(tareas_pendientes[0])
                st.session_state.mant_ingreso_id = id_retomar
                st.session_state.hallazgos_extras_ok = False
                cambiar_pagina("🛠️ Ejecución de Mantenimiento")
            else:
                controles_hechos = conn.execute("SELECT COUNT(*) FROM controles_salida WHERE ingreso_id = ?", (id_retomar,)).fetchone()[0]
                st.session_state.salida_ingreso_id = id_retomar
                st.session_state.idx_control_salida = controles_hechos
                cambiar_pagina("✅ Entrega de Equipo (Salida)")
            pass

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
        seleccion_mante = st.selectbox("Seleccionar Unidad para ver acciones:", list(opciones_select.keys()))
        
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
                if st.button("🛠️ Iniciar Mantenimiento", use_container_width=True):
                    df_tareas_db = pd.read_sql_query("SELECT descripcion FROM maestro_tareas_mantenimiento ORDER BY orden ASC", conn)
                    cola_trabajo = [{'tipo': 'mantenimiento', 'tarea': t} for t in df_tareas_db['descripcion'].tolist()]
                    
                    df_malos = pd.read_sql_query(f"SELECT tarea, observaciones FROM controles_ingreso WHERE ingreso_id = {id_buscado} AND estado = 'Malo'", conn)
                    for _, averia in df_malos.iterrows():
                        cola_trabajo.append({'tipo': 'reparacion', 'tarea': f"[{averia['tarea']}] {averia['observaciones']}"})
                    
                    st.session_state.mant_queue = cola_trabajo
                    st.session_state.mant_idx = 0
                    st.session_state.mant_ingreso_id = id_buscado
                    st.session_state.hallazgos_extras_ok = False
                    conn.execute("UPDATE equipos_ingresados SET estado_proceso = 'Mantenimiento en Proceso' WHERE id = ?", (id_buscado,))
                    conn.commit()
                    cambiar_pagina("🛠️ Ejecución de Mantenimiento")

            elif estado_actual == 'Mantenimiento Completado':
                st.success("✅ Mantenimiento finalizado técnico en taller. ¡Ya podés descargar el reporte para facturar!")

                if st.button("🔄 Reabrir mantenimiento para corregir", use_container_width=True, key=f"reabrir_mantenimiento_{id_buscado}"):
                    df_tareas_db = pd.read_sql_query("SELECT descripcion FROM maestro_tareas_mantenimiento ORDER BY orden ASC", conn)
                    cola_trabajo = [{'tipo': 'mantenimiento', 'tarea': t} for t in df_tareas_db['descripcion'].tolist()]
                    df_malos = pd.read_sql_query("SELECT tarea, observaciones FROM controles_ingreso WHERE ingreso_id = ? AND estado = 'Malo'", conn, params=(id_buscado,))
                    for _, averia in df_malos.iterrows():
                        cola_trabajo.append({'tipo': 'reparacion', 'tarea': f"[{averia['tarea']}] {averia['observaciones']}"})
                    st.session_state.mant_queue = cola_trabajo
                    st.session_state.mant_idx = 0
                    st.session_state.mant_ingreso_id = id_buscado
                    st.session_state.hallazgos_extras_ok = False
                    conn.execute("UPDATE equipos_ingresados SET estado_proceso = 'Mantenimiento en Proceso' WHERE id = ?", (id_buscado,))
                    conn.commit()
                    cambiar_pagina("🛠️ Ejecución de Mantenimiento")
                    st.stop()
                
                bytes_taller, nombre_taller = generar_pdf_taller(id_buscado)
                col_pdf_download, col_pdf_email = st.columns(2)
                with col_pdf_download:
                    st.download_button(
                        label="📥 Descargar Reporte Técnico de Taller (Para Facturar)",
                        data=bytes_taller,
                        file_name=nombre_taller,
                        mime="application/pdf",
                        use_container_width=True
                    )
                with col_pdf_email:
                    if st.button("✉️ Enviar por email", key=f"mail_taller_{id_buscado}", use_container_width=True):
                        enviado, detalle = enviar_pdf_por_email(bytes_taller, nombre_taller, "Reporte técnico de taller")
                        (st.success if enviado else st.warning)(f"Reporte enviado a {detalle}." if enviado else detalle)
                
                st.write("---")
                if st.button("📋 Iniciar Checklist de Salida / Entrega", use_container_width=True):
                    conn.execute("UPDATE equipos_ingresados SET estado_proceso = 'Checklist Salida en Proceso' WHERE id = ?", (id_buscado,))
                    conn.commit()
                    st.session_state.salida_ingreso_id = id_buscado
                    st.session_state.idx_control_salida = 0
                    cambiar_pagina("✅ Entrega de Equipo (Salida)")

            elif estado_actual == 'Equipo Entregado':
                st.success("🎉 Equipo entregado. Proceso finalizado en su totalidad.")
                bytes_taller, nombre_taller = generar_pdf_taller(id_buscado)
                bytes_entrega, nombre_entrega = generar_pdf_entrega(id_buscado)
                
                c_pdf1, c_pdf2 = st.columns(2)
                with c_pdf1:
                    st.download_button(label="📥 Descargar Reporte de Taller", data=bytes_taller, file_name=nombre_taller, mime="application/pdf", use_container_width=True, key=f"dl_t_{id_buscado}")
                    if st.button("✉️ Enviar Reporte por email", key=f"mail_taller_entregado_{id_buscado}", use_container_width=True):
                        enviado, detalle = enviar_pdf_por_email(bytes_taller, nombre_taller, "Reporte técnico de taller")
                        (st.success if enviado else st.warning)(f"Reporte enviado a {detalle}." if enviado else detalle)
                with c_pdf2:
                    st.download_button(label="📥 Descargar Certificado de Entrega", data=bytes_entrega, file_name=nombre_entrega, mime="application/pdf", use_container_width=True, key=f"dl_e_{id_buscado}")
                    if st.button("✉️ Enviar Certificado por email", key=f"mail_entrega_{id_buscado}", use_container_width=True):
                        enviado, detalle = enviar_pdf_por_email(bytes_entrega, nombre_entrega, "Certificado de entrega")
                        (st.success if enviado else st.warning)(f"Certificado enviado a {detalle}." if enviado else detalle)
    conn.close()

# ==========================================
# 3. PANTALLA: INGRESO DE EQUIPO
# ==========================================
elif menu_elegido == "🚜 Ingreso de Equipo (Guiado)":
    st.title("🚜 Recepción de Equipos y Diagnóstico")
    conn = conectar_db()
    lista_ingreso = pd.read_sql_query("SELECT descripcion FROM maestro_controles_ingreso ORDER BY orden", conn)['descripcion'].tolist()
    
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
                        st.session_state.idx_control_actual = 0
                        avanzar_paso_ingreso("checklist")
                    
    elif st.session_state.paso_ingreso == "checklist":
        idx = st.session_state.idx_control_actual
        if idx >= len(lista_ingreso):
            st.session_state.paso_ingreso = "fallas_adicionales"
            pass
            
        tarea_actual = lista_ingreso[idx]
        st.subheader(f"Inspección: Control {idx+1} de {len(lista_ingreso)}")
        st.info(f"📋 Evalúe el estado de: **{tarea_actual}**")
        with st.form(f"form_chk_{idx}"):
            estado = st.radio("Condición:", ["OK", "Malo", "No Realizado"], horizontal=True, index=None)
            obs = st.text_area("Observaciones:")
            if st.form_submit_button("Guardar y continuar ➡️"):
                if estado is None:
                    st.error("⚠️ Es obligatorio seleccionar una Condición.")
                else:
                    conn.execute("INSERT INTO controles_ingreso (ingreso_id, tarea, estado, observaciones) VALUES (?, ?, ?, ?)", (st.session_state.ultimo_ingreso_id, tarea_actual, estado, obs.strip()))
                    
                    if idx == len(lista_ingreso) - 1:
                        avanzar_paso_ingreso("fallas_adicionales")
                    else:
                        st.session_state.idx_control_actual += 1
                    
                    conn.commit()
                    
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
                
                for falla in fallas_extra:
                    conn.execute("INSERT INTO controles_ingreso (ingreso_id, tarea, estado, observaciones) VALUES (?, ?, ?, ?)", 
                                 (st.session_state.ultimo_ingreso_id, "Falla Adicional Detectada", "Malo", falla.strip()))
                
                conn.execute("UPDATE equipos_ingresados SET estado_proceso = 'Inspección Inicial Completada', hora_fin = ? WHERE id = ?", (datetime.now().strftime("%d/%m/%Y %H:%M:%S"), st.session_state.ultimo_ingreso_id))
                conn.commit()
                st.session_state.paso_ingreso = "registro_inicial"
                st.success("¡Checklist completo y fallas adicionales guardadas correctamente!")
                cambiar_pagina("📊 Tablero de Equipos")

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
            if st.button("⏸️ Pausar Tareas", use_container_width=True, key="btn_pausar_tareas"):
                st.session_state.mant_queue = [] 
                cambiar_pagina("📊 Tablero de Equipos")

        if idx >= total:
            if not st.session_state.hallazgos_extras_ok:
                st.subheader("🔧 Hallazgos extras y Reparaciones Adicionales")
                st.write("Si durante el mantenimiento encontraste y solucionaste algo más que no estaba listado, detallalo acá para sumarlo al reporte:")
                
                with st.form("form_extras_mant"):
                    h1 = st.text_input("Hallazgo / Reparación extra 1:")
                    h2 = st.text_input("Hallazgo / Reparación extra 2:")
                    h3 = st.text_input("Hallazgo / Reparación extra 3:")
                    
                    if st.form_submit_button("✅ Guardar Extras y Finalizar Mantenimiento"):
                        extras = [h for h in [h1, h2, h3] if h.strip() != ""]
                        for h in extras:
                            conn.execute("INSERT INTO controles_mantenimiento (ingreso_id, tarea, estado, observaciones, tipo_tarea) VALUES (?, ?, ?, ?, ?)", 
                                         (ingreso_id, "Reparación Adicional en proceso", "Reparado", h.strip(), "reparacion"))
                        
                        conn.execute("UPDATE equipos_ingresados SET estado_proceso = 'Mantenimiento Completado' WHERE id = ?", (ingreso_id,))
                        conn.commit()
                        st.session_state.hallazgos_extras_ok = True
                        pass
            else:
                st.success("🎉 ¡Mantenimiento finalizado! El Reporte de Taller se guardó en el servidor.")
                
                bytes_taller, nombre_taller = generar_pdf_taller(ingreso_id)
                col_pdf_download, col_pdf_email = st.columns(2)
                with col_pdf_download:
                    st.download_button(
                        label="📄 Descargar Reporte Técnico de Taller Ahora (Para Facturar)",
                        data=bytes_taller,
                        file_name=nombre_taller,
                        mime="application/pdf",
                        use_container_width=True
                    )
                with col_pdf_email:
                    if st.button("✉️ Enviar por email", key=f"mail_mantenimiento_{ingreso_id}", use_container_width=True):
                        enviado, detalle = enviar_pdf_por_email(bytes_taller, nombre_taller, "Reporte técnico de taller")
                        (st.success if enviado else st.warning)(f"Reporte enviado a {detalle}." if enviado else detalle)
                
                if st.button("Volver al Tablero de Equipos", use_container_width=True, key="btn_volver_tablero_equipos"):
                    st.session_state.mant_queue = []
                    st.session_state.hallazgos_extras_ok = False
                    cambiar_pagina("📊 Tablero de Equipos")
        else:
            item = cola[idx]
            st.progress((idx) / total)
            st.write(f"🔧 **Operación {idx + 1} de {total} (Pendientes)**")
            if item['tipo'] == 'mantenimiento': 
                st.success(f"### {item['tarea']}")
            else: 
                st.error(f"**⚠️ REPARACIÓN DE AVERÍA DETECTADA**\n### {item['tarea']}")
            
            with st.form(f"form_execute_{idx}"):
                respuestas = ["Realizado", "No Necesario", "Postergado"] if item['tipo'] == 'mantenimiento' else ["Reparado", "No Reparado"]
                accion = st.radio("Resultado:", respuestas, horizontal=True, index=None)
                notas = st.text_area("Notas / Insumos:")
                if st.form_submit_button("Registrar Paso ➡️"):
                    if accion is None:
                        st.error("⚠️ Seleccioná un Resultado.")
                    else:
                        if accion == "Postergado":
                            st.session_state.mant_queue.append(item)
                            st.warning("🔄 Paso postergado.")
                        else:
                            conn.execute("INSERT INTO controles_mantenimiento (ingreso_id, tarea, estado, observaciones, tipo_tarea) VALUES (?, ?, ?, ?, ?)", (ingreso_id, item['tarea'], accion, notas.strip(), item['tipo']))
                            conn.commit()
                        st.session_state.mant_idx += 1
        conn.close()

# ==========================================
# 5. PANTALLA: CHECKLIST DE SALIDA
# ==========================================
elif menu_elegido == "✅ Entrega de Equipo (Salida)":
    st.title("✅ Control de Calidad y Entrega")
    conn = conectar_db()
    lista_salida = pd.read_sql_query("SELECT descripcion FROM maestro_controles_salida ORDER BY orden", conn)['descripcion'].tolist()
    ingreso_id = st.session_state.salida_ingreso_id
    
    if not ingreso_id:
        st.info("No hay Checklist de Salida activo. Inicialo desde el Tablero de Equipos.")
    else:
        idx = st.session_state.idx_control_salida
        if idx >= len(lista_salida):
            conn.execute("UPDATE equipos_ingresados SET estado_proceso = 'Equipo Entregado' WHERE id = ?", (ingreso_id,))
            conn.commit()
            st.success("🎉 ¡Checklist de Salida Completado! El equipo quedó habilitado para ser retirado.")
            st.balloons()
            
            bytes_entrega, nombre_entrega = generar_pdf_entrega(ingreso_id)
            st.download_button(
                label="📄 Descargar Certificado de Entrega (PDF)",
                data=bytes_entrega,
                file_name=nombre_entrega,
                mime="application/pdf",
                use_container_width=True
            )
            if st.button("✉️ Enviar Certificado por email", key=f"mail_entrega_activa_{ingreso_id}", use_container_width=True):
                enviado, detalle = enviar_pdf_por_email(bytes_entrega, nombre_entrega, "Certificado de entrega")
                (st.success if enviado else st.warning)(f"Certificado enviado a {detalle}." if enviado else detalle)
            
            if st.button("Volver al Tablero", use_container_width=True, key="btn_volver_tablero_entrega"):
                st.session_state.salida_ingreso_id = None
                cambiar_pagina("📊 Tablero de Equipos")
        else:
            tarea_actual = lista_salida[idx]
            st.progress((idx) / len(lista_salida))
            st.subheader(f"Control Final: {idx+1} de {len(lista_salida)}")
            st.info(f"📋 Verificá para entregar: **{tarea_actual}**")
            with st.form(f"form_salida_{idx}"):
                estado = st.radio("Condición:", ["OK", "Malo (Avisar a Taller)", "No Aplica"], horizontal=True, index=None)
                obs = st.text_area("Observaciones:")
                if st.form_submit_button("Guardar y Continuar ➡️"):
                    if estado is None:
                        st.error("⚠️ Obligatorio seleccionar Condición.")
                    else:
                        conn.execute("INSERT INTO controles_salida (ingreso_id, tarea, estado, observaciones) VALUES (?, ?, ?, ?)", (ingreso_id, tarea_actual, estado, obs.strip()))
                        conn.commit()
                        st.session_state.idx_control_salida += 1
    conn.close()

# =========================================================
# 6. PANTALLA: ARCHIVO DE COMPROBANTES 
# =========================================================
elif menu_elegido == "🗂️ Archivo de PDFs":
    st.title("🗂️ Archivo de Comprobantes")
    st.write("Desde acá podés buscar y descargar los Reportes de Taller y Certificados de Entrega directamente a tu tablet.")
    
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
                with st.expander(f"📍 {row['cliente']} — Programado: {row['fecha_programada']}"):
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