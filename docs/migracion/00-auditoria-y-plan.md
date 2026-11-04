# Etapa 1 y 2: auditoría del proyecto y propuesta de migración a Python

Fecha: 04/11/2026. Todavía no se escribió código de la migración: se espera aprobación.

## 0. Cómo se hizo la auditoría

Se revisó el repositorio completo (el ZIP original equivale a este repositorio) y se **ejecutó** lo que se podía ejecutar.

| Qué | Resultado verificado |
|---|---|
| `npm test` en `01-proyecto-original-node/servidor-node/` | 19 pruebas, 19 pasan (ejecutado el 04/11/2026) |
| `01-proyecto-original-node/base-de-datos/schema.sql` contra MySQL | **No se pudo ejecutar**: en el entorno de trabajo no hay MySQL ni el servicio de Docker |
| Prototipo `01-proyecto-original-node/prototipo-web/index.html` | Revisado leyendo el código. No se probó con un navegador en esta auditoría |
| Python, Streamlit, SQLAlchemy, bcrypt | **No están instalados y no se pueden instalar** en el entorno de trabajo (sin acceso a los paquetes). Sí hay Python 3.13 y pytest |

## 1. Diagnóstico del proyecto original

El repositorio tiene tres piezas que no están conectadas entre sí:

| Pieza | Tamaño | Estado real |
|---|---|---|
| `01-proyecto-original-node/prototipo-web/index.html` | 418 líneas | Demo de una página. Guarda en el navegador (localStorage) |
| `01-proyecto-original-node/servidor-node/` (Node) | ~250 líneas + 19 pruebas | Reglas de venta y login que funcionan, pero con datos **en memoria** |
| `01-proyecto-original-node/base-de-datos/schema.sql` | 24 tablas y 1 vista | Diseño completo, **nunca ejecutado** en un MySQL |

La base de datos y el servidor nunca se conectaron: el servidor no habla con MySQL.

### 1.1 Auditoría por punto

| # | Punto | Hallazgo |
|---|---|---|
| 1 | Estructura | Ordenada (`01-proyecto-original-node/prototipo-web/`, `01-proyecto-original-node/servidor-node/`, `01-proyecto-original-node/base-de-datos/`, `docs/`, `brand/`). La carpeta `app/` estaba vacía |
| 2 | Código del servidor | Capas separadas (dominio, auth, almacén, http). Sin dependencias externas. Solo 4 rutas: login, productos, stock, ventas |
| 3 | Reglas de negocio | Implementadas y probadas: precio dentro de [mínimo, máximo], stock suficiente, fiado exige cliente, comisión solo en ventas de vendedores, costo congelado en cada venta |
| 4 | Modelo de datos | Diseño sólido (ver sección 6). Faltan descuentos, estado de pago y algunas restricciones UNIQUE |
| 5 | Base MySQL | Escrita pero sin validar contra un servidor real |
| 6 | Entidades y relaciones | Bien definidas en el SQL. En el código existen solo en memoria |
| 7 | Validaciones | Del lado del servidor: precio, cantidad, medio de pago, fiado. No hay validación de emails, longitudes ni duplicados |
| 8 | Autenticación y permisos | Hash con scrypt, sesión firmada, 3 roles. No hay registro de usuarios ni cambio de clave ni límite de intentos |
| 9 | Ventas y comisiones | La venta calcula comisión con un % único. **El prototipo usa otro criterio** (% por vendedor): hay que unificar |
| 10 | Movimientos de stock | Solo ventas e ingresos manuales. Faltan compras, transferencias, devoluciones, pérdidas y ajustes en el código |
| 11 | Pruebas | 19 pruebas reales que sirven como especificación para la migración |
| 12 | Interfaz | Prototipo con identidad nueva (rojo/negro). Sin variantes, sin ubicaciones, sin login |
| 13 | Documentación | Buena: decisiones del dueño, arquitectura, manual de marca |

