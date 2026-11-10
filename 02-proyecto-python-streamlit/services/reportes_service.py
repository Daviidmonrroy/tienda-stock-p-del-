"""Gastos y panel del dueño: ventas, costos, comisiones, gastos y ganancia neta.

Usa text() con parámetros (:desde, :hasta) para las agregaciones: SQL escrito a mano pero SIN concatenar texto,
así evitamos la inyección SQL.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select, text

from database.connection import session_scope
from models.operaciones import CategoriaGasto, Gasto
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso
from services.reglas_ventas import calcular_ganancia_neta
from utils import dinero
from utils.excepciones import ErrorDeValidacion
from utils.validaciones import validar_monto, validar_texto_corto

_RESUMEN = text("""
    SELECT COALESCE(SUM(v.total), 0)                       AS vendido,
           COALESCE(SUM(v.comision_total), 0)              AS comisiones,
           COALESCE(SUM(d.costo), 0)                       AS costos,
           COUNT(DISTINCT v.id)                            AS cantidad
    FROM ventas v
    LEFT JOIN (SELECT venta_id, SUM(costo_unitario * cantidad) AS costo FROM venta_detalle GROUP BY venta_id) d
           ON d.venta_id = v.id
    WHERE v.estado = 'confirmada' AND v.fecha >= :desde AND v.fecha < :hasta
""")
_POR_VENDEDOR = text("""
    SELECT u.nombre AS vendedor, COUNT(v.id) AS ventas, SUM(v.total) AS vendido, SUM(v.comision_total) AS comision
    FROM ventas v JOIN usuarios u ON u.id = v.vendedor_id
    WHERE v.estado = 'confirmada' AND v.fecha >= :desde AND v.fecha < :hasta
    GROUP BY u.nombre ORDER BY vendido DESC
""")
_POR_DIA = text("""
    SELECT DATE(v.fecha) AS dia, SUM(v.total) AS vendido
    FROM ventas v
    WHERE v.estado = 'confirmada' AND v.fecha >= :desde AND v.fecha < :hasta
    GROUP BY DATE(v.fecha) ORDER BY dia
""")


def _rango(desde: date, hasta: date) -> dict:
    if desde > hasta:
        raise ErrorDeValidacion("fechas", "La fecha 'desde' no puede ser posterior a 'hasta'.")
    return {"desde": datetime.combine(desde, datetime.min.time()),
            "hasta": datetime.combine(hasta + timedelta(days=1), datetime.min.time())}   # hasta inclusive


def crear_gasto(actor: UsuarioSesion, fecha: date, categoria: str, descripcion: str, monto) -> int:
    exigir_permiso(actor.rol, "gastos.gestionar")
    categoria = validar_texto_corto(categoria, "categoría")
    monto = validar_monto(monto, "monto")
    with session_scope() as s:
        cat = s.scalars(select(CategoriaGasto).where(CategoriaGasto.nombre == categoria)).first()
        if cat is None:
            cat = CategoriaGasto(nombre=categoria)
            s.add(cat)
            s.flush()
        g = Gasto(fecha=fecha, categoria_id=cat.id, descripcion=(descripcion or "").strip() or None,
                  monto=monto, usuario_id=actor.id)
        s.add(g)
        s.flush()
        return g.id


def listar_gastos(actor: UsuarioSesion, desde: date, hasta: date) -> list[dict]:
    exigir_permiso(actor.rol, "gastos.gestionar")
    with session_scope() as s:
        consulta = (select(Gasto.fecha, CategoriaGasto.nombre, Gasto.descripcion, Gasto.monto)
                    .join(CategoriaGasto, CategoriaGasto.id == Gasto.categoria_id)
                    .where(Gasto.fecha >= desde, Gasto.fecha <= hasta).order_by(Gasto.fecha.desc()))
        return [{"fecha": f, "categoría": c, "descripción": d or "", "monto": m} for f, c, d, m in s.execute(consulta)]


def panel(actor: UsuarioSesion, desde: date, hasta: date) -> dict:
    exigir_permiso(actor.rol, "reportes.ver")
    params = _rango(desde, hasta)
    with session_scope() as s:
        fila = s.execute(_RESUMEN, params).one()
        gastos = s.scalar(select(func.coalesce(func.sum(Gasto.monto), 0)).where(Gasto.fecha >= desde, Gasto.fecha <= hasta))
        vendedores = [dict(r._mapping) for r in s.execute(_POR_VENDEDOR, params)]
        dias = [dict(r._mapping) for r in s.execute(_POR_DIA, params)]
    vendido, costos, comisiones, gastos = (Decimal(str(x)) for x in (fila.vendido, fila.costos, fila.comisiones, gastos))
    return {"vendido": dinero.redondear(vendido), "costos": dinero.redondear(costos),
            "comisiones": dinero.redondear(comisiones), "gastos": dinero.redondear(gastos),
            "ganancia_neta": calcular_ganancia_neta(vendido, costos, comisiones, gastos),
            "cantidad_ventas": fila.cantidad, "por_vendedor": vendedores, "por_dia": dias}
