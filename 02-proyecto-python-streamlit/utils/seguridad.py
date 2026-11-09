"""Hash y verificación de contraseñas con bcrypt.

Conceptos de clase: bcrypt, hash_password, verify_password.
- hash_password se usa al REGISTRAR o cambiar una clave.
- verify_password se usa al INICIAR SESIÓN.
bcrypt agrega un salt aleatorio y es lento a propósito. Nunca se guarda la clave en texto plano.
"""
import bcrypt

from utils.excepciones import ErrorDeValidacion

BYTES_MAX_CLAVE = 72  # bcrypt solo procesa los primeros 72 bytes


def hash_password(clave: str) -> str:
    datos = clave.encode("utf-8")
    if len(datos) > BYTES_MAX_CLAVE:
        raise ErrorDeValidacion("clave", f"Clave: máximo {BYTES_MAX_CLAVE} bytes.")
    return bcrypt.hashpw(datos, bcrypt.gensalt()).decode("utf-8")


def verify_password(clave: str, hash_guardado: str) -> bool:
    """True si la clave coincide con el hash. Un hash corrupto o una clave demasiado larga dan False."""
    datos = clave.encode("utf-8")
    if len(datos) > BYTES_MAX_CLAVE:
        return False
    try:
        return bcrypt.checkpw(datos, hash_guardado.encode("utf-8"))
    except ValueError:
        return False
