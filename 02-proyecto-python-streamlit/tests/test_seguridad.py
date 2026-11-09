import pytest

pytest.importorskip("bcrypt", reason="bcrypt no está instalado: pip install -r requirements.txt")

from utils.excepciones import ErrorDeValidacion  # noqa: E402
from utils.seguridad import hash_password, verify_password  # noqa: E402


def test_hash_y_verificacion():
    h = hash_password("clave-segura-1")
    assert h != "clave-segura-1"
    assert h.startswith("$2")
    assert verify_password("clave-segura-1", h)
    assert not verify_password("otra-clave-1", h)


def test_el_salt_hace_distintos_a_dos_hashes_de_la_misma_clave():
    assert hash_password("misma-clave-1") != hash_password("misma-clave-1")


def test_clave_demasiado_larga():
    with pytest.raises(ErrorDeValidacion):
        hash_password("a" * 73)
    assert verify_password("a" * 73, hash_password("a" * 72)) is False


def test_hash_corrupto_da_false():
    assert verify_password("x", "no-es-un-hash") is False
