import pytest

from scripts.semilla import armar_credenciales, leer_claves
from utils.excepciones import ConfiguracionFaltante

ENV = {"ADMIN_EMAIL": "admin@vibra.com", "AUDITOR_EMAIL": "auditor@vibra.com"}


def test_leer_claves_ignora_comentarios_y_vacios():
    texto = "# comentario\n\nadmin=Clave-Uno-1\n  auditor = Clave-Dos-2  \n"
    assert leer_claves(texto) == {"admin": "Clave-Uno-1", "auditor": "Clave-Dos-2"}


@pytest.mark.parametrize("texto", ["admin", "root=Clave-1234", "admin="])
def test_leer_claves_invalido(texto):
    with pytest.raises(ConfiguracionFaltante):
        leer_claves(texto)


def test_armar_credenciales_admin_primero():
    lista = armar_credenciales(ENV, {"auditor": "b-Clave-2", "admin": "a-Clave-1"})
    assert [c.rol for c in lista] == ["admin", "auditor"]
    assert lista[0].email == "admin@vibra.com" and lista[0].clave == "a-Clave-1"


def test_falta_email_o_clave():
    with pytest.raises(ConfiguracionFaltante):
        armar_credenciales({"ADMIN_EMAIL": "a@b.com"}, {"admin": "x-Clave-1", "auditor": "y-Clave-2"})
    with pytest.raises(ConfiguracionFaltante):
        armar_credenciales(ENV, {"admin": "x-Clave-1"})
