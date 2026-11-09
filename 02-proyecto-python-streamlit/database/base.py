"""Clase base de todos los modelos ORM.

Concepto de clase: DeclarativeBase. Registra las tablas en Base.metadata.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
