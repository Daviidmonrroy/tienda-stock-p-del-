from datetime import datetime
from decimal import Decimal as D

import pytest

from services.reglas_ventas import calcular_ganancia_neta, limites_del_mes  # noqa: E402
from utils.exportacion import a_csv  # noqa: E402


def test_limites_del_mes():
    assert limites_del_mes("2026-11") == (datetime(2026, 11, 1), datetime(2026, 12, 1))
    assert limites_del_mes("2026-12")[1] == datetime(2027, 1, 1)


def test_ganancia_neta():
    assert calcular_ganancia_neta(D("10000"), D("4000"), D("1000"), D("2500")) == D("2500.00")


def test_csv():
    assert a_csv([{"a": D("1.50"), "b": "x"}]) == "a;b\n1,50;x\n"
    assert a_csv([]) == ""
