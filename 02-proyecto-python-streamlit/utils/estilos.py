"""Identidad visual de Vibra Deportiva para Streamlit (colores del manual de marca)."""
import base64
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSS = """
<style>
:root { --rojo:#D12E2B; --negro:#0B1015; --humo:#F3F1F2; }
[data-testid="stSidebar"] { background: var(--negro); }
[data-testid="stSidebar"] * { color: #F1EFF0 !important; }
h1, h2, h3 { letter-spacing: -0.01em; font-weight: 800; }
.stButton > button, .stFormSubmitButton > button { border-radius: 6px; font-weight: 700; }
div[data-testid="stMetric"] { background:#fff; border:1px solid #DDD9DC; border-radius:8px; padding:12px 14px; }
</style>
"""


def aplicar_estilos(st) -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def logo_html(archivo: str = "logo-horizontal-sobre-blanco.svg", ancho: int = 260) -> str:
    """Devuelve el logo como <img> con el SVG embebido en base64 (no depende de rutas del navegador)."""
    ruta = RAIZ / "assets" / archivo
    if not ruta.exists():
        return ""
    datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f'<img src="data:image/svg+xml;base64,{datos}" width="{ancho}" alt="Vibra Deportiva">'
