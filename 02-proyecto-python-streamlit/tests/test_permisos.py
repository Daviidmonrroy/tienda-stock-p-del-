import pytest

from services.permisos import PERMISOS_POR_ROL, ROLES, exigir_permiso, tiene_permiso
from utils.excepciones import PermisoDenegado


def test_roles():
    assert set(ROLES) == {"admin", "empleado", "vendedor"}


def test_admin_tiene_todo():
    assert all(tiene_permiso("admin", p) for p in PERMISOS_POR_ROL["admin"])
    assert tiene_permiso("admin", "usuarios.gestionar")


@pytest.mark.parametrize("rol", ["empleado", "vendedor"])
def test_empleado_y_vendedor_no_ven_costos_ni_gestionan_usuarios(rol):
    for permiso in ["usuarios.gestionar", "costos.ver", "reportes.ver", "stock.ver_todo", "comisiones.liquidar"]:
        assert not tiene_permiso(rol, permiso)
        with pytest.raises(PermisoDenegado):
            exigir_permiso(rol, permiso)


def test_solo_el_vendedor_ve_sus_comisiones():
    assert tiene_permiso("vendedor", "comisiones.ver_propias")
    assert not tiene_permiso("empleado", "comisiones.ver_propias")


def test_rol_desconocido_no_tiene_nada():
    assert not tiene_permiso("hacker", "catalogo.ver")
    with pytest.raises(PermisoDenegado):
        exigir_permiso("hacker", "catalogo.ver")
