"""Semilla de usuarios: crea, SI NO EXISTEN, un administrador y un auditor.  Ejecutar desde la carpeta del proyecto:
    python -m scripts.semilla

De dónde sale cada dato:
  - Emails:  del archivo .env  (ADMIN_EMAIL y AUDITOR_EMAIL).
  - Claves:  del archivo scripts/semilla_usuarios.txt (texto plano, solo para desarrollo local; está en .gitignore).
  - En la base de datos las claves se guardan SIEMPRE hasheadas con bcrypt (lo hace auth_service).

Es idempotente: se puede ejecutar muchas veces; solo inserta lo que falta.
Conceptos de clase: variables de entorno, if __name__ == "__main__", SystemExit, bcrypt vía servicio, IntegrityError evitado
consultando antes, excepciones propias.
"""
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from utils.excepciones import ConfiguracionFaltante, ErrorDeNegocio

@dataclass(frozen=True, slots=True)
class CredencialSemilla:
    """Un usuario a crear: el email viene del .env y la clave del .txt."""
    rol: str
    email: str
    nombre: str
    clave: str


ARCHIVO_CLAVES = Path(__file__).with_name("semilla_usuarios.txt")
VARIABLES_EMAIL = {"admin": "ADMIN_EMAIL", "auditor": "AUDITOR_EMAIL"}
NOMBRES = {"admin": "Administrador Vibra", "auditor": "Auditor Vibra"}


def leer_claves(texto: str) -> dict[str, str]:
    """Interpreta líneas 'rol=clave'. Ignora líneas vacías y comentarios (#). Función pura: se prueba sin base de datos."""
    claves: dict[str, str] = {}
    for numero, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        rol, separador, clave = linea.partition("=")
        rol, clave = rol.strip().lower(), clave.strip()
        if not separador or rol not in VARIABLES_EMAIL or not clave:
            raise ConfiguracionFaltante(f"Línea {numero} inválida en el archivo de claves (formato: rol=clave).")
        claves[rol] = clave
    return claves


def armar_credenciales(entorno: dict[str, str], claves: dict[str, str]) -> list[CredencialSemilla]:
    """Une emails (.env) y claves (.txt). El admin va primero porque hace falta para crear al auditor."""
    lista = []
    for rol, variable in VARIABLES_EMAIL.items():
        email = (entorno.get(variable) or "").strip()
        if not email:
            raise ConfiguracionFaltante(f"Falta la variable {variable} en el archivo .env.")
        if rol not in claves:
            raise ConfiguracionFaltante(f"Falta la clave de '{rol}' en {ARCHIVO_CLAVES.name}.")
        lista.append(CredencialSemilla(rol=rol, email=email, nombre=NOMBRES[rol], clave=claves[rol]))
    return lista


def sembrar(credenciales: list[CredencialSemilla]) -> list[str]:
    """Inserta lo que falta. Devuelve mensajes de lo que hizo. Importa los servicios acá adentro para que
    las funciones puras de arriba se puedan probar sin tener SQLAlchemy instalado."""
    from database.connection import session_scope
    from repositories import usuario_repository
    from services import auth_service

    def existe(email: str) -> bool:
        with session_scope() as sesion:
            return usuario_repository.buscar_por_email(sesion, email.strip().lower()) is not None

    mensajes, actor = [], None
    for cred in credenciales:               # admin primero
        if existe(cred.email):
            mensajes.append(f"{cred.rol}: ya existía ({cred.email}), no se modifica.")
        else:
            datos = auth_service.validar_datos_registro(cred.nombre, cred.email, cred.clave, cred.rol)
            auth_service.registrar_usuario(datos, actor=actor)     # actor=None solo es válido para el primer admin
            mensajes.append(f"{cred.rol}: creado ({cred.email}).")
        if cred.rol == "admin" and actor is None:
            actor = auth_service.iniciar_sesion(cred.email, cred.clave)
    return mensajes


def main() -> None:
    from config.settings import obtener_settings
    try:
        obtener_settings()                                          # también carga el .env
        if not ARCHIVO_CLAVES.exists():
            raise ConfiguracionFaltante(f"No existe {ARCHIVO_CLAVES}. Copiá semilla_usuarios.example.txt y completalo.")
        credenciales = armar_credenciales(dict(os.environ), leer_claves(ARCHIVO_CLAVES.read_text(encoding="utf-8")))
        for mensaje in sembrar(credenciales):
            print(mensaje)
    except (ConfiguracionFaltante, ErrorDeNegocio) as error:
        raise SystemExit(f"Semilla cancelada: {error}") from error


if __name__ == "__main__":
    sys.exit(main())
