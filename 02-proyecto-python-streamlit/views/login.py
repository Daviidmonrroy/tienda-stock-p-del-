"""Pantalla de inicio de sesión.

Concepto de clase: st.session_state guarda el usuario entre ejecuciones del script (cada clic).
La clave se pide con type="password" (getpass es solo para consola, no se usa acá).
"""
import logging

import streamlit as st

from services import auth_service
from utils.estilos import logo_html
from utils.excepciones import ErrorDeNegocio

logger = logging.getLogger(__name__)


def mostrar() -> None:
    st.markdown(logo_html(), unsafe_allow_html=True)
    st.subheader("Iniciar sesión")
    with st.form("form_login"):
        email = st.text_input("Email")
        clave = st.text_input("Clave", type="password")
        enviar = st.form_submit_button("Ingresar")
    if not enviar:
        return
    try:
        usuario = auth_service.iniciar_sesion(email, clave)
    except ErrorDeNegocio as error:          # error esperado: se muestra el mensaje
        st.error(str(error))
    except Exception:                        # error inesperado: se registra y se muestra un mensaje genérico
        logger.exception("Error inesperado al iniciar sesión")
        st.error("Ocurrió un error inesperado. Verificá la conexión con la base de datos.")
    else:
        st.session_state["usuario"] = usuario
        st.rerun()
