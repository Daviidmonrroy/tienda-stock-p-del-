"""Compras, clientes, ventas, cobros, comisiones y gastos."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (Date, DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

MEDIOS_PAGO = ("efectivo", "transferencia", "fiado")
ESTADOS_PAGO = ("pagada", "parcial", "pendiente")
ESTADOS_VENTA = ("confirmada", "anulada")
dinero = Numeric(12, 2)


class Configuracion(Base):
    """Pares clave/valor, ej. comision_vendedor_pct = '10'."""
    __tablename__ = "configuracion"
    clave: Mapped[str] = mapped_column(String(60), primary_key=True)
    valor: Mapped[str] = mapped_column(String(120))


class Proveedor(Base):
    __tablename__ = "proveedores"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(30))


class Compra(Base):
    __tablename__ = "compras"
    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"))
    ubicacion_id: Mapped[int] = mapped_column(ForeignKey("ubicaciones.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    total: Mapped[Decimal] = mapped_column(dinero)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    detalle: Mapped[list["CompraDetalle"]] = relationship(cascade="all, delete-orphan")


class CompraDetalle(Base):
    __tablename__ = "compra_detalle"
    id: Mapped[int] = mapped_column(primary_key=True)
    compra_id: Mapped[int] = mapped_column(ForeignKey("compras.id"))
    variante_id: Mapped[int] = mapped_column(ForeignKey("variantes.id"))
    cantidad: Mapped[int]
    costo_unitario: Mapped[Decimal] = mapped_column(dinero)


class Cliente(Base):
    """Los clientes se comparten entre todos los vendedores (decisión del dueño)."""
    __tablename__ = "clientes"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    telefono: Mapped[Optional[str]] = mapped_column(String(30))


class Venta(Base):
    __tablename__ = "ventas"
    id: Mapped[int] = mapped_column(primary_key=True)
    vendedor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)   # multitenant
    ubicacion_id: Mapped[int] = mapped_column(ForeignKey("ubicaciones.id"))
    cliente_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clientes.id"))
    descuento: Mapped[Decimal] = mapped_column(dinero, default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(dinero)
    comision_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))          # foto del % vigente
    comision_total: Mapped[Decimal] = mapped_column(dinero)
    estado_pago: Mapped[str] = mapped_column(Enum(*ESTADOS_PAGO, name="estado_pago"))
    pagado: Mapped[Decimal] = mapped_column(dinero, default=Decimal("0"))
    estado: Mapped[str] = mapped_column(Enum(*ESTADOS_VENTA, name="estado_venta"), default="confirmada")
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    lineas: Mapped[list["VentaDetalle"]] = relationship(cascade="all, delete-orphan")
    cobros: Mapped[list["Cobro"]] = relationship(cascade="all, delete-orphan")


class VentaDetalle(Base):
    """Cada línea congela costo, mínimo y comisión: cambiar el catálogo después no altera el historial."""
    __tablename__ = "venta_detalle"
    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"))
    variante_id: Mapped[int] = mapped_column(ForeignKey("variantes.id"))
    cantidad: Mapped[int]
    precio_unitario: Mapped[Decimal] = mapped_column(dinero)
    costo_unitario: Mapped[Decimal] = mapped_column(dinero)
    precio_minimo: Mapped[Decimal] = mapped_column(dinero)
    comision: Mapped[Decimal] = mapped_column(dinero)


class Cobro(Base):
    __tablename__ = "cobros"
    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id"), index=True)
    medio: Mapped[str] = mapped_column(Enum("efectivo", "transferencia", name="medio_cobro"))
    monto: Mapped[Decimal] = mapped_column(dinero)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Liquidacion(Base):
    """Comisiones de un vendedor en un mes. UNIQUE evita liquidar dos veces el mismo mes."""
    __tablename__ = "liquidaciones"
    __table_args__ = (UniqueConstraint("vendedor_id", "periodo", name="uq_liquidacion_periodo"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    vendedor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    periodo: Mapped[str] = mapped_column(String(7))      # "2026-11"
    total: Mapped[Decimal] = mapped_column(dinero)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class CategoriaGasto(Base):
    __tablename__ = "categorias_gasto"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)


class Gasto(Base):
    __tablename__ = "gastos"
    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias_gasto.id"))
    descripcion: Mapped[Optional[str]] = mapped_column(String(255))
    monto: Mapped[Decimal] = mapped_column(dinero)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
