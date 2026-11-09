"""Consultas sobre usuarios. Solo acceso a datos: no valida reglas de negocio ni maneja la transacción."""
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from models.usuario import Usuario


def buscar_por_email(session: Session, email: str) -> Usuario | None:
    return session.scalars(select(Usuario).where(Usuario.email == email)).first()


def buscar_por_id(session: Session, usuario_id: int) -> Usuario | None:
    return session.get(Usuario, usuario_id)


def listar(session: Session) -> list[Usuario]:
    return list(session.scalars(select(Usuario).order_by(Usuario.nombre)))


def contar(session: Session) -> int:
    return session.scalar(select(func.count(Usuario.id))) or 0


def registrar_intento_fallido(session: Session, usuario_id: int) -> None:
    """SQL escrito a mano con text(): un UPDATE chico y directo. Los valores van como parámetros (:id)."""
    session.execute(
        text("UPDATE usuarios SET intentos_fallidos = intentos_fallidos + 1 WHERE id = :id"),
        {"id": usuario_id},
    )


def reiniciar_intentos(session: Session, usuario_id: int) -> None:
    session.execute(text("UPDATE usuarios SET intentos_fallidos = 0 WHERE id = :id"), {"id": usuario_id})
