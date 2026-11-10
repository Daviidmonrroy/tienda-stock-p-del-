import pytest

from config.settings import Settings
from dataclasses import FrozenInstanceError
from utils.excepciones import ConfiguracionFaltante

BASE = {"DB_NAME": "vibra", "DB_USER": "vibra", "DB_PASSWORD": "clave"}


def test_valores_por_defecto():
    s = Settings.desde_entorno(dict(BASE))
    assert (s.db_host, s.db_port, s.sql_echo) == ("127.0.0.1", 3306, False)


@pytest.mark.parametrize("faltante", ["DB_NAME", "DB_USER", "DB_PASSWORD"])
def test_variable_obligatoria_faltante(faltante):
    env = dict(BASE)
    del env[faltante]
    with pytest.raises(ConfiguracionFaltante, match=faltante):
        Settings.desde_entorno(env)


def test_variable_vacia_cuenta_como_faltante():
    with pytest.raises(ConfiguracionFaltante):
        Settings.desde_entorno({**BASE, "DB_PASSWORD": "   "})


def test_puerto_invalido():
    with pytest.raises(ConfiguracionFaltante):
        Settings.desde_entorno({**BASE, "DB_PORT": "abc"})


@pytest.mark.parametrize("valor,esperado", [("true", True), ("TRUE", True), ("1", True), ("false", False), ("", False)])
def test_sql_echo(valor, esperado):
    assert Settings.desde_entorno({**BASE, "SQL_ECHO": valor}).sql_echo is esperado


def test_url_codifica_caracteres_especiales_de_la_clave():
    s = Settings.desde_entorno({**BASE, "DB_PASSWORD": "p@ss:w/rd", "DB_PORT": "3307"})
    assert s.url_base_de_datos == "mysql+pymysql://vibra:p%40ss%3Aw%2Frd@127.0.0.1:3307/vibra"


def test_es_inmutable():
    s = Settings.desde_entorno(dict(BASE))
    with pytest.raises(FrozenInstanceError):
        s.db_port = 1
    # Agregar un atributo que no existe: en Python 3.11 con slots+frozen lanza TypeError; en 3.12+ FrozenInstanceError.
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        s.nuevo = 1


def test_modo_sqlite_no_pide_usuario_ni_clave():
    s = Settings.desde_entorno({"DB_ENGINE": "sqlite"})
    assert s.db_engine == "sqlite" and s.url_base_de_datos == "sqlite:///vibra_demo.db"


def test_motor_invalido():
    with pytest.raises(ConfiguracionFaltante, match="DB_ENGINE"):
        Settings.desde_entorno({**BASE, "DB_ENGINE": "oracle"})


def test_por_defecto_sigue_siendo_mysql():
    assert Settings.desde_entorno(dict(BASE)).db_engine == "mysql"
