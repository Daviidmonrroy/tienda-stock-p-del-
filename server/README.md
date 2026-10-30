# Servidor

API en Node 22, sin dependencias externas (solo módulos incluidos en Node).

```
src/domain/   Reglas del negocio puras: dinero, precios mín/máx, comisión, validación de ventas.
src/auth/     Hash de claves (scrypt) y tokens firmados (HS256).
src/store/    Almacenes de datos. `memoria.js` (pruebas y demo). MySQL: pendiente.
src/http/     Rutas de la API.
test/         Pruebas automáticas (`npm test`).
```

## Probar
```
cd server
npm test
JWT_SECRET=un-texto-largo-y-aleatorio DEMO_CLAVE=una-clave npm start
```
Usuario demo: `admin@demo.local`. Los datos viven en memoria y se pierden al apagar.

## Rutas
| Ruta | Quién | Qué hace |
|---|---|---|
| `POST /api/login` | todos | Devuelve un token. |
| `GET /api/productos` | logueados | Variantes con precio mínimo y máximo. El costo solo lo ve el administrador. |
| `GET /api/stock` | logueados | Stock del propio lugar (el admin elige con `?ubicacion=`). |
| `POST /api/ventas` | logueados | Valida rango de precios y stock, calcula comisión y descuenta stock. Si repite el `uuid`, no duplica. |

## Reglas ya cubiertas por pruebas
Precio dentro de [mínimo, máximo]; stock suficiente; el vendedor vende solo de su mochila y el empleado de su sector;
comisión solo en ventas de vendedores; fiado exige cliente; el costo se congela en cada venta; token falsificado o vencido rechazado.

## Pendiente
Adaptador MySQL (usa `db/schema.sql`), compras, asignaciones, devoluciones, liquidación mensual, gastos y panel del dueño.
