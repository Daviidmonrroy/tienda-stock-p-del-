# 01 — Entidades (dataclass)

## Problema planteado
El prompt pide crear las entidades faltantes y necesarias para trabajar con dataclass. El proyecto solo tenía modelos
del ORM (SQLAlchemy) y `UsuarioSesion`; faltaba una representación de usuario que no dependa de una sesión de base de datos.

## Código implementado
`02-proyecto-python-streamlit/models/entities.py`
- `PerfilEntidad(usuario_id, telefono)` y `UsuarioEntidad(id, nombre, email, rol, activo, zona_id, perfil)`, ambas
  `@dataclass(frozen=True, slots=True)`.
- `usuario_a_entidad(usuario)` convierte un `Usuario` del ORM en entidad (se llama dentro de la sesión abierta).

## Solución y por qué
- `frozen=True`: nadie modifica el dato por accidente. `slots=True`: menos memoria y no se agregan atributos nuevos.
- Se mantuvo la estructura del proyecto (`models/`) en vez de crear `src/`: el prompt dice no tocar nada más.
- El `CredencialSemilla` de la semilla quedó en `scripts/semilla.py` para poder probarlo sin SQLAlchemy.
- Estado: escrito, no ejecutado (faltaba SQLAlchemy en el entorno donde se programó).
