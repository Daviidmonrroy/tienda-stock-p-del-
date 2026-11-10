"""Reglas puras de venta, pagos y comisiones (sin base de datos). Son las más importantes para defender:
todo el dinero se calcula acá con Decimal y se prueba con pytest.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from utils import dinero
from utils.excepciones import ErrorDeValidacion
from utils.validaciones import validar_cantidad, validar_monto
from services.reglas_catalogo import validar_precio_de_venta

CERO = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class LineaEntrada:
    variante_id: int
    cantidad: int
    precio_unitario: object
    costo: Decimal
    precio_minimo: Decimal
    precio_maximo: Decimal


@dataclass(frozen=True, slots=True)
class LineaCalculada:
    variante_id: int
    cantidad: int
    precio_unitario: Decimal
    costo_unitario: Decimal
    precio_minimo: Decimal
    comision: Decimal


@dataclass(frozen=True, slots=True)
class VentaCalculada:
    lineas: tuple[LineaCalculada, ...]
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    comision_total: Decimal


def calcular_venta(lineas: list[LineaEntrada], descuento, comision_pct) -> VentaCalculada:
    """Valida cada línea (cantidad, rango de precio) y calcula subtotal, total y comisión.

    La comisión se calcula por línea sobre el precio cobrado y se reduce proporcionalmente si hay descuento.
    """
    if not lineas:
        raise ErrorDeValidacion("venta", "La venta necesita al menos un producto.")
    pct = dinero.a_decimal(comision_pct)
    if not (Decimal("0") <= pct <= Decimal("100")):
        raise ErrorDeValidacion("comisión", "La comisión tiene que estar entre 0 y 100.")
    calculadas, subtotal = [], CERO
    for l in lineas:
        cant = validar_cantidad(l.cantidad)
        precio = validar_precio_de_venta(l.precio_unitario, l.precio_minimo, l.precio_maximo)
        subtotal += precio * cant
        calculadas.append((l, cant, precio))
    desc = validar_monto(descuento, "descuento", permitir_cero=True) if descuento else CERO
    if desc > subtotal:
        raise ErrorDeValidacion("descuento", "El descuento no puede superar el subtotal.")
    total = subtotal - desc
    factor = (total / subtotal) if subtotal else Decimal(1)
    out, comision_total = [], CERO
    for l, cant, precio in calculadas:
        com = dinero.calcular_comision(precio * cant * factor, pct)
        comision_total += com
        out.append(LineaCalculada(l.variante_id, cant, precio, l.costo, l.precio_minimo, com))
    return VentaCalculada(tuple(out), subtotal, desc, total, comision_total)


def estado_de_pago(total: Decimal, pagado: Decimal) -> str:
    if pagado >= total:
        return "pagada"
    return "parcial" if pagado > 0 else "pendiente"


def aplicar_cobro(total: Decimal, pagado: Decimal, monto) -> tuple[Decimal, str]:
    """Suma un cobro. No se puede cobrar más de lo que se debe. Devuelve (nuevo_pagado, estado)."""
    m = validar_monto(monto, "monto")
    if pagado + m > total:
        raise ErrorDeValidacion("monto", f"Solo se debe {dinero.formatear_pesos(total - pagado)}.")
    nuevo = pagado + m
    return nuevo, estado_de_pago(total, nuevo)


def ganancia(total: Decimal, lineas: tuple[LineaCalculada, ...]) -> Decimal:
    """Ganancia bruta = total cobrado - costo - comisión."""
    costo = sum((l.costo_unitario * l.cantidad for l in lineas), CERO)
    comision = sum((l.comision for l in lineas), CERO)
    return total - costo - comision


def validar_periodo(periodo: str) -> str:
    import re
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", periodo or ""):
        raise ErrorDeValidacion("período", "Formato AAAA-MM, por ejemplo 2026-11.")
    return periodo


def limites_del_mes(periodo: str) -> tuple[datetime, datetime]:
    """[inicio, fin) del mes. Evitamos funciones de fecha del motor para que ande igual en MySQL y SQLite."""
    anio, mes = map(int, validar_periodo(periodo).split("-"))
    fin = datetime(anio + (mes == 12), 1 if mes == 12 else mes + 1, 1)
    return datetime(anio, mes, 1), fin


def calcular_ganancia_neta(vendido, costos, comisiones, gastos) -> Decimal:
    return dinero.redondear(vendido - costos - comisiones - gastos)
