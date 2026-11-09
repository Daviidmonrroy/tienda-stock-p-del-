"""Operaciones con dinero usando Decimal (nunca float).

Concepto de clase: Decimal para operaciones monetarias sin errores de precisión.
"""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENTAVO = Decimal("0.01")


def a_decimal(valor: "str | int | Decimal") -> Decimal:
    """Convierte a Decimal. Rechaza float a propósito: 0.1 ya viene con error de precisión."""
    if isinstance(valor, bool) or isinstance(valor, float):
        raise TypeError("Para dinero usá un texto, un entero o un Decimal, nunca float.")
    texto = str(valor).strip()
    if texto.count(",") == 1 and "." not in texto:
        texto = texto.replace(",", ".")  # acepta "1234,50"; no se aceptan separadores de miles
    try:
        numero = Decimal(texto)
    except InvalidOperation as error:
        raise ValueError(f"Monto inválido: {valor!r}") from error
    if not numero.is_finite():
        raise ValueError(f"Monto inválido: {valor!r}")
    return numero


def redondear(monto: Decimal) -> Decimal:
    """Redondea al centavo (mitad hacia arriba, como en comercio)."""
    return monto.quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_comision(total: Decimal, porcentaje: Decimal) -> Decimal:
    """Comisión = total * porcentaje / 100, redondeada al centavo."""
    return redondear(total * porcentaje / Decimal(100))


def formatear_pesos(monto: Decimal) -> str:
    """Formato argentino: $ 150.000,00"""
    texto = f"{redondear(monto):,.2f}"
    return "$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")
