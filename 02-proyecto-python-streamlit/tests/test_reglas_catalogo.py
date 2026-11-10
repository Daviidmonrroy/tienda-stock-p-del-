from decimal import Decimal

import pytest

from services.reglas_catalogo import validar_precio_de_venta, validar_precios
from utils.excepciones import ErrorDeValidacion, PrecioFueraDeRango
from utils.validaciones import validar_cantidad, validar_monto, validar_sku


def test_precios_validos():
    assert validar_precios("1000", "1500", "2000", "2500")[2] == Decimal("2000.00")


@pytest.mark.parametrize("args", [("1000", "2000", "1500", "2500"), ("2000", "1500", "2000", "2500"),
                                  ("1000", "1500", "2000", "1900")])
def test_precios_incoherentes(args):
    with pytest.raises(ErrorDeValidacion):
        validar_precios(*args)


def test_precio_de_venta_en_rango():
    assert validar_precio_de_venta("1800", Decimal("1500"), Decimal("2500")) == Decimal("1800.00")


@pytest.mark.parametrize("p", ["1499.99", "2500.01"])
def test_precio_de_venta_fuera_de_rango(p):
    with pytest.raises(PrecioFueraDeRango):
        validar_precio_de_venta(p, Decimal("1500"), Decimal("2500"))


def test_sku_cantidad_monto():
    assert validar_sku("pal-01") == "PAL-01"
    with pytest.raises(ErrorDeValidacion):
        validar_sku("a b")
    assert validar_cantidad(3) == 3
    for malo in (0, -1, 1.5, True):
        with pytest.raises(ErrorDeValidacion):
            validar_cantidad(malo)
    with pytest.raises(ErrorDeValidacion):
        validar_monto("10.555", "x")
    with pytest.raises(ErrorDeValidacion):
        validar_monto(0, "x")
