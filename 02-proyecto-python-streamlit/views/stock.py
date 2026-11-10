"""Stock por ubicación, transferencias, ajustes y compras."""
import streamlit as st

from database.connection import session_scope
from repositories import catalogo_repository as repo_cat
from services import catalogo_service, compras_service, stock_service
from services.permisos import tiene_permiso
from views.guardia import requerir_permiso
from views.utilidades import ejecutar, opciones


def mostrar() -> None:
    actor = requerir_permiso("stock.ver_propio")
    st.header("Stock")
    admin = tiene_permiso(actor.rol, "stock.ajustar")
    tabs = st.tabs(["Stock actual"] + (["Transferir / ajustar", "Ubicaciones", "Compras"] if admin else []))

    with tabs[0]:
        filas = stock_service.listar_stock(actor)
        solo_bajo = st.checkbox("Solo stock bajo")
        st.dataframe([f for f in filas if f["bajo mínimo"] or not solo_bajo], use_container_width=True, hide_index=True)
    if not admin:
        return

    ubicaciones = opciones(stock_service.listar_ubicaciones(actor))
    variantes = {v.id: f"{v.sku} · {v.producto} {v.talle}/{v.color}" for v in catalogo_service.listar_variantes(actor)}
    with tabs[1]:
        if ubicaciones and variantes:
            with st.form("transferir"):
                st.subheader("Transferir")
                var = st.selectbox("Variante", list(variantes), format_func=variantes.get)
                o = st.selectbox("Desde", list(ubicaciones), format_func=ubicaciones.get)
                d = st.selectbox("Hacia", list(ubicaciones), format_func=ubicaciones.get)
                cant = st.number_input("Cantidad", min_value=1, step=1)
                if st.form_submit_button("Transferir"):
                    ejecutar(lambda: stock_service.transferir(actor, var, o, d, int(cant)), "Transferencia hecha.")
            with st.form("ajustar"):
                st.subheader("Ajuste por inventario")
                var = st.selectbox("Variante ", list(variantes), format_func=variantes.get)
                u = st.selectbox("Ubicación", list(ubicaciones), format_func=ubicaciones.get)
                nueva = st.number_input("Cantidad contada", min_value=0, step=1)
                motivo = st.text_input("Motivo")
                if st.form_submit_button("Ajustar"):
                    ejecutar(lambda: stock_service.ajustar(actor, var, u, int(nueva), motivo), "Stock ajustado.")
        else:
            st.info("Creá ubicaciones y productos primero.")
    with tabs[2]:
        with st.form("ubicacion", clear_on_submit=True):
            nombre = st.text_input("Nombre")
            tipo = st.selectbox("Tipo", ["local", "cancha", "mochila"])
            vend = st.number_input("ID del vendedor (solo mochila)", min_value=0, step=1)
            if st.form_submit_button("Crear ubicación"):
                ejecutar(lambda: stock_service.crear_ubicacion(actor, nombre, tipo, int(vend) or None), "Ubicación creada.")
        st.dataframe(stock_service.listar_ubicaciones(actor), hide_index=True)
    with tabs[3]:
        proveedores = opciones(compras_service.listar_proveedores(actor))
        with st.form("proveedor", clear_on_submit=True):
            n = st.text_input("Nuevo proveedor")
            if st.form_submit_button("Agregar proveedor"):
                ejecutar(lambda: compras_service.crear_proveedor(actor, n), "Proveedor creado.")
        if proveedores and ubicaciones and variantes:
            with st.form("compra"):
                st.subheader("Registrar compra (una variante)")
                p = st.selectbox("Proveedor", list(proveedores), format_func=proveedores.get)
                u = st.selectbox("Entra a", list(ubicaciones), format_func=ubicaciones.get)
                v = st.selectbox("Variante  ", list(variantes), format_func=variantes.get)
                q = st.number_input("Cantidad  ", min_value=1, step=1)
                c = st.text_input("Costo unitario")
                if st.form_submit_button("Registrar compra"):
                    ejecutar(lambda: compras_service.registrar_compra(
                        actor, p, u, [{"variante_id": v, "cantidad": int(q), "costo": c}]), "Compra registrada.")
