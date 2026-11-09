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
