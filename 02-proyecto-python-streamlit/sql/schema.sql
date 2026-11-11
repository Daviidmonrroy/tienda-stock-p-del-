-- Esquema MySQL 8 de Vibra Deportiva (autor: compañero del equipo).
-- Revisión: las 21 tablas y sus columnas coinciden con los modelos de models/ (verificado por script).
-- ESTADO: NO ejecutado todavía contra un servidor MySQL. Usar este archivo O python -m scripts.crear_tablas, no ambos sobre la misma base.

-- Esquema MySQL 8 para Vibra Deportiva.
-- Basado en los modelos ORM de models/ y compatible con el DB_NAME predeterminado
-- de .env.example. Si DB_NAME tiene otro valor, cambiarlo también en CREATE DATABASE y USE.
CREATE DATABASE IF NOT EXISTS vibra_deportiva
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE vibra_deportiva;

-- Ejecutar una sola vez sobre una base vacía. Para cambios posteriores, usar
-- migraciones en lugar de volver a crear o borrar tablas con datos.

CREATE TABLE zonas (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(80) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_zonas_nombre UNIQUE (nombre)
) ENGINE=InnoDB;

CREATE TABLE usuarios (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(120) NOT NULL,
  email VARCHAR(160) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  rol ENUM('admin', 'empleado', 'vendedor') NOT NULL,
  zona_id INT NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  intentos_fallidos INT NOT NULL DEFAULT 0,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uq_usuarios_email UNIQUE (email),
  CONSTRAINT ck_usuarios_intentos CHECK (intentos_fallidos >= 0),
  CONSTRAINT fk_usuarios_zona FOREIGN KEY (zona_id) REFERENCES zonas (id)
) ENGINE=InnoDB;

