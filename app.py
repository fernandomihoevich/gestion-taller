import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from fpdf import FPDF, FPDFException
import os
import re
import sqlite3
import smtplib
import json
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo
from psycopg2 import Error as PsycopgError

from database_adapter import conectar_db, ensure_database_file, crear_respaldo_db, sincronizar_supabase, ensure_remote_restore, inicializar_db, inicializar_tablas_acceso, has_remote_db, IS_CLOUD

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

    .compras-title {
        font-size: 1.45rem;
        line-height: 1.2;
        margin: 0 0 0.45rem;
    }

    .compras-section-title {
        font-size: 1.05rem;
        line-height: 1.2;
        margin: 0.35rem 0;
    }

    .st-key-compras-pendientes [data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }

    .st-key-compras-pendientes [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.35rem 0.55rem;
    }

    .st-key-compras-encabezado {
        display: block;
    }

    @media (max-width: 700px) {
        .st-key-compras-pendientes [data-testid="stHorizontalBlock"] {
            flex-direction: column;
            align-items: stretch;
            gap: 0.2rem;
        }

        .st-key-compras-pendientes [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        .st-key-compras-encabezado {
            display: none !important;
        }

        .st-key-compras-pendientes .stButton button {
            min-height: 2.75rem;
        }
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

    .st-key-ingresos-desktop,
    .st-key-ingresos-mobile {
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

        .st-key-ingresos-desktop {
            display: block !important;
        }
    }

    @media (min-width: 701px) and (max-width: 1199px) {
        .st-key-agenda-tablet {
            display: block !important;
        }

        .st-key-ingresos-desktop {
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
        .st-key-mantenimiento-checklist [data-testid="stHorizontalBlock"],
        .st-key-salida-checklist [data-testid="stHorizontalBlock"] {
            flex-direction: column;
            align-items: stretch;
            gap: 0.25rem;
        }

        .st-key-ingreso-checklist [data-testid="stColumn"],
        .st-key-mantenimiento-checklist [data-testid="stColumn"],
        .st-key-salida-checklist [data-testid="stColumn"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }

        .st-key-ingreso-checklist input[type="checkbox"],
        .st-key-mantenimiento-checklist input[type="checkbox"],
        .st-key-salida-checklist input[type="checkbox"] {
            transform: scale(1.2);
        }

        .st-key-ingreso-checklist [data-testid="stCheckbox"] label,
        .st-key-mantenimiento-checklist [data-testid="stCheckbox"] label,
        .st-key-salida-checklist [data-testid="stCheckbox"] label {
            min-height: 2.75rem;
            align-items: center;
        }

        .st-key-ingresos-desktop {
            display: none !important;
        }

        .st-key-ingresos-mobile {
            display: block !important;
        }
    }

    .st-key-ingreso-checklist [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-mantenimiento-checklist [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-salida-checklist [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.35rem 0.55rem;
    }

    .st-key-ingreso-checklist [data-testid="stVerticalBlock"],
    .st-key-mantenimiento-checklist [data-testid="stVerticalBlock"],
    .st-key-salida-checklist [data-testid="stVerticalBlock"] {
        gap: 0.35rem;
    }
    </style>
    """, unsafe_allow_html=True)

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


SECCIONES_APP = (
    ("inicio_semanal", "🏠 Inicio semanal"),
    ("tablero_taller", "📊 Tablero Taller"),
    ("tablero_equipos", "📊 Tablero de Equipos"),
    ("trabajos_clientes", "💼 Trabajos Clientes"),
    ("lista_compras", "🛒 Lista de Compras"),
    ("ingreso_equipo", "🚜 Ingreso de Equipo (Guiado)"),
    ("ejecucion_mantenimiento", "🛠️ Ejecución de Mantenimiento"),
    ("entrega_equipo", "✅ Entrega de Equipo (Salida)"),
    ("archivo_pdfs", "🗂️ Archivo de PDFs"),
    ("configuracion_general", "⚙️ Configuración General"),
    ("personal_mecanico", "👥 Personal Mecánico"),
    ("reportes_facturacion", "📈 Reportes y Facturación"),
)
ETIQUETA_A_SECCION = {
    etiqueta: clave for clave, etiqueta in SECCIONES_APP
}
PANTALLA_USUARIOS = "🔐 Usuarios y permisos"
CLAVES_ESTADO_AUTENTICACION = (
    "auth_access_token",
    "auth_refresh_token",
    "auth_user_id",
    "auth_email",
    "auth_full_name",
    "auth_is_admin",
    "auth_permissions",
)


class SupabaseAuthError(RuntimeError):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def _leer_secreto(nombre):
    valor = os.environ.get(nombre)
    if valor:
        return valor.strip()
    try:
        valor = st.secrets.get(nombre)
    except Exception:
        valor = None
    return valor.strip() if isinstance(valor, str) and valor.strip() else None


def _configuracion_autenticacion():
    nueva_clave_secreta = _leer_secreto("SUPABASE_SECRET_KEY")
    clave_service_role = _leer_secreto("SUPABASE_SERVICE_ROLE_KEY")
    return {
        "url": _leer_secreto("SUPABASE_URL"),
        "publishable_key": (
            _leer_secreto("SUPABASE_PUBLISHABLE_KEY")
            or _leer_secreto("SUPABASE_ANON_KEY")
        ),
        "secret_key": nueva_clave_secreta or clave_service_role,
        "secret_key_legacy": not nueva_clave_secreta and bool(clave_service_role),
        "app_url": _leer_secreto("APP_URL"),
        "admin_email": (_leer_secreto("ADMIN_EMAIL") or "").casefold(),
    }


def _mensaje_error_auth(cuerpo, status):
    try:
        datos = json.loads(cuerpo.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        datos = {}
    if not isinstance(datos, dict):
        datos = {}
    mensaje = (
        datos.get("msg")
        or datos.get("message")
        or datos.get("error_description")
        or datos.get("error")
    )
    if not isinstance(mensaje, str) or not mensaje.strip():
        mensaje = f"Supabase rechazó la solicitud (HTTP {status})."
    return mensaje.strip()[:400]


def _solicitud_supabase(config, endpoint, api_key, method="GET", data=None, token=None):
    url = f"{config['url'].rstrip('/')}{endpoint}"
    headers = {
        "apikey": api_key,
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"
    cuerpo = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(
        url,
        data=cuerpo,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            contenido = response.read()
    except urllib.error.HTTPError as exc:
        raise SupabaseAuthError(
            _mensaje_error_auth(exc.read(), exc.code),
            exc.code,
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise SupabaseAuthError(
            "No se pudo conectar con Supabase Auth. Verificá la URL y la conectividad."
        ) from exc
    if not contenido:
        return {}
    try:
        respuesta = json.loads(contenido.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SupabaseAuthError(
            "Supabase Auth devolvió una respuesta inválida."
        ) from exc
    if not isinstance(respuesta, dict):
        raise SupabaseAuthError("Supabase Auth devolvió un formato inesperado.")
    return respuesta


def _limpiar_sesion_autenticacion():
    st.session_state.clear()


def _guardar_tokens_auth(respuesta):
    usuario = respuesta.get("user") or {}
    user_id = usuario.get("id")
    email = usuario.get("email")
    access_token = respuesta.get("access_token")
    refresh_token = respuesta.get("refresh_token")
    if not all((user_id, email, access_token, refresh_token)):
        raise SupabaseAuthError("Supabase no devolvió una sesión completa.")
    st.session_state["auth_access_token"] = access_token
    st.session_state["auth_refresh_token"] = refresh_token
    st.session_state["auth_user_id"] = str(user_id)
    st.session_state["auth_email"] = str(email)


def _obtener_parametros_url():
    if hasattr(st, "query_params"):
        parametros = st.query_params
        return {
            nombre: parametros.get_all(nombre)
            for nombre in parametros
        }
    return st.experimental_get_query_params()


def _establecer_parametros_url(parametros):
    if hasattr(st, "query_params"):
        consulta = st.query_params
        consulta.clear()
        for nombre, valores in parametros.items():
            consulta[nombre] = valores
        return
    st.experimental_set_query_params(**parametros)


def _forzar_recarga_streamlit():
    recargar = getattr(st, "rerun", None) or getattr(
        st,
        "experimental_rerun",
        None,
    )
    if recargar is None:
        raise RuntimeError("La versión instalada de Streamlit no permite recargar la app.")
    recargar()


def _capturar_callback_invitacion():
    parametros = _obtener_parametros_url()
    tipos = parametros.get("type", [])
    hashes = parametros.get("token_hash", [])
    parametros_auth = {
        "type",
        "token_hash",
        "access_token",
        "refresh_token",
        "code",
        "token",
        "error",
        "error_description",
    }
    if not parametros_auth.intersection(parametros):
        return

    resto_parametros = {
        nombre: valores
        for nombre, valores in parametros.items()
        if nombre not in parametros_auth
    }
    _establecer_parametros_url(resto_parametros)
    for clave in CLAVES_ESTADO_AUTENTICACION:
        st.session_state.pop(clave, None)
    st.session_state.pop("auth_invite_access_token", None)
    st.session_state.pop("auth_invite_form_error", None)
    st.session_state.pop("auth_invite_processing_error", None)

    if (
        len(tipos) == 1
        and tipos[0] == "invite"
        and len(hashes) == 1
        and isinstance(hashes[0], str)
        and 0 < len(hashes[0]) <= 4096
    ):
        st.session_state["auth_invite_token_hash"] = hashes[0]
    else:
        st.session_state["auth_invite_invalid"] = True
    _forzar_recarga_streamlit()


def _procesar_configuracion_invitacion(config):
    password = st.session_state.get("auth_invite_password", "")
    confirmar = st.session_state.get("auth_invite_password_confirm", "")
    st.session_state.pop("auth_invite_password", None)
    st.session_state.pop("auth_invite_password_confirm", None)

    if not password or not confirmar:
        st.session_state["auth_invite_form_error"] = "Completá ambos campos."
        return
    if password != confirmar:
        st.session_state["auth_invite_form_error"] = (
            "Las contraseñas no coinciden."
        )
        return

    access_token = st.session_state.get("auth_invite_access_token")
    if not access_token:
        token_hash = st.session_state.pop("auth_invite_token_hash", None)
        if not token_hash:
            st.session_state["auth_invite_invalid"] = True
            return

        try:
            respuesta = _solicitud_supabase(
                config,
                "/auth/v1/verify",
                config["publishable_key"],
                method="POST",
                data={"token_hash": token_hash, "type": "invite"},
            )
        except SupabaseAuthError:
            st.session_state.pop("auth_invite_access_token", None)
            st.session_state["auth_invite_processing_error"] = True
            return

        usuario = respuesta.get("user") or {}
        access_token = respuesta.get("access_token")
        if not usuario.get("id") or not access_token:
            st.session_state.pop("auth_invite_access_token", None)
            st.session_state["auth_invite_processing_error"] = True
            return
        st.session_state["auth_invite_access_token"] = access_token

    try:
        _solicitud_supabase(
            config,
            "/auth/v1/user",
            config["publishable_key"],
            method="PUT",
            data={"password": password},
            token=access_token,
        )
    except SupabaseAuthError as exc:
        if exc.status_code in (400, 422):
            st.session_state["auth_invite_form_error"] = (
                "Supabase rechazó esta contraseña. Revisá los requisitos de "
                "contraseña del proyecto e intentá con otra; no hace falta "
                "pedir una nueva invitación."
            )
        elif exc.status_code in (401, 403):
            st.session_state.pop("auth_invite_access_token", None)
            st.session_state["auth_invite_processing_error"] = True
        else:
            st.session_state["auth_invite_form_error"] = (
                "No se pudo actualizar la contraseña por un error temporal. "
                "Volvé a intentarlo; si la invitación sigue válida no hace "
                "falta pedir otra."
            )
        return

    st.session_state.pop("auth_invite_access_token", None)
    st.session_state.pop("auth_invite_token_hash", None)
    st.session_state.pop("auth_invite_form_error", None)
    st.session_state.pop("auth_invite_processing_error", None)
    st.session_state.pop("auth_invite_password", None)
    st.session_state.pop("auth_invite_password_confirm", None)
    st.session_state["auth_invite_completed"] = True


def _mostrar_callback_invitacion(config):
    if st.session_state.pop("auth_invite_completed", False):
        st.success("Contraseña configurada. Ya podés iniciar sesión.")
        return False

    if st.session_state.pop("auth_invite_processing_error", False):
        st.title("🔐 Configurar contraseña")
        st.error(
            "No se pudo validar la invitación o guardar la contraseña. "
            "El enlace puede haber vencido o ya haberse usado. Pedile al "
            "administrador que envíe una nueva invitación."
        )
        return True

    if st.session_state.pop("auth_invite_invalid", False):
        st.title("🔐 Configurar contraseña")
        st.error("El enlace de invitación está incompleto o no es válido.")
        st.info("Pedile al administrador que envíe una nueva invitación.")
        return True

    token_hash = st.session_state.get("auth_invite_token_hash")
    access_token = st.session_state.get("auth_invite_access_token")
    if not token_hash and not access_token:
        return False

    st.title("🔐 Configurar contraseña")
    st.caption("Elegí una contraseña para activar tu acceso.")
    error_formulario = st.session_state.pop("auth_invite_form_error", None)
    if error_formulario:
        st.error(error_formulario)
    with st.form("form_configurar_contrasena_invitacion"):
        st.text_input(
            "Nueva contraseña",
            type="password",
            key="auth_invite_password",
        )
        st.text_input(
            "Confirmar contraseña",
            type="password",
            key="auth_invite_password_confirm",
        )
        st.form_submit_button(
            "Guardar contraseña",
            use_container_width=True,
            on_click=_procesar_configuracion_invitacion,
            args=({
                "url": config["url"],
                "publishable_key": config["publishable_key"],
            },),
        )
    return True


def _procesar_inicio_sesion(config):
    email = (st.session_state.get("auth_login_email") or "").strip()
    password = st.session_state.get("auth_login_password") or ""
    st.session_state.pop("auth_login_password", None)

    if not email.strip() or not password:
        st.session_state["auth_login_error"] = (
            "Ingresá el correo y la contraseña."
        )
        return
    try:
        respuesta = _solicitud_supabase(
            config,
            "/auth/v1/token?grant_type=password",
            config["publishable_key"],
            method="POST",
            data={"email": email.strip(), "password": password},
        )
        _guardar_tokens_auth(respuesta)
        st.session_state.pop("auth_login_error", None)
    except SupabaseAuthError as exc:
        st.session_state.pop("auth_access_token", None)
        st.session_state.pop("auth_refresh_token", None)
        st.session_state.pop("auth_user_id", None)
        st.session_state.pop("auth_email", None)
        st.session_state["auth_login_error"] = (
            f"No se pudo iniciar sesión: {exc}"
        )


def _mostrar_formulario_acceso(config, aviso=None):
    st.title("🔐 Iniciar sesión")
    st.caption("Ingresá con la cuenta que te invitó el administrador.")
    if aviso:
        st.error(aviso)
    error_login = st.session_state.pop("auth_login_error", None)
    if error_login:
        st.error(error_login)
    with st.form("form_inicio_sesion"):
        st.text_input("Correo electrónico", key="auth_login_email")
        st.text_input(
            "Contraseña",
            type="password",
            key="auth_login_password",
        )
        st.form_submit_button(
            "Ingresar",
            use_container_width=True,
            on_click=_procesar_inicio_sesion,
            args=({
                "url": config["url"],
                "publishable_key": config["publishable_key"],
            },),
        )
    return False


def _verificar_sesion_auth(config):
    access_token = st.session_state.get("auth_access_token")
    refresh_token = st.session_state.get("auth_refresh_token")
    if not access_token or not refresh_token:
        return None

    try:
        return _solicitud_supabase(
            config,
            "/auth/v1/user",
            config["publishable_key"],
            token=access_token,
        )
    except SupabaseAuthError as exc:
        if exc.status_code != 401:
            raise

    respuesta = _solicitud_supabase(
        config,
        "/auth/v1/token?grant_type=refresh_token",
        config["publishable_key"],
        method="POST",
        data={"refresh_token": refresh_token},
    )
    _guardar_tokens_auth(respuesta)
    return _solicitud_supabase(
        config,
        "/auth/v1/user",
        config["publishable_key"],
        token=st.session_state["auth_access_token"],
    )


def _cargar_perfil_y_permisos(usuario_auth, config):
    user_id = str(usuario_auth.get("id") or "")
    email = str(usuario_auth.get("email") or "").strip()
    if not user_id or not email:
        raise SupabaseAuthError("Supabase no devolvió la identidad del usuario.")

    es_admin = email.casefold() == config["admin_email"]
    conn = conectar_db()
    try:
        if es_admin:
            metadata = usuario_auth.get("user_metadata") or {}
            nombre = str(metadata.get("full_name") or metadata.get("name") or "Administrador")
            conn.execute(
                """INSERT INTO public.app_user_profiles AS existing
                   (user_id, email, full_name, role, is_active)
                   VALUES (?, ?, ?, 'admin', TRUE)
                   ON CONFLICT (user_id) DO UPDATE SET
                       email = EXCLUDED.email,
                       full_name = CASE
                           WHEN existing.full_name = ''
                           THEN EXCLUDED.full_name
                           ELSE existing.full_name
                       END,
                       role = 'admin',
                       is_active = TRUE""",
                (user_id, email, nombre),
            )
            conn.commit()
        perfil = conn.execute(
            "SELECT email, full_name, is_active FROM public.app_user_profiles "
            "WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not perfil:
            return None, {}, False
        permisos = {
            fila[0]: bool(fila[1])
            for fila in conn.execute(
                "SELECT section_key, enabled FROM public.app_user_permissions "
                "WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        }
        return {
            "user_id": user_id,
            "email": perfil[0],
            "full_name": perfil[1],
            "is_active": bool(perfil[2]),
            "is_admin": es_admin,
        }, permisos, es_admin
    finally:
        conn.close()


def _exigir_seccion(section_key):
    if not IS_CLOUD or st.session_state.get("auth_is_admin"):
        return
    permisos = st.session_state.get("auth_permissions", {})
    if not permisos.get(section_key, False):
        st.error("No tenés permiso para acceder a esta sección.")
        st.stop()


def _exigir_admin():
    if IS_CLOUD and not st.session_state.get("auth_is_admin"):
        st.error("Esta sección está disponible únicamente para el administrador.")
        st.stop()


def _autenticar_web():
    if not IS_CLOUD:
        return

    _capturar_callback_invitacion()
    config = _configuracion_autenticacion()
    faltantes = [
        nombre
        for nombre, valor in (
            ("DATABASE_URL", _leer_secreto("DATABASE_URL")),
            ("SUPABASE_URL", config["url"]),
            (
                "SUPABASE_PUBLISHABLE_KEY (o SUPABASE_ANON_KEY)",
                config["publishable_key"],
            ),
            (
                "SUPABASE_SECRET_KEY (o SUPABASE_SERVICE_ROLE_KEY)",
                config["secret_key"],
            ),
            ("ADMIN_EMAIL", config["admin_email"]),
        )
        if not valor
    ]
    if faltantes or not has_remote_db():
        if not has_remote_db() and "DATABASE_URL" not in faltantes:
            faltantes.append("DATABASE_URL o psycopg2-binary")
        st.error(
            "Acceso bloqueado: faltan secretos de autenticación o base de datos. "
            "Configurá: " + ", ".join(faltantes) + "."
        )
        st.stop()

    if _mostrar_callback_invitacion(config):
        st.stop()

    try:
        conn = conectar_db()
        try:
            inicializar_tablas_acceso(conn)
        finally:
            conn.close()
    except Exception as exc:
        st.error(
            "No se pudieron preparar las tablas privadas de usuarios. "
            "Verificá que DATABASE_URL permita crear tablas en el esquema public "
            f"y referenciar auth.users. Error: {type(exc).__name__}."
        )
        st.stop()

    aviso = st.session_state.pop("auth_login_aviso", None)
    for _ in range(3):
        if not st.session_state.get("auth_access_token"):
            if not _mostrar_formulario_acceso(config, aviso):
                st.stop()
            aviso = None

        try:
            usuario_auth = _verificar_sesion_auth(config)
        except SupabaseAuthError as exc:
            if exc.status_code is None or exc.status_code >= 500:
                st.error(f"No se pudo verificar la sesión con Supabase: {exc}")
                st.stop()
            _limpiar_sesion_autenticacion()
            aviso = "La sesión venció o fue revocada. Iniciá sesión nuevamente."
            continue

        if not usuario_auth:
            _limpiar_sesion_autenticacion()
            aviso = "Iniciá sesión para continuar."
            continue

        try:
            perfil, permisos, es_admin = _cargar_perfil_y_permisos(
                usuario_auth,
                config,
            )
        except Exception as exc:
            st.error(
                "No se pudo validar el perfil de acceso en la base de datos. "
                f"Error: {type(exc).__name__}."
            )
            st.stop()

        if not perfil:
            _limpiar_sesion_autenticacion()
            st.session_state["auth_login_aviso"] = (
                "Esta cuenta no fue invitada por el administrador. "
                "No hay registro público."
            )
            _forzar_recarga_streamlit()
        if not perfil["is_active"]:
            _limpiar_sesion_autenticacion()
            st.session_state["auth_login_aviso"] = (
                "La cuenta está desactivada. Contactá al administrador."
            )
            _forzar_recarga_streamlit()

        st.session_state["auth_user_id"] = perfil["user_id"]
        st.session_state["auth_email"] = perfil["email"]
        st.session_state["auth_full_name"] = perfil["full_name"]
        st.session_state["auth_is_admin"] = es_admin
        st.session_state["auth_permissions"] = {
            clave: bool(permisos.get(clave, False))
            for clave, _ in SECCIONES_APP
        }
        return

    st.error(aviso or "No se pudo validar el acceso.")
    if not st.session_state.get("auth_access_token"):
        _mostrar_formulario_acceso(config)
    st.stop()


def _permiso_actual_para_callback(section_key):
    if not IS_CLOUD:
        return True

    try:
        config = _configuracion_autenticacion()
        usuario_auth = _verificar_sesion_auth(config)
        if not usuario_auth:
            _limpiar_sesion_autenticacion()
            st.error("La sesión venció. Iniciá sesión nuevamente.")
            return False
        perfil, permisos, es_admin = _cargar_perfil_y_permisos(
            usuario_auth,
            config,
        )
    except SupabaseAuthError as exc:
        st.error(f"No se pudo validar el acceso para esta acción: {exc}")
        return False
    except Exception as exc:
        st.error(
            "No se pudo validar el acceso para esta acción. "
            f"Error: {type(exc).__name__}."
        )
        return False

    if not perfil or not perfil["is_active"]:
        _limpiar_sesion_autenticacion()
        st.error("La cuenta está desactivada o no fue invitada.")
        return False

    st.session_state["auth_user_id"] = perfil["user_id"]
    st.session_state["auth_email"] = perfil["email"]
    st.session_state["auth_full_name"] = perfil["full_name"]
    st.session_state["auth_is_admin"] = es_admin
    st.session_state["auth_permissions"] = {
        clave: bool(permisos.get(clave, False))
        for clave, _ in SECCIONES_APP
    }

    if not es_admin and not permisos.get(section_key, False):
        st.error("Tu acceso a esta sección cambió. La acción no se ejecutó.")
        return False
    return True


def _proteger_callback(section_key, callback):
    def callback_protegido(*args, **kwargs):
        if _permiso_actual_para_callback(section_key):
            return callback(*args, **kwargs)
        return None

    return callback_protegido


def _guardar_accesos_usuario(user_id, activo, permisos):
    conn = conectar_db()
    try:
        conn.execute(
            "UPDATE public.app_user_profiles SET is_active = ? "
            "WHERE user_id = ? AND role = 'common'",
            (activo, user_id),
        )
        conn.execute(
            "DELETE FROM public.app_user_permissions WHERE user_id = ?",
            (user_id,),
        )
        conn.executemany(
            "INSERT INTO public.app_user_permissions "
            "(user_id, section_key, enabled) VALUES (?, ?, ?)",
            [
                (user_id, clave, clave in permisos)
                for clave, _ in SECCIONES_APP
            ],
        )
        conn.commit()
        persistir_y_sync()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _guardar_perfil_invitado(user_id, email, nombre):
    conn = conectar_db()
    try:
        conn.execute(
            """INSERT INTO public.app_user_profiles AS existing
               (user_id, email, full_name, role, is_active)
               VALUES (?, ?, ?, 'common', TRUE)
               ON CONFLICT (user_id) DO UPDATE SET
                   email = CASE
                       WHEN existing.email = '' THEN EXCLUDED.email
                       ELSE existing.email
                   END,
                   full_name = CASE
                       WHEN existing.full_name = '' THEN EXCLUDED.full_name
                       ELSE existing.full_name
                   END,
                   role = 'common'""",
            (str(user_id), email, nombre),
        )
        conn.cursor().executemany(
            """INSERT INTO public.app_user_permissions
               (user_id, section_key, enabled) VALUES (?, ?, FALSE)
               ON CONFLICT (user_id, section_key) DO NOTHING""",
            [
                (str(user_id), clave)
                for clave, _ in SECCIONES_APP
            ],
        )
        conn.commit()
        persistir_y_sync()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _buscar_usuario_auth_existente(config, email):
    secret_key = config.get("secret_key")
    if not secret_key:
        raise SupabaseAuthError(
            "Falta la clave administrativa de Supabase para buscar usuarios."
        )

    por_pagina = 100
    pagina = 1
    encontrados = []
    while True:
        endpoint = "/auth/v1/admin/users?" + urllib.parse.urlencode(
            {"page": pagina, "per_page": por_pagina}
        )
        respuesta = _solicitud_supabase(
            config,
            endpoint,
            secret_key,
            method="GET",
            token=secret_key if config.get("secret_key_legacy") else None,
        )
        usuarios = respuesta.get("users")
        if not isinstance(usuarios, list):
            raise SupabaseAuthError(
                "Supabase devolvió un listado de usuarios con formato inesperado."
            )
        encontrados.extend(
            usuario
            for usuario in usuarios
            if isinstance(usuario, dict)
            and str(usuario.get("email") or "").casefold() == email.casefold()
        )
        if len(encontrados) > 1:
            raise SupabaseAuthError(
                "Supabase devolvió más de una cuenta con ese correo; "
                "no se recuperó ningún perfil."
            )
        if encontrados or len(usuarios) < por_pagina:
            break
        pagina += 1

    return encontrados[0] if encontrados else None


def _diagnostico_error_perfil(exc):
    causa = exc.__cause__ or exc
    detalles = [type(causa).__name__]
    if isinstance(causa, PsycopgError):
        if causa.pgcode:
            detalles.append(f"SQLSTATE {causa.pgcode}")
        restriccion = getattr(getattr(causa, "diag", None), "constraint_name", None)
        if restriccion:
            detalles.append(f"restricción {restriccion}")
    return "; ".join(detalles)


def _invitar_usuario(config, nombre, email):
    if not config.get("app_url"):
        raise SupabaseAuthError(
            "Falta configurar APP_URL. La invitación no fue enviada."
        )
    secret_key = config["secret_key"]
    respuesta = _solicitud_supabase(
        config,
        "/auth/v1/invite?"
        + urllib.parse.urlencode({"redirect_to": config["app_url"]}),
        secret_key,
        method="POST",
        data={"email": email, "data": {"full_name": nombre}},
        token=secret_key if config.get("secret_key_legacy") else None,
    )
    usuario = respuesta.get("user") or respuesta
    user_id = usuario.get("id")
    if not user_id:
        raise SupabaseAuthError(
            "Supabase envió o procesó la invitación, pero no devolvió el ID del usuario."
        )

    st.session_state["auth_pending_profile_save"] = {
        "user_id": str(user_id),
        "email": email,
        "full_name": nombre,
    }
    try:
        _guardar_perfil_invitado(user_id, email, nombre)
    except Exception as exc:
        raise RuntimeError(
            "La invitación de Auth se procesó, pero no se pudo guardar el perfil "
            "con permisos iniciales. Podés reintentar el guardado sin reenviar "
            "la invitación."
        ) from exc
    st.session_state.pop("auth_pending_profile_save", None)


def _mostrar_administracion_usuarios(config):
    _exigir_admin()
    st.title("🔐 Usuarios y permisos")
    st.caption(
        "Los permisos habilitan secciones de la app; los datos del taller son compartidos."
    )
    st.info(
        "Para que el enlace permita configurar la contraseña, la plantilla "
        "Invite User de Supabase debe dirigir a APP_URL con los parámetros "
        "token_hash y type=invite. Ver instrucciones en secrets_example.toml."
    )
    pendiente = st.session_state.get("auth_pending_profile_save")
    with st.form("form_invitar_usuario"):
        nombre = st.text_input("Nombre")
        email = st.text_input("Correo electrónico")
        invitar = st.form_submit_button(
            "✉️ Invitar usuario",
            use_container_width=True,
            disabled=bool(pendiente),
        )
    if invitar:
        email = email.strip().casefold()
        if not nombre.strip() or not email or "@" not in email:
            st.error("Ingresá un nombre y un correo electrónico válido.")
        elif email == config["admin_email"]:
            st.error("El correo administrador no se puede invitar como usuario común.")
        elif not config.get("app_url"):
            st.error(
                "Falta configurar APP_URL en Streamlit Secrets o en variables "
                "de entorno. No se envió la invitación."
            )
        else:
            try:
                _invitar_usuario(config, nombre.strip(), email)
                st.success(
                    "Invitación enviada. El invitado podrá configurar su "
                    "contraseña si la plantilla Invite User de Supabase está "
                    "configurada para el callback de la app."
                )
            except (SupabaseAuthError, RuntimeError) as exc:
                mensaje = f"No se pudo completar la invitación: {exc}"
                if isinstance(exc, RuntimeError) and exc.__cause__:
                    mensaje += (
                        f" Diagnóstico: "
                        f"{_diagnostico_error_perfil(exc)}."
                    )
                st.error(mensaje)

    if IS_CLOUD and st.session_state.get("auth_is_admin"):
        st.subheader("Recuperar cuenta existente de Supabase Auth")
        st.caption(
            "Busca una cuenta ya creada en Supabase Auth. No crea cuentas ni "
            "vuelve a enviar invitaciones."
        )
        pendiente = st.session_state.get("auth_pending_profile_save")
        with st.form("form_recuperar_usuario_auth"):
            email_recuperar = st.text_input(
                "Correo de la cuenta existente",
                value="fuerzaxtecnica@gmail.com",
            )
            recuperar = st.form_submit_button(
                "Buscar y recuperar perfil",
                use_container_width=True,
                disabled=bool(pendiente),
            )
        if recuperar:
            email_recuperar = email_recuperar.strip().casefold()
            if not email_recuperar or "@" not in email_recuperar:
                st.error("Ingresá un correo electrónico válido.")
            elif email_recuperar == config["admin_email"]:
                st.error(
                    "La cuenta administradora no se puede recuperar como "
                    "usuario común."
                )
            else:
                try:
                    usuario_auth = _buscar_usuario_auth_existente(
                        config,
                        email_recuperar,
                    )
                except SupabaseAuthError as exc:
                    status = (
                        f", HTTP {exc.status_code}"
                        if exc.status_code is not None
                        else ""
                    )
                    st.error(
                        "No se pudo buscar la cuenta existente en Supabase Auth "
                        f"({type(exc).__name__}{status}): {exc}"
                    )
                except Exception as exc:
                    st.error(
                        "No se pudo buscar la cuenta existente. "
                        f"Diagnóstico: {_diagnostico_error_perfil(exc)}."
                    )
                else:
                    if not usuario_auth:
                        st.error(
                            "No se encontró una cuenta existente con ese correo "
                            "en Supabase Auth. No se creó una cuenta ni se envió "
                            "una invitación."
                        )
                    elif not usuario_auth.get("id"):
                        st.error(
                            "Supabase encontró la cuenta, pero no devolvió su ID. "
                            "No se guardó ningún perfil."
                        )
                    else:
                        metadata = usuario_auth.get("user_metadata") or {}
                        if not isinstance(metadata, dict):
                            metadata = {}
                        pendiente = {
                            "user_id": str(usuario_auth["id"]),
                            "email": email_recuperar,
                            "full_name": str(
                                metadata.get("full_name")
                                or metadata.get("name")
                                or ""
                            ).strip(),
                        }
                        st.session_state["auth_pending_profile_save"] = pendiente
                        try:
                            _guardar_perfil_invitado(
                                pendiente["user_id"],
                                pendiente["email"],
                                pendiente["full_name"],
                            )
                        except Exception as exc:
                            st.error(
                                "No se pudo guardar el perfil recuperado. "
                                f"Diagnóstico: {_diagnostico_error_perfil(exc)}."
                            )
                        else:
                            st.session_state.pop(
                                "auth_pending_profile_save",
                                None,
                            )
                            st.success(
                                "Cuenta existente recuperada. Se guardó el perfil "
                                "común y se completaron únicamente los permisos "
                                "faltantes como deshabilitados. No se envió otra "
                                "invitación."
                            )

    pendiente = st.session_state.get("auth_pending_profile_save")
    if pendiente:
        st.warning(
            "La invitación ya fue procesada por Supabase, pero falta guardar "
            f"el perfil de {pendiente['email']}. El reintento no enviará otro correo."
        )
        if st.button(
            "Reintentar guardado del perfil",
            key="reintentar_perfil_invitado",
        ):
            try:
                _guardar_perfil_invitado(
                    pendiente["user_id"],
                    pendiente["email"],
                    pendiente["full_name"],
                )
            except Exception as exc:
                st.error(
                    "No se pudo guardar el perfil. "
                    f"Diagnóstico: {_diagnostico_error_perfil(exc)}."
                )
            else:
                st.session_state.pop("auth_pending_profile_save", None)
                st.success(
                    "Perfil y permisos iniciales guardados. "
                    "No se envió otra invitación."
                )

    conn = conectar_db()
    try:
        usuarios = conn.execute(
            "SELECT user_id, email, full_name, is_active FROM public.app_user_profiles "
            "WHERE role = 'common' ORDER BY lower(full_name), lower(email)"
        ).fetchall()
        for user_id, email_usuario, nombre_usuario, activo in usuarios:
            permisos_guardados = {
                fila[0]
                for fila in conn.execute(
                    "SELECT section_key FROM public.app_user_permissions "
                    "WHERE user_id = ? AND enabled = TRUE",
                    (user_id,),
                ).fetchall()
            }
            st.markdown(f"### {nombre_usuario or email_usuario}")
            st.caption(email_usuario)
            with st.form(f"form_accesos_{user_id}"):
                activo_nuevo = st.checkbox(
                    "Cuenta activa",
                    value=bool(activo),
                    key=f"activo_{user_id}",
                )
                permisos_nuevos = {
                    clave
                    for clave, etiqueta in SECCIONES_APP
                    if st.checkbox(
                        etiqueta,
                        value=clave in permisos_guardados,
                        key=f"permiso_{user_id}_{clave}",
                    )
                }
                guardar = st.form_submit_button("Guardar accesos")
            if guardar:
                try:
                    _guardar_accesos_usuario(
                        str(user_id),
                        activo_nuevo,
                        permisos_nuevos,
                    )
                    st.success("Accesos actualizados.")
                except Exception as exc:
                    st.error(
                        "No se pudieron guardar los permisos. "
                        f"Error: {type(exc).__name__}."
                    )
    finally:
        conn.close()


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
if IS_CLOUD:
    _autenticar_web()
else:
    DB_PATH = ensure_database_file()
    ensure_remote_restore(DB_PATH)

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

if IS_CLOUD:
    if st.session_state.get("auth_is_admin"):
        lista_opciones_menu.append(PANTALLA_USUARIOS)
    else:
        lista_opciones_menu = [
            etiqueta
            for etiqueta in lista_opciones_menu
            if st.session_state["auth_permissions"].get(
                ETIQUETA_A_SECCION[etiqueta],
                False,
            )
        ]

if not lista_opciones_menu:
    st.info("No tenés secciones habilitadas. Contactá al administrador.")
    st.sidebar.caption(st.session_state["auth_email"])
    st.sidebar.button(
        "Cerrar sesión",
        key="cerrar_sesion_sin_permisos",
        on_click=_limpiar_sesion_autenticacion,
    )
    st.stop()

if st.session_state.navegacion not in lista_opciones_menu:
    st.session_state.navegacion = lista_opciones_menu[0]
    st.session_state.pop("detalle_agenda", None)

st.sidebar.title("🔧 Sistema Taller")
if IS_CLOUD:
    st.sidebar.caption(
        f"{st.session_state['auth_full_name'] or st.session_state['auth_email']} · "
        f"{'Administrador' if st.session_state['auth_is_admin'] else 'Usuario común'}"
    )
else:
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
if IS_CLOUD:
    st.sidebar.button(
        "Cerrar sesión",
        key="cerrar_sesion",
        on_click=_limpiar_sesion_autenticacion,
    )

menu_elegido = st.session_state.navegacion


def cambiar_pagina(nueva_pagina):
    st.session_state.navegacion = nueva_pagina


if menu_elegido == PANTALLA_USUARIOS:
    _exigir_admin()
else:
    _exigir_seccion(ETIQUETA_A_SECCION[menu_elegido])

if menu_elegido != PANTALLA_USUARIOS:
    DB_PATH = ensure_database_file()
    conn_inicial = conectar_db()
    inicializar_db(conn_inicial)
    conn_inicial.close()


_ESTADOS_CHECKLIST = {
    "controles_ingreso": ("OK", "Malo", "No Realizado"),
    "controles_salida": ("OK", "Malo (Avisar a Taller)", "No Aplica"),
}
_ESTADOS_MANTENIMIENTO = {
    "mantenimiento": ("Realizado", "No Necesario", "Postergado"),
    "reparacion": ("Reparado", "No Reparado"),
}


def _cargar_respuestas_checklist(conn, tabla, ingreso_id):
    if tabla == "controles_mantenimiento":
        filas = conn.execute(
            "SELECT tarea, estado, observaciones, tipo_tarea "
            "FROM controles_mantenimiento WHERE ingreso_id = ? ORDER BY id",
            (ingreso_id,),
        ).fetchall()
        return {
            fila[0]: {
                "estado": fila[1],
                "observaciones": fila[2] or "",
                "tipo_tarea": fila[3],
            }
            for fila in filas
        }
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
    if tabla == "controles_mantenimiento":
        return sum(
            1
            for tarea, tipo_tarea in descripciones
            if tarea in respuestas
            and respuestas[tarea]["estado"]
            in _ESTADOS_MANTENIMIENTO.get(tipo_tarea, ())
            and respuestas[tarea]["estado"] != "Postergado"
        )
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
    tipo_tarea=None,
):
    estados_validos = (
        _ESTADOS_MANTENIMIENTO.get(tipo_tarea, ())
        if tabla == "controles_mantenimiento"
        else _ESTADOS_CHECKLIST.get(tabla)
    )
    if estados_validos is None:
        raise ValueError(f"Tabla de checklist no válida: {tabla}")

    conn = conectar_db()
    try:
        estado = st.session_state.get(estado_key)
        es_postergada = tabla == "controles_mantenimiento" and estado == "Postergado"
        if not st.session_state[completado_key] and not es_postergada:
            return

        if estado not in estados_validos:
            st.session_state[error_key] = (
                "Seleccioná una condición antes de marcar el paso como completo."
            )
            return
        if estado == "Postergado" and tabla == "controles_mantenimiento":
            st.session_state[completado_key] = False

        observaciones = (st.session_state.get(observaciones_key) or "").strip()
        if tabla == "controles_mantenimiento":
            respuesta = conn.execute(
                "SELECT id FROM controles_mantenimiento "
                "WHERE ingreso_id = ? AND tarea = ? ORDER BY id DESC LIMIT 1",
                (ingreso_id, tarea),
            ).fetchone()
        else:
            respuesta = conn.execute(
                f"SELECT id FROM {tabla} WHERE ingreso_id = ? AND tarea = ? "
                "ORDER BY id DESC LIMIT 1",
                (ingreso_id, tarea),
            ).fetchone()
        if respuesta:
            if tabla == "controles_mantenimiento":
                conn.execute(
                    "UPDATE controles_mantenimiento SET estado = ?, observaciones = ?, "
                    "tipo_tarea = ? WHERE id = ?",
                    (estado, observaciones, tipo_tarea, respuesta[0]),
                )
            else:
                conn.execute(
                    f"UPDATE {tabla} SET estado = ?, observaciones = ? "
                    "WHERE id = ?",
                    (estado, observaciones, respuesta[0]),
                )
        elif tabla == "controles_mantenimiento":
            conn.execute(
                "INSERT INTO controles_mantenimiento "
                "(ingreso_id, tarea, estado, observaciones, tipo_tarea) "
                "VALUES (?, ?, ?, ?, ?)",
                (ingreso_id, tarea, estado, observaciones, tipo_tarea),
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
            (
                "Paso postergado y guardado."
                if es_postergada
                else "Cambios guardados automáticamente."
            ),
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
    tipo_tarea=None,
):
    estado = st.session_state.get(estado_key)
    st.session_state[completado_key] = not (
        tabla == "controles_mantenimiento" and estado == "Postergado"
    )
    _persistir_respuesta_checklist(
        tabla,
        ingreso_id,
        tarea,
        completado_key,
        estado_key,
        observaciones_key,
        error_key,
        tipo_tarea,
    )


def _guardar_observaciones_checklist(
    tabla,
    ingreso_id,
    tarea,
    completado_key,
    estado_key,
    observaciones_key,
    error_key,
    tipo_tarea=None,
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
            tipo_tarea,
        )


def _mostrar_checklist_planilla(tipo, ingreso_id, controles, respuestas):
    tabla = {
        "ingreso": "controles_ingreso",
        "mantenimiento": "controles_mantenimiento",
        "salida": "controles_salida",
    }[tipo]
    seccion = {
        "controles_ingreso": "ingreso_equipo",
        "controles_mantenimiento": "ejecucion_mantenimiento",
        "controles_salida": "entrega_equipo",
    }[tabla]
    estados_base = (
        _ESTADOS_CHECKLIST.get(tabla)
        or _ESTADOS_MANTENIMIENTO.get("mantenimiento")
    )
    progreso = _contar_checklist_completados(
        [
            (tarea, grupo) if tipo == "mantenimiento" else tarea
            for _, tarea, grupo in controles
        ],
        respuestas,
        tabla,
    )
    total = len(controles)
    titulos = {
        "ingreso": "Checklist de ingreso",
        "mantenimiento": "Checklist de mantenimiento",
        "salida": "Checklist de salida",
    }
    titulo = titulos[tipo]

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

        grupo_actual = None
        for indice, (control_id, tarea, grupo) in enumerate(controles, start=1):
            estados = (
                _ESTADOS_MANTENIMIENTO.get(grupo, ())
                if tipo == "mantenimiento"
                else estados_base
            )
            if tipo == "mantenimiento" and grupo != grupo_actual:
                st.markdown(
                    "### "
                    + (
                        "Rutina de mantenimiento"
                        if grupo == "mantenimiento"
                        else "Reparaciones detectadas en el ingreso"
                    )
                )
                grupo_actual = grupo
            respuesta = respuestas.get(tarea)
            prefijo = f"checklist_{tipo}_{ingreso_id}_{control_id}"
            completado_key = f"{prefijo}_completado"
            estado_key = f"{prefijo}_estado"
            observaciones_key = f"{prefijo}_observaciones"
            error_key = f"{prefijo}_error"
            if completado_key not in st.session_state:
                st.session_state[completado_key] = bool(
                    respuesta
                    and respuesta["estado"] in estados
                    and respuesta["estado"] != "Postergado"
                )
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
                grupo if tipo == "mantenimiento" else None,
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
                        on_change=_proteger_callback(
                            seccion,
                            _persistir_respuesta_checklist,
                        ),
                        args=argumentos,
                        disabled=bool(
                            respuesta
                            and st.session_state[completado_key]
                        ),
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
                        on_change=_proteger_callback(
                            seccion,
                            _guardar_estado_checklist,
                        ),
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
                            on_change=_proteger_callback(
                                seccion,
                                _guardar_observaciones_checklist,
                            ),
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


def _cargar_compras_pendientes(conn, hoy=None):
    hoy = hoy or datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    df_compras = pd.read_sql_query(
        "SELECT id, rubro, descripcion, detalle, cantidad, fecha_necesaria "
        "FROM lista_compras WHERE estado = 'Pendiente'",
        conn,
    )
    compras = []
    for fila in df_compras.to_dict("records"):
        fecha_necesaria = _fecha_agenda(fila["fecha_necesaria"])
        dias_atraso = (hoy - fecha_necesaria).days if fecha_necesaria and fecha_necesaria < hoy else 0
        compras.append(
            {
                **fila,
                "fecha_necesaria_date": fecha_necesaria,
                "dias_atraso": dias_atraso,
            }
        )

    compras.sort(
        key=lambda compra: (
            2
            if compra["fecha_necesaria_date"] is None
            else 0
            if compra["fecha_necesaria_date"] < hoy
            else 1,
            compra["fecha_necesaria_date"] or date.max,
            str(compra["rubro"]).casefold(),
            int(compra["id"]),
        )
    )
    return compras


def _compras_vencidas(compras, hoy=None):
    hoy = hoy or datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    return [
        compra
        for compra in compras
        if compra["fecha_necesaria_date"] is not None
        and compra["fecha_necesaria_date"] < hoy
    ]


def _mostrar_aviso_compras_vencidas(compras, incluir_boton=False):
    if not compras:
        return

    st.warning(f"⚠️ Hay {len(compras)} compras vencidas.")
    for compra in compras:
        fecha_limite = compra["fecha_necesaria_date"].strftime("%d/%m/%Y")
        st.markdown(
            f"- **{compra['rubro']} · {compra['descripcion']}** — "
            f"cantidad: {compra['cantidad']} · límite: {fecha_limite} · "
            f"atraso: {compra['dias_atraso']} "
            f"{'día' if compra['dias_atraso'] == 1 else 'días'}"
        )
    if incluir_boton:
        st.button(
            "🛒 Abrir Lista de Compras",
            key="abrir_lista_compras_vencidas",
            on_click=cambiar_pagina,
            args=("🛒 Lista de Compras",),
        )


def _guardar_fecha_necesaria_compra(compra_id, widget_key):
    fecha = st.session_state.get(widget_key)
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    if fecha is not None and not isinstance(fecha, date):
        st.session_state[f"error_fecha_necesaria_{compra_id}"] = (
            "La fecha seleccionada no es válida."
        )
        return

    conn = conectar_db()
    try:
        actualizacion = conn.execute(
            "UPDATE lista_compras SET fecha_necesaria = ? "
            "WHERE id = ? AND estado = 'Pendiente'",
            (fecha.isoformat() if fecha else None, compra_id),
        )
        if actualizacion.rowcount != 1:
            st.session_state[f"error_fecha_necesaria_{compra_id}"] = (
                "No se pudo guardar la fecha porque la compra ya no está pendiente."
            )
            return
        conn.commit()
        persistir_y_sync()
        st.session_state[f"mensaje_fecha_necesaria_{compra_id}"] = (
            "Fecha guardada."
            if fecha
            else "Compra guardada sin fecha."
        )
        st.session_state.pop(f"error_fecha_necesaria_{compra_id}", None)
    finally:
        conn.close()


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
               e.fecha_fin_estimada, e.estado_proceso, m.marca, m.modelo,
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
        es_mantenimiento_activo = fila["estado_proceso"] == "Mantenimiento en Proceso"
        valor_fecha = (
            fila["fecha_fin_estimada"]
            if es_mantenimiento_activo
            else fila["fecha_ingreso"]
        )
        fecha = _fecha_agenda(valor_fecha)
        if fecha is None:
            fechas_invalidas += 1
            continue
        trabajos.append({
            "tipo": "mantenimiento",
            "id": int(fila["id"]),
            "fecha": fecha,
            "fecha_rotulo": (
                "Fin estimado"
                if es_mantenimiento_activo
                else "Fecha de ingreso (sin turno programado)"
            ),
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
    st.caption(
        "Trabajos internos y de clientes pendientes, más mantenimientos que superaron "
        "su fin estimado y continúan en proceso."
    )
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


def _fecha_fin_mantenimiento(fecha_inicio):
    fecha = fecha_inicio
    dias_habiles = 0
    while dias_habiles < 5:
        fecha += timedelta(days=1)
        if fecha.weekday() < 5:
            dias_habiles += 1
    return fecha


def _cargar_plan_mantenimiento(conn, ingreso_id):
    tareas = conn.execute(
        "SELECT id, descripcion FROM maestro_tareas_mantenimiento ORDER BY orden, id"
    ).fetchall()
    plan = [
        {
            "control_id": f"mantenimiento_{fila[0]}",
            "tipo": "mantenimiento",
            "tarea": fila[1],
        }
        for fila in tareas
    ]
    fallas = conn.execute(
        "SELECT id, tarea, observaciones FROM controles_ingreso "
        "WHERE ingreso_id = ? AND estado = 'Malo' ORDER BY id",
        (ingreso_id,),
    ).fetchall()
    plan.extend(
        {
            "control_id": f"reparacion_{falla[0]}",
            "tipo": "reparacion",
            "tarea": f"[{falla[1]}] {falla[2] or ''}",
        }
        for falla in fallas
    )
    return plan


def preparar_mantenimiento(ingreso_id):
    conn = conectar_db()
    try:
        ingreso = conn.execute(
            "SELECT estado_proceso, fecha_inicio_mantenimiento, fecha_fin_estimada "
            "FROM equipos_ingresados WHERE id = ?",
            (ingreso_id,),
        ).fetchone()
        if not ingreso:
            st.session_state.mensaje_mantenimiento = "No se encontró el ingreso seleccionado."
            return

        ahora = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
        fecha_inicio = ingreso[1]
        fecha_fin = ingreso[2]
        if not fecha_inicio:
            fecha_inicio = ahora.isoformat()
        else:
            fecha_inicio = _fecha_agenda(fecha_inicio)
            if fecha_inicio is None:
                fecha_inicio = ahora
            fecha_inicio = fecha_inicio.isoformat()
        if not fecha_fin:
            fecha_fin = _fecha_fin_mantenimiento(
                datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
            ).isoformat()

        conn.execute(
            "UPDATE equipos_ingresados SET estado_proceso = 'Mantenimiento en Proceso', "
            "fecha_inicio_mantenimiento = ?, fecha_fin_estimada = ? WHERE id = ?",
            (fecha_inicio, fecha_fin, ingreso_id),
        )
        conn.commit()
        persistir_y_sync()

        st.session_state.mant_queue = _cargar_plan_mantenimiento(conn, ingreso_id)
        st.session_state.mant_idx = 0
        st.session_state.mant_ingreso_id = ingreso_id
        st.session_state.hallazgos_extras_ok = False
        st.session_state.mensaje_mantenimiento = ""
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


def guardar_hallazgos_mantenimiento(ingreso_id, observaciones_key):
    conn = conectar_db()
    try:
        estado_actual = conn.execute(
            "SELECT estado_proceso FROM equipos_ingresados WHERE id = ?",
            (ingreso_id,),
        ).fetchone()
        if not estado_actual or estado_actual[0] != "Mantenimiento en Proceso":
            return
        observaciones = (st.session_state.get(observaciones_key) or "").strip()
        existente = conn.execute(
            "SELECT id FROM controles_mantenimiento WHERE ingreso_id = ? "
            "AND tarea = 'Reparación Adicional en proceso' ORDER BY id DESC LIMIT 1",
            (ingreso_id,),
        ).fetchone()
        if existente:
            conn.execute(
                "UPDATE controles_mantenimiento SET observaciones = ?, estado = 'Reparado', "
                "tipo_tarea = 'reparacion' WHERE id = ?",
                (observaciones, existente[0]),
            )
        elif observaciones:
            conn.execute(
                "INSERT INTO controles_mantenimiento "
                "(ingreso_id, tarea, estado, observaciones, tipo_tarea) "
                "VALUES (?, 'Reparación Adicional en proceso', 'Reparado', ?, 'reparacion')",
                (ingreso_id, observaciones),
            )
        conn.commit()
        persistir_y_sync()
        st.session_state.mensaje_mantenimiento = "Hallazgos guardados automáticamente."
    finally:
        conn.close()


def finalizar_mantenimiento(ingreso_id):
    st.session_state.mensaje_mantenimiento = ""
    conn = conectar_db()
    try:
        ingreso = conn.execute(
            "SELECT estado_proceso FROM equipos_ingresados WHERE id = ?",
            (ingreso_id,),
        ).fetchone()
        if not ingreso or ingreso[0] != "Mantenimiento en Proceso":
            st.session_state.mensaje_mantenimiento = (
                "El equipo ya no tiene un mantenimiento activo."
            )
            return

        plan = _cargar_plan_mantenimiento(conn, ingreso_id)
        respuestas = _cargar_respuestas_checklist(
            conn,
            "controles_mantenimiento",
            ingreso_id,
        )
        progreso = _contar_checklist_completados(
            [(item["tarea"], item["tipo"]) for item in plan],
            respuestas,
            "controles_mantenimiento",
        )
        if not plan:
            st.session_state.mensaje_mantenimiento = (
                "No hay pasos configurados para este mantenimiento; no se puede finalizar."
            )
            return
        if progreso < len(plan):
            st.session_state.mensaje_mantenimiento = (
                f"Completá todos los pasos obligatorios antes de finalizar "
                f"({progreso} de {len(plan)})."
            )
            return

        actualizacion = conn.execute(
            "UPDATE equipos_ingresados SET estado_proceso = 'Mantenimiento Completado' "
            "WHERE id = ? AND estado_proceso = 'Mantenimiento en Proceso'",
            (ingreso_id,),
        )
        if actualizacion.rowcount != 1:
            st.session_state.mensaje_mantenimiento = (
                "El estado del equipo cambió; actualizá la pantalla e intentá nuevamente."
            )
            return
        conn.commit()
        persistir_y_sync()
    finally:
        conn.close()

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
if menu_elegido == PANTALLA_USUARIOS:
    _exigir_admin()
    _mostrar_administracion_usuarios(_configuracion_autenticacion())

elif menu_elegido == "🏠 Inicio semanal":
    _exigir_seccion("inicio_semanal")
    st.markdown("<h2 class='agenda-title'>🏠 Agenda semanal del taller</h2>", unsafe_allow_html=True)
    hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    conn = conectar_db()
    try:
        trabajos_agenda, fechas_invalidas = _cargar_trabajos_agenda(conn)
        compras_pendientes = _cargar_compras_pendientes(conn, hoy)
    finally:
        conn.close()

    _mostrar_aviso_compras_vencidas(
        _compras_vencidas(compras_pendientes, hoy),
        incluir_boton=True,
    )
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
        if (
            trabajo["tipo"] in {"interno", "cliente"}
            or (
                trabajo["tipo"] == "mantenimiento"
                and trabajo["estado"] == "Mantenimiento en Proceso"
            )
        )
        and trabajo["fecha"] < hoy
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
        f"{ingresos_tecnicos} equipos activos del flujo técnico. "
        "Los mantenimientos en proceso se ubican por su fin estimado; las inspecciones y entregas "
        "activas sin fecha programada se ubican por la fecha de ingreso."
    )

# ==========================================
# 2. PANTALLA: TABLERO TALLER (TRABAJOS INTERNOS)
# ==========================================
elif menu_elegido == "📊 Tablero Taller":
    _exigir_seccion("tablero_taller")
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
    _exigir_seccion("tablero_equipos")
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
                on_click=_proteger_callback(
                    "tablero_equipos",
                    retomar_inspeccion,
                ),
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
                    on_click=_proteger_callback(
                        "tablero_equipos",
                        continuar_mantenimiento_desde_inspeccion,
                    ),
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
                on_click=_proteger_callback(
                    "tablero_equipos",
                    preparar_mantenimiento,
                ),
                args=(id_retomar,),
            )
        else:
            st.button(
                "➡️ Retomar Tarea Seleccionada",
                key="retomar_tarea_incompleta",
                use_container_width=True,
                on_click=_proteger_callback(
                    "tablero_equipos",
                    retomar_checklist_salida,
                ),
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
    
    df_ingresos = pd.read_sql_query(
        "SELECT e.id, e.interno, m.marca, m.modelo, e.horas, e.origen, "
        "e.mecanico, e.fecha_ingreso, e.hora_inicio, e.estado_proceso, "
        "e.fecha_fin_estimada FROM equipos_ingresados e "
        "JOIN maestro_equipos m ON e.interno = m.interno ORDER BY e.id DESC",
        conn,
    )
    if df_ingresos.empty:
        st.info("No hay equipos ingresados en el sistema.")
    else:
        with st.container(key="ingresos-desktop"):
            tabla_ingresos = df_ingresos.rename(
                columns={
                    "id": "ID",
                    "interno": "Interno",
                    "marca": "Marca",
                    "modelo": "Modelo",
                    "horas": "Horómetro",
                    "origen": "Origen / destino",
                    "mecanico": "Mecánico",
                    "fecha_ingreso": "Fecha de ingreso",
                    "hora_inicio": "Hora de inicio",
                    "estado_proceso": "Estado",
                    "fecha_fin_estimada": "Fin estimado",
                }
            )
            st.dataframe(
                tabla_ingresos.style.map(colorear_estados, subset=["Estado"]),
                use_container_width=True,
                hide_index=True,
            )
        with st.container(key="ingresos-mobile"):
            st.subheader("Ingresos")
            for _, ingreso in df_ingresos.iterrows():
                with st.container(border=True):
                    st.markdown(
                        f"**{ingreso['interno']} · {ingreso['marca']} {ingreso['modelo']}**"
                    )
                    st.markdown(f"**Estado:** {ingreso['estado_proceso']}")
                    st.caption(
                        f"Ingreso: {ingreso['fecha_ingreso'] or 'No informado'} · "
                        f"Origen: {ingreso['origen'] or 'No informado'}"
                    )
                    st.caption(
                        f"Mecánico: {ingreso['mecanico'] or 'No informado'} · "
                        f"Horómetro: {ingreso['horas'] if pd.notna(ingreso['horas']) else 'No informado'}"
                    )
                    if ingreso["fecha_fin_estimada"]:
                        st.caption(f"Fin estimado: {ingreso['fecha_fin_estimada']}")

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

            if estado_actual == "Mantenimiento en Proceso":
                with st.form(f"form_fin_estimado_{id_buscado}"):
                    fecha_fin_actual = _fecha_agenda(
                        ingreso_actual["fecha_fin_estimada"]
                    )
                    fecha_fin_editada = st.date_input(
                        "Fin estimado",
                        value=fecha_fin_actual
                        or datetime.now(
                            ZoneInfo("America/Argentina/Buenos_Aires")
                        ).date(),
                        format="DD/MM/YYYY",
                    )
                    if st.form_submit_button("💾 Guardar fin estimado"):
                        conn.execute(
                            "UPDATE equipos_ingresados SET fecha_fin_estimada = ? "
                            "WHERE id = ? AND estado_proceso = 'Mantenimiento en Proceso'",
                            (fecha_fin_editada.isoformat(), id_buscado),
                        )
                        conn.commit()
                        persistir_y_sync()
                        st.success("Fin estimado actualizado.")

            if estado_actual == 'Inspección Inicial Completada':
                st.info("💡 Inspección completa. Iniciar Mantenimiento.")
                st.button(
                    "🛠️ Iniciar Mantenimiento",
                    use_container_width=True,
                    key=f"iniciar_mantenimiento_{id_buscado}",
                    on_click=_proteger_callback(
                        "tablero_equipos",
                        preparar_mantenimiento,
                    ),
                    args=(id_buscado,),
                )

            elif estado_actual == 'Mantenimiento Completado':
                st.info("✅ Mantenimiento finalizado. Generá el reporte técnico para descargarlo.")

                st.button(
                    "🔄 Reabrir mantenimiento para corregir",
                    use_container_width=True,
                    key=f"reabrir_mantenimiento_{id_buscado}",
                    on_click=_proteger_callback(
                        "tablero_equipos",
                        preparar_mantenimiento,
                    ),
                    args=(id_buscado,),
                )

                st.button(
                    "📄 Generar y guardar reporte PDF",
                    key=f"generar_archivar_reporte_{id_buscado}",
                    use_container_width=True,
                    on_click=_proteger_callback(
                        "tablero_equipos",
                        generar_reportes,
                    ),
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
                    on_click=_proteger_callback(
                        "tablero_equipos",
                        iniciar_checklist_salida,
                    ),
                    args=(id_buscado,),
                )

            elif estado_actual == 'Equipo Entregado':
                st.success("🎉 Equipo entregado. Proceso finalizado en su totalidad.")
                st.button(
                    "📄 Generar y guardar reportes PDF",
                    key=f"generar_archivar_reportes_entrega_{id_buscado}",
                    use_container_width=True,
                    on_click=_proteger_callback(
                        "tablero_equipos",
                        generar_reportes,
                    ),
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
    _exigir_seccion("ingreso_equipo")
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
                on_click=_proteger_callback(
                    "ingreso_equipo",
                    avanzar_paso_ingreso,
                ),
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
    _exigir_seccion("ejecucion_mantenimiento")
    st.title("🛠️ Checklist de Mantenimiento")
    ingreso_id = st.session_state.mant_ingreso_id
    if not ingreso_id:
        st.info("No hay rutina activa. Iníciala desde el Tablero de Equipos.")
    else:
        conn = conectar_db()
        ingreso = conn.execute(
            "SELECT estado_proceso, fecha_inicio_mantenimiento, fecha_fin_estimada "
            "FROM equipos_ingresados WHERE id = ?",
            (ingreso_id,),
        ).fetchone()
        if not ingreso:
            st.error("No se encontró el ingreso seleccionado.")
            conn.close()
        else:
            plan = _cargar_plan_mantenimiento(conn, ingreso_id)
            respuestas = _cargar_respuestas_checklist(
                conn,
                "controles_mantenimiento",
                ingreso_id,
            )
            fecha_inicio = _fecha_agenda(ingreso[1]) if ingreso[1] else None
            fecha_fin = _fecha_agenda(ingreso[2]) if ingreso[2] else None
            col_inicio, col_fin = st.columns(2)
            with col_inicio:
                st.metric(
                    "Inicio de mantenimiento",
                    fecha_inicio.strftime("%d/%m/%Y") if fecha_inicio else "No informado",
                )
            with col_fin:
                st.metric(
                    "Fin estimado",
                    fecha_fin.strftime("%d/%m/%Y") if fecha_fin else "No informado",
                )
            mensaje_mantenimiento = st.session_state.pop(
                "mensaje_mantenimiento",
                "",
            )
            if mensaje_mantenimiento:
                if "no se pudo generar el PDF" in mensaje_mantenimiento:
                    st.warning(mensaje_mantenimiento)
                elif "guardados automáticamente" in mensaje_mantenimiento:
                    st.success(mensaje_mantenimiento)
                else:
                    st.error(mensaje_mantenimiento)

            if ingreso[0] == "Mantenimiento Completado":
                st.success("Mantenimiento completado.")
                mostrar_descargas_pdf(ingreso_id)
            elif ingreso[0] != "Mantenimiento en Proceso":
                st.warning("Este equipo ya no figura con un mantenimiento en proceso.")
            if ingreso[0] != "Mantenimiento en Proceso":
                st.button(
                    "Volver al Tablero de Equipos",
                    use_container_width=True,
                    key=f"btn_volver_tablero_mantenimiento_{ingreso_id}",
                    on_click=_proteger_callback(
                        "ejecucion_mantenimiento",
                        pausar_mantenimiento,
                    ),
                )
            elif not plan:
                st.error("No hay pasos configurados para este mantenimiento.")
            else:
                with st.sidebar:
                    st.markdown("### ⏱️ Control de Tiempos")
                    total_horas = conn.execute(
                        "SELECT SUM(horas) FROM registro_horas WHERE ingreso_id = ?",
                        (ingreso_id,),
                    ).fetchone()[0]
                    st.metric("Total Horas Invertidas", f"{total_horas or 0} hs")
                    with st.expander("Cargar Horas (Mecánicos)"):
                        with st.form(f"form_horas_{ingreso_id}"):
                            df_mec = pd.read_sql_query(
                                "SELECT nombre FROM mecanicos ORDER BY nombre",
                                conn,
                            )
                            if df_mec.empty:
                                st.warning("No hay mecánicos configurados.")
                            else:
                                mec_horas = st.selectbox(
                                    "Técnico:",
                                    df_mec["nombre"].tolist(),
                                )
                                h_input = st.number_input(
                                    "Horas dedicadas hoy:",
                                    min_value=0.5,
                                    step=0.5,
                                    value=1.0,
                                )
                                if st.form_submit_button("💾 Guardar Horas"):
                                    conn.execute(
                                        "INSERT INTO registro_horas "
                                        "(ingreso_id, fecha, horas, mecanico) VALUES (?, ?, ?, ?)",
                                        (
                                            ingreso_id,
                                            datetime.now(
                                                ZoneInfo("America/Argentina/Buenos_Aires")
                                            ).strftime("%d/%m/%Y"),
                                            h_input,
                                            mec_horas,
                                        ),
                                    )
                                    conn.commit()
                                    persistir_y_sync()
                                    st.success("Horas guardadas.")
                    st.markdown("---")
                    st.button(
                        "⏸️ Pausar Tareas",
                        use_container_width=True,
                        key=f"btn_pausar_tareas_{ingreso_id}",
                        on_click=_proteger_callback(
                            "ejecucion_mantenimiento",
                            pausar_mantenimiento,
                        ),
                    )

                controles_mantenimiento = [
                    (item["control_id"], item["tarea"], item["tipo"])
                    for item in plan
                ]
                progreso, total_controles = _mostrar_checklist_planilla(
                    "mantenimiento",
                    ingreso_id,
                    controles_mantenimiento,
                    respuestas,
                )
                key_hallazgos = f"hallazgos_mantenimiento_{ingreso_id}"
                if key_hallazgos not in st.session_state:
                    guardado = respuestas.get("Reparación Adicional en proceso")
                    st.session_state[key_hallazgos] = (
                        guardado["observaciones"] if guardado else ""
                    )
                st.text_area(
                    "Hallazgos adicionales, insumos u observaciones finales (opcional):",
                    key=key_hallazgos,
                    on_change=_proteger_callback(
                        "ejecucion_mantenimiento",
                        guardar_hallazgos_mantenimiento,
                    ),
                    args=(ingreso_id, key_hallazgos),
                )
                st.button(
                    "✅ Finalizar mantenimiento",
                    key=f"finalizar_mantenimiento_{ingreso_id}",
                    use_container_width=True,
                    disabled=progreso < total_controles,
                    on_click=_proteger_callback(
                        "ejecucion_mantenimiento",
                        finalizar_mantenimiento,
                    ),
                    args=(ingreso_id,),
                )
                mostrar_descargas_pdf(ingreso_id)
                st.info(
                    "Los pasos y las observaciones se guardan automáticamente. "
                    "El mantenimiento solo se finaliza cuando todos los pasos obligatorios están completos."
                )
        conn.close()

# ==========================================
# 5. PANTALLA: CHECKLIST DE SALIDA
# ==========================================
elif menu_elegido == "✅ Entrega de Equipo (Salida)":
    _exigir_seccion("entrega_equipo")
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
                on_click=_proteger_callback(
                    "entrega_equipo",
                    volver_desde_checklist_salida,
                ),
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
                on_click=_proteger_callback(
                    "entrega_equipo",
                    finalizar_checklist_salida,
                ),
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
    _exigir_seccion("archivo_pdfs")
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
    _exigir_seccion("lista_compras")
    st.markdown(
        "<h2 class='compras-title'>🛒 Gestión de Insumos y Repuestos</h2>",
        unsafe_allow_html=True,
    )
    conn = conectar_db()
    hoy = datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()
    compras_pendientes = _cargar_compras_pendientes(conn, hoy)
    _mostrar_aviso_compras_vencidas(_compras_vencidas(compras_pendientes, hoy))

    tab_pendientes, tab_cargar, tab_rubros = st.tabs(["📋 Lista de Pendientes", "📝 Cargar Necesidad", "⚙️ Configurar Rubros"])
    
    with tab_cargar:
        st.markdown(
            "<h3 class='compras-section-title'>Cargar nuevo ítem a comprar</h3>",
            unsafe_allow_html=True,
        )
        df_rubros_carga = pd.read_sql_query("SELECT nombre FROM maestro_rubros_compras ORDER BY nombre", conn)
        
        if df_rubros_carga.empty:
            st.warning("⚠️ Primero tenés que configurar al menos un rubro en la solapa 'Configurar Rubros'.")
        else:
            with st.form("form_compras"):
                rubro_sel = st.selectbox("Seleccionar Rubro / Proveedor:", df_rubros_carga['nombre'].tolist())
                desc_input = st.text_input("Descripción (Ej: Filtro de aceite, Electrodos, Lija):")
                det_input = st.text_area("Detalle Técnico / Código / Marca preferida (Opcional):")
                cant_input = st.text_input("Cantidad necesaria (Ej: 2 unidades, 5 litros):")
                fecha_necesaria_input = st.date_input(
                    "Fecha necesaria:",
                    value=None,
                    format="DD/MM/YYYY",
                )
                
                if st.form_submit_button("➕ Agregar a la lista"):
                    if desc_input.strip() and cant_input.strip() and fecha_necesaria_input:
                        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
                        conn.execute(
                            "INSERT INTO lista_compras "
                            "(rubro, descripcion, detalle, cantidad, fecha_carga, estado, fecha_necesaria) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (
                                rubro_sel,
                                desc_input.strip(),
                                det_input.strip(),
                                cant_input.strip(),
                                fecha_hoy,
                                "Pendiente",
                                fecha_necesaria_input.isoformat(),
                            ),
                        )
                        conn.commit()
                        persistir_y_sync()
                        st.success("¡Agregado exitosamente a la lista de pendientes!")
                    else:
                        st.error(
                            "⚠️ Completá la descripción, la cantidad y la fecha necesaria."
                        )

    with tab_pendientes:
        with st.container(key="compras-pendientes"):
            st.markdown(
                "<h3 class='compras-section-title'>Pendientes de compra</h3>",
                unsafe_allow_html=True,
            )
            if not compras_pendientes:
                st.success("🎉 ¡No hay compras pendientes! El taller está completamente abastecido.")
            else:
                encabezados = st.container(key="compras-encabezado")
                with encabezados:
                    c_rubro, c_articulo, c_cantidad, c_fecha, c_accion = st.columns(
                        [1.05, 2.4, 0.85, 1.8, 1.1],
                        gap="small",
                    )
                    c_rubro.caption("Rubro")
                    c_articulo.caption("Artículo / detalle")
                    c_cantidad.caption("Cantidad")
                    c_fecha.caption("Fecha necesaria")
                    c_accion.caption("Acción")

                grupo_actual = None
                for compra in compras_pendientes:
                    fecha_necesaria = compra["fecha_necesaria_date"]
                    grupo = (
                        "Sin fecha"
                        if fecha_necesaria is None
                        else "Vencidas"
                        if fecha_necesaria < hoy
                        else "Próximas"
                    )
                    if grupo != grupo_actual:
                        st.markdown(f"**{grupo}**")
                        grupo_actual = grupo

                    with st.container(border=True):
                        c_rubro, c_articulo, c_cantidad, c_fecha, c_accion = st.columns(
                            [1.05, 2.4, 0.85, 1.8, 1.1],
                            gap="small",
                        )
                        c_rubro.markdown(f"**{compra['rubro']}**")
                        c_articulo.markdown(f"**{compra['descripcion']}**")
                        if compra["detalle"]:
                            c_articulo.caption(compra["detalle"])
                        c_cantidad.caption("Cantidad")
                        c_cantidad.markdown(f"**{compra['cantidad']}**")

                        widget_key = f"fecha_necesaria_compra_{compra['id']}"
                        if widget_key not in st.session_state:
                            st.session_state[widget_key] = fecha_necesaria
                        c_fecha.date_input(
                            "Fecha necesaria",
                            format="DD/MM/YYYY",
                            key=widget_key,
                            on_change=_proteger_callback(
                                "lista_compras",
                                _guardar_fecha_necesaria_compra,
                            ),
                            args=(compra["id"], widget_key),
                        )
                        if fecha_necesaria is None:
                            c_fecha.caption("Sin fecha")
                        elif fecha_necesaria < hoy:
                            dias_atraso = compra["dias_atraso"]
                            c_fecha.error(
                                f"Vencida · {dias_atraso} "
                                f"{'día' if dias_atraso == 1 else 'días'} de atraso"
                            )

                        mensaje_fecha = st.session_state.pop(
                            f"mensaje_fecha_necesaria_{compra['id']}",
                            None,
                        )
                        if mensaje_fecha:
                            c_fecha.caption(mensaje_fecha)
                        error_fecha = st.session_state.pop(
                            f"error_fecha_necesaria_{compra['id']}",
                            None,
                        )
                        if error_fecha:
                            c_fecha.error(error_fecha)

                        if c_accion.button(
                            "✅ Ya lo compré",
                            key=f"btn_compra_{compra['id']}",
                            use_container_width=True,
                        ):
                            actualizacion = conn.execute(
                                "UPDATE lista_compras SET estado = 'Comprado' "
                                "WHERE id = ? AND estado = 'Pendiente'",
                                (compra["id"],),
                            )
                            if actualizacion.rowcount != 1:
                                st.error(
                                    "No se pudo marcar como comprada porque ya no está pendiente."
                                )
                            else:
                                conn.commit()
                                persistir_y_sync()

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
    _exigir_seccion("trabajos_clientes")
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
    _exigir_seccion("configuracion_general")
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
    _exigir_seccion("personal_mecanico")
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
    _exigir_seccion("reportes_facturacion")
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