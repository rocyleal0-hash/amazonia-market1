# Amazonia MARKET — versión web estática (GitHub Pages)

Esta carpeta es tu tienda **Amazonia MARKET** convertida a HTML/CSS/JavaScript estático,
100% compatible con **GitHub Pages**. Lee los mismos archivos JSON que tu app de escritorio
(`agregar_producto_14_1.py`) ya genera. **NO tienes que cambiar tu app de escritorio.**

---

## 📂 Estructura del proyecto

```
amazonia-market/
├── index.html               ← página principal
├── styles.css               ← estilos (topbar azul, círculos, tarjetas, carrito…)
├── app.js                   ← lógica (render, carrito, buscador, slideshow)
├── products.json            ← tus productos (generado por la app de escritorio)
├── categories.json          ← lista de apartados
├── category_styles.json     ← estilos y iconos de cada apartado
├── anuncios.json            ← banner + tarjetas de anuncios (con imágenes en base64)
├── site_settings.json       ← nombre, colores, redes sociales, textos
├── bcv_cache.json           ← tasa BCV cacheada
├── product_images/          ← ⚠️ AQUÍ tú subes las fotos de tus productos
│   └── .gitkeep
└── cat_*.png                ← imágenes redondas de las categorías (súbelas al root)
```

---

## ✅ ¿Qué se mantuvo idéntico a tu Streamlit?

- **Topbar azul** (`#2A2A9C`) con:
  - Banner de delivery **deslizándose infinito** (marquee) — se pausa al pasar el mouse
  - Logo + título "Amazonia" (Pacifico) + "MARKET" (Poppins amarillo)
  - Buscador global con botón amarillo 🔍
  - "Mi cuenta", redes sociales, icono de carrito con contador
- **Círculos de categorías** con imagen o emoji + degradado radial azul
- **Home en filas de 4 tarjetas**, cada tarjeta con mini cuadrícula 2×2 de productos y botón "Ver más →"
- **Banner de anuncios** con slideshow automático **cada 1.5 s** + 4 tarjetas inferiores
- **Apartado**: rejilla de 4 columnas con tarjeta blanca, precio verde y botón "Agregar"
- **Modal de cantidad** al agregar producto
- **Carrito completo** (sumar/restar/quitar/vaciar/total) → guardado en `localStorage` del navegador
- **Buscador global** que busca por nombre y categoría
- **Menú lateral** (☰) con la lista de apartados
- **Responsive**: layout compacto para teléfono igual que en Streamlit

## ⚠️ Diferencias inevitables (GitHub Pages es estático, no tiene servidor)

1. **Carrito por dispositivo/navegador**: se guarda con `localStorage`. Antes usabas `carts.sqlite3` en el servidor.
2. **Tasa BCV**: se lee de `bcv_cache.json`. Cuando corras la app de escritorio en tu PC y actualice el JSON, haces `git push` y la web queda al día.
3. **App admin (`agregar_producto_14_1.py`)**: sigue siendo tu app de Windows. La usas igual que ahora para agregar productos/categorías. La única diferencia: para publicar los cambios ya no lanzas Streamlit, sino que haces `git push`.

---

## 🚀 Cómo subirlo a GitHub y publicarlo (paso a paso, sin saltar nada)

### 1) Instala Git en tu computadora
- Windows: descarga desde https://git-scm.com/download/win, instala con las opciones por defecto.

### 2) Crea una cuenta y un repositorio en GitHub
1. Entra a https://github.com y crea cuenta si no tienes.
2. Arriba a la derecha → botón verde **New** (o "+" → **New repository**).
3. Nombre del repo: **`amazonia-market`** (o el que quieras).
4. Deja **Public** marcado (GitHub Pages gratis requiere repo público).
5. **NO** marques "Add a README file". Deja todo vacío.
6. Clic en **Create repository**.

### 3) Descarga y descomprime el ZIP que te generé
- Descomprímelo → te queda una carpeta `amazonia-market/` con todo dentro.

### 4) Agrega tus imágenes
- **Fotos de productos**: cópialas dentro de `amazonia-market/product_images/` (respetando los nombres que aparecen en `products.json`, ejemplo `9ac83dd9939945c8943b7721fdbe9892.jpeg`).
- **Imágenes de los círculos de categorías**: cópialas directamente en `amazonia-market/` (junto a `index.html`), con los mismos nombres que aparecen en `category_styles.json`, por ejemplo `cat_CONFITERIA_8643fe63.png`, `cat_VIVERES_6e756e29.png`, etc.

### 5) Sube todo al repo (con la terminal / Git Bash)

Abre una terminal **dentro de la carpeta `amazonia-market/`** y ejecuta:

```bash
git init
git add .
git commit -m "Primera versión de Amazonia MARKET"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/amazonia-market.git
git push -u origin main
```

> Reemplaza `TU-USUARIO` por tu usuario real de GitHub.
> La primera vez te pedirá login: usa tu usuario y un **Personal Access Token** (Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token, marca el permiso `repo`).

**Alternativa sin terminal (más fácil):**
1. Entra a tu repo en github.com.
2. Clic en "uploading an existing file".
3. Arrastra TODO el contenido de la carpeta `amazonia-market/` (index.html, styles.css, app.js, todos los JSON, la carpeta `product_images/` y los `cat_*.png`).
4. Escribe un mensaje ("Primera versión") y clic en **Commit changes**.

### 6) Activa GitHub Pages
1. En tu repo, ve a **Settings** (arriba).
2. Menú izquierdo → **Pages**.
3. En "Source" elige: **Deploy from a branch**.
4. En "Branch": elige **`main`** y carpeta **`/ (root)`**. Clic en **Save**.
5. Espera 1-2 minutos. En la misma página aparecerá:
   > **Your site is live at `https://tu-usuario.github.io/amazonia-market/`**

Ese es el link público de tu tienda. 🎉

### 7) Actualizar la web cuando agregues productos
Cada vez que uses tu app de escritorio y agregues productos/categorías:

**Opción A (con Git):**
```bash
cd amazonia-market
git add .
git commit -m "Nuevos productos"
git push
```

**Opción B (sin Git):**
- Entra al repo en github.com, clic en el archivo (`products.json` por ejemplo), botón lápiz ✏️ arriba a la derecha → pega el nuevo contenido → **Commit changes**.
- Para agregar fotos nuevas: entra a la carpeta `product_images/` → **Add file → Upload files**.

En 30-60 segundos GitHub Pages republica automáticamente.

---

## 💡 Notas importantes

- Si al abrir tu web local (doble clic en `index.html`) no cargan los JSON, es normal: el navegador bloquea `fetch()` de archivos locales. **Solo funciona bien cuando está en GitHub Pages** (o si abres con un servidor local como `python -m http.server`).
- Las rutas de las imágenes de productos vienen tal cual desde `products.json` (ej: `product_images/xxx.jpg`), así que **respeta esa carpeta**.
- Los anuncios (`anuncios.json`) traen las imágenes en **base64** dentro del JSON — no necesitas subir imágenes de banners aparte.

¡Listo! Con eso tu tienda queda igualita a la de Streamlit, pero servida gratis desde GitHub Pages.
