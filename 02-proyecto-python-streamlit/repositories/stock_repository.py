"""Consultas de stock. with_for_update() bloquea la fila para que dos ventas simultáneas no vendan la misma unidad."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.catalogo import Variante
from models.stock import MovimientoStock, StockActual, Ubicacion


def buscar_ubicacion(s: Session, ubicacion_id: int) -> Ubicacion | None:
    return s.get(Ubicacion, ubicacion_id)


def mochila_de(s: Session, usuario_id: int) -> Ubicacion | None:
    return s.scalars(select(Ubicacion).where(Ubicacion.usuario_id == usuario_id)).first()


def listar_ubicaciones(s: Session, usuario_id: int | None = None) -> list[Ubicacion]:
    consulta = select(Ubicacion).order_by(Ubicacion.nombre)
    if usuario_id is not None:      # vendedor: solo su mochila
        consulta = consulta.where(Ubicacion.usuario_id == usuario_id)
    return list(s.scalars(consulta))


def saldo_bloqueado(s: Session, ubicacion_id: int, variante_id: int) -> StockActual:
    fila = s.get(StockActual, (ubicacion_id, variante_id), with_for_update=True)
    if fila is None:
        fila = StockActual(ubicacion_id=ubicacion_id, variante_id=variante_id, cantidad=0)
        s.add(fila)
        s.flush()
    return fila


def agregar_movimiento(s: Session, **campos) -> MovimientoStock:
    m = MovimientoStock(**campos)
    s.add(m)
    return m


def listar_saldos(s: Session, ubicacion_ids: list[int] | None = None):
    """Devuelve filas (ubicación, variante, producto, cantidad)."""
    consulta = (select(Ubicacion.nombre, Variante.sku, Variante.talle, Variante.color,
                       Variante.stock_minimo, StockActual.cantidad, Variante.producto_id)
                .join(StockActual, StockActual.ubicacion_id == Ubicacion.id)
                .join(Variante, Variante.id == StockActual.variante_id)
                .order_by(Ubicacion.nombre, Variante.sku))
    if ubicacion_ids is not None:
        consulta = consulta.where(Ubicacion.id.in_(ubicacion_ids))
    return list(s.execute(consulta))
