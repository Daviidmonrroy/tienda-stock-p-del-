"""Casos de uso del catálogo. Cada función recibe el actor (UsuarioSesion) y verifica permisos."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from database.connection import session_scope
from repositories import catalogo_repository as repo
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso, tiene_permiso
from services.reglas_catalogo import validar_precios
from utils.excepciones import ErrorDeValidacion, NoEncontrado
from utils.validaciones import validar_color_hex, validar_sku, validar_texto_corto


@dataclass(frozen=True, slots=True)
class VarianteVista:
    """Lo que ve la pantalla. El costo es None si el rol no puede verlo (vendedor/empleado)."""
    id: int
    sku: str
    producto: str
    talle: str
    color: str
    color_hex: str | None
    costo: Decimal | None
    precio_lista: Decimal
    precio_minimo: Decimal
    precio_maximo: Decimal
    stock_minimo: int


def listar_variantes(actor: UsuarioSesion) -> list[VarianteVista]:
    exigir_permiso(actor.rol, "catalogo.ver")
    ve_costo = tiene_permiso(actor.rol, "costos.ver")
    with session_scope() as s:
        return [VarianteVista(v.id, v.sku, v.producto.nombre, v.talle, v.color, v.color_hex,
                              v.costo if ve_costo else None, v.precio_lista, v.precio_minimo,
                              v.precio_maximo, v.stock_minimo)
                for v in repo.listar_variantes(s)]


def crear_categoria(actor: UsuarioSesion, nombre: str):
    exigir_permiso(actor.rol, "catalogo.editar")
    nombre = validar_texto_corto(nombre, "categoría")
    try:
        with session_scope() as s:
            return repo.crear_categoria(s, nombre).id
    except IntegrityError as error:
        raise ErrorDeValidacion("categoría", "Esa categoría ya existe.") from error


def crear_marca(actor: UsuarioSesion, nombre: str):
    exigir_permiso(actor.rol, "catalogo.editar")
    nombre = validar_texto_corto(nombre, "marca")
    try:
        with session_scope() as s:
            return repo.crear_marca(s, nombre).id
    except IntegrityError as error:
        raise ErrorDeValidacion("marca", "Esa marca ya existe.") from error


def crear_producto_con_variante(actor: UsuarioSesion, *, nombre, categoria_id, marca_id, sku, talle,
                                color, color_hex, costo, minimo, lista, maximo, stock_minimo=0) -> int:
    """Crea producto + primera variante en UNA transacción: o se guardan las dos o ninguna."""
    exigir_permiso(actor.rol, "catalogo.editar")
    nombre = validar_texto_corto(nombre, "nombre", 2, 160)
    sku = validar_sku(sku)
    talle = validar_texto_corto(talle or "Único", "talle", 1, 20)
    color = validar_texto_corto(color or "Único", "color", 1, 40)
    color_hex = validar_color_hex(color_hex) if color_hex else None
    costo, minimo, lista, maximo = validar_precios(costo, minimo, lista, maximo)
    if not isinstance(stock_minimo, int) or stock_minimo < 0:
        raise ErrorDeValidacion("stock mínimo", "Stock mínimo: entero igual o mayor que cero.")
    try:
        with session_scope() as s:
            producto = repo.crear_producto(s, nombre=nombre, categoria_id=categoria_id, marca_id=marca_id)
            repo.crear_variante(s, producto_id=producto.id, sku=sku, talle=talle, color=color,
                                color_hex=color_hex, costo=costo, precio_lista=lista,
                                precio_minimo=minimo, precio_maximo=maximo, stock_minimo=stock_minimo)
            return producto.id
    except IntegrityError as error:
        raise ErrorDeValidacion("sku", "Ya existe una variante con ese código.") from error


def actualizar_precios(actor: UsuarioSesion, variante_id: int, costo, minimo, lista, maximo) -> None:
    exigir_permiso(actor.rol, "catalogo.editar")
    costo, minimo, lista, maximo = validar_precios(costo, minimo, lista, maximo)
    with session_scope() as s:
        v = repo.buscar_variante(s, variante_id)
        if v is None:
            raise NoEncontrado("La variante no existe.")
        v.costo, v.precio_minimo, v.precio_lista, v.precio_maximo = costo, minimo, lista, maximo
