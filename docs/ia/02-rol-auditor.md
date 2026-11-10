# 02 — Rol auditor (solo lectura)

## Problema planteado
El prompt pide un usuario "auditor", pero el sistema tenía solo admin, empleado y vendedor.

## Código implementado
- `services/permisos.py`: nuevo rol `auditor` con `catalogo.ver`, `costos.ver`, `stock.ver_propio`, `stock.ver_todo`,
  `ventas.ver_propias`, `ventas.ver_todas`, `reportes.ver`. No puede editar, vender, comprar, anular, gestionar gastos
  ni usuarios.
- `models/usuario.py` y `sql/schema.sql`: el ENUM de `rol` incluye `auditor`.
- `views/reportes.py`: si el rol no puede gestionar gastos, solo se muestra la pestaña "Resumen" (evita que el auditor
  vea pestañas que fallarían por permisos).
- `tests/test_permisos.py`: `test_auditor_solo_lee` y el test de roles actualizado.

## Solución y por qué
Se definió "auditor = ver todo sin modificar nada" (decisión mía; el prompt no la especificaba). El permiso se verifica en los
servicios, no solo en la vista.
Atención: si ya creaste la tabla `usuarios` en MySQL antes de este cambio, el ENUM viejo no incluye `auditor`;
hay que recrear la tabla o hacer `ALTER TABLE usuarios MODIFY rol ENUM('admin','empleado','vendedor','auditor') NOT NULL;`.
