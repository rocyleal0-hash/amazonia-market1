# ==========================================================
# AMAZONIA MARKET - App de escritorio para agregar productos
# ==========================================================
# Al ejecutar este archivo se abre una ventana de Tkinter con los
# APARTADOS (categorías) de la tienda. Desde ahí puedes:
#     - Crear un nuevo apartado (ej: Bisutería, Charcutería)
#     - Entrar a un apartado y agregar productos dentro
#     - Eliminar productos o apartados
#     - Editar la página web (nombre, logo, colores, anuncios, etc.)
#
# Los cambios se guardan directamente en los JSON que lee tu web
# (index.html + styles.css + app.js):
#     products.json, categories.json, category_styles.json,
#     site_settings.json, anuncios.json  +  carpeta product_images/
#
# Para publicar los cambios en tu tienda de GitHub Pages:
#   1) Edita lo que quieras aquí.
#   2) Sube a tu repo los JSON modificados y la carpeta
#      product_images/ (arrastra los archivos en GitHub o usa git).
#   3) GitHub Pages actualiza la tienda automáticamente.
#
# Botón "Abrir tienda" abre tu web (por defecto el index.html
# local para vista previa; cambia STORE_URL más abajo si prefieres
# abrir tu URL de GitHub Pages).
#
# Ejecutar:
#     python agregar_producto.py
#
# Requisitos:  pip install pillow windnd
#   (windnd es opcional; habilita arrastrar y soltar imágenes
#    desde el navegador o el explorador de Windows.)
# ==========================================================

import base64
import io
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.request
import uuid
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageTk

# Drag & drop opcional (Windows). Si no está instalado, la app
# sigue funcionando y solo se puede insertar imagen con el botón.
try:
    import windnd  # type: ignore
    _HAS_WINDND = True
except Exception:
    windnd = None  # type: ignore
    _HAS_WINDND = False

# Carpeta base: cuando corre como .exe (PyInstaller) usa la carpeta del .exe,
# cuando corre como .py usa la carpeta del script. Así encuentra los .json
# y product_images/ siempre que estén junto al ejecutable.
import sys as _sys
if getattr(_sys, 'frozen', False):
    BASE_DIR = Path(_sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).parent.resolve()
try:
    os.chdir(BASE_DIR)
except Exception:
    pass
DATA_FILE      = BASE_DIR / "products.json"
CATS_FILE      = BASE_DIR / "categories.json"
IMG_DIR        = BASE_DIR / "product_images"
CAT_IMG_DIR    = BASE_DIR / "cat_images"
TIENDA_PY      = BASE_DIR / "tienda.py"
IMG_DIR.mkdir(exist_ok=True)
CAT_IMG_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------
# URL de la tienda para el botón "Abrir tienda en el navegador".
# Por defecto abre el index.html local (vista previa).
# Si quieres abrir tu tienda publicada en GitHub Pages, cambia
# STORE_URL por tu URL, por ejemplo:
#     STORE_URL = "https://tu-usuario.github.io/tu-repo/"
# ----------------------------------------------------------
LOCAL_INDEX = BASE_DIR / "index.html"
STORE_URL   = "https://rocyleal0-hash.github.io/amazonia-market1/"

# --- Personalización de la página web (nombre + logo pequeño) ---
SETTINGS_FILE    = BASE_DIR / "site_settings.json"
CUSTOM_LOGO_FILE = BASE_DIR / "site_logo.png"
CAT_STYLES_FILE  = BASE_DIR / "category_styles.json"
TITLES_FILE      = BASE_DIR / "titles_settings.json"
CART_FILE        = BASE_DIR / "cart.json"
ANUNCIOS_FILE    = BASE_DIR / "anuncios.json"

# --- Familias de tipografia disponibles (mismas cargadas en la tienda) ---
FONT_FAMILIES = [
    "Poppins", "Pacifico", "Montserrat", "Playfair Display", "Bebas Neue",
    "Lobster", "Oswald", "Roboto", "Dancing Script", "Great Vibes",
    "Anton", "Merriweather", "Raleway", "Arial", "Georgia", "Times New Roman",
    "Courier New", "Verdana",
]

# --- Emojis frecuentes para elegir icono del apartado ---
ICON_CHOICES = [
    # Generales / etiquetas
    "🏷️","🛒","🛍️","🧾","🏬","🏪","📦","🎁",
    # VIVERES / abarrotes
    "🌾","🍚","🫘","🥫","🍝","🧂","🫒","🥣","🍯","🥖","🥔","🧅","🧄",
    # CONFITERIA / dulces
    "🍫","🍬","🍭","🍩","🧁","🍰","🎂","🍪","🍮","🍨","🍦","🍿",
    # LIMPIEZA
    "🧽","🧴","🧼","🧹","🧺","🪣","🧻","🧯","🚿",
    # BEBIDAS
    "🥤","🧃","🧉","🍶","🍾","🍷","🍺","🍻","🥂","🥃","🍹","🍸","☕","🫖","🧋","💧",
    # HIGIENE PERSONAL
    "💊","🪥","🪒","🧻","🧴","💄","🧖","🪞","🧿","🩹","🩺",
    # ESCOLAR
    "📚","📖","📓","📒","📝","✏️","🖊️","🖍️","📐","📏","🎒","🖇️","📎","📌","✂️","🖌️",
    # JUGUETERIA
    "🧸","🪀","🪁","🎲","🎯","🎮","🕹️","🧩","🚗","🚕","🚙","🚌","🚂","✈️","🛩️","⚽","🏀","🎨",
    # QUINCALLERIA / ferretería / hogar
    "🔧","🔩","🔨","🪛","🪚","🪓","⚙️","🧰","🔦","🔌","💡","🪞","🪟","🖼️","🕯️","🔋","📿",
    # LACTEOS
    "🥛","🧀","🧈","🍼","🐄","🥚",
    # Otros útiles
    "🍎","🍌","🍇","🍊","🍓","🍉","🍒","🍍","🥭","🥑","🥕","🌽","🍅","🥦",
    "🍞","🥐","🥨","🥯","🍕","🍔","🍟","🌭","🥗","🥩","🍗","🍖","🍳","🥞",
    "👕","👗","👖","👟","👠","👜","👒","🕶️","💍","💎",
    "📱","💻","⌨️","🖥️","🖨️","🎧","📷","📺","🔊",
    "🐾","🌸","🌹","🌻","🌵","🍀","🌟","⭐","❤️","🔥","✨",
]


def load_site_settings() -> dict:
    defaults = {"site_name": "Amazonia", "site_market": "MARKET", "site_logo_b64": ""}
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                defaults.update({k: v for k, v in data.items() if isinstance(v, str) and v.strip()})
        except Exception:
            pass
    return defaults

