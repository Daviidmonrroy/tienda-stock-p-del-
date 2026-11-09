"""Importar los modelos acá hace que queden registrados en Base.metadata (necesario para create_all)."""
from models.usuario import PerfilUsuario, Usuario
from models.zona import Zona

__all__ = ["PerfilUsuario", "Usuario", "Zona"]
