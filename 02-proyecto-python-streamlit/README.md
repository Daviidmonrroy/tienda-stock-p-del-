# Vibra Deportiva · Python, Streamlit y MySQL

Migración del sistema para la cursada: Python, Streamlit, MySQL, SQLAlchemy y bcrypt.
Plan completo: `../docs/migracion/00-auditoria-y-plan.md`. Informe de lo hecho: `../docs/migracion/01-etapas-3-a-5.md`.

**Estado: etapas 3, 4 y 5 escritas (modelo, configuración, autenticación y usuarios).**
Lo que se ejecutó y lo que falta ejecutar está detallado en el informe. Resumen: las pruebas que no necesitan librerías
externas pasaron (62); el resto (SQLAlchemy, bcrypt, MySQL, Streamlit) **todavía no se ejecutó** y hay que probarlo en una
computadora con todo instalado.

## Preparar la computadora

1. Python 3.11 o más nuevo, Git y Docker Desktop (o un MySQL 8 instalado).
2. Desde esta carpeta:

```
python -m venv .venv
# Windows:      .venv\Scripts\activate
# Mac o Linux:  source .venv/bin/activate

pip install -r requirements.txt

copy .env.example .env        # Mac o Linux: cp .env.example .env
# Editar .env: poner claves propias en DB_PASSWORD y DB_ROOT_PASSWORD

docker compose up -d          # levanta MySQL (solo si se usa Docker)
```

## Probar paso a paso (en este orden)

```
python -m pytest -q                     # 1. pruebas. Debe decir: passed, sin skipped si todo está instalado
python -m scripts.crear_tablas          # 2. crea las tablas en MySQL
python -m scripts.crear_admin           # 3. crea el primer administrador (la clave no se muestra)
streamlit run app.py                    # 4. abre la app en el navegador
```

Si un paso falla, copiar el error completo (sin mostrar el contenido de `.env`) y pasarlo.

## Estructura

```
app.py            punto de entrada de Streamlit
config/           Settings (dataclass frozen + slots) y variables de entorno
database/         DeclarativeBase, create_engine, sessionmaker, session_scope
models/           Usuario, PerfilUsuario (1 a 1), Zona
repositories/     consultas (incluye UPDATE con text())
services/         reglas de negocio: auth, usuarios, zonas, permisos
views/            pantallas de Streamlit: login, usuarios
utils/            excepciones, validaciones (regex), dinero (Decimal), seguridad (bcrypt), estilos
scripts/          crear_tablas, crear_admin (consola: getpass, __main__, SystemExit)
sql/schema.sql    esquema completo revisado (nivel físico de referencia)
tests/            pytest
```
