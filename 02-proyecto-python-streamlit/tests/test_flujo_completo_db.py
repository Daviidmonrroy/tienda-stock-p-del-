"""Flujo completo contra SQLite en memoria: catálogo -> compra -> transferencia -> venta -> anulación -> liquidación.
Necesita: pip install -r requirements.txt   (NO fue ejecutado por Claude: faltaban las librerías en su entorno)."""
from contextlib import contextmanager
from decimal import Decimal as D

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("bcrypt")

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import models  # noqa: E402,F401
from database.base import Base  # noqa: E402
from models.stock import MovimientoStock, StockActual  # noqa: E402
from services import (auth_service, catalogo_service, clientes_service, comisiones_service,  # noqa: E402
                      compras_service, reportes_service, stock_service, ventas_service, zona_service)
from utils.excepciones import ErrorDeNegocio, PermisoDenegado, PrecioFueraDeRango, StockInsuficiente  # noqa: E402

MODULOS = (auth_service, catalogo_service, clientes_service, comisiones_service, compras_service,
           reportes_service, stock_service, ventas_service, zona_service)


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

    for m in MODULOS:
        monkeypatch.setattr(m, "session_scope", scope)
    return Fabrica


@pytest.fixture()
def mundo(fabrica):
    """Admin, vendedor con mochila, un producto con 10 unidades en el local."""
    d = lambda email, rol, zona=None: auth_service.validar_datos_registro(
        "Persona Prueba", email, "clave-segura1", rol, zona, "")
    auth_service.registrar_usuario(d("admin@v.com", "admin"))
    admin = auth_service.iniciar_sesion("admin@v.com", "clave-segura1")
    zona = zona_service.crear_zona("Córdoba", admin)           # un vendedor necesita zona
    auth_service.registrar_usuario(d("vend@v.com", "vendedor", zona), actor=admin)
    vend = auth_service.iniciar_sesion("vend@v.com", "clave-segura1")
    local = stock_service.crear_ubicacion(admin, "Local", "local")
    mochila = stock_service.crear_ubicacion(admin, "Mochila Persona", "mochila", vend.id)
    cat = catalogo_service.crear_categoria(admin, "Palas")
    catalogo_service.crear_producto_con_variante(admin, nombre="Pala Control", categoria_id=cat, marca_id=None,
        sku="PAL-01", talle="Único", color="Negro", color_hex="#111111", costo="1000", minimo="1500",
        lista="2000", maximo="2500")
    variante_id = catalogo_service.listar_variantes(admin)[0].id
    prov = compras_service.crear_proveedor(admin, "Proveedor SA")
    compras_service.registrar_compra(admin, prov, local, [{"variante_id": variante_id, "cantidad": 10, "costo": "1000"}])
    comisiones_service.fijar_pct(admin, "10")
    return dict(admin=admin, vend=vend, local=local, mochila=mochila, vid=variante_id, F=fabrica)


def saldo(F, ubic, vid):
    with F() as s:
        fila = s.get(StockActual, (ubic, vid))
        return fila.cantidad if fila else 0


def test_vendedor_no_ve_costo(mundo):
    assert catalogo_service.listar_variantes(mundo["vend"])[0].costo is None
    assert catalogo_service.listar_variantes(mundo["admin"])[0].costo == D("1000.00")


def test_vendedor_no_puede_editar_catalogo(mundo):
    with pytest.raises(PermisoDenegado):
        catalogo_service.crear_categoria(mundo["vend"], "Hack")


def test_transferencia_y_stock_insuficiente(mundo):
    m = mundo
    stock_service.transferir(m["admin"], m["vid"], m["local"], m["mochila"], 4)
    assert saldo(m["F"], m["local"], m["vid"]) == 6 and saldo(m["F"], m["mochila"], m["vid"]) == 4
    with pytest.raises(StockInsuficiente):
        stock_service.transferir(m["admin"], m["vid"], m["local"], m["mochila"], 7)
    assert saldo(m["F"], m["local"], m["vid"]) == 6          # rollback: nada quedó a medias


