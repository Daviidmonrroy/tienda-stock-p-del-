"""Pruebas del servicio de autenticación contra SQLite en memoria (no hace falta MySQL).
Necesitan SQLAlchemy y bcrypt instalados: pip install -r requirements.txt
"""
from contextlib import contextmanager

import pytest

pytest.importorskip("sqlalchemy", reason="SQLAlchemy no está instalado")
pytest.importorskip("bcrypt", reason="bcrypt no está instalado")

from sqlalchemy import create_engine, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import models  # noqa: E402,F401
from database.base import Base  # noqa: E402
from models.usuario import PerfilUsuario  # noqa: E402
from services import auth_service, usuario_service, zona_service  # noqa: E402
from utils.excepciones import (CredencialesInvalidas, CuentaBloqueada, EmailDuplicado,  # noqa: E402
                               ErrorDeNegocio, ErrorDeValidacion, PermisoDenegado)


@pytest.fixture()
def fabrica(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Fabrica = sessionmaker(bind=engine)

    @contextmanager
    def scope():
        session = Fabrica()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    for modulo in (auth_service, usuario_service, zona_service):
        monkeypatch.setattr(modulo, "session_scope", scope)
    return Fabrica


def datos(email="admin@vibra.com", rol="admin", zona=None, clave="clave-admin1", nombre="Dueño Vibra"):
    return auth_service.validar_datos_registro(nombre, email, clave, rol, zona, "+54 11 5555-1234")


@pytest.fixture()
def admin(fabrica):
    auth_service.registrar_usuario(datos())
    return auth_service.iniciar_sesion("admin@vibra.com", "clave-admin1")


def test_primer_admin_se_crea_sin_actor(fabrica):
    nuevo_id = auth_service.registrar_usuario(datos())
    assert nuevo_id == 1
    with fabrica() as s:
        perfil = s.scalars(select(PerfilUsuario)).one()
        assert perfil.usuario_id == nuevo_id and perfil.telefono == "+54 11 5555-1234"


def test_sin_actor_no_se_puede_crear_un_segundo_usuario(fabrica, admin):
    with pytest.raises(ErrorDeNegocio):
        auth_service.registrar_usuario(datos(email="otro@vibra.com"))


def test_sin_actor_solo_se_puede_crear_admin(fabrica):
    with pytest.raises(ErrorDeNegocio):
        auth_service.registrar_usuario(datos(rol="empleado"))


def test_email_duplicado(fabrica, admin):
    with pytest.raises(EmailDuplicado):
        auth_service.registrar_usuario(datos(email="  ADMIN@vibra.com "), admin)


def test_vendedor_requiere_zona(fabrica):
    with pytest.raises(ErrorDeValidacion):
        datos(email="v@vibra.com", rol="vendedor", zona=None)


def test_admin_crea_zona_y_vendedor(fabrica, admin):
    zona_id = zona_service.crear_zona("Córdoba", admin)
    with pytest.raises(ErrorDeNegocio):
        zona_service.crear_zona("Córdoba", admin)
    auth_service.registrar_usuario(datos("v@vibra.com", "vendedor", zona_id, "clave-vend1", "Ana Pérez"), admin)
    vendedor = auth_service.iniciar_sesion("v@vibra.com", "clave-vend1")
    assert vendedor.rol == "vendedor" and vendedor.zona_id == zona_id


def test_login_correcto(fabrica, admin):
    assert admin.rol == "admin" and admin.email == "admin@vibra.com"


def test_login_con_email_en_mayusculas_y_espacios(fabrica, admin):
    assert auth_service.iniciar_sesion("  ADMIN@Vibra.com ", "clave-admin1").id == admin.id


def test_login_incorrecto_mensaje_generico(fabrica, admin):
    with pytest.raises(CredencialesInvalidas):
        auth_service.iniciar_sesion("admin@vibra.com", "mala-clave1")
    with pytest.raises(CredencialesInvalidas):
        auth_service.iniciar_sesion("noexiste@vibra.com", "clave-admin1")
    with pytest.raises(CredencialesInvalidas):
        auth_service.iniciar_sesion("", "")


def test_bloqueo_tras_cinco_intentos_y_los_intentos_se_guardan(fabrica, admin):
    for _ in range(auth_service.MAX_INTENTOS):
        with pytest.raises(CredencialesInvalidas):
            auth_service.iniciar_sesion("admin@vibra.com", "mala-clave1")
    with pytest.raises(CuentaBloqueada):
        auth_service.iniciar_sesion("admin@vibra.com", "clave-admin1")   # aun con la clave correcta


def test_login_correcto_reinicia_el_contador(fabrica, admin):
    for _ in range(3):
        with pytest.raises(CredencialesInvalidas):
            auth_service.iniciar_sesion("admin@vibra.com", "mala-clave1")
    auth_service.iniciar_sesion("admin@vibra.com", "clave-admin1")
    assert usuario_service.listar_usuarios(admin)[0]["intentos_fallidos"] == 0


def test_desbloquear(fabrica, admin):
    for _ in range(auth_service.MAX_INTENTOS):
        with pytest.raises(CredencialesInvalidas):
            auth_service.iniciar_sesion("admin@vibra.com", "mala-clave1")
    usuario_service.desbloquear(admin.id, admin)
    assert auth_service.iniciar_sesion("admin@vibra.com", "clave-admin1").id == admin.id


def test_usuario_desactivado_no_entra(fabrica, admin):
    zona_id = zona_service.crear_zona("Rosario", admin)
    nuevo = auth_service.registrar_usuario(datos("e@vibra.com", "empleado", None, "clave-emp1", "Lu Gómez"), admin)
    usuario_service.cambiar_estado(nuevo, False, admin)
    with pytest.raises(CredencialesInvalidas):
        auth_service.iniciar_sesion("e@vibra.com", "clave-emp1")
    assert zona_id


def test_admin_no_puede_desactivarse_a_si_mismo(fabrica, admin):
    with pytest.raises(ErrorDeNegocio):
        usuario_service.cambiar_estado(admin.id, False, admin)


def test_no_admin_no_gestiona_usuarios(fabrica, admin):
    auth_service.registrar_usuario(datos("e@vibra.com", "empleado", None, "clave-emp1", "Lu Gómez"), admin)
    empleado = auth_service.iniciar_sesion("e@vibra.com", "clave-emp1")
    with pytest.raises(PermisoDenegado):
        usuario_service.listar_usuarios(empleado)
    with pytest.raises(PermisoDenegado):
        auth_service.registrar_usuario(datos("x@vibra.com", "empleado", None, "clave-emp2", "Otro Emp"), empleado)
    with pytest.raises(PermisoDenegado):
        zona_service.crear_zona("Salta", empleado)


def test_listado_nunca_expone_el_hash(fabrica, admin):
    for fila in usuario_service.listar_usuarios(admin):
        assert "password_hash" not in fila and "clave" not in fila
