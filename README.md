# Vibra Deportiva · Sistema de stock y ventas

Sistema de gestión para una tienda de pádel: productos, stock por ubicación (local y cancha), compras, ventas,
vendedores por zona, comisiones y panel de resúmenes para el dueño.

> Repositorio público: no subir contraseñas, archivos `.env`, datos de clientes ni ventas reales.

## Carpetas

| Carpeta | Contenido |
|---|---|
| `01-proyecto-original-node/` | Primera versión (Node + HTML + diseño MySQL). Quedó completa, sin cambios de código. |
| `02-proyecto-python-streamlit/` | Migración a Python, Streamlit, MySQL, SQLAlchemy y bcrypt para la cursada. **Proyecto activo.** Etapas 3 a 5 escritas, pendientes de probar con todo instalado. |
| `docs/negocio/` | Respuestas del dueño y preguntas abiertas. |
| `docs/migracion/` | Auditoría, plan de migración por etapas e informes de cada etapa. |
| `docs/marca/` | Manual de marca (PDF). |
| `brand/` | Logos, avatar, íconos y favicon en SVG y PNG. |

## Por dónde seguir
1. Leer `docs/migracion/00-auditoria-y-plan.md`.
2. Preparar la computadora con `02-proyecto-python-streamlit/README.md`.

## Decisiones del negocio (valen para las dos versiones)
- Roles: administrador, empleado (local o cancha) y vendedor.
- Dos ubicaciones con stock propio: local y cancha. Cada vendedor suma una "mochila" propia.
- El stock sale de un libro de movimientos, no de un número editable.
- Comisión: un porcentaje único de la venta, igual para todos los productos, liquidado por mes.
- Precio mínimo y máximo por producto. Cobros en efectivo, transferencia o fiado. Sin facturación AFIP.
- El costo se congela en cada venta para que la ganancia histórica no cambie.

Detalle en `docs/negocio/decisiones-del-dueno.md`.