### 1.2 Estado de las funcionalidades

| Funcionalidad | Estado |
|---|---|
| Login, contraseñas hasheadas, roles | **Implementado** (servidor) |
| Ventas con validación de precio y stock | **Implementado** (servidor, en memoria) |
| Comisión de vendedor por venta | **Implementado** (servidor) |
| Fiado (saldo pendiente) | **Parcial**: se calcula el saldo, no hay cobros |
| Productos, categorías, marcas, zonas, proveedores, clientes | **Parcial**: alta en el prototipo, sin edición ni baja real |
| Compras | **Parcial**: solo en el prototipo y suma stock |
| Variantes (talle/color), ubicaciones, precio mín/máx | **Solo en el diseño SQL y el servidor**, no en el prototipo |
| Registro de usuarios | Falta |
| Stock del vendedor, asignaciones, transferencias, devoluciones | **Solo diseño SQL** |
| Liquidaciones de comisión | **Solo diseño SQL** |
| Gastos y ganancias | **Solo diseño SQL** |
| Panel y reportes | **Parcial**: básico en el prototipo |
| Descuentos, ventas pagadas/pendientes | Falta |

### 1.3 Problemas encontrados

1. El prototipo inserta texto del usuario en la página sin escapar (riesgo de inyección en el navegador).
2. El prototipo guarda dinero como número decimal de JavaScript.
3. El % de comisión es por vendedor en el prototipo y único en el servidor.
4. El servidor no tiene forma de crear usuarios fuera de la demo.
5. El SQL nunca se probó.

## 2. Qué conservar y qué corregir

**Conservar (se porta a Python):**
- El modelo de datos: libro de movimientos de stock, stock por ubicación, costo y precio mínimo congelados en cada venta.
- Las reglas de negocio de `01-proyecto-original-node/servidor-node/src/domain/` y las 19 pruebas, que pasan a ser las pruebas en `pytest`.
- Las decisiones del dueño (`docs/negocio/`).
- La identidad visual: colores, logos, íconos y manual de marca.

**Corregir:**
- Unificar la comisión: un solo % global (respuesta del dueño).
- Montos: pasar de centavos enteros a `DECIMAL(12,2)` con `Decimal`, que es lo que pide la cursada.
- Agregar descuentos y estado de pago (pagada/pendiente).
- Agregar restricciones `UNIQUE` faltantes (ver sección 6).
- Escapar siempre lo que ingresa el usuario (Streamlit ya lo hace por defecto).
- Agregar registro de usuarios y control de intentos de login.

**Se descarta, con justificación:**
- JWT y las rutas HTTP: en Streamlit la sesión vive en `st.session_state`.
- El identificador de venta para sincronizar sin conexión: Streamlit funciona siempre conectado.

## 3. Arquitectura propuesta en Python

Capas, de afuera hacia adentro:

```
views/  (Streamlit)  ->  services/  (reglas de negocio)  ->  repositories/  (consultas)  ->  models/ + MySQL
                              \-> utils/ (validaciones, seguridad, dinero, excepciones)
```

Reglas de la arquitectura:
- Las vistas no tienen SQL ni reglas de negocio: solo llaman a servicios.
- Los servicios abren la transacción y deciden `commit` o `rollback`.
- Los repositorios solo hacen consultas. No validan reglas.
- Se omite una capa `controllers/` porque en Streamlit la propia vista cumple ese papel y agregarla sería complejidad sin beneficio.

### Estructura de carpetas

