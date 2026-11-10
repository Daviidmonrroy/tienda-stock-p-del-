"""Panel del dueño, gastos y liquidación de comisiones."""
from datetime import date, timedelta

import streamlit as st

from services import comisiones_service, reportes_service
from services.permisos import tiene_permiso
from utils import dinero
from utils.exportacion import a_csv
from views.guardia import requerir_permiso
from views.utilidades import ejecutar


def mostrar() -> None:
    actor = requerir_permiso("reportes.ver")
    st.header("Panel del dueño")
    tabs = st.tabs(["Resumen", "Gastos", "Comisiones"])
    with tabs[0]:
        c1, c2 = st.columns(2)
        desde = c1.date_input("Desde", date.today().replace(day=1))
        hasta = c2.date_input("Hasta", date.today())
        try:
            p = reportes_service.panel(actor, desde, hasta)
        except Exception as error:
            st.error(str(error))
            return
        m = st.columns(5)
        for col, (t, k) in zip(m, [("Vendido", "vendido"), ("Costos", "costos"), ("Comisiones", "comisiones"),
                                   ("Gastos", "gastos"), ("Ganancia neta", "ganancia_neta")]):
            col.metric(t, dinero.formatear_pesos(p[k]))
        st.subheader("Por vendedor")
        st.dataframe(p["por_vendedor"], hide_index=True, use_container_width=True)
        st.subheader("Por día")
        if p["por_dia"]:
            st.bar_chart({str(d["dia"]): float(d["vendido"]) for d in p["por_dia"]})
        st.download_button("Descargar por vendedor (CSV)", a_csv(p["por_vendedor"]), "ventas_por_vendedor.csv", "text/csv")
    with tabs[1]:
        with st.form("gasto", clear_on_submit=True):
            f = st.date_input("Fecha", date.today())
            cat = st.text_input("Categoría (sueldo, publicidad, alquiler...)")
            desc, monto = st.text_input("Descripción"), st.text_input("Monto")
            if st.form_submit_button("Registrar gasto"):
                ejecutar(lambda: reportes_service.crear_gasto(actor, f, cat, desc, monto), "Gasto registrado.")
        gastos = reportes_service.listar_gastos(actor, date.today() - timedelta(days=90), date.today())
        st.dataframe(gastos, hide_index=True, use_container_width=True)
    with tabs[2]:
        periodo = st.text_input("Mes (AAAA-MM)", date.today().strftime("%Y-%m"))
        try:
            filas = comisiones_service.resumen(actor, periodo)
        except Exception as error:
            st.error(str(error))
            return
        st.dataframe(filas, hide_index=True, use_container_width=True)
        if tiene_permiso(actor.rol, "comisiones.liquidar") and filas:
            with st.form("liquidar"):
                v = st.selectbox("Vendedor", [f["vendedor_id"] for f in filas], format_func=lambda i: next(f["vendedor"] for f in filas if f["vendedor_id"] == i))
                if st.form_submit_button("Liquidar mes"):
                    ejecutar(lambda: comisiones_service.liquidar(actor, v, periodo), "Mes liquidado.")
