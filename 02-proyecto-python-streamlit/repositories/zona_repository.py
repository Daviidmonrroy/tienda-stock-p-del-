from sqlalchemy import select
from sqlalchemy.orm import Session

from models.zona import Zona


def listar(session: Session) -> list[Zona]:
    return list(session.scalars(select(Zona).order_by(Zona.nombre)))


def crear(session: Session, nombre: str) -> Zona:
    zona = Zona(nombre=nombre)
    session.add(zona)
    session.flush()  # asigna el id sin confirmar todavía
    return zona
