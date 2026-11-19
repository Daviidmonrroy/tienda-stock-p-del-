from utils.arranque import CLAVE_DEMO, EMAIL_DEMO, credenciales_admin
from utils.validaciones import validar_clave, validar_email


def test_valores_de_demo_cuando_no_hay_entorno():
    c = credenciales_admin({})
    assert (c.email, c.clave, c.rol) == (EMAIL_DEMO, CLAVE_DEMO, "admin")


def test_el_entorno_pisa_la_demo():
    c = credenciales_admin({"ADMIN_EMAIL": "dueno@vibra.com", "ADMIN_PASSWORD": "Otra-Clave-9"})
    assert (c.email, c.clave) == ("dueno@vibra.com", "Otra-Clave-9")


def test_la_demo_cumple_las_reglas():
    validar_clave(CLAVE_DEMO)
    validar_email(EMAIL_DEMO)