def test_venta_completa_descuenta_stock_y_congela_comision(mundo):
    m = mundo
    stock_service.transferir(m["admin"], m["vid"], m["local"], m["mochila"], 4)
    vid_venta = ventas_service.registrar_venta(m["vend"], [{"variante_id": m["vid"], "cantidad": 2, "precio": "2000"}],
                                               pagos=[{"medio": "efectivo", "monto": "4000"}])
    assert saldo(m["F"], m["mochila"], m["vid"]) == 2
    ventas = ventas_service.listar_ventas(m["vend"])
    assert ventas[0]["comisión"] == D("400.00") and ventas[0]["estado pago"] == "pagada"
    comisiones_service.fijar_pct(m["admin"], "20")            # cambiar el % no altera ventas pasadas
    assert ventas_service.listar_ventas(m["vend"])[0]["comisión"] == D("400.00")
    ventas_service.anular_venta(m["admin"], vid_venta)
    assert saldo(m["F"], m["mochila"], m["vid"]) == 4


def test_precio_fuera_de_rango_no_toca_el_stock(mundo):
    m = mundo
    stock_service.transferir(m["admin"], m["vid"], m["local"], m["mochila"], 4)
    with pytest.raises(PrecioFueraDeRango):
        ventas_service.registrar_venta(m["vend"], [{"variante_id": m["vid"], "cantidad": 1, "precio": "100"}])
    assert saldo(m["F"], m["mochila"], m["vid"]) == 4


def test_fiado_exige_cliente_y_se_cobra_en_partes(mundo):
    m = mundo
    stock_service.transferir(m["admin"], m["vid"], m["local"], m["mochila"], 4)
    linea = [{"variante_id": m["vid"], "cantidad": 1, "precio": "2000"}]
    with pytest.raises(ErrorDeNegocio):
        ventas_service.registrar_venta(m["vend"], linea)
    cliente = clientes_service.crear_cliente(m["vend"], "Juan Pérez")
    venta = ventas_service.registrar_venta(m["vend"], linea, cliente_id=cliente,
                                           pagos=[{"medio": "efectivo", "monto": "500"}])
    assert ventas_service.registrar_cobro(m["vend"], venta, "transferencia", "1000") == "parcial"
    assert ventas_service.registrar_cobro(m["vend"], venta, "efectivo", "500") == "pagada"


def test_liquidacion_no_se_repite(mundo):
    m = mundo
    stock_service.transferir(m["admin"], m["vid"], m["local"], m["mochila"], 4)
    ventas_service.registrar_venta(m["vend"], [{"variante_id": m["vid"], "cantidad": 1, "precio": "2000"}],
                                   pagos=[{"medio": "efectivo", "monto": "2000"}])
    from datetime import date
    periodo = date.today().strftime("%Y-%m")
    assert comisiones_service.liquidar(m["admin"], m["vend"].id, periodo) == D("200.00")
    with pytest.raises(ErrorDeNegocio):
        comisiones_service.liquidar(m["admin"], m["vend"].id, periodo)
    assert comisiones_service.resumen(m["vend"], periodo)[0]["liquidada"] is True


def test_libro_de_movimientos_cuadra_con_el_saldo(mundo):
    m = mundo
    stock_service.transferir(m["admin"], m["vid"], m["local"], m["mochila"], 3)
    with m["F"]() as s:
        for ubic in (m["local"], m["mochila"]):
            suma = sum(x.cantidad for x in s.scalars(select(MovimientoStock).where(MovimientoStock.ubicacion_id == ubic)))
            assert suma == saldo(m["F"], ubic, m["vid"])


def test_panel_del_dueno(mundo):
    from datetime import date
    m = mundo
    stock_service.transferir(m["admin"], m["vid"], m["local"], m["mochila"], 4)
    ventas_service.registrar_venta(m["vend"], [{"variante_id": m["vid"], "cantidad": 2, "precio": "2000"}],
                                   pagos=[{"medio": "efectivo", "monto": "4000"}])
    reportes_service.crear_gasto(m["admin"], date.today(), "publicidad", "", "300")
    p = reportes_service.panel(m["admin"], date.today(), date.today())
    assert (p["vendido"], p["costos"], p["comisiones"], p["gastos"]) == (D("4000.00"), D("2000.00"), D("400.00"), D("300.00"))
    assert p["ganancia_neta"] == D("1300.00")
    with pytest.raises(PermisoDenegado):
        reportes_service.panel(m["vend"], date.today(), date.today())
