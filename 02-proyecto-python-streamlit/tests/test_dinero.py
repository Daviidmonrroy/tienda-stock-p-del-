from decimal import Decimal

import pytest

from utils import dinero


def test_float_no_se_acepta():
    with pytest.raises(TypeError):
        dinero.a_decimal(0.1)
    with pytest.raises(TypeError):
        dinero.a_decimal(True)


def test_conversion_de_texto_y_enteros():
    assert dinero.a_decimal("1234.50") == Decimal("1234.50")
    assert dinero.a_decimal("1234,50") == Decimal("1234.50")
    assert dinero.a_decimal(100) == Decimal("100")


@pytest.mark.parametrize("malo", ["abc", "", "NaN", "Infinity"])
def test_montos_invalidos(malo):
    with pytest.raises(ValueError):
        dinero.a_decimal(malo)


def test_decimal_no_tiene_el_error_del_float():
    assert 0.1 + 0.2 != 0.3
    assert Decimal("0.1") + Decimal("0.2") == Decimal("0.3")


def test_redondeo_mitad_hacia_arriba():
    assert dinero.redondear(Decimal("1.005")) == Decimal("1.01")
    assert dinero.redondear(Decimal("1.004")) == Decimal("1.00")


def test_comision():
    assert dinero.calcular_comision(Decimal("100000.00"), Decimal("10")) == Decimal("10000.00")
    assert dinero.calcular_comision(Decimal("99.99"), Decimal("10")) == Decimal("10.00")
    assert dinero.calcular_comision(Decimal("0.05"), Decimal("10")) == Decimal("0.01")


def test_formato_pesos():
    assert dinero.formatear_pesos(Decimal("150000")) == "$ 150.000,00"
    assert dinero.formatear_pesos(Decimal("1234.5")) == "$ 1.234,50"
    assert dinero.formatear_pesos(Decimal("0")) == "$ 0,00"