```
vibra_deportiva/
├── app.py                      punto de entrada de Streamlit
├── requirements.txt
├── .env.example
├── .streamlit/config.toml      tema con los colores de la marca
├── config/
│   └── settings.py             @dataclass(frozen=True, slots=True) + variables de entorno
├── database/
│   ├── base.py                 DeclarativeBase
│   └── connection.py           create_engine, sessionmaker, session_scope
├── models/                     entidades ORM y relaciones
├── repositories/               consultas por entidad
├── services/                   auth, productos, stock, compras, ventas, comisiones, reportes
├── views/                      una página por módulo
├── utils/
│   ├── excepciones.py          excepciones propias
│   ├── seguridad.py            hash_password, verify_password (bcrypt)
│   ├── validaciones.py         regex, longitudes, emails
│   ├── dinero.py               Decimal
│   └── estilos.py              CSS de la marca
├── scripts/
│   └── crear_admin.py          consola: getpass + __main__ + SystemExit
├── sql/schema.sql              nivel físico (referencia)
└── tests/
```

El proyecto nuevo va en `02-proyecto-python-streamlit/`. El trabajo anterior quedó completo en `01-proyecto-original-node/`, sin borrar nada.

## 4. Dónde aplica cada contenido de la cursada

| Contenido | Dónde se usa | Cuándo **no** usarlo |
|---|---|---|
| `bcrypt`, `hash_password`, `verify_password` | `utils/seguridad.py` y `auth_service` | Nunca guardar texto plano |
| `DeclarativeBase`, `sessionmaker`, `create_engine` | `database/` | |
| `echo=True` | Solo en desarrollo, controlado por variable de entorno | En producción, porque muestra datos en el log |
| `session.close()` con `finally` | `session_scope` | |
| `flush()` | Para obtener el id de la venta antes de guardar sus detalles | No usarlo en lugar de `commit()` |
| `commit()` y `rollback()` | En los servicios que modifican varias tablas (venta, compra, transferencia, liquidación) | Para lecturas |
| `session.execute(text(...))` | Reportes con agregaciones (ventas por mes, ganancias), siempre con parámetros | Para operaciones comunes: ahí va el ORM |
| `Decimal` | Todos los montos | Nunca `float` para dinero |
| `re` | Email, código de producto, teléfono, nombre | |
| `UniqueConstraint` | Variantes, email, nombres | |
| `IntegrityError` | Capturado en servicios y convertido en una excepción propia con mensaje claro | |
| `@dataclass(frozen=True, slots=True)` | `Settings` y objetos de datos de solo lectura | Modelos ORM: `slots` no es compatible con SQLAlchemy |
| Excepciones propias y `raise` | `utils/excepciones.py` | |
| `strip()` y `lower()` | Limpieza de emails y nombres | |
| `getpass` | Solo en `scripts/crear_admin.py` (consola) | En Streamlit se usa `st.text_input(type="password")` |
| `SystemExit` | Solo en scripts de consola y al faltar configuración al iniciar | Dentro de Streamlit, que usa `st.stop()` y mensajes de error |
| `if __name__ == "__main__"` | Scripts de consola | `app.py` lo ejecuta Streamlit |
| `st.session_state` | Usuario logueado y formularios | Para datos permanentes: eso va en MySQL |
| Persistencia al recargar | Ver riesgo 2 | |
| Multitenant y `user_id` | Ver sección 4.1 | |
| Regex de color hexadecimal `^#[0-9a-fA-F]{6}$` | Campo `color_hex` de las variantes | |
| Relación 1 a 1 y `flush()` en el registro | Al registrar un usuario se crea su perfil en la misma transacción (ver sección 10) | |
| ANSI-SPARC | Físico: el servidor MySQL. Conceptual: el esquema SQL (tablas y relaciones), que el ORM representa. Aplicación: lo que ve cada rol en las vistas de Streamlit | |

### 4.1 Multitenant: una decisión que hay que tomar

Esta tienda es **un solo negocio**. Un multitenant real (varios negocios con datos separados) no lo necesita y agregaría complejidad. Propuesta: aplicar el **aislamiento por `user_id`** donde sí tiene sentido: cada vendedor solo ve sus ventas, su stock y sus comisiones, y cada empleado solo ve su sector. Así se demuestra el concepto sin inventar un requisito.

Si el profesor exige un multitenant completo (una tabla de negocios y `negocio_id` en cada tabla), se puede agregar, pero cambia todo el modelo. Hay que preguntarlo.

