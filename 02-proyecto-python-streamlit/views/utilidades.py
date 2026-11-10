"""Pequeñas ayudas de pantalla compartidas por las vistas."""
import logging

import streamlit as st

from utils.excepciones import ErrorDeNegocio

logger = logging.getLogger(__name__)


def ejecutar(accion, mensaje_ok: str):
    """Corre una acción de servicio. Errores de negocio -> mensaje claro; cualquier otro -> log + mensaje genérico
    (nunca mostramos el detalle técnico al usuario)."""
    try:
        resultado = accion()
    except ErrorDeNegocio as error:
        st.error(str(error))
        return None
    except Exception:
        logger.exception("Error inesperado")
        st.error("Ocurrió un error inesperado. Probá de nuevo.")
        return None
    st.success(mensaje_ok)
    return resultado if resultado is not None else True


def opciones(filas: list[dict], etiqueta: str = "nombre") -> dict:
    """{id: texto} para usar en st.selectbox con format_func."""
    return {f["id"]: f[etiqueta] for f in filas}
