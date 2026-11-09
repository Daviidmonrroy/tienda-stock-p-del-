"""Gestión de usuarios por parte del administrador."""
from database.connection import session_scope
from repositories import usuario_repository
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso
from utils.excepciones import ErrorDeNegocio


def listar_usuarios(actor: UsuarioSesion) -> list[dict]:
    """Devuelve diccionarios simples. Nunca incluye el hash de la contraseña."""
    exigir_permiso(actor.rol, "usuarios.gestionar")
    with session_scope() as session:
        return [
            {"id": u.id, "nombre": u.nombre, "email": u.email, "rol": u.rol, "zona_id": u.zona_id,
             "activo": u.activo, "intentos_fallidos": u.intentos_fallidos}
            for u in usuario_repository.listar(session)
        ]


def cambiar_estado(usuario_id: int, activo: bool, actor: UsuarioSesion) -> None:
    exigir_permiso(actor.rol, "usuarios.gestionar")
    if usuario_id == actor.id and not activo:
        raise ErrorDeNegocio("No podés desactivar tu propio usuario.")
    with session_scope() as session:
        usuario = usuario_repository.buscar_por_id(session, usuario_id)
        if usuario is None:
            raise ErrorDeNegocio("El usuario no existe.")
        usuario.activo = activo


def desbloquear(usuario_id: int, actor: UsuarioSesion) -> None:
    exigir_permiso(actor.rol, "usuarios.gestionar")
    with session_scope() as session:
        usuario_repository.reiniciar_intentos(session, usuario_id)