## 5. Comparación de tecnologías

| Aspecto | Original | Migración |
|---|---|---|
| Lenguaje | JavaScript (Node) | Python |
| Interfaz | HTML y JS propio | Streamlit, con CSS de la marca |
| Datos | Memoria / localStorage | MySQL |
| Acceso a datos | Ninguno | SQLAlchemy (ORM) |
| Contraseñas | scrypt | bcrypt |
| Sesión | Token JWT | `st.session_state` |
| Dinero | Enteros en centavos | `Decimal` y `DECIMAL(12,2)` |
| Pruebas | `node:test` | `pytest` |
| Uso en celular | Pensado como app instalable con modo sin conexión | Se abre en el navegador, **requiere conexión** |

## 6. Revisión del modelo de datos

Está en buena forma (tercera forma normal en general). Cardinalidades:
- 1 a N: categoría→producto, producto→variante, venta→ítems, compra→ítems, ubicación→movimientos.
- N a M resuelta con tabla intermedia: liquidación↔ítems de venta (`liquidacion_items`).
- 1 a 1: vendedor↔su "mochila" (ubicación). Falta marcarla como `UNIQUE`.

**Correcciones propuestas:**

| Cambio | Motivo |
|---|---|
| `UNIQUE (producto_id, talle, color)` en variantes | Evitar variantes duplicadas |
| `UNIQUE` en `ubicaciones.usuario_id` | Un vendedor tiene una sola mochila |
| `UNIQUE` en nombres de categoría, marca y zona | Control de duplicados |
| Montos a `DECIMAL(12,2)` | Lo pide la cursada |
| Agregar `descuento` en ventas | Funcionalidad pedida |
| Agregar `estado_pago` en ventas (pagada, pendiente) | Funcionalidad pedida |
| Quitar `uuid_cliente` | Ya no hay modo sin conexión |
| Agregar `intentos_fallidos` en usuarios | Control de login |
| Definir `ON DELETE RESTRICT` de forma explícita | Integridad referencial documentada |

`stock_actual` duplica lo que dicen los movimientos. Se mantiene a propósito, por velocidad, y se actualiza en la misma transacción que el movimiento. Hay que explicarlo ante el profesor como una desnormalización controlada.

## 7. Plan de migración por etapas

| Etapa | Contenido | Cómo se verifica |
|---|---|---|
| 3 | Revisión final del modelo y `schema.sql` | Se ejecuta en un MySQL real |
| 4 | Entorno: Python, Streamlit, MySQL, SQLAlchemy, `Settings` y conexión | Conexión real y `pytest` |
| 5 | Autenticación y usuarios | Pruebas de hash, login, roles |
| 6 | Categorías, marcas, productos y variantes | Pruebas de CRUD y duplicados |
| 7 | Stock y movimientos | Pruebas de stock insuficiente y transacciones |
| 8 | Compras | Ídem |
| 9 | Ventas | Se portan las 19 pruebas actuales |
| 10 | Vendedores y comisiones | Liquidación mensual |
| 11 | Dashboard y reportes | Revisión manual en pantalla |
| 12 | Pruebas finales, documentación y revisión | |

Al cerrar cada etapa: archivos creados, qué hace cada uno, conceptos de clase usados, salida real de las pruebas y errores encontrados.

## 8. Riesgos técnicos

