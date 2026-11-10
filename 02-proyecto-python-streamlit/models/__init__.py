"""Importar los modelos acá hace que queden registrados en Base.metadata (necesario para create_all)."""
from models.catalogo import Categoria, Marca, Producto, Variante
from models.usuario import PerfilUsuario, Usuario
from models.zona import Zona

__all__ = ["Categoria", "Marca", "PerfilUsuario", "Producto", "Usuario", "Variante", "Zona"]
