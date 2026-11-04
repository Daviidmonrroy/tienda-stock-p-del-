-- Vibra Deportiva · esquema MySQL 8 (borrador v0.2)
-- Montos en centavos (BIGINT). Stock = suma de movimientos. Sin validar contra un servidor MySQL todavía.
SET NAMES utf8mb4;

-- Las zonas son ciudades.
CREATE TABLE zonas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE usuarios (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  rol ENUM('admin','empleado','vendedor') NOT NULL,
  zona_id INT UNSIGNED NULL,               -- vendedores: su ciudad
  ubicacion_id INT UNSIGNED NULL,          -- empleados: el sector donde trabajan (local o cancha)
  activo TINYINT(1) NOT NULL DEFAULT 1,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (zona_id) REFERENCES zonas(id)
  -- FK de ubicacion_id se agrega abajo, después de crear ubicaciones
);

-- Dónde puede haber stock: local, cancha, o la "mochila" de un vendedor.
CREATE TABLE ubicaciones (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(80) NOT NULL,
  tipo ENUM('local','cancha','vendedor') NOT NULL,
  usuario_id INT UNSIGNED NULL,           -- solo si tipo = 'vendedor'
  activa TINYINT(1) NOT NULL DEFAULT 1,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
ALTER TABLE usuarios ADD FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id);

-- Ajustes del negocio (una fila por clave).
CREATE TABLE configuracion (
  clave VARCHAR(60) PRIMARY KEY,
  valor VARCHAR(255) NOT NULL
);
-- 'comision_vendedor_bp': porcentaje único de comisión en puntos básicos (1000 = 10 %). Igual para todos los productos.

CREATE TABLE categorias (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(80) NOT NULL UNIQUE);
CREATE TABLE marcas     (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(80) NOT NULL UNIQUE);

CREATE TABLE productos (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(160) NOT NULL,
  categoria_id INT UNSIGNED NOT NULL,
  marca_id INT UNSIGNED NULL,
  descripcion TEXT NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  FOREIGN KEY (categoria_id) REFERENCES categorias(id),
  FOREIGN KEY (marca_id) REFERENCES marcas(id)
);

-- Lo que realmente se vende y se cuenta: una variante (talle/color) por producto.
CREATE TABLE variantes (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  producto_id INT UNSIGNED NOT NULL,
  sku VARCHAR(40) NOT NULL UNIQUE,         -- también sirve para QR / código de barras
  talle VARCHAR(20) NULL,
  color VARCHAR(40) NULL,
  costo_centavos BIGINT NOT NULL DEFAULT 0,
  precio_lista_centavos BIGINT NOT NULL,   -- precio sugerido al público
  precio_minimo_centavos BIGINT NOT NULL,  -- piso para vendedores (lo ven)
  precio_maximo_centavos BIGINT NOT NULL,  -- techo de venta
  stock_minimo INT NOT NULL DEFAULT 0,
  activa TINYINT(1) NOT NULL DEFAULT 1,
  FOREIGN KEY (producto_id) REFERENCES productos(id),
  CHECK (precio_minimo_centavos <= precio_lista_centavos AND precio_lista_centavos <= precio_maximo_centavos)
);

CREATE TABLE clientes (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(120) NOT NULL,
  telefono VARCHAR(40) NULL,
  zona_id INT UNSIGNED NULL,
  FOREIGN KEY (zona_id) REFERENCES zonas(id)
);

CREATE TABLE proveedores (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(120) NOT NULL, contacto VARCHAR(120) NULL);

