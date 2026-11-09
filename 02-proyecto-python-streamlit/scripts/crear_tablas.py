"""Crea las tablas en MySQL a partir de los modelos.  Ejecutar desde la carpeta del proyecto:
    python -m scripts.crear_tablas
"""
import sys

from config.settings import obtener_settings
from database.base import Base
from database.connection import obtener_engine
import models  # noqa: F401  (registra los modelos en Base.metadata)
from utils.excepciones import ConfiguracionFaltante


def main() -> None:
    try:
        obtener_settings()
    except ConfiguracionFaltante as error:
        # SystemExit tiene sentido acá: es un script de consola y sin configuración no se puede seguir.
        raise SystemExit(f"Error de configuración: {error}") from error
    Base.metadata.create_all(obtener_engine())
    print("Tablas creadas (o ya existían):", ", ".join(sorted(Base.metadata.tables)))


if __name__ == "__main__":
    sys.exit(main())
