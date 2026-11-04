# Proyecto original (Node)

Primera versión del sistema. Se conserva completa como referencia y como especificación de la migración.

| Carpeta | Contenido |
|---|---|
| `prototipo-web/` | Demo de una sola página. Guarda los datos en el navegador. |
| `servidor-node/` | API con las reglas de negocio y 19 pruebas automáticas (`npm test`). Datos en memoria. |
| `base-de-datos/` | Esquema MySQL 8 (`schema.sql`). Nunca se ejecutó contra un servidor real. |
| `docs/arquitectura/` | Cómo se había pensado esta versión. |

Estado verificado: las 19 pruebas pasan (`cd servidor-node && npm test`). El servidor no está conectado a MySQL.
