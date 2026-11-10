"""Reglas puras del catálogo (sin base de datos): se pueden probar con pytest en cualquier PC."""
from decimal import Decimal

from utils import dinero
from utils.excepciones import ErrorDeValidacion, PrecioFueraDeRango
from utils.validaciones import validar_monto


def validar_precios(costo, minimo, lista, maximo) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Exige costo <= mínimo <= lista <= máximo (todos Decimal con 2 decimales)."""
    c = validar_monto(costo, "costo", permitir_cero=True)
    mn = validar_monto(minimo, "precio mínimo")
    ls = validar_monto(lista, "precio de lista")
    mx = validar_monto(maximo, "precio máximo")
    if not (mn <= ls <= mx):
        raise ErrorDeValidacion("precios", "Tiene que cumplirse: mínimo ≤ lista ≤ máximo.")
    if c > mn:
        raise ErrorDeValidacion("costo", "El costo no puede superar el precio mínimo (se vendería con pérdida).")
    return c, mn, ls, mx


def validar_precio_de_venta(precio, minimo: Decimal, maximo: Decimal) -> Decimal:
    """El precio cobrado debe estar entre el mínimo y el máximo de la variante."""
    p = dinero.redondear(dinero.a_decimal(precio))
    if p < minimo or p > maximo:
        raise PrecioFueraDeRango(
            f"El precio tiene que estar entre {dinero.formatear_pesos(minimo)} y {dinero.formatear_pesos(maximo)}.")
    return p
