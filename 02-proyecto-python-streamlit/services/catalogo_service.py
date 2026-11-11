"""Casos de uso del catálogo. Cada función recibe el actor (UsuarioSesion) y verifica permisos."""
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from database.connection import session_scope
from repositories import catalogo_repository as repo
from models.catalogo import Producto, Variante
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso, tiene_permiso
from services.reglas_catalogo import validar_precios
from utils.excepciones import ErrorDeValidacion, NoEncontrado
from utils.validaciones import (validar_color_hex, validar_entero_no_negativo, validar_sku,
                                validar_texto_corto)


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


def importar_planilla(actor: UsuarioSesion, filas: list[dict]) -> int:
    """Importa variantes desde una planilla validando todo antes de guardar.

    Cada fila representa una variante. Las filas con el mismo producto/categoría/marca
    se agrupan bajo un mismo producto. El stock inicial no se importa: debe entrar por
    Compras para que quede asentado en el libro de movimientos.
    """
    exigir_permiso(actor.rol, "catalogo.editar")
    if not filas:
        raise ErrorDeValidacion("planilla", "La planilla no tiene filas para importar.")

    try:
        with session_scope() as s:
            categorias = {c.nombre.casefold(): c.id for c in repo.listar_categorias(s)}
            marcas = {m.nombre.casefold(): m.id for m in repo.listar_marcas(s)}
            normalizadas = []
            errores = []
            skus_archivo = set()
            variantes_archivo = set()

            for numero, fila in enumerate(filas, start=2):
                try:
                    nombre = validar_texto_corto(fila.get("producto"), "producto", 2, 160)
                    categoria_nombre = validar_texto_corto(fila.get("categoria"), "categoría")
                    categoria_id = categorias.get(categoria_nombre.casefold())
                    if categoria_id is None:
                        raise ErrorDeValidacion("categoría", f"No existe la categoría '{categoria_nombre}'. Creala antes de importar.")
                    marca_nombre = str(fila.get("marca") or "").strip()
                    if marca_nombre:
                        marca_nombre = validar_texto_corto(marca_nombre, "marca")
                        marca_id = marcas.get(marca_nombre.casefold())
                        if marca_id is None:
                            raise ErrorDeValidacion("marca", f"No existe la marca '{marca_nombre}'. Creala antes de importar.")
                    else:
                        marca_id = None
                    sku = validar_sku(fila.get("sku"))
                    talle = validar_texto_corto(fila.get("talle") or "Único", "talle", 1, 20)
                    color = validar_texto_corto(fila.get("color") or "Único", "color", 1, 40)
                    color_hex_raw = str(fila.get("color_hex") or "").strip()
                    color_hex = validar_color_hex(color_hex_raw) if color_hex_raw else None
                    costo, minimo, lista, maximo = validar_precios(
                        fila.get("costo"), fila.get("precio_minimo"),
                        fila.get("precio_lista"), fila.get("precio_maximo")
                    )
                    stock_minimo = validar_entero_no_negativo(fila.get("stock_minimo"), "stock mínimo")
                    sku_key = sku.casefold()
                    variante_key = (nombre.casefold(), categoria_id, marca_id, talle.casefold(), color.casefold())
                    if sku_key in skus_archivo:
                        raise ErrorDeValidacion("sku", f"El SKU '{sku}' está repetido en la planilla.")
                    if variante_key in variantes_archivo:
                        raise ErrorDeValidacion("variante", f"Se repite el producto '{nombre}' con talle y color iguales.")
                    skus_archivo.add(sku_key)
                    variantes_archivo.add(variante_key)
                    normalizadas.append({
                        "nombre": nombre, "categoria_id": categoria_id, "marca_id": marca_id, "sku": sku,
                        "talle": talle, "color": color, "color_hex": color_hex, "costo": costo,
                        "minimo": minimo, "lista": lista, "maximo": maximo, "stock_minimo": stock_minimo,
                    })
                except (ErrorDeValidacion, TypeError, ValueError) as error:
                    mensaje = str(error) if isinstance(error, ErrorDeValidacion) else "Hay un dato con formato inválido."
                    errores.append(f"Fila {numero}: {mensaje}")

            if normalizadas:
                skus_existentes = set(s.scalars(
                    select(Variante.sku).where(Variante.sku.in_([r["sku"] for r in normalizadas]))
                ))
                for fila in normalizadas:
                    if fila["sku"] in skus_existentes:
                        errores.append(f"SKU {fila['sku']}: ya existe en el catálogo.")

            if errores:
                detalle = " ".join(errores[:8])
                if len(errores) > 8:
                    detalle += f" Y {len(errores) - 8} errores más."
                raise ErrorDeValidacion("planilla", "No se importó nada. " + detalle)

            grupos = {}
            for fila in normalizadas:
                clave = (fila["nombre"].casefold(), fila["categoria_id"], fila["marca_id"])
                grupos.setdefault(clave, []).append(fila)

            for grupo in grupos.values():
                primera = grupo[0]
                consulta = select(Producto).where(
                    Producto.nombre == primera["nombre"],
                    Producto.categoria_id == primera["categoria_id"],
                    Producto.marca_id == primera["marca_id"],
                )
                producto = s.scalar(consulta)
                if producto is None:
                    producto = repo.crear_producto(
                        s, nombre=primera["nombre"], categoria_id=primera["categoria_id"],
                        marca_id=primera["marca_id"]
                    )
                for fila in grupo:
                    repo.crear_variante(
                        s, producto_id=producto.id, sku=fila["sku"], talle=fila["talle"],
                        color=fila["color"], color_hex=fila["color_hex"], costo=fila["costo"],
                        precio_lista=fila["lista"], precio_minimo=fila["minimo"],
                        precio_maximo=fila["maximo"], stock_minimo=fila["stock_minimo"]
                    )
            return len(normalizadas)
    except IntegrityError as error:
        raise ErrorDeValidacion(
            "planilla",
            "No se importó nada: una variante ya existe (SKU o combinación de producto, talle y color)."
        ) from error

def actualizar_precios(actor: UsuarioSesion, variante_id: int, costo, minimo, lista, maximo) -> None:
    exigir_permiso(actor.rol, "catalogo.editar")
    costo, minimo, lista, maximo = validar_precios(costo, minimo, lista, maximo)
    with session_scope() as s:
        v = repo.buscar_variante(s, variante_id)
        if v is None:
            raise NoEncontrado("La variante no existe.")
        v.costo, v.precio_minimo, v.precio_lista, v.precio_maximo = costo, minimo, lista, maximo