CREATE TABLE compras (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  proveedor_id INT UNSIGNED NOT NULL,
  ubicacion_id INT UNSIGNED NOT NULL,      -- dónde entra la mercadería
  fecha DATE NOT NULL,
  total_centavos BIGINT NOT NULL,
  usuario_id INT UNSIGNED NOT NULL,
  FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
  FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
CREATE TABLE compra_items (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  compra_id INT UNSIGNED NOT NULL,
  variante_id INT UNSIGNED NOT NULL,
  cantidad INT NOT NULL CHECK (cantidad > 0),
  costo_unit_centavos BIGINT NOT NULL,
  FOREIGN KEY (compra_id) REFERENCES compras(id),
  FOREIGN KEY (variante_id) REFERENCES variantes(id)
);

-- Entrega de mercadería a un vendedor (local -> mochila del vendedor).
CREATE TABLE asignaciones (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  vendedor_id INT UNSIGNED NOT NULL,
  desde_ubicacion_id INT UNSIGNED NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  estado ENUM('abierta','cerrada') NOT NULL DEFAULT 'abierta',
  usuario_id INT UNSIGNED NOT NULL,
  FOREIGN KEY (vendedor_id) REFERENCES usuarios(id),
  FOREIGN KEY (desde_ubicacion_id) REFERENCES ubicaciones(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
CREATE TABLE asignacion_items (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  asignacion_id INT UNSIGNED NOT NULL,
  variante_id INT UNSIGNED NOT NULL,
  cantidad INT NOT NULL CHECK (cantidad > 0),
  FOREIGN KEY (asignacion_id) REFERENCES asignaciones(id),
  FOREIGN KEY (variante_id) REFERENCES variantes(id)
);

CREATE TABLE ventas (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  uuid_cliente CHAR(36) NOT NULL UNIQUE,   -- lo genera el celular: evita duplicar al sincronizar offline
  ubicacion_id INT UNSIGNED NOT NULL,
  vendedor_id INT UNSIGNED NULL,           -- NULL = venta de mostrador
  cliente_id INT UNSIGNED NULL,
  fecha DATETIME NOT NULL,
  medio_pago ENUM('efectivo','transferencia','fiado') NOT NULL,
  pagado_centavos BIGINT NOT NULL DEFAULT 0,  -- si es fiado, lo que ya pagó; el saldo es total - pagado
  estado ENUM('confirmada','anulada') NOT NULL DEFAULT 'confirmada',
  total_centavos BIGINT NOT NULL,
  FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id),
  FOREIGN KEY (vendedor_id) REFERENCES usuarios(id),
  FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);
CREATE TABLE venta_items (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  venta_id INT UNSIGNED NOT NULL,
  variante_id INT UNSIGNED NOT NULL,
  cantidad INT NOT NULL CHECK (cantidad > 0),
  precio_unit_centavos BIGINT NOT NULL,
  precio_minimo_snapshot BIGINT NOT NULL,  -- se congela al vender
  costo_snapshot BIGINT NOT NULL DEFAULT 0, -- costo unitario congelado: la ganancia histórica no cambia si sube el costo
  comision_centavos BIGINT NOT NULL DEFAULT 0, -- se calcula y congela al vender
  FOREIGN KEY (venta_id) REFERENCES ventas(id),
  FOREIGN KEY (variante_id) REFERENCES variantes(id)
);

-- Libro de stock: única fuente de verdad. cantidad con signo.
CREATE TABLE movimientos_stock (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  variante_id INT UNSIGNED NOT NULL,
  ubicacion_id INT UNSIGNED NOT NULL,
  tipo ENUM('compra','venta','asignacion_salida','asignacion_entrada','devolucion_salida','devolucion_entrada','perdida','ajuste','anulacion') NOT NULL,
  cantidad INT NOT NULL,
  referencia_tipo VARCHAR(30) NULL,
  referencia_id INT UNSIGNED NULL,
  usuario_id INT UNSIGNED NOT NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  nota VARCHAR(255) NULL,
  INDEX (variante_id, ubicacion_id),
  FOREIGN KEY (variante_id) REFERENCES variantes(id),
  FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Saldo rápido, se actualiza en la misma transacción que el movimiento.
CREATE TABLE stock_actual (
  variante_id INT UNSIGNED NOT NULL,
  ubicacion_id INT UNSIGNED NOT NULL,
  cantidad INT NOT NULL DEFAULT 0,
  PRIMARY KEY (variante_id, ubicacion_id),
  FOREIGN KEY (variante_id) REFERENCES variantes(id),
  FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id)
);

CREATE TABLE liquidaciones (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  vendedor_id INT UNSIGNED NOT NULL,
  desde DATE NOT NULL,
  hasta DATE NOT NULL,                     -- período mensual
  total_centavos BIGINT NOT NULL,
  estado ENUM('pendiente','pagada') NOT NULL DEFAULT 'pendiente',
  pagada_en DATETIME NULL,
  FOREIGN KEY (vendedor_id) REFERENCES usuarios(id)
);
CREATE TABLE liquidacion_items (
  liquidacion_id INT UNSIGNED NOT NULL,
  venta_item_id INT UNSIGNED NOT NULL UNIQUE,  -- una venta no se liquida dos veces
  PRIMARY KEY (liquidacion_id, venta_item_id),
  FOREIGN KEY (liquidacion_id) REFERENCES liquidaciones(id),
  FOREIGN KEY (venta_item_id) REFERENCES venta_items(id)
);

-- Cobros de ventas fiadas (cuenta corriente del cliente).
CREATE TABLE cobros (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  venta_id INT UNSIGNED NOT NULL,
  cliente_id INT UNSIGNED NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  monto_centavos BIGINT NOT NULL CHECK (monto_centavos > 0),
  medio_pago ENUM('efectivo','transferencia') NOT NULL,
  usuario_id INT UNSIGNED NOT NULL,
  FOREIGN KEY (venta_id) REFERENCES ventas(id),
  FOREIGN KEY (cliente_id) REFERENCES clientes(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE auditoria (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  usuario_id INT UNSIGNED NULL,
  accion VARCHAR(60) NOT NULL,
  entidad VARCHAR(40) NOT NULL,
  entidad_id INT UNSIGNED NULL,
  detalle JSON NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ===== Panel del dueño: gastos y vistas de resumen =====
CREATE TABLE categorias_gasto (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, nombre VARCHAR(80) NOT NULL UNIQUE);  -- alquiler, sueldos, luz, publicidad...

CREATE TABLE gastos (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  fecha DATE NOT NULL,
  categoria_id INT UNSIGNED NOT NULL,
  ubicacion_id INT UNSIGNED NULL,          -- local o cancha; NULL = general
  descripcion VARCHAR(255) NULL,
  monto_centavos BIGINT NOT NULL,
  usuario_id INT UNSIGNED NOT NULL,
  INDEX (fecha),
  FOREIGN KEY (categoria_id) REFERENCES categorias_gasto(id),
  FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones(id),
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Una fila por producto vendido, con ganancia bruta (vendido - costo - comisión).
CREATE VIEW v_ventas_detalle AS
SELECT v.id AS venta_id, DATE(v.fecha) AS dia, v.fecha, v.ubicacion_id, v.vendedor_id,
       vi.variante_id, vi.cantidad,
       vi.cantidad * vi.precio_unit_centavos AS vendido_centavos,
       vi.cantidad * vi.costo_snapshot        AS costo_centavos,
       vi.comision_centavos
FROM ventas v
JOIN venta_items vi ON vi.venta_id = v.id
WHERE v.estado = 'confirmada';