def save_site_settings(name: str, market: str, logo_b64: str | None = None, remove_logo: bool = False,
                       bg_b64: str | None = None, remove_bg: bool = False,
                       bg_brightness: float | None = None, bg_opacity: float | None = None,
                       hero_bg_b64: str | None = None, remove_hero_bg: bool = False,
                       hero_bg_color: str | None = None, hero_brightness: float | None = None,
                       hero_opacity: float | None = None,
                       logo_align: str | None = None, logo_size: int | None = None,
                       logo_offset_x: int | None = None,
                       img_border_color: str | None = None, img_border_width: int | None = None,
                       cart_card_bg: str | None = None,
                       cart_name_color: str | None = None,
                       cart_unit_color: str | None = None,
                       cart_price_bg: str | None = None,
                       cart_price_fg: str | None = None):
    # Conserva el logo y el fondo dentro del JSON para que funcione también en
    # GitHub / Streamlit Cloud, donde los archivos locales de tu PC no existen.
    data = load_site_settings()
    # Nombre y "segunda palabra" son OPCIONALES. Si el usuario los deja
    # vacios, la tienda no mostrara texto (util cuando solo se quiere el logo).
    data["site_name"] = name.strip()
    data["site_market"] = market.strip()
    if remove_logo:
        data.pop("site_logo_b64", None)
    elif logo_b64 is not None:
        data["site_logo_b64"] = logo_b64
    if remove_bg:
        data.pop("site_bg_b64", None)
    elif bg_b64 is not None:
        data["site_bg_b64"] = bg_b64
    if bg_brightness is not None:
        data["site_bg_brightness"] = f"{float(bg_brightness):.2f}"
    if bg_opacity is not None:
        data["site_bg_opacity"] = f"{float(bg_opacity):.2f}"
    # --- Fondo del HERO (la banda superior detras del nombre y logo) ---
    if remove_hero_bg:
        data.pop("hero_bg_b64", None)
    elif hero_bg_b64 is not None:
        data["hero_bg_b64"] = hero_bg_b64
    if hero_bg_color is not None:
        data["hero_bg_color"] = hero_bg_color.strip()
    if hero_brightness is not None:
        data["hero_brightness"] = f"{float(hero_brightness):.2f}"
    if hero_opacity is not None:
        data["hero_opacity"] = f"{float(hero_opacity):.2f}"
    # --- Logo: alineacion y tamano ---
    if logo_align is not None:
        data["logo_align"] = logo_align if logo_align in ("left", "center", "right") else "left"
    if logo_size is not None:
        data["logo_size"] = str(int(logo_size))
    if logo_offset_x is not None:
        data["logo_offset_x"] = str(int(logo_offset_x))
    # --- Borde de las imagenes de producto ---
    if img_border_color is not None:
        data["img_border_color"] = img_border_color.strip()
    if img_border_width is not None:
        data["img_border_width"] = str(int(img_border_width))
    # --- Colores del CARRITO ---
    if cart_card_bg is not None:
        data["cart_card_bg"] = cart_card_bg.strip()
    if cart_name_color is not None:
        data["cart_name_color"] = cart_name_color.strip()
    if cart_unit_color is not None:
        data["cart_unit_color"] = cart_unit_color.strip()
    if cart_price_bg is not None:
        data["cart_price_bg"] = cart_price_bg.strip()
    if cart_price_fg is not None:
        data["cart_price_fg"] = cart_price_fg.strip()
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ----------------------------------------------------------
# Titulos configurables (bloques con texto/fuente/color/tam)
# ----------------------------------------------------------
def load_titles() -> list:
    if TITLES_FILE.exists():
        try:
            data = json.loads(TITLES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                out = []
                for b in data:
                    if not isinstance(b, dict): continue
                    out.append({
                        "text":   str(b.get("text",   "")),
                        "font":   str(b.get("font",   "Poppins")),
                        "size":   int(b.get("size",   28)),
                        "color":  str(b.get("color",  "#FFFFFF")),
                        "weight": str(b.get("weight", "700")),
                    })
                return out
        except Exception:
            pass
    return []


def save_titles(blocks: list) -> None:
    TITLES_FILE.write_text(
        json.dumps(blocks, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ----------------------------------------------------------
# Estilos por apartado (icono, colores, tamanos)
# ----------------------------------------------------------
DEFAULT_CAT_STYLE = {
    "icon":         "",
    "circle_color": "#2A2A9C",
    "circle_size":  96,
    "label_color":  "#0F172A",
    "label_size":   14,
    "title_color":  "#2A2A9C",
    "title_size":   22,
    "more_bg":      "#2A2A9C",
    "more_fg":      "#FFFFFF",
    # NUEVO: permite mostrar una imagen dentro del circulo en lugar del icono/emoji
    "use_image":    False,
    "image_path":   "",   # ruta relativa dentro de product_images/
}

def load_cat_styles() -> dict:
    if CAT_STYLES_FILE.exists():
        try:
            data = json.loads(CAT_STYLES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def save_cat_styles(styles: dict) -> None:
    CAT_STYLES_FILE.write_text(
        json.dumps(styles, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_cat_style(cat: str) -> dict:
    styles = load_cat_styles()
    d = dict(DEFAULT_CAT_STYLE)
    if isinstance(styles, dict) and cat in styles and isinstance(styles[cat], dict):
        d.update(styles[cat])
    return d


def set_cat_style(cat: str, patch: dict) -> None:
    styles = load_cat_styles()
    cur = dict(DEFAULT_CAT_STYLE)
    cur.update(styles.get(cat, {}) if isinstance(styles.get(cat), dict) else {})
    cur.update(patch)
    styles[cat] = cur
    save_cat_styles(styles)


def rename_cat_style(old: str, new: str) -> None:
    styles = load_cat_styles()
    if old in styles:
        styles[new] = styles.pop(old)
        save_cat_styles(styles)


# ----------------------------------------------------------
# Guardar bloques sueltos de site_settings.json (fondo pagina, carrito,
# hide_logo, colores de secciones). No dependemos de save_site_settings
# para no romper la firma existente.
# ----------------------------------------------------------
def patch_site_settings(**kwargs) -> None:
    data = load_site_settings()
    for k, v in kwargs.items():
        if v is None:
            continue
        if v == "__REMOVE__":
            data.pop(k, None)
        else:
            data[k] = str(v) if not isinstance(v, str) else v
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ----------------------------------------------------------
# Renombrar apartado: mueve productos + estilo + limpia carrito
# ----------------------------------------------------------
def rename_category(old_name: str, new_name: str) -> bool:
    old_name = old_name.strip()
    new_name = new_name.strip()
    if not new_name or old_name == new_name:
        return False
    cats = load_categories()
    if any(c.lower() == new_name.lower() for c in cats if c != old_name):
        return False
    cats = [new_name if c == old_name else c for c in cats]
    save_categories(cats)
    prods = load_products()
    changed = False
    for p in prods:
        if p.get("categoria") == old_name:
            p["categoria"] = new_name
            changed = True
    if changed:
        save_products(prods)
    rename_cat_style(old_name, new_name)
    # limpiar carrito si existe
    try:
        if CART_FILE.exists():
            CART_FILE.unlink()
    except Exception:
        pass
    return True


# Paleta de marca
COLOR_PRIMARY   = "#4C1D95"
COLOR_PRIMARY_2 = "#7C3AED"
COLOR_ACCENT    = "#FFD400"
COLOR_BG        = "#F5F3FF"
COLOR_CARD      = "#FFFFFF"
COLOR_TEXT      = "#0F172A"
COLOR_MUTED     = "#64748B"

# ----------------------------------------------------------
# LOGO EMBEBIDO
# ----------------------------------------------------------
LOGO_B64 = """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fmFhQWuhyRNySkpKcOjQodTx48exYcMGbW3wDGU+AudTDfw6mJqawuTkJJaWll7ldfB5/f9169Y9u23btr/Zt28f6uvrszTh+daT+rJNmqtgMIipqSmcPHkSFy5ceGpyctJLPByeHS5JkiNXidLDED66V4vFUisIwhS9Nzkt9fX1x5966qkfP/HEE5TeyUo38uI9es4QzdnS0hJOnz6NK1eu/LnRaMTevXvjv/Irv6IhVjwpka9uIAOwmoCHdxbpGU1PT6O3txc9PT0d4XA4q86e9lhRUZGhra3tv/LQ/kqOt97ZovRJMBhEb28vBgcH/554Bvq8PZ9icDgc6OzsfPX48eNP7t+/HxUVFUilUppzzM+pvoMkDTKgCwsLGBwcxI9//GO89dZbVWNjY1O0DsxmMzZs2PDlz3zmM3/65JNPoqysDA6Hg0eSslI5/Lqj508cjsnJSVy5cgVXrlz5zYWFhQH+/OQRZ4vFgtLS0sqmpqbvFBYWHpuamnqhv7//66FQaEX785Eacn19YklJiWfv3r2Ln/70p7Fv3z7YbLasiIGXSiQY7UEQxGr0jj+sE8J7m3w0p6/R5AUYHlZel+vn+miG7o1KIs6cOYOf/vSnf3/z5s0veb1eqm307Ny58++6u7tRV1cHk8mkoSCr8eQEQcDIyAguX76M5eXlUx0dHac//elPY/v27ZqcLL9YPyjngOZndnaWSul+c3FxERaLBXV1dftPnDjxDrV1pcOaF29ZDWLCdxKj61taWkJfXx96enp+e3l52Z8LCidngRwat9tt6OjoOH348OHO7du3Y926dVn5L/7+9VE0GRleJz2RSKC3txf9/f24ePEibty48dter/flioqKrx49evRPEokEuru774Mic0U3vEEkQz47O4sbN24oZBC5vDJ2797tPX78OLZs2QK3252lhRCPxzE2NoYLFy7gX//1X397YmLixaWlpfvSC06nU1NFdDqd2LJly+mDBw9mvaa+OUuuw5vvezAyMoIrV65gcHDwreXlZS8dfHyax+12Y8OGDX9DcDSJ7fAkS55/oN8/iqJgamoKPT09uHjx4v81Njb2Ku+w8bBlppQ1a58/qIUmH8GmUinE4/ExfbRZXFyMXbt2vfKZz3wGDQ0NWaRZ3snTlyvy68vn82F4eBjvvvvuUiwWG966dWvf008/bd65cyeKioo0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KI8ZljMnMTUdo9zYv3CrMkUk92Bne356evpDx48f/5XJycn3Hzt2jNtuu40zZ85w/PhxItlPT0/fFIkPTx1Yaw/U1Pv9PktLS7z00ktcuHCBS5cu9V9//fXfvXr16h/euHHjwMZwWMinIvIKFZFX+KkReYym4sI0PT3NQw899Om/83f+zj956KGHeO9738vU1BTj4+PFAlZOw8cFP89zNjc32d3dZWdnh4WFBV599VUWFhZYWVmxV65c+YPl5eXPdDqd+TjTG6P28ihS2eo0z/Nio3BYE1YkhOHflSOut6KFPryYluvo7/TU6VtxRxsui7zRuRp2tYud4tF2tHw94oz3Gx3bYZup4WsTyyXxPo1uebFufuzYsY/Ozs5+IqTmR++44w7uuuuuouYenPWYmJg4tHcjy7LiXhORYnxtZWWFr33ta3zzm998+bnnnju/urpabEzihENF5BUqIq/w/wvKZFsm33LEOj09zT333PM7733ve//F+973Ph599FHOnDlTqGrFtHtMgUZLym63y8bGBlevXuXy5cssLCxw+fJlFhcX//Pm5uYXFxYW/ijWxPv9/k0NVj/uQlYthBXiPRn0/Kemp6c/NDU19VSr1Tp3//33f/j222/njjvu4PTp08zNzTE6OkoUyYmiMhHxMxIbMDc3N5mfn+eb3/wm3/72t1/+7ne/+9GFhYVL0Su9XI6KzXhxU1PeSB/mHldutqzu74rIK1R4QxIvpyyHx6rGx8eZnZ195KGHHvrCE088ceLxxx/n3LlzTE5OFmQfFyjwNdGtra0iYpmfny+IfHFx8S9WVlaeDl3la91ut4i2D+smr4i8wo+Ler1+kzhMvV4vOuaNMRw7duyXjx8//itzc3P/6O677+b2229ndnaWEydOcNtttxWRfSTZclYoSRLW1tZYWFjg0qVLXLx4kW9/+9tf/d73vvcrKysri+Uu90jsWZYV43hRsOhW92ulLFehIvIKb4pyZ21sPorRxOjoKA8//PCnH3vssX/y1FNPcf/993Ps2DFarVbRKBTrn+12m7W1NRYXF4umoMuXL19+5ZVXfrPT6bywtbW11G6337Kt51sVVKmIvMIbIW4G38hGN9rhpmnKkSNH5o4cOfKRI0eOfOTYsWP/6IknnuDYsWPMzc1x8uRJZmZmGBsbu0mkZjAYsL29zY0bN3j55Ze5cOECL7/88svf/OY3z0dZ37IT363G0yoir1AReYUfaaGLhC4i9Pt9arUad99990fuv//+p//hP/yHk/fffz/33nsvzWazULOKab/V1VWuX7/O/Pw83//+93nttddYWFj4l5cvX/7nq6urneGFqtzgVHb/erN6aIUKP5EFccg8ZnjOPfY/pGnK2NgYR44ceWx2dvYT99xzz2/dd9993H333Zw+fZqZmZmiwW5kZATwo2j9fp9Op1OUkZ555hlef/31fz0/P/+p1dXVIksQH1/Oht0qzV4ReYWKyCu8Icqp9WiSce7cud/+4Ac/+K+efPJJnnzySRqNRpFGj7X069evc/nyZS5cuMCVK1eYn5//s4WFhd9bX1+f39vbO6AxPbx4llPpZX/xisQr/Jck8FsRYLmhsV6vFwQbCb5WqzExMcGJEyc+dOedd/7ze++993133303s7OzPPDAAxw/fvwmhcLd3V3W1tZ46aWXmJ+f52tf+9ryCy+88NTy8vJ8dMw7rAv/h81AVZ+VisgrVDjQOXzq1KnmI4888uyTTz75vg984AM89NBDRY2x1+uxubnJysoKr776Ks8//zzf+973nr906dKnNjc3v7K5uXmTQUS5e/1WKfXDusLLEfrbXRmtwjuDwIcFX+I9F8VnotZBWbAGoNVqFQpwxhhGR0c5cuTI7IkTJ37tyJEjH3nPe97zwbvvvpv777+f2267rVCdixF3NOb5zne+w5e//GWee+65f3np0qXfiZ+XqtmtQkXkFX4iRD46Osodd9zxiUcfffQ/PPnkk/zcz/0cp0+fZmxsjK2tLbrdLsvLy7z88su88MILvPjii3/56quv/vb6+vrFdrt9YGY21tmjYtetFpo4MnSYO1R5IauIvMJPCmXp3YhI3uWsVMwYRWnXsvteHHGLzWvj4+OcPn36E+fPn/8P586d46677uLs2bPMzc0xPj7O5OQkIsL29javvPIKzz//PM8//zzf/e53/9vFxcVPb29vH9D6H94EV0ReASCpTkGFN1sIzp49+7GnnnrqP37kIx/hiSee4I477kBV2djYKNLnn//85/n85z//b//mb/7m783Pz//JxsbGSpzZLc8LDwt+DBuelNPow80/h80hV6jwk7zXhy1nh+/TqPJWVpyL42LlHo5I5Lu7u2xtbb1w5cqV3//BD37wZ6+//nprZWXl56Iv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"""


def clean_logo_image() -> Image.Image:
    raw = base64.b64decode(LOGO_B64)
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    px = img.load()
    w, h = img.size
    THRESH = 70
    for y in range(h):
        for x in range(w):
            r, g, b, _ = px[x, y]
            if r < THRESH and g < THRESH and b < THRESH:
                px[x, y] = (0, 0, 0, 0)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    return img


# ----------------------------------------------------------
# Persistencia
# ----------------------------------------------------------
def load_products():
    if not DATA_FILE.exists():
        return []
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_products(items):
    DATA_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False),
                         encoding="utf-8")


def load_categories():
    if not CATS_FILE.exists():
        # Recuperar automáticamente los apartados de products.json cuando
        # categories.json no vino junto al programa. Así no se ocultan los
        # apartados ni se pierde el acceso a sus productos.
        prods = load_products()
        cats = []
        needs_migrate = False
        for p in prods:
            cat = str(p.get("categoria") or "").strip()
            if not cat:
                cat = "General"
                p["categoria"] = cat
                needs_migrate = True
            if cat not in cats:
                cats.append(cat)
        if needs_migrate:
            save_products(prods)
        CATS_FILE.write_text(json.dumps(cats, indent=2, ensure_ascii=False),
                             encoding="utf-8")
        return cats
    try:
        saved = json.loads(CATS_FILE.read_text(encoding="utf-8"))
        cats = saved if isinstance(saved, list) else []
        # También reponer categorías que estén en products.json pero falten
        # del archivo de categorías (por ejemplo, tras mover/descargar archivos).
        changed = not isinstance(saved, list)
        for p in load_products():
            cat = str(p.get("categoria") or "General").strip() or "General"
            if cat not in cats:
                cats.append(cat)
                changed = True
        if changed:
            save_categories(cats)
        return cats
    except Exception:
        cats = []
        for p in load_products():
            cat = str(p.get("categoria") or "General").strip() or "General"
            if cat not in cats:
                cats.append(cat)
        if cats:
            save_categories(cats)
        return cats


def save_categories(cats):
    CATS_FILE.write_text(json.dumps(cats, indent=2, ensure_ascii=False),
                         encoding="utf-8")


# ----------------------------------------------------------
# Lanzador de la tienda
# ----------------------------------------------------------
def launch_store():
    """Abre la tienda (index.html local o URL definida en STORE_URL)."""
    if not STORE_URL:
        print("[!] No hay tienda que abrir. Coloca index.html junto a este "
              "script o define STORE_URL con tu URL de GitHub Pages.")
        return
    try:
        webbrowser.open(STORE_URL)
    except Exception as e:
        print(f"[!] No se pudo abrir la tienda: {e}")


# ==========================================================
# VENTANA PRINCIPAL: APARTADOS
# ==========================================================

# ==========================================================
# HELPERS: TASA BCV + LECTURA DE PDF (LISTA DE PRECIOS)
# ==========================================================
BCV_URL   = "https://www.bcv.org.ve/"
BCV_CACHE = BASE_DIR / "bcv_cache.json"


def _normalize_name(s: str) -> str:
    s = (s or "").strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s)
    return s


def fetch_bcv_rate(timeout: int = 15) -> float:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(
        BCV_URL,
        headers={"User-Agent": "Mozilla/5.0 AmazoniaMarket/1.0"},
    )
    html = urllib.request.urlopen(req, timeout=timeout, context=ctx).read().decode(
        "utf-8", errors="ignore"
    )
    m = re.search(
        r'id="dolar".*?<strong[^>]*>\s*([\d\.\,]+)\s*</strong>',
        html, re.DOTALL | re.IGNORECASE,
    )
    if not m:
        raise RuntimeError("No se pudo leer la tasa del BCV.")
    raw = m.group(1).strip()
    val = raw.replace(".", "").replace(",", ".")
    rate = float(val)
    if rate <= 0:
        raise RuntimeError(f"Tasa BCV invalida: {raw}")
    try:
        BCV_CACHE.write_text(
            json.dumps({"rate": rate, "raw": raw, "ts": time.time()}),
            encoding="utf-8",
        )
    except Exception:
        pass
    return rate


def get_bcv_rate_cached() -> tuple[float, str]:
    try:
        return fetch_bcv_rate(), "BCV en linea"
    except Exception as e_online:
        if BCV_CACHE.exists():
            try:
                data = json.loads(BCV_CACHE.read_text(encoding="utf-8"))
                return float(data["rate"]), f"cache local ({data.get('raw','?')})"
            except Exception:
                pass
        raise RuntimeError(f"No hay tasa BCV disponible: {e_online}")


def _parse_precio_bs(txt) -> float | None:
    if txt is None:
        return None
    t = str(txt).strip().replace(" ", "")
    if not t:
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        v = float(t)
        return v if v > 0 else None
    except ValueError:
        return None


def parse_price_list_pdf(pdf_path: str) -> list[dict]:
    """Devuelve [{'nombre','precio_bs'}] leyendo Descripcion + Precio 1."""
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError(
            "Falta el paquete 'pdfplumber'. Instalalo con:\n\n"
            "    pip install pdfplumber\n"
        ) from e

    productos: list[dict] = []
    seen: set[str] = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            used_table = False
            try:
                tables = page.extract_tables() or []
            except Exception:
                tables = []
            for tbl in tables:
                if not tbl or len(tbl) < 2:
                    continue
                header = [_normalize_name(c) if c else "" for c in tbl[0]]
                try:
                    i_desc = next(i for i, h in enumerate(header) if "DESCRIP" in h)
                    i_p1 = next(
                        i for i, h in enumerate(header)
                        if h.startswith("PRECIO 1") or h == "PRECIO1" or h == "PRECIO"
                    )
                except StopIteration:
                    continue
                used_table = True
                for row in tbl[1:]:
                    if not row or i_desc >= len(row) or i_p1 >= len(row):
                        continue
                    nombre = (row[i_desc] or "").strip()
                    precio = _parse_precio_bs(row[i_p1])
                    if not nombre or precio is None:
                        continue
                    key = _normalize_name(nombre)
                    if key in seen:
                        continue
                    seen.add(key)
                    productos.append({"nombre": nombre, "precio_bs": precio})
            if used_table:
                continue
            # Fallback: parsear texto linea a linea
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                m = re.match(
                    r"^\d{5,7}\s+(.+?)\s+(?:UND|KGS|KG|LTS|LT|PQT|CJA|CAJA)\s+"
                    r"([\d\.\,]+)\s+[\d\.\,]+\s+[\d\.\,]+\s+[\-\d\.\,]+\s*$",
                    line,
                )
                if not m:
                    continue
                nombre = re.sub(r"\s+", " ", m.group(1)).strip()
                precio = _parse_precio_bs(m.group(2))
                if not nombre or precio is None:
                    continue
                key = _normalize_name(nombre)
                if key in seen:
                    continue
                seen.add(key)
                productos.append({"nombre": nombre, "precio_bs": precio})

    return productos


class ApartadosApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Amazonia Market · Apartados")
        self.geometry("560x760")
        self.configure(bg=COLOR_BG)
        self.resizable(True, True)
        self._logo_ref = None
        # Estado de reordenamiento por arrastre
        self._pending_order = None      # lista con el nuevo orden aun sin guardar
        self._cat_frames = {}           # cat_name -> shadow frame
        self._drag_data = None          # dict con info del arrastre en curso
        self._save_order_btn = None
        self._build_ui()
        self._refresh_cats()

    def _build_ui(self):
        # Hero con logo
        hero = tk.Frame(self, bg=COLOR_PRIMARY, height=160)
        hero.pack(fill="x")
        hero.pack_propagate(False)

        logo = clean_logo_image()
        max_h = 120
        ratio = max_h / logo.height
        new_size = (int(logo.width * ratio), max_h)
        logo = logo.resize(new_size, Image.LANCZOS)
        self._logo_ref = ImageTk.PhotoImage(logo)
        tk.Label(hero, image=self._logo_ref, bg=COLOR_PRIMARY).pack(
            expand=True, pady=10
        )

        card = tk.Frame(self, bg=COLOR_CARD)
        card.pack(fill="both", expand=True, padx=22, pady=22)

        tk.Label(card, text="Apartados de la tienda",
                 font=("Segoe UI", 16, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(card,
                 text="Crea apartados (ej: Bisutería, Charcutería). Entra a uno para agregar productos.",
                 font=("Segoe UI", 10), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=470, justify="left").pack(anchor="w", padx=20, pady=(0, 12))

        # Botón GUARDAR ORDEN (aparece solo cuando arrastras apartados)
        self._save_order_btn = tk.Button(
            card, text="💾  Guardar nuevo orden",
            command=self._save_order,
            bg="#16A34A", fg="white",
            activebackground="#15803D", activeforeground="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", bd=0, cursor="hand2", pady=10,
        )
        # No se muestra todavia (pack_forget hasta que haya cambios)

        # Botón crear apartado
        add_cat_btn = tk.Button(card, text="＋  Agregar nuevo apartado",
                                command=self._create_category,
                                bg=COLOR_PRIMARY, fg="white",
                                activebackground=COLOR_PRIMARY_2,
                                activeforeground="white",
                                font=("Segoe UI", 12, "bold"),
                                relief="flat", bd=0, cursor="hand2",
                                pady=12)
        add_cat_btn.pack(fill="x", padx=20, pady=(4, 14))
        self._add_cat_btn = add_cat_btn

        # Lista scroll de apartados
        list_wrap = tk.Frame(card, bg=COLOR_CARD)
        list_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.cat_canvas = tk.Canvas(list_wrap, bg=COLOR_CARD, highlightthickness=0)
        sb = ttk.Scrollbar(list_wrap, orient="vertical", command=self.cat_canvas.yview)
        self.cat_inner = tk.Frame(self.cat_canvas, bg=COLOR_CARD)
        self.cat_inner.bind(
            "<Configure>",
            lambda e: self.cat_canvas.configure(scrollregion=self.cat_canvas.bbox("all")),
        )
        self.cat_canvas.create_window((0, 0), window=self.cat_inner, anchor="nw", width=470)
        self.cat_canvas.configure(yscrollcommand=sb.set)
        self.cat_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Botones de personalizacion extra
        extras = tk.Frame(card, bg=COLOR_CARD)
        extras.pack(fill="x", padx=20, pady=(4, 4))
        def _extra_btn(parent, text, cmd, bg):
            return tk.Button(parent, text=text, command=cmd,
                             bg=bg, fg="white",
                             activebackground=bg, activeforeground="white",
                             font=("Segoe UI", 10, "bold"),
                             relief="flat", bd=0, cursor="hand2", pady=8)
        _extra_btn(extras, "🖼  Fondo página",
                   lambda: PageBgWindow(self), "#0EA5E9").pack(side="left", expand=True, fill="x", padx=2)
        _extra_btn(extras, "🔤  Títulos + Logo",
                   lambda: TitlesWindow(self), "#8B5CF6").pack(side="left", expand=True, fill="x", padx=2)
        _extra_btn(extras, "🛒  Colores del carrito",
                   lambda: CartStyleWindow(self), "#16A34A").pack(side="left", expand=True, fill="x", padx=2)

        # Fila propia: movimiento, medidas y WhatsApp
        motion_row = tk.Frame(card, bg=COLOR_CARD)
        motion_row.pack(fill="x", padx=20, pady=(6, 0))
        _extra_btn(motion_row, "⚙️  Movimiento, medidas y WhatsApp",
                   lambda: MotionWindow(self), "#7C3AED").pack(fill="x", ipady=2)

        # Fila propia para el boton de anuncios (asi no se recorta)
        anuncios_row = tk.Frame(card, bg=COLOR_CARD)
        anuncios_row.pack(fill="x", padx=20, pady=(0, 6))
        def _open_anuncios():
            try:
                AnunciosWindow(self)
            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror(
                    "No se pudo abrir Anuncios",
                    f"Ocurrio un error al abrir la ventana de anuncios:\n\n{e}")
        _extra_btn(anuncios_row, "📢  Agregar anuncios (banner + 4 cuadros)",
                   _open_anuncios, "#EA580C").pack(fill="x", ipady=2)

        # Botón editar página web (nombre + logo)
        edit_site_btn = tk.Button(card, text="🎨  Editar página web",
                                  command=self._edit_site,
                                  bg="#0F172A", fg="white",
                                  activebackground=COLOR_PRIMARY,
                                  activeforeground="white",
                                  font=("Segoe UI", 11, "bold"),
                                  relief="flat", bd=0, cursor="hand2",
                                  pady=10)
        edit_site_btn.pack(fill="x", padx=20, pady=(4, 8))
        subcats_btn = tk.Button(card, text="🧩  Editar imágenes y texto de apartado",
                                command=lambda: SubcatsEditorWindow(self),
                                bg="#0EA5E9", fg="white",
                                activebackground="#0EA5E9", activeforeground="white",
                                font=("Segoe UI", 11, "bold"),
                                relief="flat", bd=0, cursor="hand2", pady=10)
        subcats_btn.pack(fill="x", padx=20, pady=(0, 8))

        # Botón abrir tienda
        open_btn = tk.Button(card, text="🌐  Abrir la tienda en el navegador",
                             command=launch_store,
                             bg=COLOR_CARD, fg=COLOR_PRIMARY,
                             activebackground=COLOR_BG,
                             activeforeground=COLOR_PRIMARY,
                             font=("Segoe UI", 10, "underline"),
                             relief="flat", bd=0, cursor="hand2")
        open_btn.pack(pady=(4, 10))

    def _edit_site(self):
        EditSiteWindow(self)

    def _refresh_cats(self):
        for w in self.cat_inner.winfo_children():
            w.destroy()
        self._cat_frames = {}
        cats_disk = load_categories()
        # Si hay un orden pendiente (por drag) y coincide con el conjunto
        # de apartados existentes, lo respetamos.
        if self._pending_order is not None and set(self._pending_order) == set(cats_disk):
            cats = list(self._pending_order)
        else:
            cats = cats_disk
            self._pending_order = None
        prods = load_products()
        counts = {}
        for p in prods:
            c = p.get("categoria", "General")
            counts[c] = counts.get(c, 0) + 1

        if not cats:
            tk.Label(self.cat_inner,
                     text="Aún no hay apartados.\nPulsa «Agregar nuevo apartado» para empezar.",
                     font=("Segoe UI", 10, "italic"), fg=COLOR_MUTED,
                     bg=COLOR_CARD, justify="center").pack(pady=20)
            self._update_save_order_visibility()
            return

        for cat in cats:
            self._cat_row(cat, counts.get(cat, 0))
        self._update_save_order_visibility()

    def _update_save_order_visibility(self):
        """Muestra u oculta el botón 'Guardar nuevo orden'."""
        if not self._save_order_btn:
            return
        show = (self._pending_order is not None
                and self._pending_order != load_categories())
        if show:
            try:
                self._save_order_btn.pack(fill="x", padx=20, pady=(4, 6),
                                          before=self._add_cat_btn)
            except Exception:
                self._save_order_btn.pack(fill="x", padx=20, pady=(4, 6))
        else:
            self._save_order_btn.pack_forget()

    def _save_order(self):
        if self._pending_order is None:
            return
        save_categories(list(self._pending_order))
        self._pending_order = None
        messagebox.showinfo("Orden guardado",
                            "El nuevo orden de los apartados se guardó correctamente.\n"
                            "Sube 'categories.json' a tu GitHub para que se vea en la tienda.")
        self._refresh_cats()

    def _cat_row(self, cat_name, n_prods):
        shadow = tk.Frame(self.cat_inner, bg="#475569")
        shadow.pack(fill="x", pady=8, padx=4)
        self._cat_frames[cat_name] = shadow
        card = tk.Frame(shadow, bg=COLOR_PRIMARY, bd=0)
        card.pack(fill="x", padx=(0, 4), pady=(0, 4))

        # Área clicable / arrastrable (nombre + contador)
        inner = tk.Frame(card, bg=COLOR_PRIMARY, cursor="fleur")
        inner.pack(side="left", fill="both", expand=True, padx=16, pady=14)

        name_lbl = tk.Label(inner, text="⋮⋮  " + cat_name,
                            font=("Segoe UI", 14, "bold"),
                            fg="white", bg=COLOR_PRIMARY, anchor="w",
                            cursor="fleur")
        name_lbl.pack(anchor="w", fill="x")

        sub_lbl = tk.Label(inner,
                           text=f"{n_prods} producto(s) · clic para abrir · arrastra para reordenar",
                           font=("Segoe UI", 9),
                           fg="#E9D5FF", bg=COLOR_PRIMARY, anchor="w",
                           cursor="fleur")
        sub_lbl.pack(anchor="w", fill="x")

        # Bind drag + click en las 3 zonas
        for widget in (inner, name_lbl, sub_lbl):
            widget.bind("<ButtonPress-1>",
                        lambda e, c=cat_name: self._drag_press(e, c))
            widget.bind("<B1-Motion>",
                        lambda e, c=cat_name: self._drag_motion(e, c))
            widget.bind("<ButtonRelease-1>",
                        lambda e, c=cat_name: self._drag_release(e, c))

        # Botón eliminar apartado
        del_btn = tk.Button(card, text="🗑️",
                            command=lambda c=cat_name: self._delete_category(c),
                            bg="#DC2626", fg="white",
                            activebackground="#B91C1C",
                            activeforeground="white",
                            font=("Segoe UI", 12, "bold"),
                            relief="flat", bd=0, cursor="hand2",
                            padx=12, pady=8)
        del_btn.pack(side="right", padx=(4, 10), pady=10)

        # Botón editar estilo del apartado (color, icono, tamano, "Ver mas")
        style_btn = tk.Button(card, text="🎨",
                              command=lambda c=cat_name: self._edit_cat_style(c),
                              bg="#F59E0B", fg="white",
                              activebackground="#D97706", activeforeground="white",
                              font=("Segoe UI", 12, "bold"),
                              relief="flat", bd=0, cursor="hand2",
                              padx=12, pady=8)
        style_btn.pack(side="right", padx=4, pady=10)

        # Botón renombrar apartado
        ren_btn = tk.Button(card, text="✏️",
                            command=lambda c=cat_name: self._rename_category(c),
                            bg="#0EA5E9", fg="white",
                            activebackground="#0284C7", activeforeground="white",
                            font=("Segoe UI", 12, "bold"),
                            relief="flat", bd=0, cursor="hand2",
                            padx=12, pady=8)
        ren_btn.pack(side="right", padx=4, pady=10)

    # ---------- Drag & drop de apartados ----------
    def _drag_press(self, event, cat_name):
        self._drag_data = {"cat": cat_name, "moved": False,
                           "start_x": event.x_root, "start_y": event.y_root}

    def _drag_motion(self, event, cat_name):
        if not self._drag_data:
            return
        dx = abs(event.x_root - self._drag_data["start_x"])
        dy = abs(event.y_root - self._drag_data["start_y"])
        if not self._drag_data["moved"] and (dx + dy) < 6:
            return  # aun no cuenta como arrastre
        self._drag_data["moved"] = True

        # Detectar sobre qué apartado está el puntero
        target = None
        for other, shadow in self._cat_frames.items():
            if other == cat_name:
                continue
            try:
                sy = shadow.winfo_rooty()
                sh = shadow.winfo_height()
                if sy <= event.y_root <= sy + sh:
                    target = other
                    break
            except Exception:
                continue
        if not target:
            return

        # Reordenar en memoria
        order = list(self._pending_order) if self._pending_order is not None else load_categories()
        try:
            order.remove(cat_name)
            idx = order.index(target)
            # Si arrastramos hacia abajo, insertamos después del objetivo.
            if event.y_root > self._drag_data["start_y"]:
                idx += 1
            order.insert(idx, cat_name)
        except ValueError:
            return
        if order == self._pending_order:
            return
        self._pending_order = order
        self._drag_data["start_y"] = event.y_root  # nuevo punto base
        self._refresh_cats()

    def _drag_release(self, event, cat_name):
        moved = bool(self._drag_data and self._drag_data.get("moved"))
        self._drag_data = None
        if not moved:
            # Fue un clic simple: abrir el apartado
            self._open_category(cat_name)

    def _create_category(self):
        name = simpledialog.askstring(
            "Nuevo apartado",
            "Nombre del apartado (ej: Bisutería, Charcutería):",
            parent=self,
        )
        if not name:
            return
        name = name.strip()
        if not name:
            return
        cats = load_categories()
        if any(c.lower() == name.lower() for c in cats):
            messagebox.showwarning("Ya existe", f"El apartado '{name}' ya existe.")
            return
        cats.append(name)
        save_categories(cats)
        self._refresh_cats()

    def _delete_category(self, cat):
        prods = load_products()
        n = sum(1 for p in prods if p.get("categoria") == cat)
        msg = f"¿Eliminar el apartado '{cat}'?"
        if n:
            msg += f"\n\nSe eliminarán también sus {n} producto(s)."
        if not messagebox.askyesno("Eliminar apartado", msg):
            return
        # borrar productos + sus imágenes
        keep = []
        for p in prods:
            if p.get("categoria") == cat:
                img_rel = p.get("imagen", "")
                if img_rel:
                    try:
                        (BASE_DIR / img_rel).unlink(missing_ok=True)
                    except Exception:
                        pass
            else:
                keep.append(p)
        save_products(keep)
        cats = [c for c in load_categories() if c != cat]
        save_categories(cats)
        self._refresh_cats()

    def _open_category(self, cat):
        CategoryWindow(self, cat)

    def _rename_category(self, cat):
        new_name = simpledialog.askstring(
            "Renombrar apartado",
            f"Nuevo nombre para «{cat}»:",
            initialvalue=cat, parent=self,
        )
        if not new_name:
            return
        ok = rename_category(cat, new_name.strip())
        if not ok:
            messagebox.showwarning(
                "No se pudo renombrar",
                "Nombre invalido o ya existe otro apartado con ese nombre.",
            )
            return
        self._refresh_cats()

    def _edit_cat_style(self, cat):
        CategoryStyleWindow(self, cat)


# ==========================================================
# VENTANA DE UN APARTADO: agregar / eliminar productos
# ==========================================================
class CategoryWindow(tk.Toplevel):
    def __init__(self, master: ApartadosApp, cat_name: str):
        super().__init__(master)
        self.master_app = master
        self.cat_name = cat_name
        self.title(f"Apartado: {cat_name}")
        self.geometry("620x950")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)

        self.image_path: Path | None = None
        self._preview_ref = None

        # Estado para carga automatica desde PDF
        self.pdf_products: list[dict] = []
        self.pdf_source_path: str | None = None
        self.bcv_rate: float | None = None
        self.bcv_source: str = ""
        self._current_pdf_item: dict | None = None
        self._pdf_cursor: int = 0
        self.btn_pdf = None
        self.btn_pdf_next = None
        self.pdf_status = None

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        header = tk.Frame(self, bg=COLOR_PRIMARY, height=90)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"📁  {self.cat_name}",
                 font=("Segoe UI", 18, "bold"),
                 fg="white", bg=COLOR_PRIMARY).pack(pady=24)

        card = tk.Frame(self, bg=COLOR_CARD)
        card.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(card, text="Agregar producto a este apartado",
                 font=("Segoe UI", 13, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=18, pady=(14, 10))

        # Imagen
        self._label(card, "Imagen del producto")
        img_row = tk.Frame(card, bg=COLOR_CARD)
        img_row.pack(fill="x", padx=18, pady=(0, 10))
        preview_hint = ("Sin imagen\n\nArrastra aquí\nuna imagen"
                        if _HAS_WINDND else "Sin imagen")
        self.preview = tk.Label(img_row, text=preview_hint,
                                width=14, height=7,
                                bg="#F1F5F9", fg=COLOR_MUTED,
                                font=("Segoe UI", 9), bd=1, relief="solid",
                                highlightthickness=0)
        self.preview.pack(side="left")
        self._preview_placeholder = preview_hint
        self._register_image_dnd(self.preview)
        tk.Button(img_row, text="📷  Insertar imagen",
                  command=self.pick_image,
                  bg=COLOR_PRIMARY_2, fg="white",
                  activebackground=COLOR_PRIMARY, activeforeground="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  padx=14, pady=10).pack(side="left", padx=(12, 6))

        pdf_col = tk.Frame(img_row, bg=COLOR_CARD)
        pdf_col.pack(side="left", fill="y", padx=(6, 0))
        self.btn_pdf = tk.Button(
            pdf_col, text="📄  Cargar PDF",
            command=self.load_pdf,
            bg="#0EA5E9", fg="white",
            activebackground="#0284C7", activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, cursor="hand2",
            padx=12, pady=10,
        )
        self.btn_pdf.pack(fill="x")
        self.btn_pdf_next = tk.Button(
            pdf_col, text="➕  Agregar producto no añadido",
            command=self.suggest_next_from_pdf,
            bg="#16A34A", fg="white",
            activebackground="#15803D", activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, cursor="hand2",
            padx=12, pady=10, state="disabled",
        )
        self.btn_pdf_next.pack(fill="x", pady=(6, 0))
        self.pdf_status = tk.Label(
            pdf_col, text="Sin PDF cargado",
            font=("Segoe UI", 8), fg=COLOR_MUTED, bg=COLOR_CARD,
            anchor="w", justify="left", wraplength=260,
        )
        self.pdf_status.pack(anchor="w", pady=(4, 0))

        # Nombre / precio
        self._label(card, "Nombre del producto")
        self.entry_name = self._entry(card)
        self._label(card, "Precio")
        self.entry_price = self._entry(card)

        tk.Button(card, text="＋  Agregar producto",
                  command=self.add_product,
                  bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_2, activeforeground="white",
                  font=("Segoe UI", 12, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  pady=12).pack(fill="x", padx=18, pady=(14, 8))

        sep = tk.Frame(card, bg="#E2E8F0", height=1)
        sep.pack(fill="x", padx=18, pady=(6, 10))

        tk.Label(card, text=f"Productos en «{self.cat_name}»",
                 font=("Segoe UI", 11, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=18, pady=(0, 6))

        list_wrap = tk.Frame(card, bg=COLOR_CARD)
        list_wrap.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        self.list_canvas = tk.Canvas(list_wrap, bg=COLOR_CARD, highlightthickness=0)
        sb = ttk.Scrollbar(list_wrap, orient="vertical", command=self.list_canvas.yview)
        self.list_inner = tk.Frame(self.list_canvas, bg=COLOR_CARD)
        self.list_inner.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")),
        )
        self.list_canvas.create_window((0, 0), window=self.list_inner, anchor="nw", width=470)
        self.list_canvas.configure(yscrollcommand=sb.set)
        self.list_canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _label(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=18, pady=(4, 4))

    def _entry(self, parent):
        e = tk.Entry(parent, font=("Segoe UI", 12),
                     bg="#F8FAFC", fg=COLOR_TEXT,
                     relief="flat", bd=0,
                     highlightthickness=1,
                     highlightbackground="#E2E8F0",
                     highlightcolor=COLOR_PRIMARY_2)
        e.pack(fill="x", padx=18, ipady=9, pady=(0, 6))
        return e

    def pick_image(self):
        path = filedialog.askopenfilename(
            title="Selecciona una imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                       ("Todos los archivos", "*.*")],
        )
        if not path:
            return
        self._apply_image_path(path)

    def _apply_image_path(self, path):
        """Carga una imagen desde disco y la muestra en la preview.
        Se usa tanto para el botón 'Insertar imagen' como para el
        arrastrar-y-soltar desde el navegador o el explorador."""
        try:
            p = Path(path)
            if not p.is_file():
                raise FileNotFoundError(path)
            if p.suffix.lower() not in {".png", ".jpg", ".jpeg",
                                        ".webp", ".bmp", ".gif"}:
                raise ValueError(
                    "Formato no soportado. Usa PNG, JPG, WEBP, BMP o GIF."
                )
            img = Image.open(p)
            img.thumbnail((140, 140))
            self._preview_ref = ImageTk.PhotoImage(img)
            self.preview.configure(image=self._preview_ref, text="",
                                   width=140, height=140, bg=COLOR_CARD)
            self.image_path = p
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la imagen:\n{e}")

    def _register_image_dnd(self, widget):
        """Habilita arrastrar-y-soltar de imágenes sobre `widget`.
        Requiere el paquete opcional `windnd` (Windows). Si no está
        disponible, no hace nada y el usuario sigue pudiendo pulsar
        el botón 'Insertar imagen'."""
        if not _HAS_WINDND:
            return

        def _on_drop(files):
            # windnd entrega una lista de rutas en bytes
            if not files:
                return
            raw = files[0]
            try:
                path = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            except UnicodeDecodeError:
                path = raw.decode("mbcs", errors="ignore")  # type: ignore
            # Muchos navegadores dejan la imagen como archivo temporal
            # (drag-out). windnd nos entrega la ruta de ese archivo.
            self._apply_image_path(path)

        try:
            windnd.hook_dropfiles(widget, func=_on_drop)  # type: ignore
        except Exception:
            # Si algo falla no bloqueamos la app: seguirá funcionando
            # el botón manual.
            pass


    def add_product(self):
        name = self.entry_name.get().strip()
        price_raw = self.entry_price.get().strip().replace(",", ".")
        if not name:
            messagebox.showwarning("Falta información", "Escribe el nombre del producto.")
            return
        try:
            price = float(price_raw)
        except ValueError:
            messagebox.showwarning("Precio inválido", "Escribe un precio válido, ej: 19.90")
            return
        if not self.image_path:
            messagebox.showwarning("Falta imagen", "Inserta una imagen del producto.")
            return

        ext = self.image_path.suffix.lower() or ".png"
        new_name = f"{uuid.uuid4().hex}{ext}"
        dest = IMG_DIR / new_name
        try:
            shutil.copy(self.image_path, dest)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la imagen:\n{e}")
            return

        items = load_products()
        items.append({
            "id": uuid.uuid4().hex,
            "nombre": name,
            "precio": price,
            "imagen": f"product_images/{new_name}",
            "categoria": self.cat_name,
        })
        save_products(items)

        # limpiar
        self.entry_name.delete(0, "end")
        self.entry_price.delete(0, "end")
        self.image_path = None
        self._preview_ref = None
        self.preview.configure(image="",
                               text=getattr(self, "_preview_placeholder", "Sin imagen"),
                               width=14, height=7, bg="#F1F5F9")
        self._refresh_list()
        self.master_app._refresh_cats()

        # Si veniamos de una sugerencia del PDF, reactivar el boton
        if self.pdf_products and self.bcv_rate is not None:
            pendientes = self._pending_pdf_items()
            if pendientes:
                self.btn_pdf_next.configure(state="normal")
                self.pdf_status.configure(
                    text=f"Producto agregado. Restantes: {len(pendientes)}.\n"
                         "Pulsa Agregar producto no añadido para el siguiente."
                )
            else:
                self.btn_pdf_next.configure(state="disabled")
                self.pdf_status.configure(
                    text=f"Todos los productos del PDF ya estan en {self.cat_name}."
                )
        self._current_pdf_item = None

    # -------- Carga de PDF y sugerencia automatica --------
    def load_pdf(self):
        path = filedialog.askopenfilename(
            title="Selecciona la lista de precios en PDF",
            filetypes=[("PDF", "*.pdf"), ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            productos = parse_price_list_pdf(path)
        except Exception as e:
            messagebox.showerror("Error al leer PDF", str(e))
            return
        if not productos:
            messagebox.showwarning(
                "PDF vacio",
                "No se detectaron productos en el PDF.\n"
                "Verifica que sea la lista de precios con columnas "
                "Descripcion y Precio 1.",
            )
            return
        try:
            rate, source = get_bcv_rate_cached()
        except Exception as e:
            messagebox.showerror(
                "Tasa BCV no disponible",
                f"No se pudo obtener la tasa del BCV:\n{e}\n\n"
                "Verifica tu conexion a internet.",
            )
            return

        self.pdf_products = productos
        self.pdf_source_path = path
        self.bcv_rate = rate
        self.bcv_source = source
        self._pdf_cursor = 0
        self.btn_pdf_next.configure(state="normal")

        pendientes = self._pending_pdf_items()
        self.pdf_status.configure(
            text=f"PDF: {Path(path).name}\n"
                 f"{len(productos)} productos leidos - faltan {len(pendientes)}\n"
                 f"Tasa BCV: {rate:.4f} Bs/USD ({source})"
        )
        messagebox.showinfo(
            "PDF cargado",
            f"Se leyeron {len(productos)} productos del PDF.\n"
            f"Faltan por agregar: {len(pendientes)}.\n"
            f"Tasa BCV usada: {rate:.4f} Bs/USD\n({source})",
        )

    def _pending_pdf_items(self) -> list[dict]:
        existentes = {
            _normalize_name(p.get("nombre", ""))
            for p in load_products()
            if p.get("categoria") == self.cat_name
        }
        return [p for p in self.pdf_products
                if _normalize_name(p["nombre"]) not in existentes]

    def suggest_next_from_pdf(self):
        if not self.pdf_products or self.bcv_rate is None:
            messagebox.showwarning("Sin PDF", "Primero carga el PDF.")
            return

        # Nombres ya agregados en esta categoria (para saltarlos)
        existentes = {
            _normalize_name(p.get("nombre", ""))
            for p in load_products()
            if p.get("categoria") == self.cat_name
        }
        n = len(self.pdf_products)

        # Buscar el siguiente pendiente empezando desde el cursor actual,
        # dando la vuelta al final de la lista si hace falta. Asi cada
        # pulsacion salta al SIGUIENTE producto sin reiniciar desde arriba.
        start = self._pdf_cursor % n if n else 0
        item = None
        idx = None
        for step in range(n):
            i = (start + step) % n
            cand = self.pdf_products[i]
            if _normalize_name(cand["nombre"]) not in existentes:
                item = cand
                idx = i
                break

        if item is None:
            self._current_pdf_item = None
            self.btn_pdf_next.configure(state="disabled")
            self.pdf_status.configure(
                text=f"Todos los productos del PDF ya estan en {self.cat_name}."
            )
            messagebox.showinfo(
                "Completado",
                f"Todos los productos del PDF ya estan en {self.cat_name}.",
            )
            return

        # Avanzar el cursor: la proxima pulsacion mostrara el que sigue,
        # no este mismo. Si el usuario si agrega este, el cursor ya apunta
        # al siguiente y continua hacia abajo (no reinicia desde arriba).
        self._pdf_cursor = (idx + 1) % n

        precio_usd = round(item["precio_bs"] / self.bcv_rate, 2)
        self._current_pdf_item = item

        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, item["nombre"])
        self.entry_price.delete(0, "end")
        self.entry_price.insert(0, f"{precio_usd:.2f}")

        pendientes_restantes = sum(
            1 for p in self.pdf_products
            if _normalize_name(p["nombre"]) not in existentes
        ) - 1  # menos el que acabamos de sugerir

        # Dejar el boton habilitado: si el usuario NO quiere este producto,
        # puede volver a pulsarlo para saltar al siguiente, infinitamente.
        self.btn_pdf_next.configure(state="normal")
        self.pdf_status.configure(
            text=f"Sugerido: {item['nombre']}\n"
                 f"Precio Bs: {item['precio_bs']:.2f} -> ${precio_usd:.2f}\n"
                 f"Inserta imagen y pulsa Agregar producto,\n"
                 f"o pulsa de nuevo Agregar producto no anadido para saltar.\n"
                 f"Pendientes tras este: {max(pendientes_restantes, 0)}"
        )

    def _edit_product(self, prod):
        EditProductWindow(self, prod)

    def _refresh_list(self):
        for w in self.list_inner.winfo_children():
            w.destroy()
        items = [p for p in load_products() if p.get("categoria") == self.cat_name]
        if not items:
            tk.Label(self.list_inner,
                     text="Aún no hay productos en este apartado.",
                     font=("Segoe UI", 10, "italic"),
                     fg=COLOR_MUTED, bg=COLOR_CARD).pack(anchor="w", pady=6)
            return
        for prod in items:
            self._product_row(prod)

    def _product_row(self, prod):
        shadow = tk.Frame(self.list_inner, bg="#475569")
        shadow.pack(fill="x", pady=8, padx=4)
        card = tk.Frame(shadow, bg="#FFFFFF",
                        highlightbackground="#CBD5E1", highlightthickness=1)
        card.pack(fill="x", padx=(0, 5), pady=(0, 5))

        info = tk.Frame(card, bg="#FFFFFF")
        info.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        tk.Label(info, text=prod.get("nombre", "(sin nombre)"),
                 font=("Segoe UI", 11, "bold"),
                 fg=COLOR_TEXT, bg="#FFFFFF", anchor="w").pack(anchor="w")

        precio = prod.get("precio", 0)
        try:
            precio_txt = f"${float(precio):.2f}"
        except Exception:
            precio_txt = f"${precio}"
        tk.Label(info, text=precio_txt,
                 font=("Segoe UI", 10, "bold"),
                 fg="#FFFFFF", bg="#16A34A",
                 padx=10, pady=3).pack(anchor="w", pady=(4, 0))

        tk.Button(card, text="🗑️",
                  command=lambda p=prod: self._delete_product(p),
                  bg="#DC2626", fg="white",
                  activebackground="#B91C1C", activeforeground="white",
                  font=("Segoe UI", 12, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  padx=14, pady=8).pack(side="right", padx=(4, 12), pady=10)

        tk.Button(card, text="✏️",
                  command=lambda p=prod: self._edit_product(p),
                  bg="#F59E0B", fg="white",
                  activebackground="#D97706", activeforeground="white",
                  font=("Segoe UI", 12, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  padx=14, pady=8).pack(side="right", padx=4, pady=10)

    def _delete_product(self, prod):
        nombre = prod.get("nombre", "este producto")
        if not messagebox.askyesno("Eliminar producto",
                                   f"¿Seguro que quieres eliminar '{nombre}'?"):
            return
        items = load_products()
        pid = prod.get("id")
        items = [p for p in items if p.get("id") != pid]
        save_products(items)
        img_rel = prod.get("imagen", "")
        if img_rel:
            try:
                (BASE_DIR / img_rel).unlink(missing_ok=True)
            except Exception:
                pass
        self._refresh_list()
        self.master_app._refresh_cats()


# ==========================================================
# Main
# ==========================================================
# ==========================================================
# VENTANA: EDITAR PÁGINA WEB (nombre + logo pequeño)
# ==========================================================
class EditSiteWindow(tk.Toplevel):
    """
    Permite cambiar:
      - El nombre que aparece en la portada de la tienda
        (por defecto: 'Amazonia' + 'MARKET').
      - El logo pequeño (badge gris con esquinas redondeadas
        y sombra) que sale al lado del nombre.

    IMAGEN DEL LOGO — dimensiones recomendadas:
      * Cuadrada, 512 x 512 px (mínimo 256 x 256).
      * Fondo transparente (PNG) para que se vea limpia sobre
        el fondo oscuro con esquinas redondeadas y sombra.
      * Si la imagen es rectangular igual funciona: se centra
        dentro del cuadrito sin deformarse.
      * También se guarda incrustada dentro de site_settings.json
        para que Streamlit Cloud la pueda mostrar desde GitHub.
    """
    def __init__(self, master):
        super().__init__(master)
        self.title("Editar página web")
        self.configure(bg=COLOR_BG)
        self.geometry("580x760")
        self.minsize(560, 600)
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()

        self._new_logo_path = None
        self._preview_ref = None
        self._new_bg_path = None
        self._bg_preview_ref = None
        self._bg_b64_current = None  # bytes b64 del fondo elegido nuevo
        # Estado del fondo del HERO (banda superior)
        self._new_hero_bg_path = None       # ruta nueva o "__REMOVE__"
        self._hero_preview_ref = None
        self._hero_mode = "image"           # "image" o "color"
        self._hero_color = "#7F8794"        # color base elegido
        self._hero_shade = 1.0              # multiplicador de brillo del color (0.4..1.6)

        settings = load_site_settings()

        # Header
        head = tk.Frame(self, bg=COLOR_PRIMARY, height=70)
        head.pack(fill="x")
        head.pack_propagate(False)
        tk.Label(head, text="🎨  Editar página web",
                 bg=COLOR_PRIMARY, fg="white",
                 font=("Segoe UI", 14, "bold")).pack(pady=18)

        # Barra inferior FIJA con el boton Guardar (siempre visible)
        bottom_bar = tk.Frame(self, bg=COLOR_BG)
        bottom_bar.pack(side="bottom", fill="x")
        tk.Button(bottom_bar, text="💾  Guardar cambios",
                  command=self._save,
                  bg="#16A34A", fg="white",
                  activebackground="#15803D", activeforeground="white",
                  font=("Segoe UI", 12, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  pady=12).pack(fill="x", padx=18, pady=(8, 4))
        tk.Label(bottom_bar,
                 text="Los cambios se verán en la tienda al recargar la página.",
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_BG).pack(pady=(0, 8))

        # Contenedor con SCROLL para todo el formulario
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill="both", expand=True, padx=18, pady=(18, 0))
        canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0, bd=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        card = tk.Frame(canvas, bg=COLOR_CARD)
        card_id = canvas.create_window((0, 0), window=card, anchor="nw")
        def _on_card_config(_e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        def _on_canvas_config(e):
            canvas.itemconfigure(card_id, width=e.width)
        card.bind("<Configure>", _on_card_config)
        canvas.bind("<Configure>", _on_canvas_config)
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Nombre ---
        tk.Label(card, text="Nombre de la tienda",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(card,
                 text="Aparece grande en la portada. Se muestra en dos partes: la palabra principal (en cursiva blanca) y una segunda palabra en azul (por defecto: MARKET). Puedes dejar la segunda parte vacía.",
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16)

        row = tk.Frame(card, bg=COLOR_CARD)
        row.pack(fill="x", padx=16, pady=(8, 4))
        tk.Label(row, text="Nombre:", bg=COLOR_CARD,
                 font=("Segoe UI", 10)).pack(side="left")
        self.name_var = tk.StringVar(value=settings.get("site_name", "Amazonia"))
        tk.Entry(row, textvariable=self.name_var,
                 font=("Segoe UI", 11), relief="solid", bd=1
                 ).pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)

        row2 = tk.Frame(card, bg=COLOR_CARD)
        row2.pack(fill="x", padx=16, pady=(4, 12))
        tk.Label(row2, text="Segunda palabra:", bg=COLOR_CARD,
                 font=("Segoe UI", 10)).pack(side="left")
        self.market_var = tk.StringVar(value=settings.get("site_market", "MARKET"))
        tk.Entry(row2, textvariable=self.market_var,
                 font=("Segoe UI", 11), relief="solid", bd=1
                 ).pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)

        # --- Logo pequeño ---
        tk.Label(card, text="Logo pequeño (badge junto al nombre)",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(10, 4))
        tk.Label(card,
                 text=("Recomendado: imagen CUADRADA de 512 x 512 px "
                       "(mínimo 256 x 256), preferiblemente PNG con fondo transparente. "
                       "Se mostrará dentro de un cuadrito de esquinas redondeadas, "
                       "con fondo oscuro y sombra. También queda guardada en site_settings.json "
                       "para que funcione al subirlo a GitHub / Streamlit Cloud."),
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16)

        prev_row = tk.Frame(card, bg=COLOR_CARD)
        prev_row.pack(fill="x", padx=16, pady=(10, 4))

        self.preview_lbl = tk.Label(prev_row, bg="#E5E7EB",
                                    width=14, height=7,
                                    text="(sin imagen)",
                                    fg=COLOR_MUTED, font=("Segoe UI", 9))
        self.preview_lbl.pack(side="left")
        self._refresh_preview(initial=True)

        btns = tk.Frame(prev_row, bg=COLOR_CARD)
        btns.pack(side="left", padx=14)
        tk.Button(btns, text="📷  Elegir imagen…",
                  command=self._pick_logo,
                  bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_2, activeforeground="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0, cursor="hand2", padx=12, pady=6
                  ).pack(anchor="w", pady=(0, 6))
        tk.Button(btns, text="🗑  Quitar logo personalizado",
                  command=self._remove_logo,
                  bg=COLOR_CARD, fg="#B91C1C",
                  activebackground=COLOR_BG, activeforeground="#B91C1C",
                  font=("Segoe UI", 9, "underline"),
                  relief="flat", bd=0, cursor="hand2"
                  ).pack(anchor="w")

        # --- Fondo completo de la web ---
        tk.Label(card, text="Fondo completo de la web",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(card,
                 text=("Elige una imagen que se colocara detras de TODO en la pagina "
                       "(detras del nombre, el logo, los productos, etc.). Usa los "
                       "deslizadores para ajustar el brillo y la transparencia como "
                       "si fuera una bebida: mas brillo = mas clara, menos brillo = "
                       "mas oscura. La transparencia deja ver mas o menos el fondo."),
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16)

        bg_row = tk.Frame(card, bg=COLOR_CARD)
        bg_row.pack(fill="x", padx=16, pady=(10, 4))

        self.bg_preview_lbl = tk.Label(bg_row, bg="#E5E7EB",
                                       width=18, height=6,
                                       text="(sin fondo)",
                                       fg=COLOR_MUTED, font=("Segoe UI", 9))
        self.bg_preview_lbl.pack(side="left")

        bg_btns = tk.Frame(bg_row, bg=COLOR_CARD)
        bg_btns.pack(side="left", padx=14)
        tk.Button(bg_btns, text="🖼  Elegir imagen de fondo…",
                  command=self._pick_bg,
                  bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_2, activeforeground="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0, cursor="hand2", padx=12, pady=6
                  ).pack(anchor="w", pady=(0, 6))
        tk.Button(bg_btns, text="🗑  Quitar fondo personalizado",
                  command=self._remove_bg,
                  bg=COLOR_CARD, fg="#B91C1C",
                  activebackground=COLOR_BG, activeforeground="#B91C1C",
                  font=("Segoe UI", 9, "underline"),
                  relief="flat", bd=0, cursor="hand2"
                  ).pack(anchor="w")

        # Sliders brillo / transparencia
        try:
            _cur_bright = float(settings.get("site_bg_brightness", "1.0"))
        except (ValueError, TypeError):
            _cur_bright = 1.0
        try:
            _cur_opacity = float(settings.get("site_bg_opacity", "0.6"))
        except (ValueError, TypeError):
            _cur_opacity = 0.6

        tk.Label(card, text="Brillo del fondo (0 = oscuro, 2 = muy claro)",
                 font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(10, 0))
        self.bright_var = tk.DoubleVar(value=_cur_bright)
        tk.Scale(card, variable=self.bright_var,
                 from_=0.1, to=2.0, resolution=0.05,
                 orient="horizontal", length=460,
                 bg=COLOR_CARD, troughcolor="#E5E7EB",
                 highlightthickness=0
                 ).pack(anchor="w", padx=16)

        tk.Label(card, text="Transparencia del fondo (0 = invisible, 1 = totalmente visible)",
                 font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(8, 0))
        self.opacity_var = tk.DoubleVar(value=_cur_opacity)
        tk.Scale(card, variable=self.opacity_var,
                 from_=0.0, to=1.0, resolution=0.05,
                 orient="horizontal", length=460,
                 bg=COLOR_CARD, troughcolor="#E5E7EB",
                 highlightthickness=0
                 ).pack(anchor="w", padx=16)

        self._refresh_bg_preview(initial=True)

        # ==================================================
        # NUEVA seccion: Fondo del HERO (banda superior)
        # ==================================================
        tk.Label(card, text="Fondo de la banda del logo (arriba)",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(18, 4))
        tk.Label(card,
                 text=("Cambia el fondo de la banda gris donde estan el logo y el "
                       "nombre. Puedes elegir una IMAGEN propia o un COLOR de la "
                       "paleta. Si eliges color, puedes hacerlo mas palido o mas "
                       "oscuro con el deslizador de tono, y ajustar la transparencia."),
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16)

        cur_hero_img = load_site_settings().get("hero_bg_b64", "").strip()
        cur_hero_color = load_site_settings().get("hero_bg_color", "").strip()
        try:
            cur_hero_bright = float(load_site_settings().get("hero_brightness", "1.0"))
        except Exception:
            cur_hero_bright = 1.0
        try:
            cur_hero_opac = float(load_site_settings().get("hero_opacity", "1.0"))
        except Exception:
            cur_hero_opac = 1.0
        if cur_hero_color:
            self._hero_color = cur_hero_color
            self._hero_mode = "color" if not cur_hero_img else "image"
        if cur_hero_img:
            self._hero_mode = "image"
        self._hero_shade = cur_hero_bright

        # Radio: modo imagen o color
        self.hero_mode_var = tk.StringVar(value=self._hero_mode)
        mode_row = tk.Frame(card, bg=COLOR_CARD)
        mode_row.pack(fill="x", padx=16, pady=(10, 2))
        tk.Radiobutton(mode_row, text="Usar imagen", variable=self.hero_mode_var,
                       value="image", bg=COLOR_CARD,
                       command=self._on_hero_mode_change,
                       font=("Segoe UI", 10)).pack(side="left")
        tk.Radiobutton(mode_row, text="Usar color", variable=self.hero_mode_var,
                       value="color", bg=COLOR_CARD,
                       command=self._on_hero_mode_change,
                       font=("Segoe UI", 10)).pack(side="left", padx=(14, 0))

        # --- Panel IMAGEN ---
        self.hero_img_frame = tk.Frame(card, bg=COLOR_CARD)
        self.hero_img_frame.pack(fill="x", padx=16, pady=(6, 0))
        img_row = tk.Frame(self.hero_img_frame, bg=COLOR_CARD)
        img_row.pack(fill="x")
        self.hero_preview_lbl = tk.Label(img_row, bg="#E5E7EB",
                                         width=18, height=6,
                                         text="(sin imagen)",
                                         fg=COLOR_MUTED, font=("Segoe UI", 9))
        self.hero_preview_lbl.pack(side="left")
        hb_btns = tk.Frame(img_row, bg=COLOR_CARD)
        hb_btns.pack(side="left", padx=14)
        tk.Button(hb_btns, text="🖼  Elegir imagen…",
                  command=self._pick_hero_bg,
                  bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_2, activeforeground="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0, cursor="hand2", padx=12, pady=6
                  ).pack(anchor="w", pady=(0, 6))
        tk.Button(hb_btns, text="🗑  Quitar imagen del hero",
                  command=self._remove_hero_bg,
                  bg=COLOR_CARD, fg="#B91C1C",
                  activebackground=COLOR_BG, activeforeground="#B91C1C",
                  font=("Segoe UI", 9, "underline"),
                  relief="flat", bd=0, cursor="hand2"
                  ).pack(anchor="w")
        self._refresh_hero_preview(initial=True)

        # --- Panel COLOR ---
        self.hero_color_frame = tk.Frame(card, bg=COLOR_CARD)
        self.hero_color_frame.pack(fill="x", padx=16, pady=(6, 0))
        tk.Label(self.hero_color_frame, text="Elige un color:",
                 bg=COLOR_CARD, font=("Segoe UI", 10)).pack(anchor="w")

        palette = [
            "#7F8794", "#0F172A", "#1D4ED8", "#0EA5E9", "#14B8A6",
            "#16A34A", "#65A30D", "#F59E0B", "#EF4444", "#DC2626",
            "#EC4899", "#A855F7", "#7C3AED", "#4C1D95", "#0891B2",
            "#F97316", "#84CC16", "#FBBF24", "#F5F3FF", "#FFFFFF",
        ]
        pal_wrap = tk.Frame(self.hero_color_frame, bg=COLOR_CARD)
        pal_wrap.pack(anchor="w", pady=(4, 4))
        cols_per_row = 10
        for i, hexc in enumerate(palette):
            r, c = divmod(i, cols_per_row)
            b = tk.Button(pal_wrap, bg=hexc, width=3, height=1,
                          relief="flat", bd=0, cursor="hand2",
                          command=lambda hx=hexc: self._pick_palette_color(hx))
            b.grid(row=r, column=c, padx=2, pady=2)

        pick_row = tk.Frame(self.hero_color_frame, bg=COLOR_CARD)
        pick_row.pack(anchor="w", pady=(4, 2))
        tk.Button(pick_row, text="🎨  Elegir otro color…",
                  command=self._pick_custom_color,
                  bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_2, activeforeground="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=4
                  ).pack(side="left")
        tk.Label(pick_row, text="  Actual:", bg=COLOR_CARD,
                 font=("Segoe UI", 9)).pack(side="left", padx=(8, 4))
        self.color_swatch = tk.Label(pick_row, bg=self._hero_color,
                                     width=6, height=1, relief="solid", bd=1)
        self.color_swatch.pack(side="left")

        tk.Label(self.hero_color_frame,
                 text="Tono (izquierda = mas oscuro, derecha = mas palido)",
                 font=("Segoe UI", 9, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", pady=(6, 0))
        self.hero_shade_var = tk.DoubleVar(value=self._hero_shade)
        tk.Scale(self.hero_color_frame, variable=self.hero_shade_var,
                 from_=0.4, to=1.6, resolution=0.05,
                 orient="horizontal", length=460,
                 bg=COLOR_CARD, troughcolor="#E5E7EB",
                 highlightthickness=0).pack(anchor="w")

        # Transparencia comun para el hero (aplica tanto a color como a imagen)
        tk.Label(card, text="Transparencia de la banda del logo (0 = invisible, 1 = solido)",
                 font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(10, 0))
        self.hero_opac_var = tk.DoubleVar(value=cur_hero_opac)
        tk.Scale(card, variable=self.hero_opac_var,
                 from_=0.0, to=1.0, resolution=0.05,
                 orient="horizontal", length=460,
                 bg=COLOR_CARD, troughcolor="#E5E7EB",
                 highlightthickness=0).pack(anchor="w", padx=16)

        # Aplica visibilidad inicial de los dos paneles
        self._on_hero_mode_change()

        # ==================================================
        # NUEVA seccion: Posicion y tamano del LOGO
        # ==================================================
        tk.Label(card, text="Posicion y tamano del logo",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(18, 4))
        tk.Label(card,
                 text=("Coloca el logo a la izquierda, en el centro o a la derecha. "
                       "Con el deslizador de tamano puedes hacerlo mas grande; "
                       "la banda del hero crece automaticamente para acompanarlo."),
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16)

        cur_align = load_site_settings().get("logo_align", "left")
        try:
            cur_size = int(load_site_settings().get("logo_size", "104"))
        except Exception:
            cur_size = 104

        align_row = tk.Frame(card, bg=COLOR_CARD)
        align_row.pack(fill="x", padx=16, pady=(8, 4))
        self.logo_align_var = tk.StringVar(value=cur_align)
        for txt, val in [("Izquierda", "left"), ("Centro", "center"), ("Derecha", "right")]:
            tk.Radiobutton(align_row, text=txt, variable=self.logo_align_var,
                           value=val, bg=COLOR_CARD,
                           font=("Segoe UI", 10)).pack(side="left", padx=(0, 12))

        tk.Label(card, text="Tamano del logo (mas grande = banda mas alta)",
                 font=("Segoe UI", 9, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(6, 0))
        self.logo_size_var = tk.IntVar(value=cur_size)
        tk.Scale(card, variable=self.logo_size_var,
                 from_=64, to=260, resolution=2,
                 orient="horizontal", length=460,
                 bg=COLOR_CARD, troughcolor="#E5E7EB",
                 highlightthickness=0).pack(anchor="w", padx=16)

        # --- Ajuste fino de posicion horizontal del logo ---
        tk.Label(card,
                 text="Desplazar el logo a la izquierda / derecha (px)",
                 font=("Segoe UI", 9, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD
                 ).pack(anchor="w", padx=16, pady=(8, 0))
        try:
            cur_offx = int(load_site_settings().get("logo_offset_x", "0"))
        except Exception:
            cur_offx = 0
        self.logo_offx_var = tk.IntVar(value=cur_offx)
        tk.Scale(card, variable=self.logo_offx_var,
                 from_=-200, to=200, resolution=2,
                 orient="horizontal", length=460,
                 bg=COLOR_CARD, troughcolor="#E5E7EB",
                 highlightthickness=0).pack(anchor="w", padx=16)

        # ==================================================
        # NUEVA seccion: Borde de las imagenes de producto
        # ==================================================
        tk.Label(card, text="Borde de las imagenes de producto",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(18, 4))
        tk.Label(card,
                 text=("Cambia el color y el grosor del marco alrededor de las "
                       "fotos de cada producto (en la tienda y en el carrito)."),
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16)

        cur_bcolor = load_site_settings().get("img_border_color", "#E2E8F0")
        try:
            cur_bw = int(load_site_settings().get("img_border_width", "1"))
        except Exception:
            cur_bw = 1
        self._img_border_color = cur_bcolor

        bcol_row = tk.Frame(card, bg=COLOR_CARD)
        bcol_row.pack(fill="x", padx=16, pady=(8, 4))
        tk.Button(bcol_row, text="🎨  Elegir color del borde…",
                  command=self._pick_border_color,
                  bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_2, activeforeground="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=4
                  ).pack(side="left")
        tk.Label(bcol_row, text="  Actual:", bg=COLOR_CARD,
                 font=("Segoe UI", 9)).pack(side="left", padx=(8, 4))
        self.border_swatch = tk.Label(bcol_row, bg=cur_bcolor,
                                      width=6, height=1, relief="solid", bd=1)
        self.border_swatch.pack(side="left")

        tk.Label(card, text="Grosor del borde (px)",
                 font=("Segoe UI", 9, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(6, 0))
        self.border_w_var = tk.IntVar(value=cur_bw)
        tk.Scale(card, variable=self.border_w_var,
                 from_=0, to=12, resolution=1,
                 orient="horizontal", length=460,
                 bg=COLOR_CARD, troughcolor="#E5E7EB",
                 highlightthickness=0).pack(anchor="w", padx=16)

        # ==================================================
        # NUEVA seccion: Colores del CARRITO
        # ==================================================
        tk.Label(card, text="Colores del carrito",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(18, 4))
        tk.Label(card,
                 text=("Cambia el color del fondo de cada producto dentro del "
                       "carrito, el color de la letra del nombre, el subtitulo "
                       "de precio unitario, y el cuadrito verde con el precio "
                       "total (fondo y numeros)."),
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16)

        _s = load_site_settings()
        self._cart_card_bg     = _s.get("cart_card_bg",     "#FFFFFF")
        self._cart_name_color  = _s.get("cart_name_color",  "#0F172A")
        self._cart_unit_color  = _s.get("cart_unit_color",  "#64748B")
        self._cart_price_bg    = _s.get("cart_price_bg",    "#16A34A")
        self._cart_price_fg    = _s.get("cart_price_fg",    "#FFFFFF")

        self._cart_swatches = {}

        def _add_cart_color_row(label_text, attr):
            row = tk.Frame(card, bg=COLOR_CARD)
            row.pack(fill="x", padx=16, pady=(6, 0))
            tk.Label(row, text=label_text, bg=COLOR_CARD,
                     font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT,
                     width=28, anchor="w").pack(side="left")
            tk.Button(row, text="🎨  Elegir color…",
                      command=lambda a=attr: self._pick_cart_color(a),
                      bg=COLOR_PRIMARY, fg="white",
                      activebackground=COLOR_PRIMARY_2, activeforeground="white",
                      font=("Segoe UI", 9, "bold"),
                      relief="flat", bd=0, cursor="hand2",
                      padx=10, pady=3).pack(side="left")
            sw = tk.Label(row, bg=getattr(self, attr),
                          width=6, height=1, relief="solid", bd=1)
            sw.pack(side="left", padx=(8, 0))
            self._cart_swatches[attr] = sw

        _add_cart_color_row("Fondo de cada producto",       "_cart_card_bg")
        _add_cart_color_row("Color del nombre del producto","_cart_name_color")
        _add_cart_color_row("Color del precio unitario",    "_cart_unit_color")
        _add_cart_color_row("Fondo del precio total",       "_cart_price_bg")
        _add_cart_color_row("Color de los numeros del precio","_cart_price_fg")

        # ==================================================
        # NUEVA seccion: BARRA SUPERIOR AZUL (topbar Madison)
        # ==================================================
        tk.Label(card, text="Barra superior azul (menú, búsqueda, carrito)",
                 font=("Segoe UI", 12, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(22, 4))
        tk.Label(card,
                 text=("Personaliza la barra superior azul de la tienda: el "
                       "texto del banner de delivery, el fondo (color o imagen "
                       "con difuminado / brillo / saturación / opacidad) y los "
                       "colores de los 3 botones (Menú, Lupa de búsqueda y "
                       "Carrito). Los cambios se ven al recargar la página."),
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16)

        _st = load_site_settings()
        self._tb_defaults = {
            "topbar_bg_color":      "#2A2A9C",
            "topbar_bg_image_b64":  "",
            "topbar_bg_blur":       "0",
            "topbar_bg_brightness": "100",
            "topbar_bg_saturation": "100",
            "topbar_bg_opacity":    "100",
            "btn_menu_bg":   "#3A3AAF",
            "btn_menu_fg":   "#FFFFFF",
            "btn_search_bg": "#F5B301",
            "btn_search_fg": "#0F172A",
            "btn_cart_bg":   "#3A3AAF",
            "btn_cart_fg":   "#FFFFFF",
            "menu_panel_bg": "#2A2A9C",
            "menu_panel_fg": "#FFFFFF",
            "delivery_text": "🚚  Delivery GRATIS en toda la zona de Coro",
            "delivery_text_color": "#FFFFFF",
            # --- Color global del botón "Ver más" (por apartado en la home) ---
            "section_more_bg": "#2A2A9C",
            "section_more_fg": "#FFFFFF",
            # --- Redes sociales en la barra superior ---
            "social_facebook_url":  "",
            "social_instagram_url": "",
            "social_tiktok_url":    "",
        }
        self._tb_vars = {
            k: tk.StringVar(value=_st.get(k, v))
            for k, v in self._tb_defaults.items()
        }
        self._tb_swatches = {}

        # --- Texto del banner ---
        r_txt = tk.Frame(card, bg=COLOR_CARD)
        r_txt.pack(fill="x", padx=16, pady=(10, 2))
        tk.Label(r_txt, text="Texto del banner de delivery:",
                 bg=COLOR_CARD, font=("Segoe UI", 9, "bold"),
                 fg=COLOR_TEXT).pack(anchor="w")
        tk.Entry(r_txt, textvariable=self._tb_vars["delivery_text"],
                 font=("Segoe UI", 10), relief="solid", bd=1
                 ).pack(fill="x", ipady=4, pady=(2, 0))

        # --- Color de la letra del banner de delivery ---
        r_col = tk.Frame(card, bg=COLOR_CARD)
        r_col.pack(fill="x", padx=16, pady=(8, 0))
        tk.Label(r_col, text="Color de la letra del banner:",
                 bg=COLOR_CARD, font=("Segoe UI", 9, "bold"),
                 fg=COLOR_TEXT, width=28, anchor="w").pack(side="left")
        tk.Button(r_col, text="🎨  Cambiar color de letra…",
                  command=lambda: self._pick_topbar_color("delivery_text_color"),
                  bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_2, activeforeground="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  padx=10, pady=3).pack(side="left")
        _dc_ini = self._tb_vars["delivery_text_color"].get() or "#FFFFFF"
        if not _dc_ini.startswith("#"):
            _dc_ini = "#FFFFFF"
        _dc_sw = tk.Label(r_col, bg=_dc_ini, width=6, height=1,
                          relief="solid", bd=1)
        _dc_sw.pack(side="left", padx=(8, 0))
        self._tb_swatches["delivery_text_color"] = _dc_sw

        # --- Fondo: color ---
        def _tb_color_row(label_text, key, container=card):
            row = tk.Frame(container, bg=COLOR_CARD)
            row.pack(fill="x", padx=16, pady=(6, 0))
            tk.Label(row, text=label_text, bg=COLOR_CARD,
                     font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT,
                     width=28, anchor="w").pack(side="left")
            tk.Button(row, text="🎨  Elegir color…",
                      command=lambda k=key: self._pick_topbar_color(k),
                      bg=COLOR_PRIMARY, fg="white",
                      activebackground=COLOR_PRIMARY_2, activeforeground="white",
                      font=("Segoe UI", 9, "bold"),
                      relief="flat", bd=0, cursor="hand2",
                      padx=10, pady=3).pack(side="left")
            initial = self._tb_vars[key].get()
            if not initial.startswith("#"):
                initial = "#3A3AAF"
            sw = tk.Label(row, bg=initial, width=6, height=1,
                          relief="solid", bd=1)
            sw.pack(side="left", padx=(8, 0))
            self._tb_swatches[key] = sw

        tk.Label(card, text="Fondo de la barra azul",
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT,
                 bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(12, 0))
        _tb_color_row("Color de fondo:", "topbar_bg_color")

        # --- Fondo: imagen + sliders ---
        img_row = tk.Frame(card, bg=COLOR_CARD)
        img_row.pack(fill="x", padx=16, pady=(8, 0))
        tk.Label(img_row, text="Imagen de fondo:", bg=COLOR_CARD,
                 font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT,
                 width=28, anchor="w").pack(side="left")
        tk.Button(img_row, text="🖼  Elegir…",
                  command=self._pick_topbar_image,
                  bg=COLOR_PRIMARY, fg="white",
                  activebackground=COLOR_PRIMARY_2, activeforeground="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  padx=10, pady=3).pack(side="left", padx=(0, 6))
        tk.Button(img_row, text="🗑  Quitar",
                  command=self._clear_topbar_image,
                  bg=COLOR_CARD, fg="#B91C1C",
                  activebackground=COLOR_BG, activeforeground="#B91C1C",
                  font=("Segoe UI", 9, "underline"),
                  relief="flat", bd=0, cursor="hand2"
                  ).pack(side="left")
        self._tb_img_status = tk.Label(
            img_row,
            text=("(imagen cargada)" if self._tb_vars["topbar_bg_image_b64"].get()
                  else "(sin imagen)"),
            bg=COLOR_CARD, fg=COLOR_MUTED, font=("Segoe UI", 9))
        self._tb_img_status.pack(side="left", padx=(10, 0))

        def _tb_slider_row(label_text, key, from_, to_):
            tk.Label(card, text=label_text, bg=COLOR_CARD,
                     font=("Segoe UI", 9, "bold"),
                     fg=COLOR_TEXT).pack(anchor="w", padx=16, pady=(6, 0))
            try: cur = float(self._tb_vars[key].get())
            except Exception: cur = float(from_)
            var = tk.DoubleVar(value=cur)

            def on_change(v, k=key, vv=var):
                self._tb_vars[k].set(str(int(float(v))))

            tk.Scale(card, variable=var,
                     from_=from_, to=to_, resolution=1,
                     orient="horizontal", length=460,
                     bg=COLOR_CARD, troughcolor="#E5E7EB",
                     highlightthickness=0, command=on_change
                     ).pack(anchor="w", padx=16)

        _tb_slider_row("Difuminado imagen (blur px)", "topbar_bg_blur",       0, 20)
        _tb_slider_row("Brillo imagen (%)",           "topbar_bg_brightness", 0, 200)
        _tb_slider_row("Saturación imagen (%)",       "topbar_bg_saturation", 0, 200)
        _tb_slider_row("Opacidad imagen (%)",         "topbar_bg_opacity",    0, 100)

        # --- Botones 1/2/3 ---
        for n_, key_bg, key_fg, name_ in [
            ("Botón 1 — Menú (☰)",        "btn_menu_bg",   "btn_menu_fg",   "menu"),
            ("Botón 2 — Lupa buscar (🔍)","btn_search_bg", "btn_search_fg", "search"),
            ("Botón 3 — Carrito (🛒)",    "btn_cart_bg",   "btn_cart_fg",   "cart"),
        ]:
            tk.Label(card, text=n_, font=("Segoe UI", 10, "bold"),
                     fg=COLOR_TEXT, bg=COLOR_CARD
                     ).pack(anchor="w", padx=16, pady=(12, 0))
            _tb_color_row("Color de fondo:", key_bg)
            _tb_color_row("Color de la letra:", key_fg)

        # --- Lista desplegable del Menú (aparece al hacer clic en ☰) ---
        tk.Label(card, text="Lista desplegable del menú (☰)",
                 font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD
                 ).pack(anchor="w", padx=16, pady=(14, 0))
        tk.Label(card,
                 text=("Cuando el visitante haga clic en ☰ Menú se abrirá una "
                       "lista al lado izquierdo con los apartados existentes. "
                       "Personaliza aquí sus colores."),
                 font=("Segoe UI", 9), fg=COLOR_MUTED,
                 bg=COLOR_CARD, wraplength=460, justify="left"
                 ).pack(anchor="w", padx=16, pady=(0, 4))
        _tb_color_row("Color de fondo del menú:", "menu_panel_bg")
        _tb_color_row("Color de las letras del menú:", "menu_panel_fg")

        # -----------------------------------------------------------
        # Botón «Ver más» de cada apartado (color global)
        # -----------------------------------------------------------
        tk.Label(card, text="Botón «Ver más» de cada apartado",
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT,
                 bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(14, 0))
        tk.Label(card,
                 text="Cambia el color de fondo y del texto del botón «Ver más» que aparece "
                      "en la página de inicio, al lado del nombre de cada apartado.",
                 font=("Segoe UI", 9), fg=COLOR_MUTED, bg=COLOR_CARD,
                 wraplength=520, justify="left").pack(anchor="w", padx=16, pady=(0, 4))
        _tb_color_row("Color de fondo «Ver más»:", "section_more_bg")
        _tb_color_row("Color del texto «Ver más»:", "section_more_fg")

        # -----------------------------------------------------------
        # Redes sociales (aparecen en la barra superior)
        # -----------------------------------------------------------
        tk.Label(card, text="Redes sociales (barra superior)",
                 font=("Segoe UI", 10, "bold"), fg=COLOR_TEXT,
                 bg=COLOR_CARD).pack(anchor="w", padx=16, pady=(16, 0))
        tk.Label(card,
                 text="Pega la URL de tu negocio en cada red. Los iconos se muestran "
                      "al lado de «Iniciar sesión / Registrar» y llevan a tus páginas. "
                      "Si dejas un campo vacío, ese icono no aparece.",
                 font=("Segoe UI", 9), fg=COLOR_MUTED, bg=COLOR_CARD,
                 wraplength=520, justify="left").pack(anchor="w", padx=16, pady=(0, 4))

        def _social_row(label_text, key, placeholder):
            row = tk.Frame(card, bg=COLOR_CARD)
            row.pack(fill="x", padx=16, pady=(6, 0))
            tk.Label(row, text=label_text, bg=COLOR_CARD,
                     font=("Segoe UI", 9, "bold"), fg=COLOR_TEXT,
                     width=22, anchor="w").pack(side="left")
            ent = tk.Entry(row, textvariable=self._tb_vars[key],
                           font=("Segoe UI", 10), relief="solid", bd=1)
            ent.pack(side="left", fill="x", expand=True, ipady=3)
            if not self._tb_vars[key].get():
                # placeholder visual (opcional, no bloquea)
                pass
            return ent

        _social_row("URL de Facebook:",  "social_facebook_url",  "https://facebook.com/tu-negocio")
        _social_row("URL de Instagram:", "social_instagram_url", "https://instagram.com/tu-negocio")
        _social_row("URL de TikTok:",    "social_tiktok_url",    "https://tiktok.com/@tu-negocio")

        # Espacio inferior dentro del scroll
        tk.Frame(card, bg=COLOR_CARD, height=18).pack()

    # ---- helpers Topbar Madison ----
    def _pick_topbar_color(self, key):
        cur = self._tb_vars[key].get()
        if not cur.startswith("#"):
            cur = "#3A3AAF"
        color = colorchooser.askcolor(color=cur, title="Elegir color")
        if color and color[1]:
            self._tb_vars[key].set(color[1])
            sw = self._tb_swatches.get(key)
            if sw is not None:
                sw.configure(bg=color[1])

    def _pick_topbar_image(self):
        path = filedialog.askopenfilename(
            title="Elegir imagen de fondo de la barra",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp"),
                       ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
            max_side = 1600
            w, h = img.size
            scale = min(1.0, max_side / max(w, h))
            if scale < 1.0:
                img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=85, optimize=True)
            b64 = base64.b64encode(out.getvalue()).decode("ascii")
            self._tb_vars["topbar_bg_image_b64"].set(b64)
            self._tb_img_status.configure(text=f"(cargada, {len(b64)//1024} KB)")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def _clear_topbar_image(self):
        self._tb_vars["topbar_bg_image_b64"].set("")
        self._tb_img_status.configure(text="(sin imagen)")

    # ---- helpers HERO fondo ----
    def _on_hero_mode_change(self):
        mode = self.hero_mode_var.get()
        if mode == "image":
            self.hero_img_frame.pack(fill="x", padx=16, pady=(6, 0))
            self.hero_color_frame.pack_forget()
        else:
            self.hero_color_frame.pack(fill="x", padx=16, pady=(6, 0))
            self.hero_img_frame.pack_forget()

    def _refresh_hero_preview(self, initial=False):
        src = self._new_hero_bg_path
        try:
            if src == "__REMOVE__":
                self.hero_preview_lbl.configure(image="", text="(sin imagen)")
                self._hero_preview_ref = None
                return
            if src is not None:
                img = Image.open(src).convert("RGB")
            else:
                hero_b64 = load_site_settings().get("hero_bg_b64", "").strip()
                if not hero_b64:
                    self.hero_preview_lbl.configure(image="", text="(sin imagen)")
                    self._hero_preview_ref = None
                    return
                img = Image.open(io.BytesIO(base64.b64decode(hero_b64))).convert("RGB")
            img.thumbnail((180, 110), Image.LANCZOS)
            self._hero_preview_ref = ImageTk.PhotoImage(img)
            self.hero_preview_lbl.configure(image=self._hero_preview_ref, text="")
        except Exception as e:
            if not initial:
                messagebox.showerror("Imagen invalida", str(e))
            self.hero_preview_lbl.configure(image="", text="(imagen invalida)")

    def _pick_hero_bg(self):
        path = filedialog.askopenfilename(
            title="Elige la imagen del hero",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp *.bmp")],
        )
        if not path:
            return
        self._new_hero_bg_path = path
        self._refresh_hero_preview()

    def _remove_hero_bg(self):
        if not messagebox.askyesno("Quitar imagen del hero",
                                   "Quitar la imagen del hero y volver al fondo por defecto?"):
            return
        self._new_hero_bg_path = "__REMOVE__"
        self.hero_preview_lbl.configure(image="", text="(sin imagen)")
        self._hero_preview_ref = None

    def _pick_palette_color(self, hexc: str):
        self._hero_color = hexc
        self.color_swatch.configure(bg=hexc)

    def _pick_custom_color(self):
        c = colorchooser.askcolor(color=self._hero_color, title="Elige color del hero")
        if c and c[1]:
            self._hero_color = c[1]
            self.color_swatch.configure(bg=c[1])

    def _pick_border_color(self):
        c = colorchooser.askcolor(color=self._img_border_color,
                                  title="Elige color del borde de las imagenes")
        if c and c[1]:
            self._img_border_color = c[1]
            self.border_swatch.configure(bg=c[1])

    def _pick_cart_color(self, attr: str):
        current = getattr(self, attr, "#FFFFFF")
        c = colorchooser.askcolor(color=current,
                                  title="Elige color")
        if c and c[1]:
            setattr(self, attr, c[1])
            sw = self._cart_swatches.get(attr)
            if sw is not None:
                sw.configure(bg=c[1])

    def _refresh_preview(self, initial=False):
        src = self._new_logo_path
        try:
            if src is not None:
                img = Image.open(src).convert("RGBA")
            elif CUSTOM_LOGO_FILE.exists():
                img = Image.open(CUSTOM_LOGO_FILE).convert("RGBA")
            else:
                logo_b64 = load_site_settings().get("site_logo_b64", "").strip()
                if not logo_b64:
                    self.preview_lbl.configure(image="", text="(sin imagen)")
                    self._preview_ref = None
                    return
                img = Image.open(io.BytesIO(base64.b64decode(logo_b64))).convert("RGBA")
            img.thumbnail((110, 110), Image.LANCZOS)
            self._preview_ref = ImageTk.PhotoImage(img)
            self.preview_lbl.configure(image=self._preview_ref, text="")
        except Exception as e:
            if not initial:
                messagebox.showerror("Imagen inválida", str(e))
            self.preview_lbl.configure(image="", text="(imagen inválida)")

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Elige el logo pequeño",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp")],
        )
        if not path:
            return
        self._new_logo_path = path
        self._refresh_preview()

    def _remove_logo(self):
        if not messagebox.askyesno(
            "Quitar logo",
            "¿Quitar el logo personalizado y volver al logo por defecto?"
        ):
            return
        self._new_logo_path = "__REMOVE__"
        try:
            if CUSTOM_LOGO_FILE.exists():
                CUSTOM_LOGO_FILE.unlink()
        except Exception:
            pass
        self.preview_lbl.configure(image="", text="(sin imagen)")
        self._preview_ref = None

    def _refresh_bg_preview(self, initial=False):
        src = self._new_bg_path
        try:
            if src == "__REMOVE__":
                self.bg_preview_lbl.configure(image="", text="(sin fondo)")
                self._bg_preview_ref = None
                return
            if src is not None:
                img = Image.open(src).convert("RGB")
            else:
                bg_b64 = load_site_settings().get("site_bg_b64", "").strip()
                if not bg_b64:
                    self.bg_preview_lbl.configure(image="", text="(sin fondo)")
                    self._bg_preview_ref = None
                    return
                img = Image.open(io.BytesIO(base64.b64decode(bg_b64))).convert("RGB")
            img.thumbnail((180, 110), Image.LANCZOS)
            self._bg_preview_ref = ImageTk.PhotoImage(img)
            self.bg_preview_lbl.configure(image=self._bg_preview_ref, text="")
        except Exception as e:
            if not initial:
                messagebox.showerror("Imagen invalida", str(e))
            self.bg_preview_lbl.configure(image="", text="(imagen invalida)")

    def _pick_bg(self):
        path = filedialog.askopenfilename(
            title="Elige la imagen de fondo de la web",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp *.bmp")],
        )
        if not path:
            return
        self._new_bg_path = path
        self._refresh_bg_preview()

    def _remove_bg(self):
        if not messagebox.askyesno(
            "Quitar fondo",
            "Quitar el fondo personalizado y volver al fondo por defecto?"
        ):
            return
        self._new_bg_path = "__REMOVE__"
        self.bg_preview_lbl.configure(image="", text="(sin fondo)")
        self._bg_preview_ref = None

    def _save(self):
        # El nombre y la segunda palabra son OPCIONALES. Si el usuario los deja
        # vacios, se guarda sin texto (util cuando solo se muestra el logo,
        # o cuando no se quiere ni logo ni texto).
        name = self.name_var.get().strip()
        market = self.market_var.get().strip()

        remove_logo = self._new_logo_path == "__REMOVE__"
        logo_b64 = None

        # Guardar logo si se eligió uno nuevo. Se guarda en dos sitios:
        # 1) site_logo.png para uso local.
        # 2) site_settings.json como base64 para que Streamlit Cloud lo lea
        #    desde GitHub aunque no se suba la imagen aparte.
        if self._new_logo_path and not remove_logo:
            try:
                img = Image.open(self._new_logo_path).convert("RGBA")
                out = io.BytesIO()
                img.save(out, format="PNG")
                png_bytes = out.getvalue()
                CUSTOM_LOGO_FILE.write_bytes(png_bytes)
                logo_b64 = base64.b64encode(png_bytes).decode("ascii")
            except Exception as e:
                messagebox.showerror("Error con la imagen", str(e))
                return

        # Preparar fondo (si se eligio uno nuevo)
        remove_bg = self._new_bg_path == "__REMOVE__"
        bg_b64 = None
        if self._new_bg_path and not remove_bg:
            try:
                img_bg = Image.open(self._new_bg_path).convert("RGB")
                # Redimensionar para que no pese demasiado en el JSON
                max_side = 1600
                w, h = img_bg.size
                scale = min(1.0, max_side / max(w, h))
                if scale < 1.0:
                    img_bg = img_bg.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
                out_bg = io.BytesIO()
                img_bg.save(out_bg, format="JPEG", quality=85, optimize=True)
                bg_b64 = base64.b64encode(out_bg.getvalue()).decode("ascii")
            except Exception as e:
                messagebox.showerror("Error con la imagen de fondo", str(e))
                return

        try:
            bright = float(self.bright_var.get())
        except Exception:
            bright = 1.0
        try:
            opac = float(self.opacity_var.get())
        except Exception:
            opac = 0.6

        # Guardar nombre, logo y fondo incrustados
        try:
            # --- Hero: preparar imagen o color ---
            hero_mode = self.hero_mode_var.get()
            hero_b64 = None
            remove_hero = False
            hero_color_val = None
            if hero_mode == "image":
                # Si se eligio quitar la imagen, la borramos
                if self._new_hero_bg_path == "__REMOVE__":
                    remove_hero = True
                elif self._new_hero_bg_path:
                    try:
                        img_h = Image.open(self._new_hero_bg_path).convert("RGB")
                        max_side = 1600
                        w, h = img_h.size
                        scale = min(1.0, max_side / max(w, h))
                        if scale < 1.0:
                            img_h = img_h.resize((int(w * scale), int(h * scale)),
                                                 Image.LANCZOS)
                        out_h = io.BytesIO()
                        img_h.save(out_h, format="JPEG", quality=85, optimize=True)
                        hero_b64 = base64.b64encode(out_h.getvalue()).decode("ascii")
                    except Exception as e:
                        messagebox.showerror("Error con la imagen del hero", str(e))
                        return
                # Si esta en modo imagen, limpiamos color (dejamos que use la imagen)
                hero_color_val = ""  # limpiar color guardado
            else:  # color
                remove_hero = True   # quitamos cualquier imagen guardada
                hero_color_val = self._hero_color

            try:
                hero_bright = float(self.hero_shade_var.get())
            except Exception:
                hero_bright = 1.0
            try:
                hero_opac = float(self.hero_opac_var.get())
            except Exception:
                hero_opac = 1.0

            logo_align_val = self.logo_align_var.get()
            try:
                logo_size_val = int(self.logo_size_var.get())
            except Exception:
                logo_size_val = 104
            try:
                border_w_val = int(self.border_w_var.get())
            except Exception:
                border_w_val = 1

            save_site_settings(name, market,
                               logo_b64=logo_b64, remove_logo=remove_logo,
                               bg_b64=bg_b64, remove_bg=remove_bg,
                               bg_brightness=bright, bg_opacity=opac,
                               hero_bg_b64=hero_b64, remove_hero_bg=remove_hero,
                               hero_bg_color=hero_color_val,
                               hero_brightness=hero_bright,
                               hero_opacity=hero_opac,
                               logo_align=logo_align_val,
                               logo_size=logo_size_val,
                               logo_offset_x=int(self.logo_offx_var.get()),
                               img_border_color=self._img_border_color,
                               img_border_width=border_w_val,
                               cart_card_bg=self._cart_card_bg,
                               cart_name_color=self._cart_name_color,
                               cart_unit_color=self._cart_unit_color,
                               cart_price_bg=self._cart_price_bg,
                               cart_price_fg=self._cart_price_fg)

            # --- Persistir ajustes de la BARRA SUPERIOR (topbar Madison) ---
            try:
                cur = {}
                if SETTINGS_FILE.exists():
                    try:
                        cur = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                        if not isinstance(cur, dict):
                            cur = {}
                    except Exception:
                        cur = {}
                for k in self._tb_defaults.keys():
                    v = self._tb_vars[k].get()
                    # No sobreescribir con vacio si la clave ya tenia contenido,
                    # excepto para la imagen (donde vacio = quitar imagen).
                    if k == "topbar_bg_image_b64":
                        cur[k] = v  # permite limpiar la imagen
                    else:
                        cur[k] = v if v != "" else self._tb_defaults[k]
                SETTINGS_FILE.write_text(
                    json.dumps(cur, ensure_ascii=False, indent=2),
                    encoding="utf-8")
            except Exception as e:
                messagebox.showwarning(
                    "Aviso",
                    f"El resto se guardó, pero los ajustes de la barra superior "
                    f"no se pudieron escribir:\n{e}")
        except Exception as e:
            messagebox.showerror("Error al guardar", str(e))
            return

        messagebox.showinfo("Listo",
                            "Página web actualizada. Recarga la tienda en el navegador para ver los cambios. Si usas GitHub/Streamlit Cloud, sube también site_settings.json actualizado.")
        self.destroy()



# ==========================================================
# UTILIDADES UI COMPARTIDAS
# ==========================================================
def _pick_color(parent, current: str, on_pick):
    """Abre un colorchooser y llama on_pick(hex) si el usuario elige un color."""
    color = colorchooser.askcolor(color=current, parent=parent)
    if color and color[1]:
        on_pick(color[1])


def _labeled_color(parent, label_text, initial, on_change, row):
    """Fila: label + swatch + boton 'Cambiar color'. Devuelve un dict con
    metodos {get, set}."""
    box = tk.Frame(parent, bg="white")
    box.grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
    tk.Label(box, text=label_text, font=("Segoe UI", 10, "bold"),
             fg="#0F172A", bg="white", width=26, anchor="w").pack(side="left")
    state = {"color": initial or "#000000"}
    swatch = tk.Label(box, text="  ", bg=state["color"], width=6, relief="ridge", bd=1)
    swatch.pack(side="left", padx=8)
    def _do_pick():
        def _apply(hex_):
            state["color"] = hex_
            swatch.configure(bg=hex_)
            if on_change:
                on_change(hex_)
        _pick_color(parent, state["color"], _apply)
    tk.Button(box, text="Cambiar color", command=_do_pick,
              bg="#0F172A", fg="white", relief="flat", bd=0,
              cursor="hand2", padx=10, pady=4,
              font=("Segoe UI", 9, "bold")).pack(side="left")
    def _get(): return state["color"]
    def _set(v):
        state["color"] = v; swatch.configure(bg=v)
    return {"get": _get, "set": _set}


def _labeled_spin(parent, label_text, initial, minv, maxv, row, unit=""):
    box = tk.Frame(parent, bg="white")
    box.grid(row=row, column=0, columnspan=3, sticky="ew", pady=6)
    tk.Label(box, text=label_text, font=("Segoe UI", 10, "bold"),
             fg="#0F172A", bg="white", width=26, anchor="w").pack(side="left")
    var = tk.IntVar(value=int(initial))
    sp = tk.Spinbox(box, from_=minv, to=maxv, textvariable=var,
                    width=6, font=("Segoe UI", 10))
    sp.pack(side="left", padx=8)
    if unit:
        tk.Label(box, text=unit, bg="white", fg="#64748B",
                 font=("Segoe UI", 9)).pack(side="left")
    return var


# ==========================================================
# VENTANA: FONDO COMPLETO DE LA PAGINA
# ==========================================================
class PageBgWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Fondo completo de la página web")
        self.geometry("520x560")
        self.configure(bg="white")
        self.resizable(False, False)
        s = load_site_settings()
        pad = tk.Frame(self, bg="white"); pad.pack(fill="both", expand=True, padx=22, pady=20)

        tk.Label(pad, text="Fondo de toda la página",
                 font=("Segoe UI", 15, "bold"), fg="#0F172A", bg="white"
                 ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        tk.Label(pad, text="Elige un color, una imagen o desactiva el fondo.",
                 font=("Segoe UI", 9), fg="#64748B", bg="white"
                 ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.type_var = tk.StringVar(value=s.get("page_bg_type", "color"))
        rf = tk.Frame(pad, bg="white"); rf.grid(row=2, column=0, columnspan=3, sticky="w", pady=6)
        for label, val in [("Color plano", "color"), ("Imagen", "image"), ("Sin fondo", "none")]:
            tk.Radiobutton(rf, text=label, value=val, variable=self.type_var,
                           bg="white", font=("Segoe UI", 10)).pack(side="left", padx=8)

        self.color_ctl = _labeled_color(pad, "Color de fondo",
                                        s.get("page_bg_color", "#F4F5F7"), None, row=3)

        # Imagen actual + boton elegir/quitar
        img_box = tk.Frame(pad, bg="white")
        img_box.grid(row=4, column=0, columnspan=3, sticky="ew", pady=6)
        tk.Label(img_box, text="Imagen de fondo", font=("Segoe UI", 10, "bold"),
                 fg="#0F172A", bg="white", width=26, anchor="w").pack(side="left")
        self._img_b64 = s.get("page_bg_image_b64", "")
        self._remove_img = False
        self._img_status = tk.Label(img_box,
                                    text=("(imagen cargada)" if self._img_b64 else "(sin imagen)"),
                                    fg="#64748B", bg="white", font=("Segoe UI", 9))
        self._img_status.pack(side="left", padx=6)
        tk.Button(img_box, text="Elegir imagen…", command=self._pick_img,
                  bg="#0EA5E9", fg="white", relief="flat", bd=0, cursor="hand2",
                  padx=10, pady=4, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
        tk.Button(img_box, text="Quitar", command=self._remove_image,
                  bg="#EF4444", fg="white", relief="flat", bd=0, cursor="hand2",
                  padx=10, pady=4, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)

        self.blur_var  = _labeled_spin(pad, "Difuminado (blur)",
                                       s.get("page_bg_blur", "0"), 0, 30, row=5, unit="px")
        self.bri_var   = _labeled_spin(pad, "Brillo",
                                       s.get("page_bg_brightness", "100"), 0, 200, row=6, unit="%")
        self.op_var    = _labeled_spin(pad, "Opacidad (imagen)",
                                       s.get("page_bg_opacity", "100"), 0, 100, row=7, unit="%")

        tk.Label(pad, text="El difuminado y la opacidad solo se aplican cuando eliges Imagen.",
                 font=("Segoe UI", 8, "italic"), fg="#94A3B8", bg="white"
                 ).grid(row=8, column=0, columnspan=3, sticky="w", pady=(4, 12))

        tk.Button(pad, text="Guardar", command=self._save,
                  bg="#16A34A", fg="white", relief="flat", bd=0, cursor="hand2",
                  font=("Segoe UI", 11, "bold"), pady=10
                  ).grid(row=9, column=0, columnspan=3, sticky="ew")

    def _pick_img(self):
        p = filedialog.askopenfilename(parent=self, title="Elegir imagen de fondo",
                                       filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp")])
        if not p:
            return
        try:
            im = Image.open(p).convert("RGB")
            im.thumbnail((1920, 1920))
            buf = io.BytesIO(); im.save(buf, format="JPEG", quality=85)
            self._img_b64 = base64.b64encode(buf.getvalue()).decode()
            self._remove_img = False
            self._img_status.configure(text="(imagen nueva cargada)")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def _remove_image(self):
        self._img_b64 = ""
        self._remove_img = True
        self._img_status.configure(text="(sin imagen)")

    def _save(self):
        kwargs = dict(
            page_bg_type=self.type_var.get(),
            page_bg_color=self.color_ctl["get"](),
            page_bg_blur=str(int(self.blur_var.get())),
            page_bg_brightness=str(int(self.bri_var.get())),
            page_bg_opacity=str(int(self.op_var.get())),
        )
        if self._remove_img:
            kwargs["page_bg_image_b64"] = ""
        elif self._img_b64:
            kwargs["page_bg_image_b64"] = self._img_b64
        patch_site_settings(**kwargs)
        messagebox.showinfo("Guardado", "Fondo actualizado.\nActualiza la tienda con F5.")
        self.destroy()


# ==========================================================
# VENTANA: TITULOS + LOGO
# ==========================================================
class TitlesWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Títulos y logo de la cabecera")
        self.geometry("760x640")
        self.configure(bg="white")
        pad = tk.Frame(self, bg="white"); pad.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(pad, text="Títulos de la parte superior",
                 font=("Segoe UI", 15, "bold"), fg="#0F172A", bg="white"
                 ).pack(anchor="w")
        tk.Label(pad, text="Puedes añadir varios títulos (ej. «Amazonia» y «MARKET»). "
                          "Cada uno con su fuente, color y tamaño.",
                 font=("Segoe UI", 9), fg="#64748B", bg="white",
                 wraplength=700, justify="left").pack(anchor="w", pady=(0, 8))

        # Toggle ocultar logo / ocultar titulos
        s = load_site_settings()
        self.hide_var = tk.BooleanVar(
            value=str(s.get("hide_logo", "0")).strip() in ("1","true","True","yes")
        )
        tk.Checkbutton(pad, text="Ocultar el logo pequeño (mostrar solo los títulos)",
                       variable=self.hide_var, bg="white",
                       font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(4, 2))
        self.hide_titles_var = tk.BooleanVar(
            value=str(s.get("hide_titles", "0")).strip() in ("1","true","True","yes")
        )
        tk.Checkbutton(pad, text="Ocultar los títulos (mostrar solo el logo pequeño)",
                       variable=self.hide_titles_var, bg="white",
                       font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        # Lista scroll de bloques
        list_wrap = tk.Frame(pad, bg="white")
        list_wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(list_wrap, bg="white", highlightthickness=0)
        sb = ttk.Scrollbar(list_wrap, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg="white")
        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw", width=690)
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.rows = []
        blocks = load_titles()
        if not blocks:
            blocks = [
                {"text": s.get("site_name","Amazonia"),  "font":"Pacifico","size":30,"color":"#FFFFFF","weight":"400"},
                {"text": s.get("site_market","MARKET"),  "font":"Poppins", "size":16,"color":"#F5B301","weight":"900"},
            ]
        for b in blocks:
            self._add_row(b)

        # Botones
        btns = tk.Frame(pad, bg="white"); btns.pack(fill="x", pady=(8, 0))
        tk.Button(btns, text="＋  Añadir título", command=lambda: self._add_row(None),
                  bg="#0EA5E9", fg="white", relief="flat", bd=0, cursor="hand2",
                  padx=12, pady=8, font=("Segoe UI", 10, "bold")
                  ).pack(side="left")
        tk.Button(btns, text="Guardar todo", command=self._save,
                  bg="#16A34A", fg="white", relief="flat", bd=0, cursor="hand2",
                  padx=16, pady=8, font=("Segoe UI", 10, "bold")
                  ).pack(side="right")

    def _add_row(self, block):
        b = block or {"text": "", "font": "Poppins", "size": 24,
                      "color": "#FFFFFF", "weight": "700"}
        row = tk.Frame(self.inner, bg="#F8FAFC", bd=1, relief="solid")
        row.pack(fill="x", pady=6)

        r1 = tk.Frame(row, bg="#F8FAFC"); r1.pack(fill="x", padx=8, pady=6)
        tk.Label(r1, text="Texto:", bg="#F8FAFC", font=("Segoe UI", 9, "bold")
                 ).pack(side="left")
        text_var = tk.StringVar(value=b["text"])
        tk.Entry(r1, textvariable=text_var, font=("Segoe UI", 10), width=40
                 ).pack(side="left", padx=6, fill="x", expand=True)

        r2 = tk.Frame(row, bg="#F8FAFC"); r2.pack(fill="x", padx=8, pady=(0, 6))
        tk.Label(r2, text="Fuente:", bg="#F8FAFC", font=("Segoe UI", 9)).pack(side="left")
        font_var = tk.StringVar(value=b["font"])
        ttk.Combobox(r2, textvariable=font_var, values=FONT_FAMILIES,
                     state="readonly", width=18).pack(side="left", padx=4)
        tk.Label(r2, text="Tam:", bg="#F8FAFC", font=("Segoe UI", 9)).pack(side="left", padx=(8,0))
        size_var = tk.IntVar(value=int(b["size"]))
        tk.Spinbox(r2, from_=8, to=120, textvariable=size_var, width=5
                   ).pack(side="left", padx=4)
        tk.Label(r2, text="Grosor:", bg="#F8FAFC", font=("Segoe UI", 9)).pack(side="left", padx=(8,0))
        weight_var = tk.StringVar(value=str(b["weight"]))
        ttk.Combobox(r2, textvariable=weight_var,
                     values=["300","400","600","700","800","900"],
                     state="readonly", width=5).pack(side="left", padx=4)
        color_state = {"c": b["color"]}
        sw = tk.Label(r2, text="  ", bg=b["color"], width=4, relief="ridge", bd=1)
        sw.pack(side="left", padx=(10,4))
        def _pick(sw=sw, st_=color_state):
            def _apply(hx):
                st_["c"] = hx; sw.configure(bg=hx)
            _pick_color(self, st_["c"], _apply)
        tk.Button(r2, text="Color letra", command=_pick,
                  bg="#0F172A", fg="white", relief="flat", bd=0, cursor="hand2",
                  padx=8, pady=2, font=("Segoe UI", 9, "bold")).pack(side="left")

        def _remove():
            self.rows.remove(entry)
            row.destroy()
        tk.Button(r2, text="✕", command=_remove, bg="#EF4444", fg="white",
                  relief="flat", bd=0, cursor="hand2", padx=8, pady=2,
                  font=("Segoe UI", 9, "bold")).pack(side="right")

        entry = {"text": text_var, "font": font_var, "size": size_var,
                 "weight": weight_var, "color": color_state}
        self.rows.append(entry)

    def _save(self):
        blocks = []
        for r in self.rows:
            txt = r["text"].get().strip()
            if not txt:
                continue
            blocks.append({
                "text": txt,
                "font": r["font"].get() or "Poppins",
                "size": int(r["size"].get() or 24),
                "weight": r["weight"].get() or "700",
                "color": r["color"]["c"],
            })
        save_titles(blocks)
        patch_site_settings(
            hide_logo="1" if self.hide_var.get() else "0",
            hide_titles="1" if self.hide_titles_var.get() else "0",
        )
        messagebox.showinfo("Guardado", "Títulos y logo actualizados.")
        self.destroy()


# ==========================================================
# VENTANA: COLORES DEL CARRITO
# ==========================================================
class CartStyleWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Colores del carrito")
        self.geometry("560x780")
        self.configure(bg="white")
        self.resizable(True, True)
        self.minsize(520, 640)
        s = load_site_settings()
        pad = tk.Frame(self, bg="white"); pad.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(pad, text="Colores del carrito de compras",
                 font=("Segoe UI", 15, "bold"), fg="#0F172A", bg="white"
                 ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,10))

        self.ctls = {}
        rows = [
            ("Fondo de la página del carrito", "cart_page_bg",     "#EFF3FF"),
            ("Color del nombre del producto",  "cart_name_color",  "#2A2A9C"),
            ("Color del precio unitario",      "cart_price_color", "#0F172A"),
            ("Color del número (cantidad)",    "cart_qty_color",   "#2A2A9C"),
            ("Fondo del precio por línea",     "cart_line_bg",     "#16A34A"),
            ("Letra del precio por línea",     "cart_line_fg",     "#FFFFFF"),
            ("Color del TOTAL grande",         "cart_total_color", "#16A34A"),
            ("Fondo botón «Pagar ahora»",      "cart_pay_bg",      "#16A34A"),
            ("Letra botón «Pagar ahora»",      "cart_pay_fg",      "#FFFFFF"),
            ("Fondo botón «Añadir más»",       "cart_add_bg",      "#2A2A9C"),
            ("Letra botón «Añadir más»",       "cart_add_fg",      "#FFFFFF"),
            ("Fondo botón papelera",           "cart_del_bg",      "#EF4444"),
            ("Letra botón papelera",           "cart_del_fg",      "#FFFFFF"),
        ]
        for i, (label, key, default) in enumerate(rows, start=1):
            self.ctls[key] = _labeled_color(
                pad, label, s.get(key, default), None, row=i
            )

        tk.Button(pad, text="Guardar", command=self._save,
                  bg="#16A34A", fg="white", relief="flat", bd=0, cursor="hand2",
                  font=("Segoe UI", 11, "bold"), pady=10
                  ).grid(row=len(rows)+2, column=0, columnspan=3, sticky="ew", pady=(14,0))

    def _save(self):
        patch_site_settings(**{k: c["get"]() for k, c in self.ctls.items()})
        messagebox.showinfo("Guardado", "Colores del carrito actualizados.")
        self.destroy()


# ==========================================================
# VENTANA: MOVIMIENTO, MEDIDAS Y WHATSAPP
# Controla la velocidad de la cinta de delivery, los segundos
# del banner principal (imagenes y videos), los productos
# destacados y la posicion / numero del boton de WhatsApp.
# ==========================================================
class MotionWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Movimiento, medidas y WhatsApp")
        self.geometry("560x640")
        self.configure(bg="white")
        self.minsize(520, 560)
        s = load_site_settings()
        pad = tk.Frame(self, bg="white"); pad.pack(fill="both", expand=True, padx=22, pady=18)

        tk.Label(pad, text="Movimiento, medidas y WhatsApp",
                 font=("Segoe UI", 15, "bold"), fg="#0F172A", bg="white"
                 ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        tk.Label(pad, text="Todo lo que cambies aqui se aplica en la tienda al recargar (F5).",
                 font=("Segoe UI", 9), fg="#64748B", bg="white"
                 ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self.speed_var = _labeled_spin(
            pad, "Cinta delivery: duracion", s.get("delivery_speed_s", "14"),
            4, 60, row=2, unit="s (menos = mas rapido)")
        self.img_secs_var = _labeled_spin(
            pad, "Banner: segundos por imagen", s.get("hero_image_seconds", "3"),
            1, 30, row=3, unit="s")
        self.vid_secs_var = _labeled_spin(
            pad, "Banner: maximo por video", s.get("hero_video_max_seconds", "15"),
            3, 60, row=4, unit="s")
        self.feat_count_var = _labeled_spin(
            pad, "Destacados: cuantos productos", s.get("featured_count", "18"),
            4, 60, row=5, unit="productos")
        self.feat_min_var = _labeled_spin(
            pad, "Destacados: ancho de tarjeta", s.get("featured_min_width", "180"),
            120, 400, row=6, unit="px")
        self.wa_bottom_var = _labeled_spin(
            pad, "WhatsApp: altura desde abajo", s.get("wa_bottom", "74"),
            0, 400, row=7, unit="px (mas = mas arriba)")

        ph_box = tk.Frame(pad, bg="white")
        ph_box.grid(row=8, column=0, columnspan=3, sticky="ew", pady=6)
        tk.Label(ph_box, text="Numero de WhatsApp", font=("Segoe UI", 10, "bold"),
                 fg="#0F172A", bg="white", width=26, anchor="w").pack(side="left")
        self.phone_var = tk.StringVar(value=s.get("whatsapp_phone", "584246687700"))
        tk.Entry(ph_box, textvariable=self.phone_var, font=("Segoe UI", 10),
                 relief="solid", bd=1, width=22).pack(side="left", padx=8, ipady=3)
        tk.Label(pad, text="Escribe el numero con el codigo del pais y sin signos. Ej: 584246687700",
                 font=("Segoe UI", 8, "italic"), fg="#94A3B8", bg="white"
                 ).grid(row=9, column=0, columnspan=3, sticky="w", pady=(0, 12))

        tk.Button(pad, text="Guardar", command=self._save,
                  bg="#16A34A", fg="white", relief="flat", bd=0, cursor="hand2",
                  font=("Segoe UI", 11, "bold"), pady=10
                  ).grid(row=10, column=0, columnspan=3, sticky="ew")

    def _save(self):
        phone = re.sub(r"[^0-9]", "", self.phone_var.get() or "")
        patch_site_settings(
            delivery_speed_s=str(int(self.speed_var.get())),
            hero_image_seconds=str(int(self.img_secs_var.get())),
            hero_video_max_seconds=str(int(self.vid_secs_var.get())),
            featured_count=str(int(self.feat_count_var.get())),
            featured_min_width=str(int(self.feat_min_var.get())),
            wa_bottom=str(int(self.wa_bottom_var.get())),
            whatsapp_phone=phone,
        )
        messagebox.showinfo("Guardado",
                            "Listo. Actualiza la tienda con F5 para ver los cambios.")
        self.destroy()


# ==========================================================
# VENTANA: ESTILO DE UN APARTADO
# ==========================================================
class CategoryStyleWindow(tk.Toplevel):
    def __init__(self, master, cat_name):
        super().__init__(master)
        self.master_app = master
        self.cat_name = cat_name
        self.title(f"Estilo del apartado · {cat_name}")
        self.geometry("580x820")
        self.configure(bg="white")
        self.resizable(False, False)
        s = get_cat_style(cat_name)

        pad = tk.Frame(self, bg="white"); pad.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(pad, text=f"Personalizar «{cat_name}»",
                 font=("Segoe UI", 15, "bold"), fg="#0F172A", bg="white"
                 ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        tk.Label(pad, text="Configura el círculo de la barra superior y la sección "
                          "de este apartado en el inicio.",
                 font=("Segoe UI", 9), fg="#64748B", bg="white", wraplength=500,
                 justify="left"
                 ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        # Icono (emoji) - fila propia con combobox
        ic_box = tk.Frame(pad, bg="white")
        ic_box.grid(row=2, column=0, columnspan=3, sticky="ew", pady=6)
        tk.Label(ic_box, text="Ícono dentro del círculo",
                 font=("Segoe UI", 10, "bold"), fg="#0F172A", bg="white",
                 width=26, anchor="w").pack(side="left")
        self.icon_var = tk.StringVar(value=s["icon"] or "🏷️")
        cb = ttk.Combobox(ic_box, textvariable=self.icon_var,
                          values=ICON_CHOICES, width=6, font=("Segoe UI", 14))
        cb.pack(side="left", padx=6)
        tk.Label(ic_box, text="(o escribe cualquier emoji)",
                 fg="#64748B", bg="white", font=("Segoe UI", 8, "italic")
                 ).pack(side="left", padx=4)

        # ================================================================
        # NUEVO: Ocultar icono y mostrar imagen dentro del circulo
        # ================================================================
        self._image_path = s.get("image_path", "") or ""
        self._image_b64 = s.get("image_b64", "") or ""
        self.use_image_var = tk.BooleanVar(value=bool(s.get("use_image", False)))

        img_wrap = tk.Frame(pad, bg="white")
        img_wrap.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(4, 6))

        chk = tk.Checkbutton(
            img_wrap,
            text="Ocultar ícono y mostrar imagen dentro del círculo",
            variable=self.use_image_var,
            bg="white", fg="#0F172A", activebackground="white",
            font=("Segoe UI", 10, "bold"),
            command=lambda: self._toggle_image_row(),
        )
        chk.pack(anchor="w")

        # Panel (aparece cuando la casilla esta activa)
        self.img_row = tk.Frame(pad, bg="#F1F5F9", bd=0, relief="flat")
        self.img_row.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(0, 6))

        inner = tk.Frame(self.img_row, bg="#F1F5F9")
        inner.pack(fill="x", padx=10, pady=10)

        tk.Label(inner, text="Imagen del círculo",
                 font=("Segoe UI", 10, "bold"), fg="#0F172A", bg="#F1F5F9",
                 ).pack(anchor="w")
        tk.Label(inner,
                 text="Se recomienda una imagen cuadrada (PNG/JPG). Se recortará circular.",
                 font=("Segoe UI", 8), fg="#64748B", bg="#F1F5F9",
                 ).pack(anchor="w", pady=(0, 6))

        btns = tk.Frame(inner, bg="#F1F5F9")
        btns.pack(fill="x")
        tk.Button(btns, text="Insertar imagen…",
                  command=self._pick_image,
                  bg="#2A2A9C", fg="white", relief="flat", bd=0, cursor="hand2",
                  font=("Segoe UI", 10, "bold"), padx=14, pady=6,
                  ).pack(side="left")
        tk.Button(btns, text="Quitar imagen",
                  command=self._clear_image,
                  bg="#E2E8F0", fg="#0F172A", relief="flat", bd=0, cursor="hand2",
                  font=("Segoe UI", 10), padx=12, pady=6,
                  ).pack(side="left", padx=6)

        self.img_info_lbl = tk.Label(inner, text="", font=("Segoe UI", 9),
                                     fg="#0F172A", bg="#F1F5F9", anchor="w",
                                     justify="left", wraplength=460)
        self.img_info_lbl.pack(anchor="w", pady=(8, 0))

        self._refresh_image_info()
        self._toggle_image_row()

        self.ctl_circle_color = _labeled_color(pad, "Color del círculo",
                                               s["circle_color"], None, row=5)
        self.ctl_circle_size  = _labeled_spin(pad, "Tamaño del círculo",
                                              s["circle_size"], 50, 180, row=6, unit="px")
        self.ctl_label_color  = _labeled_color(pad, "Color del nombre bajo círculo",
                                               s["label_color"], None, row=7)
        self.ctl_label_size   = _labeled_spin(pad, "Tamaño nombre bajo círculo",
                                              s["label_size"], 8, 30, row=8, unit="px")

        ttk.Separator(pad, orient="horizontal").grid(row=9, column=0, columnspan=3,
                                                     sticky="ew", pady=10)

        tk.Label(pad, text="Fila del apartado en la página principal:",
                 font=("Segoe UI", 10, "bold"), fg="#0F172A", bg="white"
                 ).grid(row=10, column=0, columnspan=3, sticky="w")

        self.ctl_title_color = _labeled_color(pad, "Color del título",
                                              s["title_color"], None, row=11)
        self.ctl_title_size  = _labeled_spin(pad, "Tamaño del título",
                                             s["title_size"], 12, 60, row=12, unit="px")
        self.ctl_more_bg     = _labeled_color(pad, "Fondo botón «Ver más»",
                                              s["more_bg"], None, row=13)
        self.ctl_more_fg     = _labeled_color(pad, "Letra botón «Ver más»",
                                              s["more_fg"], None, row=14)

        tk.Button(pad, text="Guardar estilo", command=self._save,
                  bg="#16A34A", fg="white", relief="flat", bd=0, cursor="hand2",
                  font=("Segoe UI", 11, "bold"), pady=10
                  ).grid(row=15, column=0, columnspan=3, sticky="ew", pady=(14,0))

    # ---------- helpers para la imagen del circulo ----------
    def _toggle_image_row(self):
        if self.use_image_var.get():
            self.img_row.grid()
        else:
            self.img_row.grid_remove()

    def _refresh_image_info(self):
        if self._image_path:
            self.img_info_lbl.config(text=f"Imagen actual: {self._image_path}",
                                     fg="#0F172A")
        else:
            self.img_info_lbl.config(text="Aún no has seleccionado una imagen.",
                                     fg="#64748B")

    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="Selecciona la imagen para el círculo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.bmp *.gif")],
        )
        if not path:
            return
        try:
            src = Path(path)
            # copiar a product_images con nombre unico basado en el apartado
            safe = re.sub(r"[^A-Za-z0-9_-]+", "_", self.cat_name).strip("_") or "cat"
            ext = src.suffix.lower() or ".png"
            dest_name = f"cat_{safe}_{uuid.uuid4().hex[:8]}{ext}"
            dest = CAT_IMG_DIR / dest_name
            # Reajustar imagen (cuadrada, max 512) para mantener peso bajo
            try:
                im = Image.open(src).convert("RGBA")
                w, h = im.size
                m = min(w, h)
                left = (w - m) // 2
                top = (h - m) // 2
                im = im.crop((left, top, left + m, top + m))
                if m > 512:
                    im = im.resize((512, 512), Image.LANCZOS)
                if ext in (".jpg", ".jpeg"):
                    im = im.convert("RGB")
                    im.save(dest, quality=90)
                else:
                    im.save(dest)
            except Exception:
                shutil.copy2(src, dest)
            self._image_path = f"cat_images/{dest_name}"
            # Guardamos tambien la imagen dentro del JSON (base64) para que
            # se vea en GitHub incluso si la carpeta de imagenes no se sube.
            try:
                _im = Image.open(dest).convert("RGBA")
                _buf = io.BytesIO()
                _im.save(_buf, format="PNG", optimize=True)
                self._image_b64 = base64.b64encode(_buf.getvalue()).decode()
            except Exception:
                self._image_b64 = ""
            self.use_image_var.set(True)
            self._toggle_image_row()
            self._refresh_image_info()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def _clear_image(self):
        self._image_path = ""
        self._image_b64 = ""
        self._refresh_image_info()

    def _save(self):
        patch = {
            "icon":         self.icon_var.get().strip(),
            "circle_color": self.ctl_circle_color["get"](),
            "circle_size":  int(self.ctl_circle_size.get()),
            "label_color":  self.ctl_label_color["get"](),
            "label_size":   int(self.ctl_label_size.get()),
            "title_color":  self.ctl_title_color["get"](),
            "title_size":   int(self.ctl_title_size.get()),
            "more_bg":      self.ctl_more_bg["get"](),
            "more_fg":      self.ctl_more_fg["get"](),
            "use_image":    bool(self.use_image_var.get()),
            "image_path":   self._image_path or "",
            "image_b64":    self._image_b64 or "",
        }
        set_cat_style(self.cat_name, patch)
        messagebox.showinfo("Guardado", f"Estilo de «{self.cat_name}» actualizado.")
        self.destroy()



# ==========================================================
# VENTANA: EDITAR PRODUCTO (nombre, precio, imagen)
# ==========================================================
class EditProductWindow(tk.Toplevel):
    def __init__(self, master, prod):
        super().__init__(master)
        self.master_cat = master
        self.prod = prod
        self.title(f"Editar producto - {prod.get('nombre','')}")
        self.geometry("480x520")
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)
        self._new_image_path = None
        self._preview_ref = None

        header = tk.Frame(self, bg=COLOR_PRIMARY, height=70)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text="✏️  Editar producto",
                 font=("Segoe UI", 15, "bold"),
                 fg="white", bg=COLOR_PRIMARY).pack(pady=18)

        card = tk.Frame(self, bg=COLOR_CARD)
        card.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(card, text="Imagen actual",
                 font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD
                 ).pack(anchor="w", padx=18, pady=(14, 4))
        img_row = tk.Frame(card, bg=COLOR_CARD)
        img_row.pack(fill="x", padx=18, pady=(0, 10))
        preview_hint = ("Sin imagen\n\nArrastra aquí\nuna imagen"
                        if _HAS_WINDND else "Sin imagen")
        self.preview = tk.Label(img_row, text=preview_hint,
                                width=14, height=7, bg="#F1F5F9",
                                fg=COLOR_MUTED, font=("Segoe UI", 9),
                                bd=1, relief="solid")
        self.preview.pack(side="left")
        if _HAS_WINDND:
            try:
                windnd.hook_dropfiles(  # type: ignore
                    self.preview,
                    func=lambda files: self._on_drop_image(files),
                )
            except Exception:
                pass
        try:
            rel = prod.get("imagen", "")
            if rel:
                img = Image.open(BASE_DIR / rel)
                img.thumbnail((140, 140))
                self._preview_ref = ImageTk.PhotoImage(img)
                self.preview.configure(image=self._preview_ref, text="",
                                       width=140, height=140, bg=COLOR_CARD)
        except Exception:
            pass
        tk.Button(img_row, text="📷  Cambiar imagen",
                  command=self._pick_image,
                  bg=COLOR_PRIMARY_2, fg="white",
                  activebackground=COLOR_PRIMARY, activeforeground="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  padx=14, pady=10).pack(side="left", padx=12)

        tk.Label(card, text="Nombre del producto",
                 font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD
                 ).pack(anchor="w", padx=18, pady=(6, 4))
        self.entry_name = tk.Entry(card, font=("Segoe UI", 12),
                                   bg="#F8FAFC", relief="flat", bd=0,
                                   highlightthickness=1,
                                   highlightbackground="#E2E8F0",
                                   highlightcolor=COLOR_PRIMARY_2)
        self.entry_name.pack(fill="x", padx=18, ipady=9)
        self.entry_name.insert(0, prod.get("nombre", ""))

        tk.Label(card, text="Precio (USD)",
                 font=("Segoe UI", 10, "bold"),
                 fg=COLOR_TEXT, bg=COLOR_CARD
                 ).pack(anchor="w", padx=18, pady=(10, 4))
        self.entry_price = tk.Entry(card, font=("Segoe UI", 12),
                                    bg="#F8FAFC", relief="flat", bd=0,
                                    highlightthickness=1,
                                    highlightbackground="#E2E8F0",
                                    highlightcolor=COLOR_PRIMARY_2)
        self.entry_price.pack(fill="x", padx=18, ipady=9)
        try:
            self.entry_price.insert(0, f"{float(prod.get('precio', 0)):.2f}")
        except Exception:
            self.entry_price.insert(0, str(prod.get("precio", "")))

        btns = tk.Frame(card, bg=COLOR_CARD)
        btns.pack(fill="x", padx=18, pady=(18, 8))
        tk.Button(btns, text="Guardar cambios", command=self._save,
                  bg="#16A34A", fg="white",
                  activebackground="#15803D", activeforeground="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  pady=10).pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Button(btns, text="Cancelar", command=self.destroy,
                  bg="#64748B", fg="white",
                  activebackground="#475569", activeforeground="white",
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", bd=0, cursor="hand2",
                  pady=10).pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="Nueva imagen",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp *.bmp *.gif")],
        )
        if not path:
            return
        self._apply_new_image(path)

    def _apply_new_image(self, path):
        try:
            p = Path(path)
            if not p.is_file():
                raise FileNotFoundError(path)
            if p.suffix.lower() not in {".png", ".jpg", ".jpeg",
                                        ".webp", ".bmp", ".gif"}:
                raise ValueError("Formato no soportado.")
            img = Image.open(p)
            img.thumbnail((140, 140))
            self._preview_ref = ImageTk.PhotoImage(img)
            self.preview.configure(image=self._preview_ref, text="",
                                   width=140, height=140, bg=COLOR_CARD)
            self._new_image_path = p
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la imagen:\n{e}")

    def _on_drop_image(self, files):
        if not files:
            return
        raw = files[0]
        try:
            path = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        except UnicodeDecodeError:
            path = raw.decode("mbcs", errors="ignore")  # type: ignore
        self._apply_new_image(path)


    def _save(self):
        name = self.entry_name.get().strip()
        price_raw = self.entry_price.get().strip().replace(",", ".")
        if not name:
            messagebox.showwarning("Falta nombre", "Escribe el nombre del producto.")
            return
        try:
            price = float(price_raw)
        except ValueError:
            messagebox.showwarning("Precio invalido", "Escribe un precio valido, ej: 19.90")
            return

        items = load_products()
        pid = self.prod.get("id")
        for it in items:
            if it.get("id") == pid:
                it["nombre"] = name
                it["precio"] = price
                if self._new_image_path:
                    ext = self._new_image_path.suffix.lower() or ".png"
                    new_name = f"{uuid.uuid4().hex}{ext}"
                    dest = IMG_DIR / new_name
                    try:
                        shutil.copy(self._new_image_path, dest)
                    except Exception as e:
                        messagebox.showerror("Error",
                                             f"No se pudo copiar la imagen:\n{e}")
                        return
                    old_rel = it.get("imagen", "")
                    if old_rel:
                        try:
                            (BASE_DIR / old_rel).unlink(missing_ok=True)
                        except Exception:
                            pass
                    it["imagen"] = f"product_images/{new_name}"
                break
        save_products(items)
        self.master_cat._refresh_list()
        self.master_cat.master_app._refresh_cats()
        self.destroy()


# ==========================================================
# VENTANA: AGREGAR ANUNCIOS (banner Amazon-style + 4 tarjetas)
# ==========================================================
class AnunciosWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("📢 Agregar anuncios")
        self.configure(bg="#F4F5F7")
        self.geometry("780x760")
        self.transient(master)

        self._data = self._load()
        self._card_widgets = []   # lista de dicts con refs por tarjeta

        header = tk.Label(self, text="Anuncios de la tienda (estilo Amazon)",
                          font=("Segoe UI", 14, "bold"),
                          bg="#F4F5F7", fg="#0F172A")
        header.pack(pady=(14, 4))
        tk.Label(self,
                 text="Configura el banner grande de fondo y los 4 cuadros de anuncios que\n"
                      "aparecen sobre el banner. Cada cuadro puede enlazar a una URL.",
                 font=("Segoe UI", 9), bg="#F4F5F7", fg="#64748B",
                 justify="center").pack(pady=(0, 10))

        # --- Scrollable area ---
        outer = tk.Frame(self, bg="#F4F5F7")
        outer.pack(fill="both", expand=True, padx=14, pady=6)
        canvas = tk.Canvas(outer, bg="#F4F5F7", highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        body = tk.Frame(canvas, bg="#F4F5F7")
        win_id = canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_conf(_=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())
        body.bind("<Configure>", _on_conf)
        canvas.bind("<Configure>", _on_conf)

        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_wheel)

        # -------- Banner de fondo (4 imagenes en slideshow) --------
        banner_card = tk.Frame(body, bg="white", bd=0, highlightthickness=1,
                               highlightbackground="#E2E8F0")
        banner_card.pack(fill="x", pady=(2, 12))
        tk.Label(banner_card, text="Imágenes o VIDEOS de fondo del banner (4 - se deslizan cada 1.5s)",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#0F172A").pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(banner_card,
                 text="Agrega hasta 4 imágenes grandes de fondo. Se irán pasando solas\n"
                      "cada 1.5 segundos. Cada imagen tiene su propia URL: al hacer clic\n"
                      "sobre la imagen grande, redirige a esa URL.\n\n"
                      "También puedes poner un VIDEO en cualquiera de los 4 (máximo 15\n"
                      "segundos). El banner sigue pasando solo; cuando llega al video\n"
                      "espera a que termine y luego continúa con las imágenes.",
                 font=("Segoe UI", 9), bg="white", fg="#64748B",
                 justify="left").pack(anchor="w", padx=14, pady=(0, 8))

        slides_grid = tk.Frame(banner_card, bg="white")
        slides_grid.pack(fill="x", padx=10, pady=(2, 10))
        self._slide_widgets = []
        for i in range(4):
            self._slide_widgets.append(self._build_slide(slides_grid, i))
        for c in range(2):
            slides_grid.columnconfigure(c, weight=1, uniform="slides")

        # -- Sliders: brillo, desenfoque, oscurecer, altura --
        sliders = tk.Frame(banner_card, bg="white")
        sliders.pack(fill="x", padx=14, pady=(4, 12))

        def _mk_slider(label, key, from_, to_, default):
            frm = tk.Frame(sliders, bg="white")
            frm.pack(fill="x", pady=3)
            tk.Label(frm, text=label, bg="white", fg="#0F172A",
                     font=("Segoe UI", 9, "bold"), width=22, anchor="w").pack(side="left")
            var = tk.IntVar(value=int(self._data.get(key, default)))
            sc = tk.Scale(frm, from_=from_, to=to_, orient="horizontal",
                          variable=var, bg="white", highlightthickness=0,
                          troughcolor="#E2E8F0", length=380)
            sc.pack(side="left", fill="x", expand=True)
            return var

        self._var_bright = _mk_slider("Brillo (0-200)",       "banner_brightness",  0, 200, 100)
        self._var_blur   = _mk_slider("Desenfoque (0-20 px)", "banner_blur",        0,  20,   0)
        self._var_ovr    = _mk_slider("Oscurecer (0-70)",     "banner_overlay",     0,  70,   0)
        self._var_h      = _mk_slider("Altura (px)",          "banner_height",    160, 500, 320)

        # -------- Banner secundario (fino, debajo de charcutería) --------
        sec_card = tk.Frame(body, bg="white", bd=0, highlightthickness=1,
                            highlightbackground="#E2E8F0")
        sec_card.pack(fill="x", pady=(2, 12))
        tk.Label(sec_card, text="Banner secundario (fino - debajo de los apartados)",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#0F172A").pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(sec_card,
                 text="Se muestra fino, a lo ancho de toda la pantalla, debajo de\n"
                      "las categorías (por ejemplo debajo de Charcutería). Cambia\n"
                      "automáticamente al mismo tiempo que el banner principal.\n"
                      "Cada imagen puede tener su URL de destino.",
                 font=("Segoe UI", 9), bg="white", fg="#64748B",
                 justify="left").pack(anchor="w", padx=14, pady=(0, 8))
        sec_grid = tk.Frame(sec_card, bg="white")
        sec_grid.pack(fill="x", padx=10, pady=(2, 12))
        self._sec_widgets = []
        for i in range(4):
            self._sec_widgets.append(self._build_sec_slide(sec_grid, i))
        for c in range(2):
            sec_grid.columnconfigure(c, weight=1, uniform="secslides")

        # -------- Tercer banner (fino, justo debajo de Charcuteria) --------
        ter_card = tk.Frame(body, bg="white", bd=0, highlightthickness=1,
                            highlightbackground="#E2E8F0")
        ter_card.pack(fill="x", pady=(2, 12))
        tk.Label(ter_card, text="Tercer banner (fino - justo debajo de Charcuteria)",
                 font=("Segoe UI", 11, "bold"),
                 bg="white", fg="#0F172A").pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(ter_card,
                 text="Igual que el banner secundario (tamano recomendado 1920 x 130 px).\n"
                      "Se muestra a lo ancho de toda la pantalla, justo debajo del\n"
                      "apartado Charcuteria. Si lo dejas vacio, se usaran las mismas\n"
                      "imagenes del banner secundario.",
                 font=("Segoe UI", 9), bg="white", fg="#64748B",
                 justify="left").pack(anchor="w", padx=14, pady=(0, 8))
        ter_grid = tk.Frame(ter_card, bg="white")
        ter_grid.pack(fill="x", padx=10, pady=(2, 12))
        self._ter_widgets = []
        for i in range(4):
            self._ter_widgets.append(self._build_ter_slide(ter_grid, i))
        for c in range(2):
            ter_grid.columnconfigure(c, weight=1, uniform="terslides")

        # -------- 4 cuadros --------
        tk.Label(body, text="Cuadros de anuncios (máx. 4)",
                 font=("Segoe UI", 11, "bold"),
                 bg="#F4F5F7", fg="#0F172A").pack(anchor="w", pady=(4, 6))

        grid = tk.Frame(body, bg="#F4F5F7")
        grid.pack(fill="x")
        for i in range(4):
            self._card_widgets.append(self._build_card(grid, i))
        for c in range(2):
            grid.columnconfigure(c, weight=1, uniform="ads")

        # -------- Botones de accion --------
        actions = tk.Frame(self, bg="#F4F5F7")
        actions.pack(fill="x", padx=14, pady=(8, 14))
        tk.Button(actions, text="💾  Guardar anuncios",
                  bg="#16A34A", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 11, "bold"), cursor="hand2", pady=10,
                  command=self._save).pack(side="right")
        tk.Button(actions, text="Cerrar",
                  bg="#E2E8F0", fg="#0F172A", relief="flat", bd=0,
                  font=("Segoe UI", 10), cursor="hand2", pady=8,
                  command=self.destroy).pack(side="right", padx=8)

    # ---------- helpers ----------
    def _load(self) -> dict:
        defaults = {
            "banner_img_b64": "",
            "banner_brightness": 100,
            "banner_blur": 0,
            "banner_overlay": 0,
            "banner_height": 320,
            "banner_slides": [
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
            ],
            "banner_secundario": [
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
            ],
            "banner_tercero": [
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
                {"img_b64": "", "url": "", "video_b64": "", "video_dur": 0},
            ],
            "cards": [
                {"title": "", "img_b64": "", "url": ""},
                {"title": "", "img_b64": "", "url": ""},
                {"title": "", "img_b64": "", "url": ""},
                {"title": "", "img_b64": "", "url": ""},
            ],
        }
        if ANUNCIOS_FILE.exists():
            try:
                d = json.loads(ANUNCIOS_FILE.read_text(encoding="utf-8"))
                for k, v in defaults.items():
                    d.setdefault(k, v)
                cards = list(d.get("cards", []))
                while len(cards) < 4:
                    cards.append({"title": "", "img_b64": "", "url": ""})
                d["cards"] = cards[:4]
                slides = list(d.get("banner_slides", []))
                # Migracion: si habia un banner_img_b64 antiguo, usarlo como slide 1
                if d.get("banner_img_b64") and not any(s.get("img_b64") for s in slides):
                    if not slides:
                        slides = [{"img_b64": "", "url": ""} for _ in range(4)]
                    slides[0] = {"img_b64": d["banner_img_b64"], "url": ""}
                while len(slides) < 4:
                    slides.append({"img_b64": "", "url": ""})
                d["banner_slides"] = slides[:4]
                sec = list(d.get("banner_secundario", []))
                while len(sec) < 4:
                    sec.append({"img_b64": "", "url": ""})
                d["banner_secundario"] = sec[:4]
                ter = list(d.get("banner_tercero", []))
                while len(ter) < 4:
                    ter.append({"img_b64": "", "url": ""})
                d["banner_tercero"] = ter[:4]
                # Asegurar claves de video en todos los slides (compatibilidad)
                for _k in ("banner_slides", "banner_secundario", "banner_tercero"):
                    for _s in d.get(_k, []):
                        _s.setdefault("video_b64", "")
                        _s.setdefault("video_dur", 0)
                return d
            except Exception:
                pass
        return defaults

    def _build_card(self, parent, idx):
        card = tk.Frame(parent, bg="white", bd=0, highlightthickness=1,
                        highlightbackground="#E2E8F0")
        r, c = divmod(idx, 2)
        card.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)

        info = self._data["cards"][idx]

        tk.Label(card, text=f"Cuadro #{idx+1}",
                 bg="white", fg="#0F172A",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 2))

        tk.Label(card, text="Título (aparece arriba del cuadro):",
                 bg="white", fg="#64748B",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10)
        var_title = tk.StringVar(value=info.get("title", ""))
        tk.Entry(card, textvariable=var_title, font=("Segoe UI", 10),
                 relief="solid", bd=1).pack(fill="x", padx=10, pady=(2, 8))

        preview = tk.Label(card, bg="#F1F5F9",
                           text="(Sin imagen)", fg="#94A3B8",
                           width=30, height=6)
        preview.pack(padx=10, pady=4, fill="x")

        row_btn = tk.Frame(card, bg="white")
        row_btn.pack(fill="x", padx=10, pady=(2, 6))
        tk.Button(row_btn, text="🖼 Elegir imagen",
                  bg="#2563EB", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4,
                  command=lambda i=idx: self._pick_card_img(i)).pack(side="left")
        tk.Button(row_btn, text="🗑",
                  bg="#DC2626", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4, padx=8,
                  command=lambda i=idx: self._clear_card_img(i)).pack(side="left", padx=4)

        tk.Label(card, text="URL de destino (a dónde redirige al hacer clic):",
                 bg="white", fg="#64748B",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(4, 0))
        var_url = tk.StringVar(value=info.get("url", ""))
        tk.Entry(card, textvariable=var_url, font=("Segoe UI", 10),
                 relief="solid", bd=1).pack(fill="x", padx=10, pady=(2, 12))

        refs = {"title": var_title, "url": var_url, "preview": preview}
        self._render_card_preview(idx, preview)
        return refs

    # ================= VIDEOS EN LOS BANNERS =================
    # Cada slide de banner puede tener imagen O video (max. 15 s).
    MAX_VIDEO_SECONDS = 15
    MAX_VIDEO_MB = 12
    _GROUP_WIDGETS = {
        "banner_slides": "_slide_widgets",
        "banner_secundario": "_sec_widgets",
        "banner_tercero": "_ter_widgets",
    }

    def _group_preview(self, group, idx):
        widgets = getattr(self, self._GROUP_WIDGETS[group], [])
        if idx < len(widgets):
            return widgets[idx].get("preview")
        return None

    def _rerender_group(self, group, idx):
        prev = self._group_preview(group, idx)
        if prev is None:
            return
        if group == "banner_slides":
            self._render_slide_preview(idx, prev)
        elif group == "banner_secundario":
            self._render_sec_preview(idx, prev)
        else:
            self._render_ter_preview(idx, prev)

    @staticmethod
    def _video_duration_seconds(path):
        """Devuelve la duracion del video en segundos (0 si no se pudo leer).
        Lee el atomo mvhd de MP4/MOV sin depender de programas externos."""
        try:
            with open(path, "rb") as f:
                data = f.read(4 * 1024 * 1024)   # con la cabecera basta
            i = data.find(b"mvhd")
            if i < 0:
                return 0
            version = data[i + 4]
            if version == 1:
                timescale = int.from_bytes(data[i + 20:i + 24], "big")
                duration = int.from_bytes(data[i + 24:i + 32], "big")
            else:
                timescale = int.from_bytes(data[i + 12:i + 16], "big")
                duration = int.from_bytes(data[i + 16:i + 20], "big")
            if not timescale:
                return 0
            return round(duration / timescale, 2)
        except Exception:
            return 0

    def _pick_video(self, group, idx):
        path = filedialog.askopenfilename(
            title=f"Elegir video (maximo {self.MAX_VIDEO_SECONDS} segundos) #{idx+1}",
            filetypes=[("Videos MP4", "*.mp4 *.m4v *.mov"), ("Todos", "*.*")])
        if not path:
            return
        try:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            if size_mb > self.MAX_VIDEO_MB:
                messagebox.showerror(
                    "Video demasiado pesado",
                    f"El video pesa {size_mb:.1f} MB y el maximo permitido es "
                    f"{self.MAX_VIDEO_MB} MB.\n\nComprimelo o recortalo e intenta de nuevo.")
                return
            dur = self._video_duration_seconds(path)
            if dur and dur > self.MAX_VIDEO_SECONDS + 0.5:
                messagebox.showerror(
                    "Video muy largo",
                    f"El video dura {dur:.1f} segundos y el maximo permitido es "
                    f"{self.MAX_VIDEO_SECONDS} segundos.\n\nRecortalo e intenta de nuevo.")
                return
            if not dur:
                if not messagebox.askyesno(
                        "No se pudo leer la duracion",
                        "No se pudo leer la duracion del video.\n\n"
                        f"Asegurate de que dure {self.MAX_VIDEO_SECONDS} segundos o menos.\n"
                        "En la web solo se reproduciran los primeros "
                        f"{self.MAX_VIDEO_SECONDS} segundos.\n\n¿Deseas usarlo igual?"):
                    return
            with open(path, "rb") as f:
                raw = f.read()
            self._data[group][idx]["video_b64"] = base64.b64encode(raw).decode()
            self._data[group][idx]["video_dur"] = min(dur or self.MAX_VIDEO_SECONDS,
                                                      self.MAX_VIDEO_SECONDS)
            # El video manda: se quita la imagen de ese slide para no duplicar.
            self._data[group][idx]["img_b64"] = ""
            self._rerender_group(group, idx)
            messagebox.showinfo(
                "Video agregado",
                "Video agregado correctamente.\n\nEn la web las imagenes seguiran pasando "
                "solas y, al llegar a este slide, el banner esperara a que el video "
                "termine antes de continuar.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el video:\n{e}")

    def _clear_video(self, group, idx):
        self._data[group][idx]["video_b64"] = ""
        self._data[group][idx]["video_dur"] = 0
        self._rerender_group(group, idx)

    def _video_buttons_row(self, parent, group, idx, bg):
        row = tk.Frame(parent, bg=bg)
        row.pack(fill="x", padx=10, pady=(0, 6))
        tk.Button(row, text="🎬 Agregar video",
                  bg="#7C3AED", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4,
                  command=lambda: self._pick_video(group, idx)).pack(side="left")
        tk.Button(row, text="🗑 Quitar video",
                  bg="#DC2626", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4, padx=8,
                  command=lambda: self._clear_video(group, idx)).pack(side="left", padx=4)
        tk.Label(row, text=f"máx. {self.MAX_VIDEO_SECONDS}s",
                 bg=bg, fg="#94A3B8", font=("Segoe UI", 8)).pack(side="left", padx=4)
        return row

    def _show_video_preview(self, group, idx, preview_widget):
        """Si el slide tiene video, pinta el aviso y devuelve True."""
        info = self._data[group][idx]
        vb64 = (info.get("video_b64") or "").strip()
        if not vb64:
            return False
        dur = info.get("video_dur") or 0
        mb = len(vb64) * 3 / 4 / (1024 * 1024)
        txt = "🎬 VIDEO cargado"
        if dur:
            txt += f" ({dur:g}s)"
        txt += f"\n{mb:.1f} MB"
        preview_widget.configure(image="", text=txt, fg="#7C3AED")
        preview_widget.image = None
        return True

    def _build_slide(self, parent, idx):
        card = tk.Frame(parent, bg="#F8FAFC", bd=0, highlightthickness=1,
                        highlightbackground="#E2E8F0")
        r, c = divmod(idx, 2)
        card.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)

        info = self._data["banner_slides"][idx]

        tk.Label(card, text=f"Imagen de fondo #{idx+1}",
                 bg="#F8FAFC", fg="#0F172A",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

        preview = tk.Label(card, bg="#EEF2FF",
                           text="(Sin imagen)", fg="#94A3B8",
                           width=30, height=5)
        preview.pack(padx=10, pady=4, fill="x")

        row_btn = tk.Frame(card, bg="#F8FAFC")
        row_btn.pack(fill="x", padx=10, pady=(2, 6))
        tk.Button(row_btn, text="🖼 Elegir imagen",
                  bg="#2563EB", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4,
                  command=lambda i=idx: self._pick_slide_img(i)).pack(side="left")
        tk.Button(row_btn, text="🗑",
                  bg="#DC2626", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4, padx=8,
                  command=lambda i=idx: self._clear_slide_img(i)).pack(side="left", padx=4)

        self._video_buttons_row(card, "banner_slides", idx, "#F8FAFC")

        tk.Label(card, text="URL al hacer clic en esta imagen o video:",
                 bg="#F8FAFC", fg="#64748B",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(4, 0))
        var_url = tk.StringVar(value=info.get("url", ""))
        tk.Entry(card, textvariable=var_url, font=("Segoe UI", 10),
                 relief="solid", bd=1).pack(fill="x", padx=10, pady=(2, 10))

        refs = {"url": var_url, "preview": preview}
        self._render_slide_preview(idx, preview)
        return refs

    def _render_slide_preview(self, idx, preview_widget):
        if self._show_video_preview("banner_slides", idx, preview_widget):
            return
        preview_widget.configure(fg="#94A3B8")
        b64 = self._data["banner_slides"][idx].get("img_b64", "")
        if not b64:
            preview_widget.configure(image="", text="(Sin imagen)")
            preview_widget.image = None
            return
        try:
            raw = base64.b64decode(b64)
            img = Image.open(io.BytesIO(raw))
            img.thumbnail((320, 160))
            ph = ImageTk.PhotoImage(img)
            preview_widget.configure(image=ph, text="")
            preview_widget.image = ph
        except Exception:
            preview_widget.configure(image="", text="(imagen invalida)")

    def _pick_slide_img(self, idx):
        path = filedialog.askopenfilename(
            title=f"Elegir imagen de fondo #{idx+1}",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp *.bmp"),
                       ("Todos", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((1800, 900))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)
            self._data["banner_slides"][idx]["img_b64"] = base64.b64encode(buf.getvalue()).decode()
            self._data["banner_slides"][idx]["video_b64"] = ""
            self._data["banner_slides"][idx]["video_dur"] = 0
            self._render_slide_preview(idx, self._slide_widgets[idx]["preview"])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def _clear_slide_img(self, idx):
        self._data["banner_slides"][idx]["img_b64"] = ""
        self._render_slide_preview(idx, self._slide_widgets[idx]["preview"])

    def _build_sec_slide(self, parent, idx):
        card = tk.Frame(parent, bg="#F8FAFC", bd=0, highlightthickness=1,
                        highlightbackground="#E2E8F0")
        r, c = divmod(idx, 2)
        card.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)

        info = self._data["banner_secundario"][idx]

        tk.Label(card, text=f"Banner secundario #{idx+1}",
                 bg="#F8FAFC", fg="#0F172A",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

        preview = tk.Label(card, bg="#EEF2FF",
                           text="(Sin imagen)", fg="#94A3B8",
                           width=30, height=3)
        preview.pack(padx=10, pady=4, fill="x")

        row_btn = tk.Frame(card, bg="#F8FAFC")
        row_btn.pack(fill="x", padx=10, pady=(2, 6))
        tk.Button(row_btn, text="🖼 Elegir imagen",
                  bg="#2563EB", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4,
                  command=lambda i=idx: self._pick_sec_img(i)).pack(side="left")
        tk.Button(row_btn, text="🗑",
                  bg="#DC2626", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4, padx=8,
                  command=lambda i=idx: self._clear_sec_img(i)).pack(side="left", padx=4)

        self._video_buttons_row(card, "banner_secundario", idx, "#F8FAFC")

        tk.Label(card, text="URL al hacer clic en esta imagen o video:",
                 bg="#F8FAFC", fg="#64748B",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(4, 0))
        var_url = tk.StringVar(value=info.get("url", ""))
        tk.Entry(card, textvariable=var_url, font=("Segoe UI", 10),
                 relief="solid", bd=1).pack(fill="x", padx=10, pady=(2, 10))

        refs = {"url": var_url, "preview": preview}
        self._render_sec_preview(idx, preview)
        return refs

    def _render_sec_preview(self, idx, preview_widget):
        if self._show_video_preview("banner_secundario", idx, preview_widget):
            return
        preview_widget.configure(fg="#94A3B8")
        b64 = self._data["banner_secundario"][idx].get("img_b64", "")
        if not b64:
            preview_widget.configure(image="", text="(Sin imagen)")
            preview_widget.image = None
            return
        try:
            raw = base64.b64decode(b64)
            img = Image.open(io.BytesIO(raw))
            img.thumbnail((320, 90))
            ph = ImageTk.PhotoImage(img)
            preview_widget.configure(image=ph, text="")
            preview_widget.image = ph
        except Exception:
            preview_widget.configure(image="", text="(imagen invalida)")

    def _pick_sec_img(self, idx):
        path = filedialog.askopenfilename(
            title=f"Elegir imagen de banner secundario #{idx+1}",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp *.bmp"),
                       ("Todos", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((2000, 500))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)
            self._data["banner_secundario"][idx]["img_b64"] = base64.b64encode(buf.getvalue()).decode()
            self._data["banner_secundario"][idx]["video_b64"] = ""
            self._data["banner_secundario"][idx]["video_dur"] = 0
            self._render_sec_preview(idx, self._sec_widgets[idx]["preview"])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def _clear_sec_img(self, idx):
        self._data["banner_secundario"][idx]["img_b64"] = ""
        self._render_sec_preview(idx, self._sec_widgets[idx]["preview"])

    # ---------- Tercer banner ----------
    def _build_ter_slide(self, parent, idx):
        card = tk.Frame(parent, bg="#F8FAFC", bd=0, highlightthickness=1,
                        highlightbackground="#E2E8F0")
        r, c = divmod(idx, 2)
        card.grid(row=r, column=c, sticky="nsew", padx=6, pady=6)

        info = self._data["banner_tercero"][idx]

        tk.Label(card, text=f"Tercer banner #{idx+1}",
                 bg="#F8FAFC", fg="#0F172A",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

        preview = tk.Label(card, bg="#EEF2FF",
                           text="(Sin imagen)", fg="#94A3B8",
                           width=30, height=3)
        preview.pack(padx=10, pady=4, fill="x")

        row_btn = tk.Frame(card, bg="#F8FAFC")
        row_btn.pack(fill="x", padx=10, pady=(2, 6))
        tk.Button(row_btn, text="\U0001F5BC Elegir imagen",
                  bg="#2563EB", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4,
                  command=lambda i=idx: self._pick_ter_img(i)).pack(side="left")
        tk.Button(row_btn, text="\U0001F5D1",
                  bg="#DC2626", fg="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2", pady=4, padx=8,
                  command=lambda i=idx: self._clear_ter_img(i)).pack(side="left", padx=4)

        self._video_buttons_row(card, "banner_tercero", idx, "#F8FAFC")

        tk.Label(card, text="URL al hacer clic en esta imagen:",
                 bg="#F8FAFC", fg="#64748B",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(4, 0))
        var_url = tk.StringVar(value=info.get("url", ""))
        tk.Entry(card, textvariable=var_url, font=("Segoe UI", 10),
                 relief="solid", bd=1).pack(fill="x", padx=10, pady=(2, 10))

        refs = {"url": var_url, "preview": preview}
        self._render_ter_preview(idx, preview)
        return refs

    def _render_ter_preview(self, idx, preview_widget):
        if self._show_video_preview("banner_tercero", idx, preview_widget):
            return
        preview_widget.configure(fg="#94A3B8")
        b64 = self._data["banner_tercero"][idx].get("img_b64", "")
        if not b64:
            preview_widget.configure(image="", text="(Sin imagen)")
            preview_widget.image = None
            return
        try:
            raw = base64.b64decode(b64)
            img = Image.open(io.BytesIO(raw))
            img.thumbnail((320, 90))
            ph = ImageTk.PhotoImage(img)
            preview_widget.configure(image=ph, text="")
            preview_widget.image = ph
        except Exception:
            preview_widget.configure(image="", text="(imagen invalida)")

    def _pick_ter_img(self, idx):
        path = filedialog.askopenfilename(
            title=f"Elegir imagen del tercer banner #{idx+1}",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp *.bmp"),
                       ("Todos", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((2000, 500))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)
            self._data["banner_tercero"][idx]["img_b64"] = base64.b64encode(buf.getvalue()).decode()
            self._data["banner_tercero"][idx]["video_b64"] = ""
            self._data["banner_tercero"][idx]["video_dur"] = 0
            self._render_ter_preview(idx, self._ter_widgets[idx]["preview"])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def _clear_ter_img(self, idx):
        self._data["banner_tercero"][idx]["img_b64"] = ""
        self._render_ter_preview(idx, self._ter_widgets[idx]["preview"])

    def _render_card_preview(self, idx, preview_widget):
        b64 = self._data["cards"][idx].get("img_b64", "")
        if not b64:
            preview_widget.configure(image="", text="(Sin imagen)")
            preview_widget.image = None
            return
        try:
            raw = base64.b64decode(b64)
            img = Image.open(io.BytesIO(raw))
            img.thumbnail((220, 140))
            ph = ImageTk.PhotoImage(img)
            preview_widget.configure(image=ph, text="")
            preview_widget.image = ph
        except Exception:
            preview_widget.configure(image="", text="(imagen invalida)")

    def _pick_card_img(self, idx):
        path = filedialog.askopenfilename(
            title=f"Elegir imagen del cuadro #{idx+1}",
            filetypes=[("Imagenes", "*.png *.jpg *.jpeg *.webp *.bmp"),
                       ("Todos", "*.*")])
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
            img.thumbnail((900, 900))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88)
            self._data["cards"][idx]["img_b64"] = base64.b64encode(buf.getvalue()).decode()
            self._render_card_preview(idx, self._card_widgets[idx]["preview"])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la imagen:\n{e}")

    def _clear_card_img(self, idx):
        self._data["cards"][idx]["img_b64"] = ""
        self._render_card_preview(idx, self._card_widgets[idx]["preview"])

    def _save(self):
        self._data["banner_brightness"] = int(self._var_bright.get())
        self._data["banner_blur"]       = int(self._var_blur.get())
        self._data["banner_overlay"]    = int(self._var_ovr.get())
        self._data["banner_height"]     = int(self._var_h.get())
        # Guardar URLs de cada slide del banner
        for i, refs in enumerate(self._slide_widgets):
            self._data["banner_slides"][i]["url"] = refs["url"].get().strip()
        for i, refs in enumerate(self._sec_widgets):
            self._data["banner_secundario"][i]["url"] = refs["url"].get().strip()
        for i, refs in enumerate(getattr(self, "_ter_widgets", [])):
            self._data["banner_tercero"][i]["url"] = refs["url"].get().strip()
        for i, refs in enumerate(self._card_widgets):
            self._data["cards"][i]["title"] = refs["title"].get().strip()
            self._data["cards"][i]["url"]   = refs["url"].get().strip()
        try:
            ANUNCIOS_FILE.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8")
            messagebox.showinfo("Guardado",
                                "Anuncios guardados. Refresca la tienda (F5) para verlos.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")


def main():
    # Ya NO se lanza Streamlit. La tienda ahora es la web estática
    # (index.html + styles.css + app.js). Usa el botón "Abrir la
    # tienda en el navegador" cuando quieras previsualizar.
    app = ApartadosApp()
    app.mainloop()


# La llamada a main() está al final del archivo. Es importante que el parche
# se defina primero; de lo contrario Tkinter abre la ventana antes de conocer
# SubcatsEditorWindow y el botón produce NameError.





# =========================================================
# PARCHE para agregar_producto.py
# Añade un botón "🧩  Editar imágenes y texto de apartado"
# y su ventana editora. Guarda en subcategorias.json (que
# lee tu index.html/app.js para mostrar la fila estilo Madison).
#
# CÓMO INSTALAR:
# 1) Abre agregar_producto.py con un editor de texto.
# 2) Copia y pega TODO este archivo AL FINAL de agregar_producto.py
#    (después de la última línea) — es autocontenido y no rompe nada.
# 3) Busca en agregar_producto.py el bloque donde se crea el botón
#    "🎨  Editar página web" (dentro del método _build_ui de la clase
#    principal, aprox. líneas 689-698). Justo DEBAJO de la línea:
#         edit_site_btn.pack(fill="x", padx=20, pady=(4, 8))
#    pega estas 3 líneas (respeta la indentación con espacios):
#
#         subcats_btn = tk.Button(card, text="🧩  Editar imágenes y texto de apartado",
#                                 command=lambda: SubcatsEditorWindow(self),
#                                 bg="#0EA5E9", fg="white",
#                                 activebackground="#0EA5E9", activeforeground="white",
#                                 font=("Segoe UI", 11, "bold"),
#                                 relief="flat", bd=0, cursor="hand2", pady=10)
#         subcats_btn.pack(fill="x", padx=20, pady=(0, 8))
#
# 4) Guarda y ejecuta:  python agregar_producto.py
# =========================================================

import base64 as _b64
import io as _io
import json as _json
import shutil as _shutil
import uuid as _uuid
from pathlib import Path as _Path
import tkinter as _tk
from tkinter import filedialog as _filedialog
from tkinter import messagebox as _messagebox
from tkinter import ttk as _ttk
from PIL import Image as _Image, ImageTk as _ImageTk

_BASE_DIR = _Path(__file__).parent.resolve()
_SUBCATS_FILE = _BASE_DIR / "subcategorias.json"
_SUBCAT_IMG_DIR = _BASE_DIR / "subcat_images"
_SUBCAT_IMG_DIR.mkdir(exist_ok=True)
_CATS_FILE_LOCAL = _BASE_DIR / "categories.json"


def _load_subcats() -> dict:
    if not _SUBCATS_FILE.exists():
        return {}
    try:
        with open(_SUBCATS_FILE, "r", encoding="utf-8") as f:
            data = _json.load(f)
        if isinstance(data, dict):
            data.pop("_ejemplo_borrar", None)
            return data
        return {}
    except Exception:
        return {}


def _save_subcats(data: dict) -> None:
    with open(_SUBCATS_FILE, "w", encoding="utf-8") as f:
        _json.dump(data, f, ensure_ascii=False, indent=2)


def _load_cats_local() -> list:
    if not _CATS_FILE_LOCAL.exists():
        return []
    try:
        with open(_CATS_FILE_LOCAL, "r", encoding="utf-8") as f:
            data = _json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


class SubcatsEditorWindow(_tk.Toplevel):
    """Editor de sub-apartados (mosaicos estilo Madison)."""

    def __init__(self, master):
        super().__init__(master)
        self.title("🧩 Editar imágenes y texto de apartado")
        self.geometry("760x640")
        self.configure(bg="#F4F5F7")
        self.transient(master)
        self.grab_set()

        self._current_cat = None
        self._slots = []          # lista de dicts para los 4 slots
        self._preview_imgs = []   # refs Tk para que no se recolecten

        cats = _load_cats_local()
        if not cats:
            _tk.Label(self, text="Todavía no hay apartados creados.\nCrea uno primero en la pantalla principal.",
                      bg="#F4F5F7", fg="#334155", font=("Segoe UI", 11)).pack(pady=40)
            return

        top = _tk.Frame(self, bg="#F4F5F7")
        top.pack(fill="x", padx=16, pady=(16, 8))
        _tk.Label(top, text="Elige el apartado:", bg="#F4F5F7",
                  font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 8))
        self.cat_var = _tk.StringVar(value=cats[0])
        self.cat_combo = _ttk.Combobox(top, values=cats, state="readonly",
                                       textvariable=self.cat_var, width=32)
        self.cat_combo.pack(side="left")
        self.cat_combo.bind("<<ComboboxSelected>>", lambda e: self._load_cat(self.cat_var.get()))

        hint = _tk.Label(self,
                         text="Cada apartado puede tener hasta 4 mosaicos.\n"
                              "Cada mosaico se muestra en la página principal con su imagen + nombre.\n"
                              "Cuando el cliente hace clic, se filtran los productos del apartado por las palabras clave.",
                         bg="#F4F5F7", fg="#475569", justify="left",
                         font=("Segoe UI", 9))
        hint.pack(fill="x", padx=16, pady=(0, 10))

        # Zona scrollable con los 4 slots
        cont = _tk.Frame(self, bg="#F4F5F7")
        cont.pack(fill="both", expand=True, padx=12)
        canvas = _tk.Canvas(cont, bg="#F4F5F7", highlightthickness=0)
        sb = _ttk.Scrollbar(cont, orient="vertical", command=canvas.yview)
        self.inner = _tk.Frame(canvas, bg="#F4F5F7")
        self.inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Botones inferiores
        btns = _tk.Frame(self, bg="#F4F5F7")
        btns.pack(fill="x", padx=16, pady=12)
        _tk.Button(btns, text="💾  Guardar cambios", command=self._save,
                   bg="#16A34A", fg="white", font=("Segoe UI", 11, "bold"),
                   relief="flat", cursor="hand2", pady=8).pack(side="right")
        _tk.Button(btns, text="Cerrar", command=self.destroy,
                   bg="#E2E8F0", fg="#0F172A", font=("Segoe UI", 10),
                   relief="flat", cursor="hand2", pady=8).pack(side="right", padx=8)

        self._load_cat(cats[0])

    def _load_cat(self, cat: str):
        self._current_cat = cat
        for w in self.inner.winfo_children():
            w.destroy()
        self._slots = []
        self._preview_imgs = []
        data = _load_subcats()
        existing = data.get(cat, []) if isinstance(data.get(cat), list) else []
        for i in range(4):
            src = existing[i] if i < len(existing) else {}
            self._build_slot(i, src)

    def _build_slot(self, idx: int, data: dict):
        card = _tk.Frame(self.inner, bg="white", bd=0, highlightthickness=1,
                         highlightbackground="#e5e7eb")
        card.pack(fill="x", padx=6, pady=6, ipady=8)

        _tk.Label(card, text=f"Mosaico #{idx+1}",
                  bg="white", fg="#2A2A9C",
                  font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=3,
                                                       sticky="w", padx=10, pady=(6, 4))

        # Nombre
        _tk.Label(card, text="Nombre visible:", bg="white",
                  font=("Segoe UI", 9)).grid(row=1, column=0, sticky="e", padx=(10, 4), pady=3)
        nombre_var = _tk.StringVar(value=data.get("nombre") or data.get("name") or "")
        _tk.Entry(card, textvariable=nombre_var, font=("Segoe UI", 10),
                  width=42).grid(row=1, column=1, sticky="we", pady=3)

        # Keywords
        _tk.Label(card, text="Palabras clave\n(separadas por coma):", bg="white",
                  font=("Segoe UI", 9), justify="right").grid(row=2, column=0, sticky="e", padx=(10, 4), pady=3)
        kws = data.get("keywords") or data.get("palabras") or []
        kws_var = _tk.StringVar(value=", ".join(kws))
        _tk.Entry(card, textvariable=kws_var, font=("Segoe UI", 10),
                  width=42).grid(row=2, column=1, sticky="we", pady=3)

        # Preview imagen
        preview = _tk.Label(card, bg="#F4F5F7", width=14, height=7, text="(sin imagen)",
                            fg="#94a3b8")
        preview.grid(row=1, column=2, rowspan=3, padx=10, pady=6)

        slot = {
            "nombre_var": nombre_var,
            "kws_var": kws_var,
            "image_path": data.get("image_path", "") or "",
            "image_b64": data.get("image_b64", "") or "",
            "preview": preview,
        }
        self._slots.append(slot)
        self._refresh_preview(slot)

        # Botón elegir imagen
        _tk.Button(card, text="🖼  Elegir imagen…",
                   command=lambda s=slot: self._pick_image(s),
                   bg="#0EA5E9", fg="white", font=("Segoe UI", 9, "bold"),
                   relief="flat", cursor="hand2", padx=10, pady=4
                   ).grid(row=3, column=1, sticky="w", pady=(4, 8))
        _tk.Button(card, text="Quitar imagen",
                   command=lambda s=slot: self._clear_image(s),
                   bg="#EF4444", fg="white", font=("Segoe UI", 9),
                   relief="flat", cursor="hand2", padx=10, pady=4
                   ).grid(row=3, column=1, sticky="e", pady=(4, 8), padx=(0, 10))

        card.columnconfigure(1, weight=1)

    def _pick_image(self, slot):
        path = _filedialog.askopenfilename(
            title="Elegir imagen del mosaico",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.webp *.gif"), ("Todos", "*.*")]
        )
        if not path:
            return
        # Copiamos a subcat_images/ con nombre único, así queda en tu repo
        ext = _Path(path).suffix.lower() or ".png"
        dest_name = f"sub_{_uuid.uuid4().hex}{ext}"
        dest = _SUBCAT_IMG_DIR / dest_name
        try:
            _shutil.copyfile(path, dest)
        except Exception as e:
            _messagebox.showerror("Error", f"No se pudo copiar la imagen:\n{e}")
            return
        slot["image_path"] = f"subcat_images/{dest_name}"
        # Tambien en base64 dentro del JSON (asi se ve siempre en la web)
        try:
            _im = _Image.open(dest).convert("RGBA")
            _im.thumbnail((640, 640))
            _b = _io.BytesIO()
            _im.save(_b, format="PNG", optimize=True)
            slot["image_b64"] = _b64.b64encode(_b.getvalue()).decode()
        except Exception:
            slot["image_b64"] = ""
        self._refresh_preview(slot)

    def _clear_image(self, slot):
        slot["image_path"] = ""
        slot["image_b64"] = ""
        self._refresh_preview(slot)

    def _refresh_preview(self, slot):
        img_widget = slot["preview"]
        img_path = slot["image_path"]
        img_b64 = slot["image_b64"]
        try:
            if img_path and (_BASE_DIR / img_path).exists():
                im = _Image.open(_BASE_DIR / img_path)
            elif img_b64:
                im = _Image.open(_io.BytesIO(_b64.b64decode(img_b64)))
            else:
                img_widget.configure(image="", text="(sin imagen)", width=14, height=7)
                return
            im.thumbnail((120, 120))
            tkimg = _ImageTk.PhotoImage(im)
            self._preview_imgs.append(tkimg)  # evitar GC
            img_widget.configure(image=tkimg, text="", width=120, height=120)
        except Exception:
            img_widget.configure(image="", text="(imagen no disponible)", width=18, height=7)

    def _save(self):
        if not self._current_cat:
            return
        data = _load_subcats()
        lst = []
        for slot in self._slots:
            nombre = (slot["nombre_var"].get() or "").strip()
            kws_raw = (slot["kws_var"].get() or "").strip()
            image_path = slot["image_path"]
            image_b64 = slot["image_b64"]
            if not nombre and not image_path and not image_b64 and not kws_raw:
                continue  # slot vacío -> no lo guardamos
            kws = [k.strip() for k in kws_raw.split(",") if k.strip()]
            lst.append({
                "nombre": nombre,
                "image_path": image_path,
                "image_b64": image_b64,
                "keywords": kws,
            })
        data[self._current_cat] = lst
        try:
            _save_subcats(data)
            _messagebox.showinfo(
                "Guardado",
                "Cambios guardados en subcategorias.json.\n\n"
                "Recuerda subir a GitHub:\n"
                " • subcategorias.json\n"
                " • carpeta subcat_images/ (si añadiste imágenes nuevas)"
            )
        except Exception as e:
            _messagebox.showerror("Error", f"No se pudo guardar:\n{e}")


if __name__ == "__main__":
    main()
