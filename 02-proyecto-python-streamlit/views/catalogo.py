"""Catálogo: productos y variantes con precios mínimo/lista/máximo. El vendedor no ve el costo."""
import streamlit as st

from repositories import catalogo_repository as repo
from database.connection import session_scope
from services import catalogo_service, comisiones_service
from services.permisos import tiene_permiso
from utils import dinero
from views.guardia import requerir_permiso
from views.utilidades import ejecutar


def _listas():
    with session_scope() as s:
        return ({c.id: c.nombre for c in repo.listar_categorias(s)}, {m.id: m.nombre for m in repo.listar_marcas(s)})


def mostrar() -> None:
    actor = requerir_permiso("catalogo.ver")
    st.header("Catálogo")
    puede_editar = tiene_permiso(actor.rol, "catalogo.editar")
    pestañas = ["Productos"] + (["Nuevo producto", "Categorías y marcas", "Comisión"] if puede_editar else [])
    tabs = st.tabs(pestañas)

    with tabs[0]:
        variantes = catalogo_service.listar_variantes(actor)
        filas = [{"Código": v.sku, "Producto": v.producto, "Talle": v.talle, "Color": v.color,
                  **({"Costo": dinero.formatear_pesos(v.costo)} if v.costo is not None else {}),
                  "Mínimo": dinero.formatear_pesos(v.precio_minimo), "Lista": dinero.formatear_pesos(v.precio_lista),
                  "Máximo": dinero.formatear_pesos(v.precio_maximo)} for v in variantes]
        st.dataframe(filas, use_container_width=True, hide_index=True)

    if not puede_editar:
        return
    categorias, marcas = _listas()
    with tabs[1]:
        with st.form("nuevo_producto", clear_on_submit=False):
            nombre = st.text_input("Nombre del producto")
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Categoría", list(categorias), format_func=categorias.get) if categorias else None
            marca = c2.selectbox("Marca", [None, *marcas], format_func=lambda i: marcas.get(i, "(sin marca)"))
            c3, c4, c5 = st.columns(3)
            sku, talle, color = c3.text_input("Código (SKU)"), c4.text_input("Talle", "Único"), c5.text_input("Color", "Único")
            hexa = st.text_input("Color en hexadecimal (opcional, ej. #FF5500)")
            p1, p2, p3, p4 = st.columns(4)
            costo, minimo = p1.text_input("Costo"), p2.text_input("Precio mínimo")
            lista, maximo = p3.text_input("Precio de lista"), p4.text_input("Precio máximo")
            stock_min = st.number_input("Stock mínimo (alerta)", min_value=0, step=1, value=0)
            if st.form_submit_button("Guardar") and cat is not None:
                ejecutar(lambda: catalogo_service.crear_producto_con_variante(
                    actor, nombre=nombre, categoria_id=cat, marca_id=marca, sku=sku, talle=talle, color=color,
                    color_hex=hexa, costo=costo, minimo=minimo, lista=lista, maximo=maximo,
                    stock_minimo=int(stock_min)), "Producto guardado.")
        if not categorias:
            st.info("Primero creá una categoría en la pestaña siguiente.")
    with tabs[2]:
        c1, c2 = st.columns(2)
        with c1.form("f_cat", clear_on_submit=True):
            n = st.text_input("Nueva categoría")
            if st.form_submit_button("Agregar categoría"):
                ejecutar(lambda: catalogo_service.crear_categoria(actor, n), "Categoría creada.")
        with c2.form("f_marca", clear_on_submit=True):
            n = st.text_input("Nueva marca")
            if st.form_submit_button("Agregar marca"):
                ejecutar(lambda: catalogo_service.crear_marca(actor, n), "Marca creada.")
    with tabs[3]:
        st.write(f"Comisión actual de vendedores: **{comisiones_service.pct_actual(actor)} %** (igual para todos los productos).")
        with st.form("f_pct"):
            pct = st.text_input("Nuevo porcentaje")
            if st.form_submit_button("Cambiar") and tiene_permiso(actor.rol, "comisiones.liquidar"):
                ejecutar(lambda: comisiones_service.fijar_pct(actor, pct), "Porcentaje actualizado.")
