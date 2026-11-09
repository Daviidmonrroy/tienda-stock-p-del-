from database.connection import session_scope
from repositories import zona_repository
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso
from sqlalchemy.exc import IntegrityError
from utils import validaciones
from utils.excepciones import ErrorDeNegocio


def listar_zonas() -> list[dict]:
    with session_scope() as session:
        return [{"id": z.id, "nombre": z.nombre} for z in zona_repository.listar(session)]


def crear_zona(nombre: str, actor: UsuarioSesion) -> int:
    exigir_permiso(actor.rol, "usuarios.gestionar")
    nombre = validaciones.validar_longitud(validaciones.limpiar_texto(nombre), "zona", 2, 80)
    with session_scope() as session:
        try:
            return zona_repository.crear(session, nombre).id
        except IntegrityError as error:
            raise ErrorDeNegocio("Esa zona ya existe.") from error
