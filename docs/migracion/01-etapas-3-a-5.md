# Informe de las etapas 3, 4 y 5

Fecha: 09/11/2026. Carpeta: `02-proyecto-python-streamlit/`.

## Qué se ejecutó de verdad y qué no

| Verificación | Resultado |
|---|---|
| `python -m pytest -q` en mi entorno | **62 pruebas pasaron**, 0 fallaron, **2 archivos omitidos** |
| Archivos omitidos | `test_seguridad.py` (falta bcrypt) y `test_auth_service_db.py` (falta SQLAlchemy). Son 4 y 16 pruebas aproximadamente que **no se corrieron** |
| Compilación de todo el código (`py_compile`) | Sin errores de sintaxis |
| `sql/schema.sql` en MySQL | **No ejecutado** |
| Modelos, repositorios, servicios con la base, vistas y `app.py` | **No ejecutados**: no se pueden instalar SQLAlchemy, bcrypt, Streamlit ni MySQL en mi entorno |

Lo que pasó es la lógica pura (validaciones, dinero, configuración, permisos). Todo lo que usa las librerías externas está
escrito siguiendo su forma documentada pero **no está probado**. Tiene que correrse en una computadora con todo instalado.

## Etapa 3: modelo de datos

`sql/schema.sql` (versión 0.3). Cambios respecto al diseño del proyecto 1:

| Cambio | Motivo |
|---|---|
| Montos `BIGINT` en centavos pasan a `DECIMAL(12,2)` | La cursada usa `Decimal` |
| Comisión: `comision_vendedor_pct` (por ejemplo `10.00`) en vez de puntos básicos | Más simple de explicar |
| Tabla nueva `perfiles_usuario` (1 a 1, `UNIQUE` en `usuario_id`) | Relación 1 a 1 y `flush()` en el registro |
| `usuarios.intentos_fallidos` | Bloqueo tras 5 intentos |
| `variantes.color_hex` con `CHECK` de regex y `UNIQUE (producto_id, talle, color)` | Regex de la clase y control de duplicados |
| `talle` y `color` pasan a `NOT NULL DEFAULT 'Único'` | En MySQL un `UNIQUE` con `NULL` no evita duplicados |
| `UNIQUE` en `ubicaciones.nombre` y `ubicaciones.usuario_id` | Un vendedor tiene una sola mochila |
| `ventas.descuento` y `ventas.estado_pago` | Funcionalidades pedidas |
| Se quita `ventas.uuid_cliente` | Ya no hay modo sin conexión |

## Etapa 4: configuración

| Archivo | Qué hace | Concepto de clase |
|---|---|---|
| `config/settings.py` | `Settings` con los datos de conexión, leídos de variables de entorno. Falla con un mensaje claro si falta alguno | `@dataclass(frozen=True, slots=True)`, variables de entorno |
| `database/base.py` | Clase base de los modelos | `DeclarativeBase` |
| `database/connection.py` | `create_engine` (con `echo` configurable), `sessionmaker` y `session_scope` | engine, `echo=True`, `commit`, `rollback`, `finally` + `close()` |
| `scripts/crear_tablas.py` | Crea las tablas desde los modelos | `if __name__ == "__main__"`, `SystemExit` |
| `.env.example`, `docker-compose.yml`, `requirements.txt` | Entorno | |

## Etapa 5: autenticación y usuarios

| Archivo | Qué hace | Concepto de clase |
|---|---|---|
| `utils/excepciones.py` | Excepciones propias | excepciones propias, `raise` |
| `utils/validaciones.py` | Limpieza y validación de email (con dominio), nombre, clave (máx. 72 bytes), color hexadecimal y teléfono | `strip`, `lower`, `re`, longitudes |
| `utils/dinero.py` | `Decimal`, redondeo, comisión y formato en pesos | `Decimal` |
| `utils/seguridad.py` | `hash_password` y `verify_password` | bcrypt |
| `models/usuario.py`, `models/zona.py` | `Usuario`, `PerfilUsuario` (1 a 1), `Zona` | relaciones ORM, `UniqueConstraint` y `__table_args__` |
| `repositories/usuario_repository.py` | Consultas. El contador de intentos usa `UPDATE` con `text()` | `session.execute(text(...))` |
| `services/permisos.py` | Permisos por rol, verificados en los servicios | roles y permisos |
| `services/auth_service.py` | Registro (usuario y perfil en una transacción con `flush`) y login con bloqueo | `flush`, `IntegrityError`, transacciones |
| `services/usuario_service.py`, `zona_service.py` | Listar, activar, desbloquear usuarios; zonas | aislamiento por permisos |
| `views/login.py`, `views/usuarios.py`, `views/guardia.py`, `app.py` | Pantallas de Streamlit | `st.session_state` |
| `scripts/crear_admin.py` | Crea el primer administrador por consola | `getpass`, `SystemExit` |
| `tests/` | 6 archivos de pruebas | |

## Decisiones que conviene confirmar

1. **No hay registro público.** El primer administrador se crea por consola y los demás usuarios los crea un administrador.
   Se hizo así porque el dueño maneja a vendedores y empleados. Si el profesor pide un registro abierto, se agrega.
2. **Bloqueo a los 5 intentos fallidos.** Un administrador desbloquea desde la pantalla de usuarios.
3. **Un vendedor necesita una zona** (ciudad) al crearse.
4. **La sesión vive en `st.session_state`.** Si se recarga el navegador con F5 se pierde el login.

## Errores y riesgos encontrados

- Con `st.dataframe(..., use_container_width=True)`, las versiones nuevas de Streamlit pueden mostrar un aviso de uso obsoleto. No rompe nada.
- `bcrypt` solo procesa 72 bytes: se valida el máximo y se rechaza lo que lo supere.
- `iniciar_sesion` lanza las excepciones **después** de cerrar el bloque `with`, para que el rollback no deshaga el contador de intentos.

## Criterio para pasar a la etapa 6

Antes de avanzar a productos, categorías y variantes: correr los 4 pasos del README de la carpeta y confirmar que `pytest`
pasa sin pruebas omitidas, que se crea el administrador y que se puede iniciar sesión y crear un usuario desde la pantalla.
