"""Stock por ubicación (local, cancha, mochila de vendedor) y su libro de movimientos."""
from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base

TIPOS_UBICACION = ("local", "cancha", "mochila")
TIPOS_MOVIMIENTO = ("compra", "venta", "ajuste", "transferencia_in", "transferencia_out", "anulacion")


class Ubicacion(Base):
    __tablename__ = "ubicaciones"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    tipo: Mapped[str] = mapped_column(Enum(*TIPOS_UBICACION, name="tipo_ubicacion"))
    # Una mochila pertenece a UN vendedor (multitenant por usuario); local y cancha no tienen dueño.
    usuario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuarios.id"), unique=True)


class StockActual(Base):
    """Saldo actual. Se actualiza en la MISMA transacción que el movimiento que lo causa."""
    __tablename__ = "stock_actual"
    __table_args__ = (CheckConstraint("cantidad >= 0", name="ck_stock_no_negativo"),)
    ubicacion_id: Mapped[int] = mapped_column(ForeignKey("ubicaciones.id"), primary_key=True)
    variante_id: Mapped[int] = mapped_column(ForeignKey("variantes.id"), primary_key=True)
    cantidad: Mapped[int] = mapped_column(default=0)


class MovimientoStock(Base):
    """Libro mayor: nunca se edita ni se borra. cantidad > 0 entra, < 0 sale."""
    __tablename__ = "movimientos_stock"
    id: Mapped[int] = mapped_column(primary_key=True)
    variante_id: Mapped[int] = mapped_column(ForeignKey("variantes.id"), index=True)
    ubicacion_id: Mapped[int] = mapped_column(ForeignKey("ubicaciones.id"), index=True)
    tipo: Mapped[str] = mapped_column(Enum(*TIPOS_MOVIMIENTO, name="tipo_movimiento"))
    cantidad: Mapped[int]
    referencia: Mapped[Optional[str]] = mapped_column(String(40))   # ej. "venta:12", "compra:3"
    nota: Mapped[Optional[str]] = mapped_column(String(255))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
