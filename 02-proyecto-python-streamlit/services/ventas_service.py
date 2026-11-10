"""Registro de ventas: valida precios, descuenta stock, congela costos/comisión y registra cobros. Todo en UNA transacción:
si falla cualquier paso (ej. stock insuficiente) no queda nada a medias."""
from decimal import Decimal

from sqlalchemy import select

from database.connection import session_scope
from models.catalogo import Variante
from models.operaciones import Cliente, Cobro, Venta, VentaDetalle
from repositories import stock_repository
from services import stock_service
from services.auth_service import UsuarioSesion
from services.comisiones_service import obtener_pct
from services.permisos import exigir_permiso, tiene_permiso
from services.reglas_ventas import LineaEntrada, aplicar_cobro, calcular_venta, estado_de_pago
from utils.excepciones import ErrorDeNegocio, ErrorDeValidacion, NoEncontrado, PermisoDenegado
from utils.validaciones import validar_monto

MEDIOS_COBRO = ("efectivo", "transferencia")


def _ubicacion_de_venta(s, actor: UsuarioSesion, ubicacion_id: int | None) -> int:
    """El vendedor siempre vende desde SU mochila; admin/empleado eligen local o cancha."""
    if actor.rol == "vendedor":
        mochila = stock_repository.mochila_de(s, actor.id)
        if mochila is None:
            raise NoEncontrado("Todavía no tenés mochila asignada. Pedile al administrador que la cree.")
        return mochila.id
    if ubicacion_id is None or stock_repository.buscar_ubicacion(s, ubicacion_id) is None:
        raise ErrorDeValidacion("ubicación", "Elegí desde qué ubicación se vende.")
    return ubicacion_id


def registrar_venta(actor: UsuarioSesion, lineas: list[dict], *, ubicacion_id: int | None = None,
                    cliente_id: int | None = None, descuento=0, pagos: list[dict] | None = None) -> int:
    """lineas: [{'variante_id','cantidad','precio'}]; pagos: [{'medio','monto'}] (lo no pagado queda como fiado)."""
    exigir_permiso(actor.rol, "ventas.registrar")
    with session_scope() as s:
        ubic = _ubicacion_de_venta(s, actor, ubicacion_id)
        entradas = []
        for l in lineas:
            v = s.get(Variante, l["variante_id"])
            if v is None or not v.activa:
                raise NoEncontrado("Una de las variantes no existe o está inactiva.")
            entradas.append(LineaEntrada(v.id, l["cantidad"], l["precio"], v.costo, v.precio_minimo, v.precio_maximo))
        # La comisión solo aplica a vendedores; el % vigente se congela en la venta.
        pct = obtener_pct(s) if actor.rol == "vendedor" else Decimal("0")
        calc = calcular_venta(entradas, descuento, pct)

        pagado = Decimal("0.00")
        cobros = []
        for p in pagos or []:
            if p["medio"] not in MEDIOS_COBRO:
                raise ErrorDeValidacion("medio", "Medio de pago inválido.")
            m = validar_monto(p["monto"], "monto")
            pagado += m
            cobros.append((p["medio"], m))
        if pagado > calc.total:
            raise ErrorDeValidacion("pagos", "Los pagos superan el total de la venta.")
        if pagado < calc.total:     # queda deuda -> fiado: exige cliente identificado
            if cliente_id is None or s.get(Cliente, cliente_id) is None:
                raise ErrorDeValidacion("cliente", "Para dejar saldo a fiado hay que elegir un cliente.")

        venta = Venta(vendedor_id=actor.id, ubicacion_id=ubic, cliente_id=cliente_id, descuento=calc.descuento,
                      total=calc.total, comision_pct=pct, comision_total=calc.comision_total,
                      pagado=pagado, estado_pago=estado_de_pago(calc.total, pagado))
        s.add(venta)
        s.flush()
        for l in calc.lineas:
            venta.lineas.append(VentaDetalle(variante_id=l.variante_id, cantidad=l.cantidad,
                                             precio_unitario=l.precio_unitario, costo_unitario=l.costo_unitario,
                                             precio_minimo=l.precio_minimo, comision=l.comision))
            stock_service.mover(s, variante_id=l.variante_id, ubicacion_id=ubic, delta=-l.cantidad, tipo="venta",
                                usuario_id=actor.id, referencia=f"venta:{venta.id}")
        for medio, m in cobros:
            venta.cobros.append(Cobro(medio=medio, monto=m, usuario_id=actor.id))
        return venta.id


def _venta_accesible(s, actor: UsuarioSesion, venta_id: int) -> Venta:
    venta = s.get(Venta, venta_id)
    if venta is None or (venta.vendedor_id != actor.id and not tiene_permiso(actor.rol, "ventas.ver_todas")):
        raise NoEncontrado("La venta no existe.")        # no revelamos que existe si es de otro
    return venta


def registrar_cobro(actor: UsuarioSesion, venta_id: int, medio: str, monto) -> str:
    exigir_permiso(actor.rol, "ventas.registrar")
    if medio not in MEDIOS_COBRO:
        raise ErrorDeValidacion("medio", "Medio de pago inválido.")
    with session_scope() as s:
        venta = _venta_accesible(s, actor, venta_id)
        if venta.estado != "confirmada":
            raise ErrorDeNegocio("La venta está anulada.")
        venta.pagado, venta.estado_pago = aplicar_cobro(venta.total, venta.pagado, monto)
        venta.cobros.append(Cobro(medio=medio, monto=validar_monto(monto, "monto"), usuario_id=actor.id))
        return venta.estado_pago


def anular_venta(actor: UsuarioSesion, venta_id: int) -> None:
    """Devuelve el stock con movimientos de 'anulacion' (el libro no se edita) y marca la venta anulada."""
    exigir_permiso(actor.rol, "ventas.anular")
    with session_scope() as s:
        venta = s.get(Venta, venta_id, with_for_update=True)
        if venta is None:
            raise NoEncontrado("La venta no existe.")
        if venta.estado == "anulada":
            raise ErrorDeNegocio("La venta ya estaba anulada.")
        for l in venta.lineas:
            stock_service.mover(s, variante_id=l.variante_id, ubicacion_id=venta.ubicacion_id, delta=l.cantidad,
                                tipo="anulacion", usuario_id=actor.id, referencia=f"venta:{venta.id}")
        venta.estado = "anulada"


def listar_ventas(actor: UsuarioSesion, limite: int = 200) -> list[dict]:
    """Multitenant: sin 'ventas.ver_todas' solo se ven las propias. Nunca se devuelve el costo."""
    if not (tiene_permiso(actor.rol, "ventas.ver_todas") or tiene_permiso(actor.rol, "ventas.ver_propias")):
        exigir_permiso(actor.rol, "ventas.ver_propias")
    consulta = select(Venta).order_by(Venta.fecha.desc()).limit(limite)
    if not tiene_permiso(actor.rol, "ventas.ver_todas"):
        consulta = consulta.where(Venta.vendedor_id == actor.id)
    with session_scope() as s:
        return [{"id": v.id, "fecha": v.fecha, "total": v.total, "pagado": v.pagado, "estado pago": v.estado_pago,
                 "estado": v.estado, "comisión": v.comision_total} for v in s.scalars(consulta)]
