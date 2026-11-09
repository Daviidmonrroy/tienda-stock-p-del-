"""Crea el primer usuario administrador desde la consola.  Ejecutar desde la carpeta del proyecto:
    python -m scripts.crear_admin

Conceptos de clase: getpass (clave oculta en consola), if __name__ == "__main__", SystemExit,
excepciones controladas. Esto es un script de consola: por eso acá SÍ corresponde getpass.
"""
from getpass import getpass

from config.settings import obtener_settings
from services import auth_service
from utils.excepciones import ConfiguracionFaltante, ErrorDeNegocio


def main() -> None:
    try:
        obtener_settings()
    except ConfiguracionFaltante as error:
        raise SystemExit(f"Error de configuración: {error}") from error

    nombre = input("Nombre y apellido: ")
    email = input("Email: ")
    clave = getpass("Clave (no se muestra): ")
    repetida = getpass("Repetí la clave: ")
    if clave != repetida:
        raise SystemExit("Las claves no coinciden.")
    try:
        datos = auth_service.validar_datos_registro(nombre, email, clave, "admin")
        nuevo_id = auth_service.registrar_usuario(datos)   # actor=None: solo vale si no hay usuarios
    except ErrorDeNegocio as error:                         # error controlado: mensaje claro y salida limpia
        raise SystemExit(f"No se pudo crear el administrador: {error}") from error
    print(f"Administrador creado con id {nuevo_id}.")


if __name__ == "__main__":
    main()
