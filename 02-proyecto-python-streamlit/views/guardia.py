"""Control de acceso de las páginas. Cada vista debe llamar a estas funciones al principio."""
import streamlit as st

from services.permisos import tiene_permiso


def usuario_actual():
    """Devuelve el UsuarioSesion guardado en st.session_state o None."""
    return st.session_state.get("usuario")


def requerir_permiso(permiso: str):
    usuario = usuario_actual()
    if usuario is None:
        st.error("Tenés que iniciar sesión.")
        st.stop()
    if not tiene_permiso(usuario.rol, permiso):
        st.error("No tenés permiso para ver esta página.")
        st.stop()
    return usuario
