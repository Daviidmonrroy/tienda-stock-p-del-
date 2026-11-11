"""Importación de variantes desde planilla, contra SQLite en memoria.
Necesita SQLAlchemy (pip install -r requirements.txt). NO fue ejecutado por Claude: faltaban las librerías en su entorno."""
from contextlib import contextmanager

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine, func, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import models  # noqa: E402,F401
from database.base import Base  # noqa: E402
from models.catalogo import Producto, Variante  # noqa: E402
from services import catalogo_service  # noqa: E402
from services.auth_service import UsuarioSesion  # noqa: E402
from utils.excepciones import ErrorDeValidacion, PermisoDenegado  # noqa: E402

ADMIN = UsuarioSesion(1, "Admin", "a@v.com", "admin", None)
VENDEDOR = UsuarioSesion(2, "Vende", "v@v.com", "vendedor", 1)


@pytest.fixture()
def fabrica(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Fabrica = sessionmaker(bind=engine)

    @contextmanager
    def scope():
        s = Fabrica()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    monkeypatch.setattr(catalogo_service, "session_scope", scope)
    catalogo_service.crear_categoria(ADMIN, "Palas")
    catalogo_service.crear_marca(ADMIN, "Bullpadel")
    return Fabrica


def fila(sku="PAL-01", producto="Pala Control", talle="Único", color="Negro", **extra):
    base = {"producto": producto, "categoria": "palas", "marca": "BULLPADEL", "sku": sku, "talle": talle,
            "color": color, "color_hex": "#111111", "costo": "1000", "precio_minimo": "1500",
            "precio_lista": "2000", "precio_maximo": "2500", "stock_minimo": 2}
    base.update(extra)
    return base


def contar(F):
    with F() as s:
        return s.scalar(select(func.count(Producto.id))), s.scalar(select(func.count(Variante.id)))


def test_importa_y_agrupa_variantes_bajo_un_producto(fabrica):
    filas = [fila("PAL-01", color="Negro"), fila("PAL-02", color="Rojo"), fila("ZAP-01", producto="Zapatilla X")]
    assert catalogo_service.importar_planilla(ADMIN, filas) == 3
    assert contar(fabrica) == (2, 3)          # 2 productos, 3 variantes


def test_celda_vacia_de_stock_minimo_vale_cero(fabrica):
    catalogo_service.importar_planilla(ADMIN, [fila(stock_minimo=None), fila("PAL-02", color="Rojo", stock_minimo="")])
    with fabrica() as s:
        assert {v.stock_minimo for v in s.scalars(select(Variante))} == {0}


def test_si_una_fila_falla_no_se_importa_nada(fabrica):
    filas = [fila("PAL-01"), fila("PAL-02", color="Rojo", precio_minimo="3000")]   # mínimo > lista
    with pytest.raises(ErrorDeValidacion, match="Fila 3"):
        catalogo_service.importar_planilla(ADMIN, filas)
    assert contar(fabrica) == (0, 0)


def test_sku_repetido_en_la_planilla(fabrica):
    with pytest.raises(ErrorDeValidacion, match="repetido"):
        catalogo_service.importar_planilla(ADMIN, [fila("PAL-01"), fila("PAL-01", color="Rojo")])
    assert contar(fabrica) == (0, 0)


def test_sku_que_ya_existe_en_el_catalogo(fabrica):
    catalogo_service.importar_planilla(ADMIN, [fila("PAL-01")])
    with pytest.raises(ErrorDeValidacion, match="ya existe"):
        catalogo_service.importar_planilla(ADMIN, [fila("PAL-01", color="Rojo")])
    assert contar(fabrica) == (1, 1)


def test_categoria_inexistente(fabrica):
    with pytest.raises(ErrorDeValidacion, match="No existe la categoría"):
        catalogo_service.importar_planilla(ADMIN, [fila(categoria="Inexistente")])


def test_planilla_vacia_y_permiso(fabrica):
    with pytest.raises(ErrorDeValidacion):
        catalogo_service.importar_planilla(ADMIN, [])
    with pytest.raises(PermisoDenegado):
        catalogo_service.importar_planilla(VENDEDOR, [fila()])
