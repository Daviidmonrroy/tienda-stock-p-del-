# Guía para defender el proyecto 2

Esta guía sigue los cuatro puntos de la consigna y describe el código que está en `02-proyecto-python-streamlit/`. Conviene acompañarla con una demostración breve de inicio de sesión, una venta y la consulta de stock.

## 1. Alcance del proyecto

### Problema que resuelve

Vibra Deportiva centraliza tareas de una tienda deportiva que, si se llevan por separado o en planillas, son difíciles de relacionar: catálogo y precios, existencias por ubicación, compras, ventas, cobros, clientes y resultados del negocio. El sistema deja registradas las operaciones para poder consultar qué pasó y quién las realizó.

### Funcionalidades que incluye el código

- Inicio de sesión, usuarios con roles y permisos.
- Catálogo de productos y variantes por talle/color, con SKU, precios y stock mínimo.
- Consulta de stock por ubicación: local, cancha o mochila de vendedor; transferencias y ajustes de inventario.
- Registro de compras a proveedores, que aumenta existencias y actualiza el costo vigente.
- Ventas, pagos en efectivo o transferencia, saldos pendientes (fiado), cobros posteriores y anulación con devolución de stock.
- Clientes y datos de proveedores.
- Comisiones de vendedores y panel de reportes para el dueño, con ventas, costos, comisiones, gastos y ganancia neta.
- Validaciones de datos y registro de movimientos de stock.

La función de servicio para importar variantes desde filas de una planilla existe en `services/catalogo_service.py`; la pantalla actual de catálogo todavía no ofrece la carga de un archivo. El stock inicial se ingresa mediante compras para conservar el historial de movimientos.

### Qué queda fuera o requiere confirmación

- No se integra con AFIP, facturación electrónica, tarjetas, bancos ni una pasarela de pago: se registran montos y medios, no se procesa dinero.
- No hay aplicación móvil ni acceso de clientes; es una interfaz web interna hecha con Streamlit.
- La importación directa de Excel/CSV desde la interfaz no está conectada.
- El sistema depende de configurar y levantar MySQL (o la base indicada en la configuración). El esquema de referencia está en `sql/schema.sql`.
- El repositorio documenta que la integración externa (Streamlit, SQLAlchemy, bcrypt y MySQL) necesita verificarse en una computadora con las dependencias y la base configuradas. No presentar esa instalación como validada si no se ejecutó allí.

## 2. Lógica de negocio

### Roles y permisos

Los roles actuales son `admin`, `empleado` y `vendedor`. El administrador puede gestionar todas las funciones; empleado y vendedor tienen un conjunto limitado. El vendedor registra sus ventas desde su propia mochila y solo consulta sus operaciones permitidas. Los costos se ocultan a quien no tiene el permiso correspondiente.

Los permisos se revisan en dos lugares: la aplicación filtra las opciones del menú y cada servicio vuelve a exigir el permiso antes de ejecutar la operación. La segunda comprobación protege la regla aunque se invoque el servicio sin pasar por esa pantalla.

### Reglas principales

- Los precios se validan dentro del rango mínimo y máximo definido para la variante.
- Una venta no puede dejar el stock negativo. Se descuenta de la ubicación asociada a la venta.
- El importe pagado no puede superar el total. Si queda saldo pendiente, se exige un cliente identificado.
- Se guarda en la venta la comisión vigente y los valores relevantes del detalle para que cambios futuros del catálogo no reescriban operaciones pasadas.
- Una compra suma existencias y registra su movimiento; el costo de compra pasa a ser el costo vigente de la variante.
- Una transferencia descuenta en el origen y suma en el destino como una sola operación. Un ajuste deja un motivo.
- Anular una venta no borra el historial: crea movimientos de devolución y marca la venta como anulada.
- Tras cinco intentos fallidos de inicio de sesión la cuenta se bloquea hasta que un administrador la desbloquee.
- Las operaciones que modifican varias tablas usan una transacción: si algo falla, se revierte el conjunto y no queda una operación a medias.

### Cálculo del reporte

El servicio del panel suma ventas confirmadas del período, costos de los artículos vendidos, comisiones y gastos registrados. La ganancia neta se calcula con esos componentes. Las consultas de fechas usan un límite superior exclusivo para incluir completo el último día seleccionado.

## 3. Funcionamiento: de una acción al resultado

La aplicación sigue este recorrido general:

`Usuario → vista de Streamlit → servicio (reglas y permisos) → repositorio/SQLAlchemy → MySQL → resultado en la vista`

