"""Roles y permisos. Los permisos se verifican en los servicios, no solo ocultando botones en la vista."""
from utils.excepciones import PermisoDenegado

_TODOS = frozenset({
    "usuarios.gestionar", "catalogo.ver", "catalogo.editar", "costos.ver", "clientes.gestionar",
    "stock.ver_propio", "stock.ver_todo", "stock.ajustar", "compras.registrar",
    "ventas.registrar", "ventas.ver_propias", "ventas.ver_todas",
    "comisiones.ver_propias", "comisiones.liquidar", "reportes.ver", "gastos.gestionar",
})

PERMISOS_POR_ROL: dict[str, frozenset[str]] = {
    "admin": _TODOS,
    "empleado": frozenset({"catalogo.ver", "clientes.gestionar", "stock.ver_propio",
                           "ventas.registrar", "ventas.ver_propias"}),
    "vendedor": frozenset({"catalogo.ver", "clientes.gestionar", "stock.ver_propio",
                           "ventas.registrar", "ventas.ver_propias", "comisiones.ver_propias"}),
}
ROLES = tuple(PERMISOS_POR_ROL)


def tiene_permiso(rol: str, permiso: str) -> bool:
    return permiso in PERMISOS_POR_ROL.get(rol, frozenset())


def exigir_permiso(rol: str, permiso: str) -> None:
    """Lanza PermisoDenegado si el rol no tiene el permiso."""
    if not tiene_permiso(rol, permiso):
        raise PermisoDenegado("No tenés permiso para realizar esta acción.")
