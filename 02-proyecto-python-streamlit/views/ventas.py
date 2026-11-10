"""Registro de ventas, cobros de fiados, anulaciones y clientes."""
import streamlit as st

from services import catalogo_service, clientes_service, stock_service, ventas_service
from services.permisos import tiene_permiso
from utils import dinero
from views.guardia import requerir_permiso
from views.utilidades import ejecutar, opciones


def mostrar() -> None:
    actor = requerir_permiso("ventas.registrar")
    st.header("Ventas")
    tabs = st.tabs(["Nueva venta", "Historial y cobros", "Clientes"])
    clientes = opciones(clientes_service.listar_clientes(actor))
    variantes = {v.id: v for v in catalogo_service.listar_variantes(actor)}

    with tabs[0]:
        if not variantes:
            st.info("No hay productos cargados.")
        else:
            with st.form("venta"):
                if actor.rol != "vendedor":
                    ubicaciones = opciones(stock_service.listar_ubicaciones(actor))
                    ubic = st.selectbox("Vende desde", list(ubicaciones), format_func=ubicaciones.get) if ubicaciones else None
                else:
                    ubic = None
                vid = st.selectbox("Producto", list(variantes), format_func=lambda i: f"{variantes[i].sku} · {variantes[i].producto} {variantes[i].talle}/{variantes[i].color}")
                v = variantes[vid]
                st.caption(f"Precio permitido: {dinero.formatear_pesos(v.precio_minimo)} a {dinero.formatear_pesos(v.precio_maximo)} (lista {dinero.formatear_pesos(v.precio_lista)})")
                c1, c2, c3 = st.columns(3)
                cant, precio, desc = c1.number_input("Cantidad", min_value=1, step=1), c2.text_input("Precio unitario"), c3.text_input("Descuento", "0")
                cliente = st.selectbox("Cliente (obligatorio si queda a fiado)", [None, *clientes], format_func=lambda i: clientes.get(i, "(sin cliente)"))
                m1, m2 = st.columns(2)
                efectivo, transf = m1.text_input("Pago en efectivo", "0"), m2.text_input("Pago por transferencia", "0")
                if st.form_submit_button("Registrar venta"):
                    pagos = [{"medio": m, "monto": x} for m, x in (("efectivo", efectivo), ("transferencia", transf)) if x not in ("", "0", "0,00")]
                    ejecutar(lambda: ventas_service.registrar_venta(
                        actor, [{"variante_id": vid, "cantidad": int(cant), "precio": precio}], ubicacion_id=ubic,
                        cliente_id=cliente, descuento=desc or 0, pagos=pagos), "Venta registrada.")
    with tabs[1]:
        ventas = ventas_service.listar_ventas(actor)
        st.dataframe(ventas, use_container_width=True, hide_index=True)
        pendientes = [x for x in ventas if x["estado"] == "confirmada" and x["estado pago"] != "pagada"]
        if pendientes:
            with st.form("cobro"):
                vid = st.selectbox("Venta con saldo", [x["id"] for x in pendientes])
                medio = st.selectbox("Medio", ["efectivo", "transferencia"])
                monto = st.text_input("Monto cobrado")
                if st.form_submit_button("Registrar cobro"):
                    ejecutar(lambda: ventas_service.registrar_cobro(actor, vid, medio, monto), "Cobro registrado.")
        if tiene_permiso(actor.rol, "ventas.anular") and ventas:
            with st.form("anular"):
                vid = st.selectbox("Venta a anular", [x["id"] for x in ventas if x["estado"] == "confirmada"] or [None])
                if st.form_submit_button("Anular (devuelve el stock)") and vid:
                    ejecutar(lambda: ventas_service.anular_venta(actor, vid), "Venta anulada.")
    with tabs[2]:
        with st.form("cliente", clear_on_submit=True):
            n, t = st.text_input("Nombre"), st.text_input("Teléfono (opcional)")
            if st.form_submit_button("Agregar cliente"):
                ejecutar(lambda: clientes_service.crear_cliente(actor, n, t), "Cliente creado.")
        st.dataframe(clientes_service.listar_clientes(actor), hide_index=True)
