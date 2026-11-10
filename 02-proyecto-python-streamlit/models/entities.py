"""Entidades de dominio: dataclasses inmutables que representan a los usuarios SIN depender de SQLAlchemy.

Los modelos del ORM (models/usuario.py) son para hablar con la base de datos; estas entidades son para pasar
datos entre capas (servicios -> vistas) sin arrastrar una sesión de base de datos abierta.
Conceptos de clase: @dataclass(frozen=True, slots=True).
"""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PerfilEntidad:
    usuario_id: int
    telefono: str | None = None


@dataclass(frozen=True, slots=True)
class UsuarioEntidad:
    id: int
    nombre: str
    email: str
    rol: str                    # admin | empleado | vendedor
    activo: bool = True
    zona_id: int | None = None
    perfil: PerfilEntidad | None = None


def usuario_a_entidad(usuario) -> UsuarioEntidad:
    """Convierte un models.usuario.Usuario (ORM) en una UsuarioEntidad. Hacerlo DENTRO de la sesión abierta."""
    perfil = usuario.perfil
    return UsuarioEntidad(
        id=usuario.id, nombre=usuario.nombre, email=usuario.email, rol=usuario.rol, activo=usuario.activo, zona_id=usuario.zona_id,
        perfil=PerfilEntidad(usuario.id, perfil.telefono) if perfil else None)
