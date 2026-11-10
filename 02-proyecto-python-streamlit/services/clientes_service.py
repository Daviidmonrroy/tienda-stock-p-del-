"""Clientes compartidos entre todos los vendedores."""
from sqlalchemy import select

from database.connection import session_scope
from models.operaciones import Cliente
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso
from utils.validaciones import limpiar_texto, validar_telefono, validar_texto_corto


def crear_cliente(actor: UsuarioSesion, nombre: str, telefono: str = "") -> int:
    exigir_permiso(actor.rol, "clientes.gestionar")
    nombre = validar_texto_corto(nombre, "nombre", 2, 120)
    tel = validar_telefono(telefono) if limpiar_texto(telefono) else None
    with session_scope() as s:
        c = Cliente(nombre=nombre, telefono=tel)
        s.add(c)
        s.flush()
        return c.id


def listar_clientes(actor: UsuarioSesion) -> list[dict]:
    exigir_permiso(actor.rol, "clientes.gestionar")
    with session_scope() as s:
        return [{"id": c.id, "nombre": c.nombre, "teléfono": c.telefono or ""}
                for c in s.scalars(select(Cliente).order_by(Cliente.nombre))]
