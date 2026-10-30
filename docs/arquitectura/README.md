# Arquitectura

- **App:** web instalable (PWA), mobile first, modo claro y oscuro, con la identidad de `brand/`.
- **Servidor:** API REST. Toda la lógica de stock, precios mínimos y comisiones vive en el servidor.
- **Base de datos:** MySQL 8 (`db/schema.sql`). Ventas y movimientos de stock en una sola transacción.
- **Acceso:** login con sesión segura, contraseñas con hash, permisos por rol verificados en el servidor.
- **Hosting:** VPS con Docker Compose (nginx con HTTPS, API, MySQL). Copia diaria de la base a almacenamiento externo.
- **Entornos:** desarrollo y producción separados; cambios de base por migraciones versionadas.
- **Sin conexión:** las ventas del celular se guardan localmente y se envían al reconectar (idempotentes por `uuid_cliente`).

## Panel del dueño
Resúmenes por día, semana y mes: ventas, ganancia bruta (vendido − costo), neta (− comisiones − gastos), por vendedor,
local contra cancha, alertas de stock bajo y comisiones pendientes. Alimentado por `v_ventas_detalle` y `gastos`.
