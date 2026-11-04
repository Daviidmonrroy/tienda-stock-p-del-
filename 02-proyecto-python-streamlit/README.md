# Vibra Deportiva · Python, Streamlit y MySQL

Migración del sistema para la cursada: Python, Streamlit, MySQL, SQLAlchemy y bcrypt.

**Estado: preparación del entorno.** Todavía no hay código de la aplicación. Esta carpeta solo tiene lo necesario
para dejar lista la computadora. El plan está en `../docs/migracion/00-auditoria-y-plan.md`.

## Qué instalar en la computadora (checklist para probar)

1. **Python 3.11 o más nuevo.** Comprobar con `python --version` (en Windows, a veces `py --version`).
2. **MySQL 8.** Hay dos caminos; alcanza con uno:
   - **Docker Desktop** (recomendado): usar el `docker-compose.yml` de esta carpeta.
   - **MySQL instalado directamente** (por ejemplo, el de XAMPP o MySQL Installer).
3. **Git**, para clonar el repositorio.

## Pasos

```
git clone https://github.com/Daviidmonrroy/tienda-stock-p-del-.git
cd tienda-stock-p-del-/02-proyecto-python-streamlit

python -m venv .venv
# Windows:      .venv\Scripts\activate
# Mac o Linux:  source .venv/bin/activate

pip install -r requirements.txt

copy .env.example .env        # en Mac o Linux: cp .env.example .env
# Editar .env y poner una clave propia en DB_PASSWORD

docker compose up -d          # solo si se usa Docker
```

## Qué mirar y pasarme (para la próxima etapa)

- Salida de `python --version` y de `pip install -r requirements.txt` (si dio algún error, copiarlo completo).
- Si MySQL arrancó: `docker compose ps` o el nombre del programa que se usó.
- Cualquier mensaje de error, sin tachar. **Nunca copiar el contenido del archivo `.env`**.

> Los archivos de esta carpeta (`requirements.txt`, `docker-compose.yml`, `.env.example`) **todavía no se ejecutaron**:
> no pude instalar Python ni MySQL en mi entorno de trabajo. Si algo falla, es un dato útil: pasame el error.
