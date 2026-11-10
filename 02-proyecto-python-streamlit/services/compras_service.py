"""Compras a proveedores: suman stock y actualizan el último costo."""
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from database.connection import session_scope
from models.catalogo import Variante
from models.operaciones import Compra, CompraDetalle, Proveedor
from services import stock_service
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso
from utils.excepciones import ErrorDeValidacion, NoEncontrado
from utils.validaciones import limpiar_texto, validar_cantidad, validar_monto, validar_telefono, validar_texto_corto


def crear_proveedor(actor: UsuarioSesion, nombre: str, telefono: str = "") -> int:
    exigir_permiso(actor.rol, "compras.registrar")
    nombre = validar_texto_corto(nombre, "nombre", 2, 120)
    tel = validar_telefono(telefono) if limpiar_texto(telefono) else None
    try:
        with session_scope() as s:
            p = Proveedor(nombre=nombre, telefono=tel)
            s.add(p)
            s.flush()
            return p.id
    except IntegrityError as error:
        raise ErrorDeValidacion("nombre", "Ese proveedor ya existe.") from error


def listar_proveedores(actor: UsuarioSesion) -> list[dict]:
    exigir_permiso(actor.rol, "compras.registrar")
    with session_scope() as s:
        return [{"id": p.id, "nombre": p.nombre} for p in s.scalars(select(Proveedor).order_by(Proveedor.nombre))]


def registrar_compra(actor: UsuarioSesion, proveedor_id: int, ubicacion_id: int, items: list[dict]) -> int:
    """items: [{'variante_id', 'cantidad', 'costo'}]. Compra + detalle + stock + movimientos en una transacción."""
    exigir_permiso(actor.rol, "compras.registrar")
    if not items:
        raise ErrorDeValidacion("compra", "Agregá al menos un producto.")
    limpios = [(i["variante_id"], validar_cantidad(i["cantidad"]), validar_monto(i["costo"], "costo")) for i in items]
    total = sum((c * q for _, q, c in limpios), Decimal("0.00"))
    with session_scope() as s:
        if s.get(Proveedor, proveedor_id) is None:
            raise NoEncontrado("El proveedor no existe.")
        compra = Compra(proveedor_id=proveedor_id, ubicacion_id=ubicacion_id, usuario_id=actor.id, total=total)
        s.add(compra)
        s.flush()
        for vid, cant, costo in limpios:
            variante = s.get(Variante, vid)
            if variante is None:
                raise NoEncontrado(f"La variante {vid} no existe.")
            compra.detalle.append(CompraDetalle(variante_id=vid, cantidad=cant, costo_unitario=costo))
            variante.costo = costo           # el último costo de compra pasa a ser el costo vigente
            stock_service.mover(s, variante_id=vid, ubicacion_id=ubicacion_id, delta=cant, tipo="compra",
                                usuario_id=actor.id, referencia=f"compra:{compra.id}")
        return compra.id
