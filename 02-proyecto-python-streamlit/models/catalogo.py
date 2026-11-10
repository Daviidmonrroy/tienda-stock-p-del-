"""Modelos del catálogo: categoría, marca, producto y variante (lo que realmente se vende)."""
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Categoria(Base):
    __tablename__ = "categorias"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)


class Marca(Base):
    __tablename__ = "marcas"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)


class Producto(Base):
    __tablename__ = "productos"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(160))
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"))
    marca_id: Mapped[Optional[int]] = mapped_column(ForeignKey("marcas.id"))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(default=True)

    categoria: Mapped["Categoria"] = relationship()
    marca: Mapped[Optional["Marca"]] = relationship()
    variantes: Mapped[list["Variante"]] = relationship(back_populates="producto")


class Variante(Base):
    __tablename__ = "variantes"
    __table_args__ = (
        UniqueConstraint("producto_id", "talle", "color", name="uq_variante"),
        CheckConstraint("precio_minimo <= precio_lista AND precio_lista <= precio_maximo",
                        name="ck_variante_precios"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    sku: Mapped[str] = mapped_column(String(40), unique=True)
    talle: Mapped[str] = mapped_column(String(20), default="Único")
    color: Mapped[str] = mapped_column(String(40), default="Único")
    color_hex: Mapped[Optional[str]] = mapped_column(String(7))
    costo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"))
    precio_lista: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    precio_minimo: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    precio_maximo: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    stock_minimo: Mapped[int] = mapped_column(default=0)
    activa: Mapped[bool] = mapped_column(default=True)

    producto: Mapped["Producto"] = relationship(back_populates="variantes")
