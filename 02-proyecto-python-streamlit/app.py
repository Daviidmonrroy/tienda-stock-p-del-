"""Punto de entrada de Streamlit.  Ejecutar:  streamlit run app.py

Streamlit vuelve a ejecutar este archivo completo en cada interacción; por eso el usuario
logueado se guarda en st.session_state (una variable común se reiniciaría en cada ejecución).
"""
import streamlit as st

from config.settings import obtener_settings
from services.permisos import tiene_permiso
from utils.estilos import aplicar_estilos, logo_html
from utils.excepciones import ConfiguracionFaltante
from views import catalogo, login, reportes, stock, usuarios, ventas

st.set_page_config(page_title="Vibra Deportiva", layout="wide")
aplicar_estilos(st)

try:
    obtener_settings()
except ConfiguracionFaltante as error:
    st.error(str(error))
    st.stop()

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
