# 03 — Revisión de login y registro

## Problema planteado
El prompt pide los procesos completos de login y registro, con sus vistas.

## Resultado del escaneo
Ya existían: `views/login.py` (login), `views/usuarios.py` pestaña "Nuevo usuario" (registro) y
`services/auth_service.py` (validación, bcrypt, bloqueo tras 5 intentos fallidos, email duplicado).
Decisión: el registro lo hace solo un administrador (el negocio no tiene autoservicio de altas). El primer admin se crea
con `scripts.crear_admin` o con la semilla. No se modificó el flujo existente.
