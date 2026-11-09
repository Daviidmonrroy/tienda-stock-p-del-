"""Autenticación y registro de usuarios.

Conceptos de clase: bcrypt (via utils.seguridad), excepciones propias, strip/lower, regex (via utils.validaciones),
flush() para obtener el id, IntegrityError, text() (en el repositorio), commit/rollback/close (en session_scope).
"""
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from database.connection import session_scope
from models.usuario import PerfilUsuario, Usuario
from repositories import usuario_repository
from services.permisos import ROLES, exigir_permiso
from utils import validaciones
from utils.excepciones import (CredencialesInvalidas, CuentaBloqueada, EmailDuplicado,
                               ErrorDeNegocio, ErrorDeValidacion)
from utils.seguridad import hash_password, verify_password

MAX_INTENTOS = 5


@dataclass(frozen=True, slots=True)
class UsuarioSesion:
    """Lo que se guarda en st.session_state. Es un dato simple (no un objeto ORM) para no depender de una sesión cerrada."""
    id: int
    nombre: str
    email: str
    rol: str
    zona_id: int | None


@dataclass(frozen=True, slots=True)
class DatosRegistro:
    nombre: str
    email: str
    clave: str
    rol: str
    zona_id: int | None
    telefono: str | None


def validar_datos_registro(nombre, email, clave, rol, zona_id=None, telefono=None) -> DatosRegistro:
    """Limpia y valida todo ANTES de tocar la base de datos. Función pura: se prueba sin MySQL."""
    nombre = validaciones.validar_nombre(nombre)
    email = validaciones.validar_email(validaciones.limpiar_email(email))
    clave = validaciones.validar_clave(clave)
    if rol not in ROLES:
        raise ErrorDeValidacion("rol", "Rol inválido.")
    if rol == "vendedor" and zona_id is None:
        raise ErrorDeValidacion("zona", "Un vendedor necesita una zona (ciudad).")
    return DatosRegistro(nombre, email, clave, rol, zona_id, validaciones.validar_telefono(telefono))


def registrar_usuario(datos: DatosRegistro, actor: UsuarioSesion | None = None) -> int:
    """Crea el usuario y su perfil en UNA transacción. Devuelve el id.

    actor=None solo se permite si todavía no existe ningún usuario (primer administrador).
    """
    with session_scope() as session:
        if actor is None:
            if usuario_repository.contar(session) > 0 or datos.rol != "admin":
                raise ErrorDeNegocio("Solo un administrador puede crear usuarios.")
        else:
            exigir_permiso(actor.rol, "usuarios.gestionar")

        usuario = Usuario(nombre=datos.nombre, email=datos.email, rol=datos.rol,
                          zona_id=datos.zona_id, password_hash=hash_password(datos.clave))
        session.add(usuario)
        try:
            session.flush()  # MySQL asigna el id; todavía no hay commit
        except IntegrityError as error:
            # session_scope hace el rollback al salir por la excepción.
            if "email" in str(error.orig).lower():
                raise EmailDuplicado("Ya existe un usuario con ese email.") from error
            raise ErrorDeNegocio("No se pudo guardar: revisá que la zona exista.") from error
        session.add(PerfilUsuario(usuario_id=usuario.id, telefono=datos.telefono))
        return usuario.id


def iniciar_sesion(email: str, clave: str) -> UsuarioSesion:
    """Valida credenciales. Las excepciones se lanzan FUERA del bloque with para que el commit
    del contador de intentos fallidos no se deshaga con el rollback."""
    email = validaciones.limpiar_email(email)
    if not email or not clave:
        raise CredencialesInvalidas()

    resultado: UsuarioSesion | None = None
    error: Exception | None = None
    with session_scope() as session:
        usuario = usuario_repository.buscar_por_email(session, email)
        if usuario is None or not usuario.activo:
            error = CredencialesInvalidas()
        elif usuario.intentos_fallidos >= MAX_INTENTOS:
            error = CuentaBloqueada("Cuenta bloqueada por demasiados intentos. Pedile a un administrador que la desbloquee.")
        elif not verify_password(clave, usuario.password_hash):
            usuario_repository.registrar_intento_fallido(session, usuario.id)
            error = CredencialesInvalidas()
        else:
            usuario_repository.reiniciar_intentos(session, usuario.id)
            resultado = UsuarioSesion(usuario.id, usuario.nombre, usuario.email, usuario.rol, usuario.zona_id)
    if error is not None:
        raise error
    return resultado
