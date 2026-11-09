"""Administración de usuarios y zonas (solo rol admin)."""
import logging

import streamlit as st

from services import auth_service, usuario_service, zona_service
from services.permisos import ROLES
from utils.excepciones import ErrorDeNegocio
from views.guardia import requerir_permiso

logger = logging.getLogger(__name__)


def mostrar() -> None:
    actor = requerir_permiso("usuarios.gestionar")
    st.header("Usuarios")
    tab_lista, tab_nuevo, tab_zonas = st.tabs(["Listado", "Nuevo usuario", "Zonas"])

    with tab_lista:
        try:
            usuarios = usuario_service.listar_usuarios(actor)
        except Exception:
            logger.exception("No se pudo listar usuarios")
            st.error("No se pudieron cargar los usuarios.")
            usuarios = []
        busqueda = st.text_input("Buscar por nombre o email").strip().lower()
        if busqueda:
            usuarios = [u for u in usuarios if busqueda in u["nombre"].lower() or busqueda in u["email"]]
        st.dataframe(usuarios, use_container_width=True, hide_index=True)

        st.markdown("**Cambiar estado o desbloquear**")
        if usuarios:
            elegido = st.selectbox("Usuario", usuarios, format_func=lambda u: f'{u["nombre"]} ({u["email"]})')
            col1, col2 = st.columns(2)
            if col1.button("Desactivar" if elegido["activo"] else "Activar"):
                try:
                    usuario_service.cambiar_estado(elegido["id"], not elegido["activo"], actor)
                    st.success("Estado actualizado.")
                    st.rerun()
                except ErrorDeNegocio as error:
                    st.error(str(error))
            if col2.button("Desbloquear (reiniciar intentos)"):
                usuario_service.desbloquear(elegido["id"], actor)
                st.success("Intentos reiniciados.")
                st.rerun()

    with tab_zonas:
        zonas = zona_service.listar_zonas()
        st.dataframe(zonas, use_container_width=True, hide_index=True)
        with st.form("form_zona", clear_on_submit=True):
            nombre_zona = st.text_input("Nueva zona (ciudad)")
            if st.form_submit_button("Agregar zona"):
                try:
                    zona_service.crear_zona(nombre_zona, actor)
                    st.success("Zona creada.")
                    st.rerun()
                except ErrorDeNegocio as error:
                    st.error(str(error))

    with tab_nuevo:
        zonas = zona_service.listar_zonas()
        with st.form("form_usuario", clear_on_submit=False):
            nombre = st.text_input("Nombre y apellido")
            email = st.text_input("Email")
            clave = st.text_input("Clave (mínimo 8, con letra y número)", type="password")
            rol = st.selectbox("Rol", ROLES)
            zona = st.selectbox("Zona (obligatoria para vendedores)", [None] + zonas,
                                format_func=lambda z: "—" if z is None else z["nombre"])
            telefono = st.text_input("Teléfono (opcional)")
            enviar = st.form_submit_button("Crear usuario")
        if enviar:
            try:
                datos = auth_service.validar_datos_registro(
                    nombre, email, clave, rol, zona["id"] if zona else None, telefono)
                auth_service.registrar_usuario(datos, actor)
                st.success("Usuario creado.")
            except ErrorDeNegocio as error:
                st.error(str(error))
            except Exception:
                logger.exception("Error inesperado al crear usuario")
                st.error("Ocurrió un error inesperado.")