1. **Entrada:** `streamlit run app.py` carga configuración, aplica estilos y revisa si hay un usuario en `st.session_state`.
2. **Autenticación:** si no hay sesión, `views/login.py` recoge las credenciales y llama al servicio de autenticación. Este busca el usuario, compara el hash de contraseña con bcrypt y aplica el contador de intentos. Si es correcto, devuelve un `UsuarioSesion` liviano que queda en el estado de Streamlit.
3. **Navegación:** `app.py` arma las páginas visibles según los permisos del rol y llama a la función `mostrar()` de la vista elegida.
4. **Acción:** por ejemplo, al confirmar una venta, `views/ventas.py` reúne variante, cantidad, precio, descuento, ubicación, cliente y pagos, y llama a `ventas_service.registrar_venta()`.
5. **Reglas y persistencia:** el servicio vuelve a validar permiso y datos, calcula importes, revisa stock y registra venta, detalles, cobros y movimientos usando una sesión de base de datos.
6. **Cierre:** `session_scope()` confirma con `commit` si todo sale bien; ante una excepción hace `rollback` y siempre cierra la sesión.
7. **Respuesta:** la vista muestra confirmación o el error de negocio y luego puede consultar el nuevo saldo/historial.

Streamlit vuelve a ejecutar el archivo de entrada en cada interacción. Por eso los datos de sesión del usuario se guardan en `st.session_state`, en lugar de una variable global que se perdería al rerun. Los datos persistentes del negocio se guardan en MySQL.

## 4. Código y decisiones técnicas

### Estructura por capas

- `app.py`: configuración de la app, sesión, menú y selección de vistas.
- `config/`: carga de variables de entorno y configuración.
- `database/`: engine de SQLAlchemy, fábrica de sesiones y contexto transaccional.
- `models/`: modelos ORM que representan tablas y relaciones de la base de datos.
- `repositories/`: consultas y operaciones de acceso a datos reutilizables.
- `services/`: casos de uso y reglas del negocio; no dependen de que la acción venga de un botón particular.
- `views/`: formularios, tablas y mensajes de Streamlit.
- `utils/`: validaciones, dinero, seguridad y excepciones propias.
- `scripts/`: tareas de consola, por ejemplo crear tablas o el primer administrador.
- `sql/schema.sql`: definición de referencia del esquema; `tests/`: pruebas automatizadas.

### Tecnologías

- **Python:** lenguaje principal y permite expresar las reglas de negocio en funciones pequeñas.
- **Streamlit:** construye la interfaz web en Python, adecuada para un panel interno y formularios sin separar frontend y backend.
- **SQLAlchemy:** mapea clases Python a tablas y administra sesiones/transacciones; permite consultar datos sin concatenar SQL.
- **MySQL + PyMySQL:** guarda datos persistentes y permite que varias operaciones trabajen sobre el mismo catálogo y stock.
- **bcrypt:** almacena contraseñas como hashes lentos con salt; la contraseña original no se guarda.
- **python-dotenv:** carga configuración local desde el entorno/`.env`, para no poner contraseñas de base de datos en el código.
- **pytest:** ejecuta las pruebas automatizadas.

### Piezas para explicar en el código

- `session_scope()` en `database/connection.py`: concentra el ciclo de vida de la sesión y asegura commit, rollback y cierre. Así las vistas no tienen que repetir ese manejo.
- `UsuarioSesion` en `services/auth_service.py`: dataclass inmutable y pequeña. Se guarda en la sesión web sin mantener vivo un objeto ORM ligado a una sesión ya cerrada.
- `exigir_permiso()` en `services/permisos.py`: transforma la matriz de roles en una regla central; lanza una excepción si falta autorización.
- `stock_service.mover()`: es el núcleo común de entradas y salidas. Recibe una sesión existente, bloquea/consulta el saldo, evita negativos, actualiza el saldo y agrega el movimiento sin hacer commit propio. Así una venta o compra incluye ese cambio en su misma transacción.
- `ventas_service.registrar_venta()`: coordina validaciones, cálculo, venta/detalle, cobros y descuento de stock. La vista solo recoge los datos y presenta el resultado.
- `Decimal` en precios y pagos: evita errores de precisión binaria típicos de `float` en dinero.
- Excepciones propias como `ErrorDeValidacion`, `StockInsuficiente` y `PermisoDenegado`: expresan fallos esperables del negocio para que la interfaz pueda mostrarlos de forma entendible.
- Consultas parametrizadas en reportes: los valores de fechas se pasan por parámetros, no se concatenan en el SQL, lo que evita inyección por esos datos.

### Límite entre lo implementado y lo comprobado

El código describe las funcionalidades anteriores, pero el README del proyecto indica que la conexión completa con dependencias externas y MySQL debe probarse en el equipo de ejecución. Para la defensa, conviene poder distinguir “está implementado en el repositorio” de “lo ejecuté y comprobé en esta computadora”. Los resultados históricos de pruebas solo deben mencionarse con su fecha/contexto y sin presentarlos como una ejecución actual.

## Guion breve para la exposición

1. Presentar el problema y el alcance; señalar qué queda fuera.
2. Iniciar sesión con un rol y mostrar que las opciones dependen de sus permisos.
3. Mostrar catálogo/stock y explicar variante, ubicación y movimiento.
4. Registrar una venta; explicar validación de precio, stock, pagos y fiado.
5. Consultar el reporte y relacionar ventas, costos, comisión y gastos.
6. Abrir `app.py`, `services/ventas_service.py` y `database/connection.py` para recorrer interfaz, reglas y transacción.
