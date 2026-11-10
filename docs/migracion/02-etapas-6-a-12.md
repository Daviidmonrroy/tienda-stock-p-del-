# Etapas 6 a 12 — catálogo, stock, compras, ventas, comisiones, panel

## Qué se hizo
| Etapa | Archivos principales | Conceptos de clase |
|---|---|---|
| 6 Catálogo | models/catalogo.py, repositories/catalogo_repository.py, services/catalogo_service.py, services/reglas_catalogo.py, views/catalogo.py | DeclarativeBase, UniqueConstraint, CheckConstraint, Decimal, regex (SKU, color hex), IntegrityError |
| 7 Stock | models/stock.py, repositories/stock_repository.py, services/stock_service.py, views/stock.py | libro de movimientos + saldo en la misma transacción, flush, rollback, `with_for_update` (bloqueo de fila), multitenant (mochila por usuario) |
| 8 Compras | services/compras_service.py | transacción única compra+detalle+stock |
| 9 Ventas | models/operaciones.py, services/reglas_ventas.py, services/ventas_service.py, services/clientes_service.py, views/ventas.py | foto (snapshot) de costo/mínimo/comisión, fiado y cobros, anulación sin borrar |
| 10 Comisiones | services/comisiones_service.py | % global en tabla `configuracion`, liquidación mensual con UNIQUE(vendedor, período) |
| 11 Panel y gastos | services/reportes_service.py, utils/exportacion.py, views/reportes.py | `text()` con parámetros, agregaciones SQL, CSV |
| 12 Tests y docs | tests/test_reglas_*.py, test_extras_puros.py, test_flujo_completo_db.py | pytest, SQLite solo para tests |

## Reglas de negocio (dónde viven)
- Precio de venta entre mínimo y máximo: `reglas_catalogo.validar_precio_de_venta`.
- Comisión: solo vendedores, % global congelado en cada venta: `reglas_ventas.calcular_venta`.
- El vendedor nunca recibe el costo (`VarianteVista.costo = None`) y solo ve su mochila, sus ventas y su comisión.
- Stock nunca negativo: `stock_service.mover` + CHECK en la tabla.

## Estado de verificación (honesto)
- **Ejecutado por Claude (pytest, solo librería estándar):** validaciones, dinero, settings, permisos, reglas de catálogo, reglas de venta/cobro/comisión/período, CSV → 82 pruebas pasan.
- **NO ejecutado (faltaban SQLAlchemy, bcrypt, Streamlit y MySQL en el entorno de Claude):** modelos, repositorios, servicios, vistas, `tests/test_flujo_completo_db.py`, `tests/test_auth_service_db.py`, `test_seguridad.py`. Solo se verificó que la sintaxis compile.
- `sql/schema.sql` es documentación de referencia; las tablas reales las crea `python -m scripts.crear_tablas` desde los modelos (los nombres de tablas de los modelos pueden diferir levemente del .sql).

## Para verificar en tu PC
1. `pip install -r requirements.txt`
2. `python -m pytest -q`  (deberían ejecutarse también los tests de base de datos)
3. `python -m scripts.crear_tablas` y `python -m scripts.crear_admin`
4. `streamlit run app.py`
Pasame cualquier error y lo corrijo.
