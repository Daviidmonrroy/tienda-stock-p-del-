"""Configuración de la aplicación, leída de variables de entorno.

Conceptos de clase: @dataclass(frozen=True, slots=True) y variables de entorno.
- frozen=True: la configuración no se puede modificar mientras la app corre.
- slots=True: sin diccionario interno por objeto (menos memoria, no admite atributos nuevos).
"""
import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import quote_plus

from utils.excepciones import ConfiguracionFaltante

_VERDADERO = {"1", "true", "yes", "si", "sí", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    sql_echo: bool = False

    @property
    def url_base_de_datos(self) -> str:
        """URL de conexión para SQLAlchemy. La clave se codifica por si tiene @, : o /."""
        usuario = quote_plus(self.db_user)
        clave = quote_plus(self.db_password)
        return f"mysql+pymysql://{usuario}:{clave}@{self.db_host}:{self.db_port}/{self.db_name}"

    @classmethod
    def desde_entorno(cls, entorno: "dict[str, str] | None" = None) -> "Settings":
        """Arma la configuración desde un diccionario (por defecto os.environ)."""
        env = os.environ if entorno is None else entorno

        def obligatoria(nombre: str) -> str:
            valor = env.get(nombre, "").strip()
            if not valor:
                raise ConfiguracionFaltante(f"Falta la variable de entorno {nombre} (ver .env.example).")
            return valor

        try:
            puerto = int(env.get("DB_PORT", "3306"))
        except ValueError as error:
            raise ConfiguracionFaltante("DB_PORT debe ser un número.") from error
        return cls(
            db_host=env.get("DB_HOST", "127.0.0.1").strip() or "127.0.0.1",
            db_port=puerto,
            db_name=obligatoria("DB_NAME"),
            db_user=obligatoria("DB_USER"),
            db_password=obligatoria("DB_PASSWORD"),
            sql_echo=env.get("SQL_ECHO", "false").strip().lower() in _VERDADERO,
        )


def _cargar_archivo_env() -> None:
    """Carga el archivo .env si python-dotenv está instalado. Si no, se usan las variables del sistema."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


@lru_cache(maxsize=1)
def obtener_settings() -> Settings:
    """Una sola instancia para toda la app (se calcula la primera vez)."""
    _cargar_archivo_env()
    return Settings.desde_entorno()
