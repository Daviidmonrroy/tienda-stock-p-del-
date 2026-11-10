"""Acceso a datos del catálogo. Solo consultas; las reglas viven en los servicios."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models.catalogo import Categoria, Marca, Producto, Variante


def listar_categorias(s: Session) -> list[Categoria]:
    return list(s.scalars(select(Categoria).order_by(Categoria.nombre)))


def listar_marcas(s: Session) -> list[Marca]:
    return list(s.scalars(select(Marca).order_by(Marca.nombre)))


def crear_categoria(s: Session, nombre: str) -> Categoria:
    c = Categoria(nombre=nombre)
    s.add(c)
    s.flush()
    return c


def crear_marca(s: Session, nombre: str) -> Marca:
    m = Marca(nombre=nombre)
    s.add(m)
    s.flush()
    return m


def crear_producto(s: Session, **campos) -> Producto:
    p = Producto(**campos)
    s.add(p)
    s.flush()
    return p


def buscar_producto(s: Session, producto_id: int) -> Producto | None:
    return s.get(Producto, producto_id)


def listar_variantes(s: Session, solo_activas: bool = True) -> list[Variante]:
    consulta = select(Variante).options(joinedload(Variante.producto)).order_by(Variante.sku)
    if solo_activas:
        consulta = consulta.where(Variante.activa.is_(True))
    return list(s.scalars(consulta))


def buscar_variante(s: Session, variante_id: int) -> Variante | None:
    return s.get(Variante, variante_id)


def crear_variante(s: Session, **campos) -> Variante:
    v = Variante(**campos)
    s.add(v)
    s.flush()
    return v