1. **No puedo ejecutar el sistema nuevo en mi entorno.** Sin MySQL, Streamlit, SQLAlchemy ni bcrypt instalables, el código de esas capas lo escribo sin poder correrlo. Mitigación: (a) la lógica pura (regex, `Decimal`, comisión, reglas de venta) la escribo sin librerías externas y **sí la pruebo acá con `pytest`**; (b) el resto lo ejecutás vos en tu computadora con Docker o MySQL local y me pasás la salida; (c) en cada informe separo "ejecutado por mí" de "pendiente de que lo ejecutes". No voy a afirmar que algo funciona si no se corrió.
2. **Sesión al recargar:** `st.session_state` se pierde al recargar la página del navegador. Hay que resolver cómo persistir el login (una opción: un token firmado en la URL o una cookie). Requiere decidir con cuidado la seguridad.
3. **Sin modo sin conexión:** la idea de vendedores usando la app sin señal se pierde con Streamlit. Es una decisión que hay que aceptar.
4. **Doble clic:** Streamlit vuelve a ejecutar el script en cada interacción. Una venta podría guardarse dos veces. Hay que bloquear el botón mientras se guarda.
5. **Concurrencia de stock:** dos ventas simultáneas pueden vender la última unidad. Se resuelve bloqueando la fila (`with_for_update`).
6. **Permisos en cada página:** en Streamlit cada vista debe verificar el rol. Si se olvida una, queda abierta.
7. **Alcance:** son 12 etapas. Se prioriza primero el núcleo (usuarios, productos, stock, ventas).
8. **Secretos:** el repositorio es público. `.env` nunca se sube. Las claves de demo no se guardan en el código.
9. **Streamlit en producción:** sirve muy bien para el trabajo académico y un negocio chico. Para muchos usuarios simultáneos habría que evaluar otra opción más adelante.
10. **bcrypt** solo procesa los primeros 72 bytes de la clave: hay que validar la longitud máxima.

## 9. Preguntas que necesito que respondas antes de empezar

1. ¿Podés ejecutar Python, Streamlit y MySQL en tu computadora (o con Docker) para correr las pruebas y pasarme la salida?
2. (Resuelta por el temario de la clase del 29/10) Multitenant es aislamiento por `user_id` en una misma base de datos.
3. ¿Aceptás que la app necesite conexión (sin modo sin conexión)?
4. (Resuelta) El proyecto nuevo va en una carpeta aparte y el anterior quedó intacto en otra.

## 10. Contraste con el temario de octubre (13, 15, 20, 22, 27 y 29)

Contrastado el 04/11/2026 contra el resumen de clases que pasó un compañero. Es información de segunda mano: conviene confirmarla con los apuntes o el profesor.

| Clase | Contenido | Estado en el plan |
|---|---|---|
| 13/10 | bcrypt, `hash_password`, `verify_password`, `DeclarativeBase`, `sessionmaker`, conexión MySQL | Cubierto |
| 15/10 | `getpass`, `strip`, `lower`, excepciones propias, `raise` y `SystemExit`, `st.session_state`, `__main__` | Cubierto |
| 20/10 | `session_state` frente a variables normales, `dataclass(frozen=True)`, `echo=True`, `finally` y `close()` | Cubierto. Se agrega una demostración corta de por qué un diccionario normal se reinicia en cada ejecución |
| 22/10 | `Decimal`, regex de color hexadecimal, `UniqueConstraint` con `__table_args__`, `slots=True` | **Ajuste:** el regex de color no tenía lugar en el modelo. Se agrega `color_hex` a las variantes |
| 27/10 | `flush()` para obtener el id y crear el perfil, `text()` para actualizar contadores | **Ajuste:** faltaba el perfil de usuario (relación 1 a 1). Se agrega `perfiles_usuario`. El contador `intentos_fallidos` se actualiza con `text()` |
| 29/10 | Multitenant por `user_id`, ANSI-SPARC, validación de longitudes y email, `IntegrityError` | **Ajuste:** la definición de la clase coincide con la propuesta de la sección 4.1. Se corrigió el mapeo de ANSI-SPARC y se agrega validación del dominio del email |

Aclaración sobre la sesión: según el resumen de la clase del 20/10, `st.session_state` conserva los datos entre ejecuciones del script (cada clic). Eso es distinto de recargar el navegador con F5, que abre una sesión nueva. El riesgo 2 pasa a ser opcional, a menos que el profesor pida lo segundo.
