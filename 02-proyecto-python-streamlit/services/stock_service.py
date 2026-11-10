"""Stock: cada cambio escribe un movimiento (libro) y actualiza el saldo en la MISMA transacción."""
from sqlalchemy.exc import IntegrityError

from database.connection import session_scope
from models.stock import TIPOS_UBICACION, Ubicacion
from models.usuario import Usuario
from repositories import stock_repository as repo
from services.auth_service import UsuarioSesion
from services.permisos import exigir_permiso, tiene_permiso
from utils.excepciones import ErrorDeValidacion, NoEncontrado, StockInsuficiente
from utils.validaciones import validar_cantidad, validar_texto_corto


def mover(s, *, variante_id, ubicacion_id, delta, tipo, usuario_id, referencia=None, nota=None) -> int:
    """Núcleo del stock. delta > 0 entra, < 0 sale. Lanza StockInsuficiente si el saldo quedaría negativo.
    Se usa dentro de otras transacciones (ventas, compras), por eso recibe la sesión y NO hace commit."""
    saldo = repo.saldo_bloqueado(s, ubicacion_id, variante_id)
    nuevo = saldo.cantidad + delta
    if nuevo < 0:
        raise StockInsuficiente(f"Stock insuficiente: hay {saldo.cantidad} y se piden {-delta}.")
    saldo.cantidad = nuevo
    repo.agregar_movimiento(s, variante_id=variante_id, ubicacion_id=ubicacion_id, tipo=tipo, cantidad=delta,
                            referencia=referencia, nota=nota, usuario_id=usuario_id)
    return nuevo


def crear_ubicacion(actor: UsuarioSesion, nombre: str, tipo: str, vendedor_id: int | None = None) -> int:
    exigir_permiso(actor.rol, "ubicaciones.gestionar")
    nombre = validar_texto_corto(nombre, "nombre")
    if tipo not in TIPOS_UBICACION:
        raise ErrorDeValidacion("tipo", "Tipo de ubicación inválido.")
    if (tipo == "mochila") != (vendedor_id is not None):
        raise ErrorDeValidacion("tipo", "Solo las mochilas tienen vendedor, y toda mochila necesita uno.")
    try:
        with session_scope() as s:
            if vendedor_id is not None and s.get(Usuario, vendedor_id) is None:
                raise NoEncontrado("El vendedor no existe.")
            u = Ubicacion(nombre=nombre, tipo=tipo, usuario_id=vendedor_id)
            s.add(u)
            s.flush()
            return u.id
    except IntegrityError as error:
        raise ErrorDeValidacion("nombre", "Ya existe esa ubicación (o ese vendedor ya tiene mochila).") from error


def listar_ubicaciones(actor: UsuarioSesion) -> list[dict]:
    solo_propias = not tiene_permiso(actor.rol, "stock.ver_todo")
    with session_scope() as s:
        return [{"id": u.id, "nombre": u.nombre, "tipo": u.tipo}
                for u in repo.listar_ubicaciones(s, actor.id if solo_propias else None)]


def listar_stock(actor: UsuarioSesion) -> list[dict]:
    """Multitenant: quien no tiene 'stock.ver_todo' solo ve SU mochila."""
    exigir_permiso(actor.rol, "stock.ver_propio")
    solo_propias = not tiene_permiso(actor.rol, "stock.ver_todo")
    with session_scope() as s:
        ids = [u.id for u in repo.listar_ubicaciones(s, actor.id if solo_propias else None)]
        filas = repo.listar_saldos(s, ids)
    return [{"ubicación": n, "código": sku, "talle": t, "color": c, "cantidad": cant,
             "stock mínimo": minimo, "bajo mínimo": cant <= minimo}
            for n, sku, t, c, minimo, cant, _ in filas]


def ajustar(actor: UsuarioSesion, variante_id: int, ubicacion_id: int, nueva_cantidad: int, nota: str) -> int:
    """Corrige el stock a un valor contado (inventario). Queda registrado el motivo."""
    exigir_permiso(actor.rol, "stock.ajustar")
    if isinstance(nueva_cantidad, bool) or not isinstance(nueva_cantidad, int) or nueva_cantidad < 0:
        raise ErrorDeValidacion("cantidad", "La cantidad contada debe ser un entero igual o mayor que cero.")
    nota = validar_texto_corto(nota, "motivo", 3, 255)
    with session_scope() as s:
        actual = repo.saldo_bloqueado(s, ubicacion_id, variante_id).cantidad
        if nueva_cantidad == actual:
            return actual
        return mover(s, variante_id=variante_id, ubicacion_id=ubicacion_id, delta=nueva_cantidad - actual,
                     tipo="ajuste", usuario_id=actor.id, nota=nota)


def transferir(actor: UsuarioSesion, variante_id: int, origen_id: int, destino_id: int, cantidad: int) -> None:
    """Mueve stock entre ubicaciones (ej. local -> mochila de un vendedor). Salida y entrada: todo o nada."""
    exigir_permiso(actor.rol, "stock.ajustar")
    cantidad = validar_cantidad(cantidad)
    if origen_id == destino_id:
        raise ErrorDeValidacion("destino", "El origen y el destino tienen que ser distintos.")
    with session_scope() as s:
        for uid in (origen_id, destino_id):
            if repo.buscar_ubicacion(s, uid) is None:
                raise NoEncontrado("La ubicación no existe.")
        mover(s, variante_id=variante_id, ubicacion_id=origen_id, delta=-cantidad, tipo="transferencia_out",
              usuario_id=actor.id, referencia=f"hacia:{destino_id}")
        mover(s, variante_id=variante_id, ubicacion_id=destino_id, delta=cantidad, tipo="transferencia_in",
              usuario_id=actor.id, referencia=f"desde:{origen_id}")
