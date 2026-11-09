import pytest

from utils import validaciones as v
from utils.excepciones import ErrorDeValidacion


def test_limpiar_email_quita_espacios_y_pasa_a_minusculas():
    assert v.limpiar_email("   David@Gmail.COM  ") == "david@gmail.com"
    assert v.limpiar_email(None) == ""


@pytest.mark.parametrize("email", ["david@gmail.com", "a.b+c@sub.dominio.com.ar", "x_y%z@mail.io"])
def test_emails_validos(email):
    assert v.validar_email(email) == email


@pytest.mark.parametrize("email", [
    "", "david", "david@gmail", "@gmail.com", "david@@gmail.com", "da vid@gmail.com",
    ".david@gmail.com", "david.@gmail.com", "da..vid@gmail.com", "david@-gmail.com",
    "david@gmail..com", "david@gmail.c", "a" * 161 + "@x.com",
])
def test_emails_invalidos(email):
    with pytest.raises(ErrorDeValidacion):
        v.validar_email(email)


def test_validar_longitud():
    assert v.validar_longitud("abc", "campo", 2, 5) == "abc"
    with pytest.raises(ErrorDeValidacion):
        v.validar_longitud("a", "campo", 2, 5)
    with pytest.raises(ErrorDeValidacion):
        v.validar_longitud("abcdef", "campo", 2, 5)


@pytest.mark.parametrize("nombre", ["Ana", "José Luis", "O'Brien", "María-José", "  Lu  "])
def test_nombres_validos(nombre):
    assert v.validar_nombre(nombre) == nombre.strip()


@pytest.mark.parametrize("nombre", ["", "A", "12345", "Ana <script>", "-Ana"])
def test_nombres_invalidos(nombre):
    with pytest.raises(ErrorDeValidacion):
        v.validar_nombre(nombre)


def test_clave_valida_e_invalidas():
    assert v.validar_clave("abcdefg1") == "abcdefg1"
    for mala in [None, "", "abc1", "abcdefgh", "12345678"]:
        with pytest.raises(ErrorDeValidacion):
            v.validar_clave(mala)


def test_clave_maxima_72_bytes():
    assert v.validar_clave("a" * 71 + "1")  # 72 bytes
    with pytest.raises(ErrorDeValidacion):
        v.validar_clave("a" * 72 + "1")  # 73 bytes
    with pytest.raises(ErrorDeValidacion):
        v.validar_clave("ñ" * 40 + "1")   # 40 caracteres pero 81 bytes


def test_clave_no_se_limpia_con_strip():
    assert v.validar_clave("  abcdef1 ") == "  abcdef1 "


def test_color_hex():
    assert v.validar_color_hex("#f03a37") == "#F03A37"
    assert v.validar_color_hex("") is None
    assert v.validar_color_hex(None) is None
    for malo in ["#fff", "F03A37", "#GGGGGG", "#F03A37F", "rojo"]:
        with pytest.raises(ErrorDeValidacion):
            v.validar_color_hex(malo)


def test_telefono():
    assert v.validar_telefono("+54 9 11 1234-5678") == "+54 9 11 1234-5678"
    assert v.validar_telefono(" ") is None
    with pytest.raises(ErrorDeValidacion):
        v.validar_telefono("abc")
