# Vibra Deportiva · Sistema de stock y ventas

Sistema para una tienda de pádel: productos, stock por ubicación (local y cancha), ventas, compras,
vendedores por zona, comisiones y un panel de resúmenes para el dueño. Pensado para usarse desde el celular.

> Repositorio público: no subir contraseñas, archivos `.env`, datos de clientes ni ventas reales.

## Estructura
| Carpeta | Contenido |
|---|---|
| `prototype/` | Prototipo funcional de una sola página (guarda en el navegador). Sirve de referencia visual. |
| `db/` | Esquema MySQL 8 (borrador v0.1). |
| `server/` | API (pendiente). |
| `app/` | App web instalable en el celular (pendiente). |
| `brand/` | Logos, avatar, íconos y favicon en SVG y PNG. |
| `docs/` | Manual de marca, arquitectura y preguntas abiertas. |

## Decisiones tomadas
- Roles iniciales: administrador y vendedor.
- Dos ubicaciones con stock propio: local y cancha. Cada vendedor suma una "mochila" propia.
- El stock sale de un libro de movimientos, no de un número editable.
- Montos en centavos enteros. Ventas desde el celular con identificador propio para sincronizar sin duplicar.
- Comisión configurable por producto: porcentaje, o lo que el vendedor agrega sobre el precio mínimo.
- El costo se congela en cada venta para que la ganancia histórica no cambie.

## Etapas
1. Servidor, login y roles. Productos, variantes, stock por ubicación y ventas.
2. Compras, asignación a vendedores y devoluciones.
3. Comisiones y liquidaciones.
4. Modo celular y sin conexión para vendedores.
5. Panel del dueño: resúmenes por día, semana y mes; gastos.
6. Extras: Mercado Pago, AFIP, WhatsApp.

Ver `docs/` para el detalle y las preguntas pendientes con el dueño.
