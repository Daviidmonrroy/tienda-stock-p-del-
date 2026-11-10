# 04 — Modo demostración con SQLite (opcional)

## Problema planteado
En la PC donde se probó el proyecto no había Docker (la virtualización estaba desactivada) ni MySQL instalado.

## Código implementado
- `config/settings.py`: variable `DB_ENGINE` (`mysql` por defecto, o `sqlite`). Con `sqlite` no se piden usuario ni clave de
  base de datos y la URL es `sqlite:///<DB_NAME>.db` (por defecto `vibra_demo.db`).
- `database/connection.py`: para SQLite se pasa `check_same_thread=False` (Streamlit usa varios hilos).
- `.env.example` (línea comentada) y `.gitignore` (`*.db`). Tests nuevos en `tests/test_settings.py`.

## Solución y límites
- Se activa agregando `DB_ENGINE=sqlite` al `.env`. El resto de los pasos no cambia (`crear_tablas`, `semilla`, `streamlit run`).
- Es solo para demostrar o probar rápido. El sistema definitivo usa MySQL: no hay bloqueo de filas (`with_for_update` se
  ignora), no se verifican claves foráneas por defecto y `Numeric` se guarda como decimal aproximado.
- Estado: la configuración se probó con pytest; la conexión real a SQLite con la app no se ejecutó.
