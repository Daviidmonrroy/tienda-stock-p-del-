# Vibra Deportiva · Python, Streamlit y MySQL

Migración del sistema para la cursada: Python, Streamlit, MySQL, SQLAlchemy y bcrypt.

La [guía de defensa](docs/guia-defensa.md) explica el alcance, las reglas de negocio, el recorrido de las operaciones y las decisiones del código. También se conserva el [plan de migración](../docs/migracion/00-auditoria-y-plan.md) y el [informe histórico de etapas 3 a 5](../docs/migracion/01-etapas-3-a-5.md).

**Estado:** el repositorio contiene módulos para autenticación y usuarios, catálogo, stock, compras, ventas, clientes, comisiones y reportes. La disponibilidad de código no confirma por sí sola que la aplicación esté integrada y probada en una computadora: la conexión de Streamlit, SQLAlchemy, bcrypt y MySQL debe verificarse en el entorno donde se vaya a presentar.

## Preparar la computadora

1. Python 3.11 o más nuevo, Git y Docker Desktop (o un MySQL 8 instalado).
2. Desde esta carpeta:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Editá `.env` con claves propias para `DB_PASSWORD` y `DB_ROOT_PASSWORD`. No publiques ese archivo.

Si usás Docker para MySQL:

```powershell
docker compose up -d
```

## Ejecutar

En este orden:

```powershell
python -m pytest -q
python -m scripts.crear_tablas
python -m scripts.semilla
streamlit run app.py
```

- `python -m scripts.semilla` crea, si no existe, el administrador. El email sale de `ADMIN_EMAIL` en el `.env` y la clave del archivo `scripts/semilla_usuarios.txt` (copiar `scripts/semilla_usuarios.example.txt`; ese archivo no se sube a Git). En la base la clave queda hasheada con bcrypt. Alternativa interactiva: `python -m scripts.crear_admin`.
- **Esquema SQL alternativo:** en vez de `crear_tablas` se puede ejecutar `sql/schema.sql` en MySQL 8 sobre una base vacía. Usar uno u otro, no ambos sobre la misma base.
- **Modo demostración sin MySQL:** agregar `DB_ENGINE=sqlite` al `.env` usa un archivo local `vibra_demo.db`. No reemplaza a MySQL (no bloquea filas ni verifica claves foráneas estrictas). Ver `../docs/ia/04-modo-demo-sqlite.md`.

## Estado de verificación

- **Ejecutado:** el 10/11/2026 la suite completa dio **121 pruebas aprobadas, 0 fallas** (Codespaces, Python 3.14). Cubre validaciones, dinero, comisiones, permisos, configuración, bcrypt, login y el flujo completo (compra, transferencia, venta, fiado, anulación, liquidación y panel) contra SQLite.
- **Pendiente de verificar:** las pantallas de Streamlit en un navegador y el comportamiento sobre MySQL real.

Si un paso falla, guardar el error completo sin compartir el contenido de `.env`.

## Estructura

```
app.py            entrada de Streamlit: sesión, menú y permisos de navegación
config/           Settings y variables de entorno
database/         engine, sesiones y transacciones
models/           modelos ORM
repositories/     consultas y acceso a datos
services/         reglas de negocio y casos de uso
views/            pantallas de Streamlit
utils/            excepciones, validaciones, dinero, seguridad y estilos
scripts/          crear tablas, semilla del administrador, crear_admin
sql/schema.sql    esquema MySQL 8 completo (alternativa a crear_tablas)
tests/            pruebas automatizadas
docs/guia-defensa.md explicación para la presentación
../docs/ia/        registro detallado de cambios (problema, código, solución)
```