CREATE TABLE perfiles_usuario (
  id INT NOT NULL AUTO_INCREMENT,
  usuario_id INT NOT NULL,
  telefono VARCHAR(30) NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_perfil_usuario UNIQUE (usuario_id),
  CONSTRAINT fk_perfiles_usuario_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuarios (id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE categorias (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(80) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_categorias_nombre UNIQUE (nombre)
) ENGINE=InnoDB;

CREATE TABLE marcas (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(80) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_marcas_nombre UNIQUE (nombre)
) ENGINE=InnoDB;

CREATE TABLE productos (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(160) NOT NULL,
  categoria_id INT NOT NULL,
  marca_id INT NULL,
  descripcion TEXT NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  KEY ix_productos_categoria_id (categoria_id),
  KEY ix_productos_marca_id (marca_id),
  CONSTRAINT fk_productos_categoria FOREIGN KEY (categoria_id) REFERENCES categorias (id),
  CONSTRAINT fk_productos_marca FOREIGN KEY (marca_id) REFERENCES marcas (id)
) ENGINE=InnoDB;

-- Cada variante representa el artículo que se vende y cuyo stock se controla.
CREATE TABLE variantes (
  id INT NOT NULL AUTO_INCREMENT,
  producto_id INT NOT NULL,
  sku VARCHAR(40) NOT NULL,
  talle VARCHAR(20) NOT NULL DEFAULT 'Único',
  color VARCHAR(40) NOT NULL DEFAULT 'Único',
  color_hex VARCHAR(7) NULL,
  costo DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  precio_lista DECIMAL(12, 2) NOT NULL,
  precio_minimo DECIMAL(12, 2) NOT NULL,
  precio_maximo DECIMAL(12, 2) NOT NULL,
  stock_minimo INT NOT NULL DEFAULT 0,
  activa TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (id),
  CONSTRAINT uq_variantes_sku UNIQUE (sku),
  CONSTRAINT uq_variante_producto_talle_color UNIQUE (producto_id, talle, color),
  CONSTRAINT ck_variantes_precios CHECK (
    precio_minimo <= precio_lista AND precio_lista <= precio_maximo
  ),
  CONSTRAINT ck_variantes_importes CHECK (
    costo >= 0 AND precio_minimo >= 0 AND precio_lista >= 0 AND precio_maximo >= 0
  ),
  CONSTRAINT ck_variantes_stock_minimo CHECK (stock_minimo >= 0),
  CONSTRAINT fk_variantes_producto FOREIGN KEY (producto_id) REFERENCES productos (id)
) ENGINE=InnoDB;

CREATE TABLE ubicaciones (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(80) NOT NULL,
  tipo ENUM('local', 'cancha', 'mochila') NOT NULL,
  usuario_id INT NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_ubicaciones_nombre UNIQUE (nombre),
  CONSTRAINT uq_ubicaciones_usuario UNIQUE (usuario_id),
  CONSTRAINT fk_ubicaciones_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB;

CREATE TABLE stock_actual (
  ubicacion_id INT NOT NULL,
  variante_id INT NOT NULL,
  cantidad INT NOT NULL DEFAULT 0,
  PRIMARY KEY (ubicacion_id, variante_id),
  CONSTRAINT ck_stock_actual_no_negativo CHECK (cantidad >= 0),
  CONSTRAINT fk_stock_actual_ubicacion FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones (id),
  CONSTRAINT fk_stock_actual_variante FOREIGN KEY (variante_id) REFERENCES variantes (id)
) ENGINE=InnoDB;

-- Libro de movimientos: positivos ingresan stock y negativos lo descuentan.
CREATE TABLE movimientos_stock (
  id INT NOT NULL AUTO_INCREMENT,
  variante_id INT NOT NULL,
  ubicacion_id INT NOT NULL,
  tipo ENUM(
    'compra', 'venta', 'ajuste', 'transferencia_in', 'transferencia_out', 'anulacion'
  ) NOT NULL,
  cantidad INT NOT NULL,
  referencia VARCHAR(40) NULL,
  nota VARCHAR(255) NULL,
  usuario_id INT NOT NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_movimientos_stock_variante_id (variante_id),
  KEY ix_movimientos_stock_ubicacion_id (ubicacion_id),
  CONSTRAINT fk_movimientos_stock_variante FOREIGN KEY (variante_id) REFERENCES variantes (id),
  CONSTRAINT fk_movimientos_stock_ubicacion FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones (id),
  CONSTRAINT fk_movimientos_stock_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB;

CREATE TABLE configuracion (
  clave VARCHAR(60) NOT NULL,
  valor VARCHAR(120) NOT NULL,
  PRIMARY KEY (clave)
) ENGINE=InnoDB;

CREATE TABLE proveedores (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(120) NOT NULL,
  telefono VARCHAR(30) NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_proveedores_nombre UNIQUE (nombre)
) ENGINE=InnoDB;

CREATE TABLE compras (
  id INT NOT NULL AUTO_INCREMENT,
  proveedor_id INT NOT NULL,
  ubicacion_id INT NOT NULL,
  usuario_id INT NOT NULL,
  total DECIMAL(12, 2) NOT NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_compras_proveedor_id (proveedor_id),
  KEY ix_compras_ubicacion_id (ubicacion_id),
  KEY ix_compras_usuario_id (usuario_id),
  CONSTRAINT ck_compras_total CHECK (total >= 0),
  CONSTRAINT fk_compras_proveedor FOREIGN KEY (proveedor_id) REFERENCES proveedores (id),
  CONSTRAINT fk_compras_ubicacion FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones (id),
  CONSTRAINT fk_compras_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB;

CREATE TABLE compra_detalle (
  id INT NOT NULL AUTO_INCREMENT,
  compra_id INT NOT NULL,
  variante_id INT NOT NULL,
  cantidad INT NOT NULL,
  costo_unitario DECIMAL(12, 2) NOT NULL,
  PRIMARY KEY (id),
  KEY ix_compra_detalle_compra_id (compra_id),
  KEY ix_compra_detalle_variante_id (variante_id),
  CONSTRAINT ck_compra_detalle_cantidad CHECK (cantidad > 0),
  CONSTRAINT ck_compra_detalle_costo CHECK (costo_unitario >= 0),
  CONSTRAINT fk_compra_detalle_compra FOREIGN KEY (compra_id) REFERENCES compras (id),
  CONSTRAINT fk_compra_detalle_variante FOREIGN KEY (variante_id) REFERENCES variantes (id)
) ENGINE=InnoDB;

CREATE TABLE clientes (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(120) NOT NULL,
  telefono VARCHAR(30) NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE ventas (
  id INT NOT NULL AUTO_INCREMENT,
  vendedor_id INT NOT NULL,
  ubicacion_id INT NOT NULL,
  cliente_id INT NULL,
  descuento DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  total DECIMAL(12, 2) NOT NULL,
  comision_pct DECIMAL(5, 2) NOT NULL,
  comision_total DECIMAL(12, 2) NOT NULL,
  estado_pago ENUM('pagada', 'parcial', 'pendiente') NOT NULL,
  pagado DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
  estado ENUM('confirmada', 'anulada') NOT NULL DEFAULT 'confirmada',
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_ventas_vendedor_id (vendedor_id),
  KEY ix_ventas_ubicacion_id (ubicacion_id),
  KEY ix_ventas_cliente_id (cliente_id),
  KEY ix_ventas_fecha (fecha),
  CONSTRAINT ck_ventas_importes CHECK (
    descuento >= 0 AND total >= 0 AND comision_pct >= 0 AND
    comision_total >= 0 AND pagado >= 0 AND pagado <= total
  ),
  CONSTRAINT fk_ventas_vendedor FOREIGN KEY (vendedor_id) REFERENCES usuarios (id),
  CONSTRAINT fk_ventas_ubicacion FOREIGN KEY (ubicacion_id) REFERENCES ubicaciones (id),
  CONSTRAINT fk_ventas_cliente FOREIGN KEY (cliente_id) REFERENCES clientes (id)
) ENGINE=InnoDB;

CREATE TABLE venta_detalle (
  id INT NOT NULL AUTO_INCREMENT,
  venta_id INT NOT NULL,
  variante_id INT NOT NULL,
  cantidad INT NOT NULL,
  precio_unitario DECIMAL(12, 2) NOT NULL,
  costo_unitario DECIMAL(12, 2) NOT NULL,
  precio_minimo DECIMAL(12, 2) NOT NULL,
  comision DECIMAL(12, 2) NOT NULL,
  PRIMARY KEY (id),
  KEY ix_venta_detalle_venta_id (venta_id),
  KEY ix_venta_detalle_variante_id (variante_id),
  CONSTRAINT ck_venta_detalle_cantidad CHECK (cantidad > 0),
  CONSTRAINT ck_venta_detalle_importes CHECK (
    precio_unitario >= 0 AND costo_unitario >= 0 AND precio_minimo >= 0 AND comision >= 0
  ),
  CONSTRAINT fk_venta_detalle_venta FOREIGN KEY (venta_id) REFERENCES ventas (id),
  CONSTRAINT fk_venta_detalle_variante FOREIGN KEY (variante_id) REFERENCES variantes (id)
) ENGINE=InnoDB;

CREATE TABLE cobros (
  id INT NOT NULL AUTO_INCREMENT,
  venta_id INT NOT NULL,
  medio ENUM('efectivo', 'transferencia') NOT NULL,
  monto DECIMAL(12, 2) NOT NULL,
  usuario_id INT NOT NULL,
  fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_cobros_venta_id (venta_id),
  KEY ix_cobros_usuario_id (usuario_id),
  CONSTRAINT ck_cobros_monto CHECK (monto > 0),
  CONSTRAINT fk_cobros_venta FOREIGN KEY (venta_id) REFERENCES ventas (id),
  CONSTRAINT fk_cobros_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB;

CREATE TABLE liquidaciones (
  id INT NOT NULL AUTO_INCREMENT,
  vendedor_id INT NOT NULL,
  periodo VARCHAR(7) NOT NULL,
  total DECIMAL(12, 2) NOT NULL,
  creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uq_liquidacion_periodo UNIQUE (vendedor_id, periodo),
  CONSTRAINT ck_liquidaciones_total CHECK (total >= 0),
  CONSTRAINT ck_liquidaciones_periodo CHECK (periodo REGEXP '^[0-9]{4}-(0[1-9]|1[0-2])$'),
  CONSTRAINT fk_liquidaciones_vendedor FOREIGN KEY (vendedor_id) REFERENCES usuarios (id)
) ENGINE=InnoDB;

CREATE TABLE categorias_gasto (
  id INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(80) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT uq_categorias_gasto_nombre UNIQUE (nombre)
) ENGINE=InnoDB;

CREATE TABLE gastos (
  id INT NOT NULL AUTO_INCREMENT,
  fecha DATE NOT NULL,
  categoria_id INT NOT NULL,
  descripcion VARCHAR(255) NULL,
  monto DECIMAL(12, 2) NOT NULL,
  usuario_id INT NOT NULL,
  PRIMARY KEY (id),
  KEY ix_gastos_fecha (fecha),
  KEY ix_gastos_categoria_id (categoria_id),
  KEY ix_gastos_usuario_id (usuario_id),
  CONSTRAINT ck_gastos_monto CHECK (monto >= 0),
  CONSTRAINT fk_gastos_categoria FOREIGN KEY (categoria_id) REFERENCES categorias_gasto (id),
  CONSTRAINT fk_gastos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB;

-- Vista para consultar ventas confirmadas con sus costos y comisiones históricos.
CREATE VIEW v_ventas_detalle AS
SELECT
  v.id AS venta_id,
  DATE(v.fecha) AS dia,
  v.fecha,
  v.ubicacion_id,
  v.vendedor_id,
  vd.variante_id,
  vd.cantidad,
  vd.cantidad * vd.precio_unitario AS vendido,
  vd.cantidad * vd.costo_unitario AS costo,
  vd.comision
FROM ventas AS v
JOIN venta_detalle AS vd ON vd.venta_id = v.id
WHERE v.estado = 'confirmada';