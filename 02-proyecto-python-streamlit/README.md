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
python -m scripts.crear_admin
streamlit run app.py
```

La suite debe ejecutarse en el mismo entorno donde están instaladas las dependencias. Luego hay que comprobar la conexión a la base y recorrer los flujos principales en la aplicación. No se afirma aquí un resultado de ejecución actual.

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
scripts/          crear tablas y primer administrador
sql/schema.sql    esquema de referencia
tests/            pruebas automatizadas
docs/guia-defensa.md explicación para la presentación
```
