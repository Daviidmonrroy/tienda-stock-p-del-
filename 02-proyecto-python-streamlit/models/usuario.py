"""Usuarios del sistema y su perfil (relación 1 a 1).

Conceptos de clase: relaciones ORM, claves primarias y foráneas, UniqueConstraint con __table_args__.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("email", name="uq_usuarios_email"),)  # tupla: la coma final es obligatoria

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[str] = mapped_column(Enum("admin", "empleado", "vendedor", "auditor", name="rol_usuario"))
    zona_id: Mapped[Optional[int]] = mapped_column(ForeignKey("zonas.id"), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    perfil: Mapped[Optional["PerfilUsuario"]] = relationship(
        back_populates="usuario", uselist=False, cascade="all, delete-orphan"
    )


class PerfilUsuario(Base):
    __tablename__ = "perfiles_usuario"
    __table_args__ = (UniqueConstraint("usuario_id", name="uq_perfil_usuario"),)  # esto hace que sea 1 a 1

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    usuario: Mapped[Usuario] = relationship(back_populates="perfil")
