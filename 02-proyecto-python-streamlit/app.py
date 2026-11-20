"""Punto de entrada de Streamlit.  Ejecutar:  streamlit run app.py

Streamlit vuelve a ejecutar este archivo completo en cada interacción; por eso el usuario
logueado se guarda en st.session_state (una variable común se reiniciaría en cada ejecución).
"""
import os

import streamlit as st

from config.settings import obtener_settings
from services.permisos import tiene_permiso
from utils import arranque
from utils.estilos import aplicar_estilos, logo_html
from utils.excepciones import ConfiguracionFaltante
from views import catalogo, login, reportes, stock, usuarios, ventas

st.set_page_config(page_title="Vibra Deportiva", layout="wide")
aplicar_estilos(st)

def _pasar_secrets_al_entorno() -> None:
    """En Streamlit Cloud las variables se cargan en 'Secrets'. Las copiamos a os.environ para que settings las lea.
    En local no hay secrets (se usa .env), por eso el try/except."""
    try:
        for clave, valor in st.secrets.items():
            if isinstance(valor, (str, int, float, bool)):
                os.environ.setdefault(clave, str(valor))
    except Exception:
        pass


@st.cache_resource(show_spinner="Preparando la base de datos...")
def _preparar_una_vez() -> bool:
    """cache_resource: se ejecuta una sola vez por servidor, no en cada interacción."""
    arranque.preparar_base()
    return True


def _modo_demo_si_no_hay_base() -> bool:
    """Si no se configuró NINGUNA variable de base de datos, se usa SQLite (demo) en vez de fallar.
    Si hay alguna configurada, no se toca nada: así un error de configuración real sigue viéndose."""
    if any(os.environ.get(v) for v in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_ENGINE")):
        return False
    os.environ["DB_ENGINE"] = "sqlite"
    return True


_pasar_secrets_al_entorno()
en_demo = _modo_demo_si_no_hay_base()
try:
    obtener_settings()
    _preparar_una_vez()
except ConfiguracionFaltante as error:
    st.error(str(error))
    st.stop()
except Exception as error:      # base inalcanzable, clave incorrecta, etc.
    st.error(f"No se pudo preparar la base de datos: {error}")
    st.stop()

if en_demo:
    st.warning("Modo demostración (SQLite): los datos se borran cuando la app se reinicia.")

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None


def inicio() -> None:
    usuario = st.session_state["usuario"]
    st.header(f"Hola, {usuario.nombre}")
    st.write(f"Rol: **{usuario.rol}**. Usá el menú de la izquierda.")


# nombre del menú -> (función de la vista, permiso necesario o None si es libre)
PAGINAS = {
    "Inicio": (inicio, None),
    "Catálogo": (catalogo.mostrar, "catalogo.ver"),
    "Stock": (stock.mostrar, "stock.ver_propio"),
    "Ventas": (ventas.mostrar, "ventas.registrar"),
    "Panel del dueño": (reportes.mostrar, "reportes.ver"),
    "Usuarios": (usuarios.mostrar, "usuarios.gestionar"),
}

usuario = st.session_state["usuario"]
if usuario is None:
    login.mostrar()
else:
    with st.sidebar:
        st.markdown(logo_html("logo-horizontal-sobre-negro.svg", 200), unsafe_allow_html=True)
        st.caption(f"{usuario.nombre} · {usuario.rol}")
        visibles = [n for n, (_, permiso) in PAGINAS.items() if permiso is None or tiene_permiso(usuario.rol, permiso)]
        pagina = st.radio("Menú", visibles, label_visibility="collapsed")
        if st.button("Cerrar sesión"):
            st.session_state["usuario"] = None
            st.rerun()
    PAGINAS[pagina][0]()
