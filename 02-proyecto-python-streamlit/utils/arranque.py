"""Preparación automática al iniciar la app (pensada para la nube, donde no hay terminal).

Hace lo mismo que `python -m scripts.crear_tablas` y `python -m scripts.semilla`, pero solo si falta algo:
  1. Crea las tablas que no existan (create_all no toca las existentes ni borra datos).
  2. Crea el administrador si no existe. Email y clave salen de ADMIN_EMAIL y ADMIN_PASSWORD;
     si no están definidas se usan los valores de DEMOSTRACIÓN de abajo.
La clave se guarda hasheada con bcrypt, igual que cualquier usuario.
"""
import os

# Valores de demostración (fáciles de recordar). En un sistema real se cambian con los secrets.
EMAIL_DEMO = "admin@vibra.com"
CLAVE_DEMO = "Vibra2026"


def credenciales_admin(entorno: dict[str, str]):
    """Función pura: arma la credencial del admin desde el entorno o con los valores de demostración."""
    from scripts.semilla import CredencialSemilla
    email = (entorno.get("ADMIN_EMAIL") or "").strip() or EMAIL_DEMO
    clave = entorno.get("ADMIN_PASSWORD") or CLAVE_DEMO
    return CredencialSemilla(rol="admin", email=email, nombre="Administrador Vibra", clave=clave)


def preparar_base() -> list[str]:
    """Crea tablas y admin si faltan. Devuelve mensajes de lo que hizo."""
    from database.base import Base
    from database.connection import obtener_engine
    import models  # noqa: F401  (registra los modelos en Base.metadata)
    from scripts.semilla import sembrar

    Base.metadata.create_all(obtener_engine())
    return sembrar([credenciales_admin(dict(os.environ))])
