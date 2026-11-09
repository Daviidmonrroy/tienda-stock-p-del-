"""Conexión a MySQL con SQLAlchemy.

Conceptos de clase: create_engine, echo=True (depuración), sessionmaker, session.commit/rollback/close.
El engine y el sessionmaker se crean la primera vez que se piden (lru_cache), no al importar el módulo.
"""
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import obtener_settings


@lru_cache(maxsize=1)
def obtener_engine():
    settings = obtener_settings()
    # echo=True imprime cada SQL por consola: útil para depurar, no para producción.
    return create_engine(settings.url_base_de_datos, echo=settings.sql_echo, pool_pre_ping=True)


@lru_cache(maxsize=1)
def obtener_sessionmaker() -> sessionmaker:
    return sessionmaker(bind=obtener_engine())


@contextmanager
def session_scope():
    """Abre una sesión y garantiza el cierre de la transacción.

    with session_scope() as session:
        ...             # si todo sale bien -> commit
                        # si hay una excepción -> rollback y se vuelve a lanzar
                        # siempre -> close (bloque finally)
    """
    session: Session = obtener_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
