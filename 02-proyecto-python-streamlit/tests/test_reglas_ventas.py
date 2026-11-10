from decimal import Decimal as D

import pytest

from services.reglas_ventas import (LineaEntrada, aplicar_cobro, calcular_venta, estado_de_pago, ganancia,
                                    validar_periodo)
from utils.excepciones import ErrorDeValidacion, PrecioFueraDeRango


def linea(precio="2000", cant=1, costo="1000", mn="1500", mx="2500", vid=1):
    return LineaEntrada(vid, cant, precio, D(costo), D(mn), D(mx))


def test_venta_simple_con_comision():
    v = calcular_venta([linea(cant=2)], 0, "10")
    assert (v.subtotal, v.total, v.comision_total) == (D("4000.00"), D("4000.00"), D("400.00"))
    assert ganancia(v.total, v.lineas) == D("1600.00")        # 4000 - 2000 costo - 400 comisión


def test_descuento_reduce_total_y_comision():
    v = calcular_venta([linea(cant=2)], "400", "10")
    assert v.total == D("3600.00") and v.comision_total == D("360.00")


def test_varias_lineas_suman():
    v = calcular_venta([linea(vid=1), linea("1800", 3, vid=2)], 0, "5")
    assert v.subtotal == D("7400.00") and v.comision_total == D("370.00")


def test_se_congelan_costo_y_minimo():
    l = calcular_venta([linea()], 0, "10").lineas[0]
    assert l.costo_unitario == D("1000") and l.precio_minimo == D("1500")


@pytest.mark.parametrize("precio", ["1499.99", "2500.01"])
def test_precio_fuera_de_rango(precio):
    with pytest.raises(PrecioFueraDeRango):
        calcular_venta([linea(precio)], 0, "10")


def test_errores_de_validacion():
    for args in (([], 0, "10"), ([linea()], 0, "101"), ([linea()], "9999", "10"), ([linea(cant=0)], 0, "10")):
        with pytest.raises(ErrorDeValidacion):
            calcular_venta(*args)


def test_estados_y_cobros():
    assert estado_de_pago(D("100"), D("0")) == "pendiente"
    nuevo, est = aplicar_cobro(D("100"), D("0"), "40")
    assert (nuevo, est) == (D("40.00"), "parcial")
    assert aplicar_cobro(D("100"), nuevo, "60") == (D("100.00"), "pagada")
    with pytest.raises(ErrorDeValidacion):
        aplicar_cobro(D("100"), nuevo, "60.01")


def test_periodo():
    assert validar_periodo("2026-11") == "2026-11"
    for malo in ("2026-13", "26-11", "", None):
        with pytest.raises(ErrorDeValidacion):
            validar_periodo(malo)
