# 03 — Semilla de admin y auditor

## Problema planteado
Hace falta un script que cree, si no existen, un admin y un auditor. Los emails están en `.env`, las claves en un `.txt`
(texto plano, solo desarrollo local) y en la base de datos las claves deben estar hasheadas.

## Código implementado
- `scripts/semilla.py` (`python -m scripts.semilla`):
  - `leer_claves(texto)` y `armar_credenciales(entorno, claves)`: funciones puras, probadas con pytest.
  - `sembrar(credenciales)`: consulta si el email existe; si no, crea el usuario con `auth_service.registrar_usuario`
    (que hashea con bcrypt). El admin se crea primero (`actor=None` solo vale para el primer admin) y luego inicia sesión
    para poder crear al auditor. Es idempotente.
- `scripts/semilla_usuarios.txt`: claves inventadas (`admin=Vibra-Admin-2026`, `auditor=Vibra-Audit-2026`). Está en `.gitignore`.
- `scripts/semilla_usuarios.example.txt`: plantilla que sí se sube al repo.
- `.env.example`: variables `ADMIN_EMAIL` y `AUDITOR_EMAIL`.
- `tests/test_semilla.py`.

## Solución y por qué
- Las claves del `.txt` nunca llegan a la base de datos en texto plano: pasan por bcrypt en el servicio.
- El `.txt` no se sube a GitHub porque el repositorio es público; en otra PC se copia el `.example` y se completa.
- Orden de uso: `.env` con `ADMIN_EMAIL`/`AUDITOR_EMAIL` → `python -m scripts.crear_tablas` → `python -m scripts.semilla`.
- Estado: las funciones puras se ejecutaron (pytest); `sembrar` y `main` no, por falta de SQLAlchemy y bcrypt.
