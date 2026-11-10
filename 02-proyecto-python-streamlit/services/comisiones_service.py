"""Porcentaje global de comisión y liquidación mensual por vendedor."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from database.connection import session_scope
from models.operaciones import Configuracion, Liquidacion, Venta
from models.usuario import Usuario
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso, tiene_permiso
from services.reglas_ventas import limites_del_mes
from utils import dinero
from utils.excepciones import ErrorDeNegocio, ErrorDeValidacion, NoEncontrado

CLAVE_PCT = "comision_vendedor_pct"


def obtener_pct(s) -> Decimal:
    fila = s.get(Configuracion, CLAVE_PCT)
    return Decimal(fila.valor) if fila else Decimal("0")


def pct_actual(actor: UsuarioSesion) -> Decimal:
    exigir_permiso(actor.rol, "catalogo.ver")
    with session_scope() as s:
        return obtener_pct(s)


def fijar_pct(actor: UsuarioSesion, pct) -> Decimal:
    """Solo admin. Las ventas ya hechas conservan el % con el que se hicieron (foto en cada venta)."""
    exigir_permiso(actor.rol, "comisiones.liquidar")
    p = dinero.a_decimal(pct)
    if not (Decimal("0") <= p <= Decimal("100")):
        raise ErrorDeValidacion("comisión", "El porcentaje tiene que estar entre 0 y 100.")
    with session_scope() as s:
        fila = s.get(Configuracion, CLAVE_PCT)
        if fila is None:
            s.add(Configuracion(clave=CLAVE_PCT, valor=str(p)))
        else:
            fila.valor = str(p)
    return p


def resumen(actor: UsuarioSesion, periodo: str) -> list[dict]:
    """Comisión por vendedor en el mes. El vendedor solo ve la suya (multitenant)."""
    if not (tiene_permiso(actor.rol, "comisiones.liquidar") or tiene_permiso(actor.rol, "comisiones.ver_propias")):
        exigir_permiso(actor.rol, "comisiones.ver_propias")
    desde, hasta = limites_del_mes(periodo)
    consulta = (select(Usuario.id, Usuario.nombre, func.count(Venta.id), func.coalesce(func.sum(Venta.total), 0),
                       func.coalesce(func.sum(Venta.comision_total), 0))
                .join(Venta, Venta.vendedor_id == Usuario.id)
                .where(Venta.estado == "confirmada", Venta.fecha >= desde, Venta.fecha < hasta)
                .group_by(Usuario.id, Usuario.nombre).order_by(Usuario.nombre))
    if not tiene_permiso(actor.rol, "comisiones.liquidar"):
        consulta = consulta.where(Usuario.id == actor.id)
    with session_scope() as s:
        liquidados = {l.vendedor_id for l in s.scalars(select(Liquidacion).where(Liquidacion.periodo == periodo))}
        return [{"vendedor_id": i, "vendedor": n, "ventas": c, "vendido": dinero.redondear(Decimal(t)),
                 "comisión": dinero.redondear(Decimal(k)), "liquidada": i in liquidados}
                for i, n, c, t, k in s.execute(consulta)]


def liquidar(actor: UsuarioSesion, vendedor_id: int, periodo: str) -> Decimal:
    """Registra el pago del mes. UNIQUE(vendedor, período) impide liquidar dos veces."""
    exigir_permiso(actor.rol, "comisiones.liquidar")
    desde, hasta = limites_del_mes(periodo)
    try:
        with session_scope() as s:
            if s.get(Usuario, vendedor_id) is None:
                raise NoEncontrado("El vendedor no existe.")
            total = s.scalar(select(func.coalesce(func.sum(Venta.comision_total), 0)).where(
                Venta.vendedor_id == vendedor_id, Venta.estado == "confirmada",
                Venta.fecha >= desde, Venta.fecha < hasta))
            total = dinero.redondear(Decimal(total))
            s.add(Liquidacion(vendedor_id=vendedor_id, periodo=periodo, total=total))
            s.flush()
            return total
    except IntegrityError as error:
        raise ErrorDeNegocio("Ese mes ya está liquidado para ese vendedor.") from error
