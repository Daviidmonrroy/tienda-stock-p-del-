"""Limpieza y validación de datos de entrada.

Conceptos de clase: strip(), lower(), expresiones regulares (re), validación de longitudes,
validación de emails. Son funciones puras: no tocan la base de datos ni Streamlit.
"""
import re

from utils.excepciones import ErrorDeValidacion

# --- expresiones regulares (compiladas una sola vez) ---
_EMAIL_LOCAL = re.compile(r"^[a-z0-9._%+-]{1,64}$")
_EMAIL_DOMINIO = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}$")
_COLOR_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_TELEFONO = re.compile(r"^\+?[0-9 ()-]{6,20}$")
_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ '.-]*$")

LARGO_MAX_EMAIL = 160
LARGO_MAX_NOMBRE = 120
BYTES_MAX_CLAVE = 72  # límite de bcrypt: solo procesa los primeros 72 bytes


def limpiar_texto(valor: str | None) -> str:
    """Quita espacios al principio y al final. None se trata como texto vacío."""
    return (valor or "").strip()


def limpiar_email(valor: str | None) -> str:
    """Primero se limpia, después se valida: espacios fuera y todo en minúsculas."""
    return limpiar_texto(valor).lower()


def validar_longitud(valor: str, campo: str, minimo: int, maximo: int) -> str:
    if not (minimo <= len(valor) <= maximo):
        raise ErrorDeValidacion(campo, f"{campo.capitalize()}: debe tener entre {minimo} y {maximo} caracteres.")
    return valor


def validar_email(email: str) -> str:
    """Espera un email ya limpiado con limpiar_email(). Devuelve el mismo email si es válido."""
    if not email or len(email) > LARGO_MAX_EMAIL or email.count("@") != 1:
        raise ErrorDeValidacion("email", "Email: formato inválido.")
    local, dominio = email.split("@")
    if (not _EMAIL_LOCAL.fullmatch(local) or local.startswith(".") or local.endswith(".")
            or ".." in local or not _EMAIL_DOMINIO.fullmatch(dominio)):
        raise ErrorDeValidacion("email", "Email: formato inválido.")
    return email


def validar_nombre(valor: str) -> str:
    valor = limpiar_texto(valor)
    validar_longitud(valor, "nombre", 2, LARGO_MAX_NOMBRE)
    if not _NOMBRE.fullmatch(valor):
        raise ErrorDeValidacion("nombre", "Nombre: solo letras, espacios, apóstrofe, punto y guion.")
    return valor


def validar_clave(clave: str | None) -> str:
    """La clave NO se limpia con strip(): los espacios podrían ser parte de la clave."""
    if clave is None or len(clave) < 8:
        raise ErrorDeValidacion("clave", "Clave: mínimo 8 caracteres.")
    if len(clave.encode("utf-8")) > BYTES_MAX_CLAVE:
        raise ErrorDeValidacion("clave", f"Clave: máximo {BYTES_MAX_CLAVE} bytes (aprox. {BYTES_MAX_CLAVE} caracteres).")
    if not re.search(r"[A-Za-z]", clave) or not re.search(r"[0-9]", clave):
        raise ErrorDeValidacion("clave", "Clave: debe tener al menos una letra y un número.")
    return clave


def validar_color_hex(valor: str | None) -> str | None:
    """El color es opcional: vacío o None devuelve None. Si hay valor, debe ser #RRGGBB."""
    valor = limpiar_texto(valor)
    if not valor:
        return None
    if not _COLOR_HEX.fullmatch(valor):
        raise ErrorDeValidacion("color", "Color: formato #RRGGBB (por ejemplo #F03A37).")
    return valor.upper()


def validar_telefono(valor: str | None) -> str | None:
    valor = limpiar_texto(valor)
    if not valor:
        return None
    if not _TELEFONO.fullmatch(valor):
        raise ErrorDeValidacion("teléfono", "Teléfono: entre 6 y 20 caracteres (números, espacios, + ( ) -).")
    return valor


# ---------- catálogo, stock y dinero ----------
from decimal import Decimal  # noqa: E402

from utils import dinero  # noqa: E402

_SKU = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,39}$")
MONTO_MAXIMO = Decimal("9999999999.99")


def validar_texto_corto(valor: str | None, campo: str, minimo: int = 2, maximo: int = 80) -> str:
    return validar_longitud(limpiar_texto(valor), campo, minimo, maximo)


def validar_sku(valor: str | None) -> str:
    """Código de variante: mayúsculas, números y guiones, entre 3 y 40 caracteres."""
    sku = limpiar_texto(valor).upper()
    if not _SKU.fullmatch(sku):
        raise ErrorDeValidacion("sku", "Código: 3 a 40 caracteres, solo letras, números y guiones (ej. PAL-CTRL-01).")
    return sku


def validar_cantidad(valor: object, campo: str = "cantidad") -> int:
    """Entero mayor que cero. Rechaza decimales y booleanos."""
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise ErrorDeValidacion(campo, f"{campo.capitalize()}: tiene que ser un número entero mayor que cero.")
    return valor


def validar_monto(valor: object, campo: str, permitir_cero: bool = False) -> Decimal:
    """Convierte a Decimal y exige un monto positivo con hasta 2 decimales."""
    try:
        monto = dinero.a_decimal(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError) as error:
        raise ErrorDeValidacion(campo, f"{campo.capitalize()}: monto inválido.") from error
    if monto != dinero.redondear(monto):
        raise ErrorDeValidacion(campo, f"{campo.capitalize()}: como máximo 2 decimales.")
    if monto < 0 or (monto == 0 and not permitir_cero) or monto > MONTO_MAXIMO:
        raise ErrorDeValidacion(campo, f"{campo.capitalize()}: tiene que ser mayor que cero.")
    return monto
