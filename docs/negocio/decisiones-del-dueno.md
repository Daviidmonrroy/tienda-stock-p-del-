# Respuestas del dueño (29/10/2026)

| Tema | Respuesta | Qué implica en el sistema |
|---|---|---|
| Comisión | Porcentaje de la venta, igual para todos los productos | Un solo porcentaje en `configuracion` (`comision_vendedor_bp`). Sin reglas por producto. |
| Precios | Hay mínimo y máximo | `precio_minimo` y `precio_maximo` por variante; el sistema no deja vender fuera del rango. |
| Pago de comisión | Por mes | Liquidación mensual por vendedor. |
| Vista del vendedor | Ve el precio mínimo, no el costo | El costo nunca se envía a la app del vendedor. |
| Mercadería | Se lleva y rinde, y también pide al local | Asignaciones del local al vendedor + pedidos (a definir pantalla). |
| Devoluciones | Las devuelven; en el peor caso las cubre el dueño | Movimientos `devolucion_*` y `perdida` (la pérdida va a cuenta del negocio). |
| Zonas | Por ciudades | `zonas` = ciudades. |
| Clientes | De cualquiera | Clientes compartidos. |
| Personal | Hay empleados para cada sector | Nuevo rol `empleado`, asignado a una ubicación. |
| Ubicaciones | Un solo local; la cancha va por separado | Dos ubicaciones, stock y caja separados. |
| Cobros | Efectivo o transferencia, a veces fiado | `fiado` con saldo y tabla `cobros`. Sin tarjeta ni Mercado Pago. |
| Facturación | No factura | Sin AFIP. |
| Gastos | Sueldos y publicidad | Categorías de gasto iniciales. |
| Productos | Todos con variantes (zapatillas, ropa, etc.) | Variantes (talle/color) para todo producto. |
| Datos | Tiene una lista; quiere cargarla | Importador desde planilla. |
| Panel | Quiere ver ventas y ganancia | Panel del dueño con ambas. |
