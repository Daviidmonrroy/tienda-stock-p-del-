# 04 — Revisión de login y registro

## Problema planteado
El prompt pide los procesos completos de login y registro, con sus vistas.

## Resultado del escaneo
Ya existían: `views/login.py` (login), `views/usuarios.py` pestaña "Nuevo usuario" (registro) y
`services/auth_service.py` (validación, bcrypt, bloqueo tras 5 intentos fallidos, email duplicado).
Decisión: el registro lo hace solo un administrador (el negocio no tiene autoservicio de altas). El primer admin se crea
con `scripts.crear_admin` o con la semilla. Con el rol nuevo, el administrador también puede dar de alta auditores desde
esa pestaña (la lista de roles sale de `ROLES`).
No se modificó el flujo existente.
