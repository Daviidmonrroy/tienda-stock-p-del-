"""Importar los modelos acá hace que queden registrados en Base.metadata (necesario para create_all)."""
from models.catalogo import Categoria, Marca, Producto, Variante
from models.operaciones import (CategoriaGasto, Cliente, Cobro, Compra, CompraDetalle, Configuracion, Gasto,
                                Liquidacion, Proveedor, Venta, VentaDetalle)
from models.stock import MovimientoStock, StockActual, Ubicacion
from models.usuario import PerfilUsuario, Usuario
from models.zona import Zona

__all__ = ["Categoria", "CategoriaGasto", "Cliente", "Cobro", "Compra", "CompraDetalle", "Configuracion",
           "Gasto", "Liquidacion", "Marca", "MovimientoStock", "PerfilUsuario", "Producto", "Proveedor",
           "StockActual", "Ubicacion", "Usuario", "Variante", "Venta", "VentaDetalle", "Zona"]
