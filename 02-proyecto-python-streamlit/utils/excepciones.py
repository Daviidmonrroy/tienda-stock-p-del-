"""Excepciones propias del proyecto.

Concepto de clase: excepciones propias + raise.
- ErrorDeNegocio y sus hijas son errores ESPERADOS: la app los captura y muestra el mensaje al usuario.
- ConfiguracionFaltante es un error de arranque: sin configuración no tiene sentido seguir.
"""


class ErrorDeNegocio(Exception):
    """Base de los errores controlados. Su mensaje se puede mostrar al usuario."""


class ErrorDeValidacion(ErrorDeNegocio):
    """Un dato ingresado no cumple el formato o la longitud pedida."""

    def __init__(self, campo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.campo = campo


class EmailDuplicado(ErrorDeNegocio):
    """Ya existe un usuario con ese email."""


class CredencialesInvalidas(ErrorDeNegocio):
    """Email o clave incorrectos. El mensaje es el mismo en todos los casos para no dar pistas."""

    def __init__(self) -> None:
        super().__init__("Email o clave incorrectos.")


class CuentaBloqueada(ErrorDeNegocio):
    """Demasiados intentos fallidos de inicio de sesión."""


class PermisoDenegado(ErrorDeNegocio):
    """El rol del usuario no permite esta acción."""


class ConfiguracionFaltante(Exception):
    """Falta una variable de entorno o tiene un valor inválido."""
