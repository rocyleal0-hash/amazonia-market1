/* =========================================================
   AMAZONIA MARKET - app.js  (versión mejorada)
   - Lee TODAS las opciones que guarda agregar_producto.py:
     colores de la barra azul, color del texto "Delivery gratis",
     imagen de fondo con blur/brillo/saturación/opacidad,
     botones ☰ 🔍 🛒, panel del menú, botón "Ver más",
     colores del carrito, borde de imágenes de producto,
     alineación/tamaño/desplazamiento del logo, ocultar logo/títulos.
   ========================================================= */
(() => {
'use strict';

const $  = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
const escapeHtml = s => String(s ?? '')
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
const escapeAttr = escapeHtml;

const truthy = v => /^(1|true|yes|si|sí)$/i.test(String(v ?? '').trim());
const intOr  = (v, d) => { const n = parseInt(v, 10); return Number.isFinite(n) ? n : d; };
const numOr  = (v, d) => { const n = parseFloat(v);   return Number.isFinite(n) ? n : d; };

/* Carpetas donde pueden estar las imágenes en el repo de GitHub.
   Se prueban en orden hasta que una cargue (ver fallback más abajo). */
const IMG_FOLDERS = [
  'cat_images', 'subcat_images', 'product_images', 'product_images2',
  'banner_images', 'ads_images'
];

function imgCandidates(path) {
  if (!path) return [];
  let p = String(path).trim();
  if (p.startsWith('data:') || p.startsWith('http://') || p.startsWith('https://')) return [p];
  p = p.replace(/^\/+/, '').replace(/^\.\//, '');
  p = p.replace(/^public\//, '');

  const known = IMG_FOLDERS.find(f => p.startsWith(f + '/'));
  const file = known ? p.slice(known.length + 1) : p;

  // Si el nombre trae carpeta desconocida, usamos solo el nombre del archivo
  const base = file.includes('/') ? file.split('/').pop() : file;

  // Orden de búsqueda: primero la carpeta indicada (si la hay), luego
  // una pista por el prefijo del nombre (cat_ / subcat_), luego el resto.
  const order = [];
  if (known) order.push(known);
  if (/^cat_/i.test(base)) order.push('cat_images');
  if (/^subcat_/i.test(base)) order.push('subcat_images');
  for (const f of IMG_FOLDERS) if (!order.includes(f)) order.push(f);

  const list = [];
  for (const f of order) {
    list.push('./public/' + f + '/' + base);
    list.push('./' + f + '/' + base);
  }
  // Por último, la ruta tal cual venía
  list.push('./public/' + p);
  list.push('./' + p);
  return list.filter((v, i, a) => a.indexOf(v) === i);
}

function fixImgSrc(path) {
  const c = imgCandidates(path);
  return c.length ? c[0] : '';
}

function fetchJSON(path, fallback) {
  return fetch(path, { cache: 'no-store' })
    .then(r => { if (!r.ok) throw new Error('http ' + r.status); return r.json(); })
    .catch(e => { console.warn('No se pudo cargar', path, e); return fallback; });
}

function formatPrice(p, currency='$') {
  const n = Number(p);
  if (!isFinite(n)) return currency + p;
  return currency + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function iconForCategory(name) {
  const n = String(name || '').toLowerCase();
  const map = {
    'viveres':'🌽','víveres':'🌽','confiteria':'🍫','confitería':'🍫',
    'limpieza':'🧹','bebidas':'🍹','higiene personal':'🧴','higiene':'🧴',
    'escolar':'✏️','jugueteria':'🧸','juguetería':'🧸','jugeteria':'🧸',
    'quincalleria':'🏷️','quincallería':'🏷️',
    'lacteos':'🥛','lácteos':'🥛','charcuteria':'🥩','charcutería':'🥩',
    'ropa':'👕','cosmetico':'💄','cosmético':'💄','cosmeticos':'💄','cosméticos':'💄',
    'carniceria':'🥩','carnicería':'🥩','vegetales y verduras':'🥦',
    'frutas y hortalizas':'🍎','helados':'🍦','bolsos y carteras':'👜',
    'ferreteria':'🔧','ferretería':'🔧','panaderia':'🍞','panadería':'🍞',
    'papeleria':'📄','papelería':'📄','telefonia':'📱','telefonía':'📱',
  };
  return map[n] || '🏷️';
}

/* ---------------- CARRITO (localStorage) ---------------- */
const CART_KEY = 'amazonia_cart_v1';
function loadCart() { try { return JSON.parse(localStorage.getItem(CART_KEY) || '{}'); } catch { return {}; } }
function saveCart(c) { localStorage.setItem(CART_KEY, JSON.stringify(c)); updateCartBadge(); }
function cartCount() { return Object.values(loadCart()).reduce((s, it) => s + (Number(it.qty)||0), 0); }
function cartTotal() { return Object.values(loadCart()).reduce((s, it) => s + (Number(it.precio)||0)*(Number(it.qty)||0), 0); }
function cartAdd(prod, qty=1) {
  const c = loadCart();
  const name = prod.nombre;
  if (!c[name]) c[name] = { id: prod.id, nombre: prod.nombre, precio: Number(prod.precio)||0,
                            imagen: prod.imagen, categoria: prod.categoria, qty: 0 };
  c[name].qty += qty;
  if (c[name].qty <= 0) delete c[name];
  saveCart(c);
}
function cartSet(name, qty) {
  const c = loadCart();
  if (!c[name]) return;
  if (qty <= 0) delete c[name]; else c[name].qty = qty;
  saveCart(c);
}
function cartClear() { saveCart({}); }
function updateCartBadge() {
  const n = cartCount(); const b = $('#cartBadge');
  const payBtn = document.getElementById('amPayNow');
  if (payBtn) payBtn.style.display = n > 0 ? 'flex' : 'none';
  const t = document.getElementById('cartTotalTop');
  if (t) t.textContent = formatPrice(cartTotal());
  if (!b) return;
  if (n > 0) { b.textContent = n; b.hidden = false; } else b.hidden = true;
}

let toastTimer = null;
function toast(msg) {
  const t = $('#toast'); if (!t) return;
  t.textContent = msg; t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 1800);
}

/* ---------------- ESTADO ---------------- */
let SETTINGS = {};
let PRODUCTS = [];
let CATEGORIES = [];
let CAT_STYLES = {};
let ANUNCIOS = {};
let SUBCATS   = {};   // { "VIVERES": [ {nombre, image_path, image_b64, keywords:[...] }, ... ] }

/* ---------------- TEMA (aplica TODOS los ajustes del editor) ---------------- */
function applyTheme() {
  const s = SETTINGS || {};
  const root = document.documentElement.style;

  const setVar = (name, val) => { if (val !== undefined && val !== null && String(val).trim() !== '') root.setProperty(name, String(val).trim()); };

  // Barra superior (topbar)
  setVar('--tb-bg',          s.topbar_bg_color || s.hero_bg_color);
  setVar('--tb-delivery-fg', s.delivery_text_color);
  setVar('--tb-menu-bg',     s.btn_menu_bg);
  setVar('--tb-menu-fg',     s.btn_menu_fg);
  setVar('--tb-search-bg',   s.btn_search_bg);
  setVar('--tb-search-fg',   s.btn_search_fg);
  setVar('--tb-cart-bg',     s.btn_cart_bg);
  setVar('--tb-cart-fg',     s.btn_cart_fg);

  // Color primario de la marca (botones "Agregar", etc.): usa el azul del logo,
  // no el color de fondo de la barra (que puede ser negro/imagen).
  const brandBlue = (s.brand_color || s.cart_add_bg || s.btn_cart_bg || s.btn_menu_bg || s.menu_panel_bg || '#0B3B8F');
  setVar('--primary', brandBlue);
  setVar('--brand-blue', brandBlue);

  // Menú lateral
  setVar('--menu-bg', s.menu_panel_bg);
  setVar('--menu-fg', s.menu_panel_fg);

  // Botón "Ver más"
  setVar('--more-bg', s.section_more_bg);
  setVar('--more-fg', s.section_more_fg);

  // Borde de imágenes de producto
  setVar('--img-border-color', s.img_border_color);
  const bw = intOr(s.img_border_width, null);
  if (bw !== null) root.setProperty('--img-border-width', bw + 'px');

  // Carrito
  setVar('--cart-card-bg',  s.cart_card_bg);
  setVar('--cart-name-fg',  s.cart_name_color);
  setVar('--cart-unit-fg',  s.cart_unit_color);
  setVar('--cart-price-bg', s.cart_price_bg);
  setVar('--cart-price-fg', s.cart_price_fg);

  // Alineación / desplazamiento del logo
  const align = String(s.logo_align || 'left').toLowerCase();
  const justify = align === 'center' ? 'center' : (align === 'right' ? 'flex-end' : 'flex-start');
  root.setProperty('--brand-justify', justify);
  const off = intOr(s.logo_offset_x, 0);
  root.setProperty('--brand-offset-x', off + 'px');

  // Imagen de fondo de la barra + blur/brillo/saturación/opacidad
  const tb = document.getElementById('topbar');
  const imgB64 = String(s.topbar_bg_image_b64 || s.hero_bg_b64 || '').trim();
  const styleId = 'am-topbar-bgimg';
  let st = document.getElementById(styleId);
  if (!st) { st = document.createElement('style'); st.id = styleId; document.head.appendChild(st); }
  if (tb && imgB64) {
    const blur = intOr(s.topbar_bg_blur ?? s.hero_blur, 0);
    const bri  = intOr(s.topbar_bg_brightness ?? s.hero_brightness_pct ?? Math.round(numOr(s.hero_brightness, 1) * 100), 100);
    const sat  = intOr(s.topbar_bg_saturation, 100);
    const opRaw = s.topbar_bg_opacity ?? s.hero_opacity_pct;
    const op   = opRaw !== undefined
      ? Math.max(0, Math.min(1, intOr(opRaw, 100) / 100))
      : Math.max(0, Math.min(1, numOr(s.hero_opacity, 1)));
    st.textContent = `
      .am-topbar { position: relative; isolation: isolate; overflow: hidden; }
      .am-topbar::before {
        content:''; position:absolute; inset:0; z-index:-1;
        background: url('data:image/png;base64,${imgB64}') center/cover no-repeat;
        filter: blur(${blur}px) brightness(${bri}%) saturate(${sat}%);
        opacity: ${op.toFixed(2)};
        pointer-events: none;
      }
    `;
  } else {
    st.textContent = '';
  }

  /* ============================================================
     Mejora #1: FONDO COMPLETO DE LA WEB
     Compatible con la ventana "Fondo completo de la página web"
     de agregar_producto_corregido.py.

     El editor nuevo guarda:
       - page_bg_type: color | image | none
       - page_bg_color
       - page_bg_image_b64
       - page_bg_blur / page_bg_brightness / page_bg_opacity

     También conserva compatibilidad con la clave vieja site_bg_b64.
     ============================================================ */
  const pageStyleId = 'am-page-bgimg';
  let pst = document.getElementById(pageStyleId);
  if (!pst) { pst = document.createElement('style'); pst.id = pageStyleId; document.head.appendChild(pst); }

  const pageBg = String(s.page_bg_image_b64 || s.site_bg_b64 || '').trim();
  const savedType = String(s.page_bg_type || '').trim().toLowerCase();
  const pageType = savedType || (pageBg ? 'image' : (s.page_bg_color ? 'color' : ''));
  const pageColor = String(s.page_bg_color || '#F4F5F7').trim();

  const pct = (value, fallback) => {
    const n = numOr(value, fallback);
    // Claves viejas: 1.00 / 0.60. Claves nuevas: 100 / 60.
    return n <= 2 ? Math.round(n * 100) : Math.round(n);
  };
  const ratio = (value, fallback) => {
    const n = numOr(value, fallback);
    return n > 1 ? n / 100 : n;
  };
  const mimeFromB64 = (b64) => {
    if (b64.startsWith('data:')) return '';
    if (b64.startsWith('/9j/')) return 'image/jpeg';
    if (b64.startsWith('iVBORw0KGgo')) return 'image/png';
    if (b64.startsWith('UklGR')) return 'image/webp';
    if (b64.startsWith('R0lGOD')) return 'image/gif';
    return 'image/jpeg';
  };

  if (pageType === 'none') {
    pst.textContent = `
      html, body { background: transparent !important; }
      body::before { content: none !important; }
    `;
  } else if (pageType === 'image' && pageBg) {
    const blur = Math.max(0, Math.min(30, intOr(s.page_bg_blur, 0)));
    const briPct = Math.max(0, Math.min(200, pct(s.page_bg_brightness ?? s.site_bg_brightness, 100)));
    const opClamp = Math.max(0, Math.min(1, ratio(s.page_bg_opacity ?? s.site_bg_opacity, 100))).toFixed(2);
    const mime = mimeFromB64(pageBg);
    const imageUrl = pageBg.startsWith('data:') ? pageBg : `data:${mime};base64,${pageBg}`;
    const blurScale = blur > 0 ? 1.04 : 1;

    pst.textContent = `
      html { min-height: 100%; background: ${pageColor} !important; }
      body {
        position: relative;
        min-height: 100vh;
        background: transparent !important;
        isolation: isolate;
      }
      body::before {
        content: '';
        position: fixed;
        inset: 0;
        z-index: -1;
        background-image: url("${imageUrl}");
        background-position: center center;
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
        filter: blur(${blur}px) brightness(${briPct}%);
        opacity: ${opClamp};
        transform: scale(${blurScale});
        pointer-events: none;
      }
    `;
  } else {
    pst.textContent = `
      html, body { background: ${pageColor} !important; }
      body::before { content: none !important; }
    `;
  }
}

/* ---------------- RENDERS ---------------- */
function renderDeliveryBanner() {
  const text = SETTINGS.delivery_text || '🚚 Delivery GRATIS en toda la zona de Coro';
  const color = (SETTINGS.delivery_text_color || '').trim();
  const style = color ? ` style="color:${escapeAttr(color)};"` : '';
  const one = `<span${style}>${escapeHtml(text)}</span>`;
  const group = one.repeat(6);
  const el = $('#deliveryTrack');
  if (el) el.innerHTML = group + group;
}

function renderBrand() {
  const siteName   = SETTINGS.site_name   || 'Amazonia';
  const siteMarket = SETTINGS.site_market || 'MARKET';

  const logoB64 = (SETTINGS.site_logo_b64 || '').trim();
  const logoEl = $('#brandLogo');
  const hideLogo = truthy(SETTINGS.hide_logo);
  if (logoEl) {
    if (logoB64 && !hideLogo) {
      logoEl.src = 'data:image/png;base64,' + logoB64;
      logoEl.style.display = 'block';
      const sz = intOr(SETTINGS.logo_size, 54);
      logoEl.style.height = sz + 'px';
    } else {
      logoEl.style.display = 'none';
    }
  }

  const hideTitles = truthy(SETTINGS.hide_titles);
  const bt = $('#brandTitles');
  if (bt) {
    bt.innerHTML = hideTitles ? '' : `
      <div class="am-brand-name">${escapeHtml(siteName)}</div>
      <div class="am-brand-market">${escapeHtml(siteMarket)}</div>
    `;
  }
}

function renderSocials() {
  const fb = (SETTINGS.social_facebook_url || '').trim();
  const ig = (SETTINGS.social_instagram_url || '').trim();
  const tk = (SETTINGS.social_tiktok_url || '').trim();
  const svg = {
    fb: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="#fff"><path d="M22.675 0H1.325C.593 0 0 .593 0 1.325v21.351C0 23.407.593 24 1.325 24H12.82v-9.294H9.692v-3.622h3.128V8.413c0-3.1 1.894-4.788 4.659-4.788 1.325 0 2.464.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12V24h6.116C23.407 24 24 23.407 24 22.676V1.325C24 .593 23.407 0 22.675 0z"/></svg>`,
    ig: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="#fff"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163C8.741 0 8.332.014 7.052.072 2.695.272.273 2.69.073 7.052.014 8.332 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.332 23.986 8.741 24 12 24s3.668-.014 4.948-.072c4.354-.2 6.782-2.618 6.979-6.98.058-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.163 6.163 0 1 0 0 12.326 6.163 6.163 0 0 0 0-12.326zm0 10.162a3.999 3.999 0 1 1 0-7.998 3.999 3.999 0 0 1 0 7.998zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/></svg>`,
    tk: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="#fff"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.8 20.1a6.34 6.34 0 0 0 10.86-4.43V8.66a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.84-.09z"/></svg>`,
  };
  const items = [];
  if (fb) items.push(`<a href="${escapeAttr(fb)}" target="_blank" rel="noopener" title="Facebook" style="border-radius:50%;background:#1877F2;">${svg.fb}</a>`);
  if (ig) items.push(`<a href="${escapeAttr(ig)}" target="_blank" rel="noopener" title="Instagram" style="border-radius:10px;background:radial-gradient(circle at 30% 110%,#FEDA75 0%,#FA7E1E 25%,#D62976 50%,#962FBF 75%,#4F5BD5 100%);">${svg.ig}</a>`);
  if (tk) items.push(`<a href="${escapeAttr(tk)}" target="_blank" rel="noopener" title="TikTok" style="border-radius:50%;background:#000;">${svg.tk}</a>`);
  const soc = $('#amSocials');
  if (soc) soc.innerHTML = items.join('');
}

function renderMenuPanel() {
  const items = CATEGORIES.map(c =>
    `<a href="?cat=${encodeURIComponent(c)}">${escapeHtml(cap(c))}</a>`
  ).join('');
  const mp = $('#menuPanel');
  if (mp) {
    mp.innerHTML =
      `<div class="am-menu-head">Apartados</div>` +
      (items || `<div style="padding:14px 18px;opacity:.85;font-size:13px;">Aún no hay apartados.</div>`);
  }
  // Botón ☰ abre/cierra
  const btn = $('#btnMenu');
  if (btn && mp && !btn._wired) {
    btn._wired = true;
    btn.addEventListener('click', () => { mp.hidden = !mp.hidden; });
  }
}

function catStyle(name) {
  const defaults = {
    icon:'', circle_color:'#2A2A9C', circle_size:96,
    label_color:'#0F172A', label_size:14,
    title_color:'#2A2A9C', title_size:22,
    more_bg: SETTINGS.section_more_bg || '#2A2A9C',
    more_fg: SETTINGS.section_more_fg || '#FFFFFF',
    use_image:false, image_path:''
  };
  const s = Object.assign({}, defaults, CAT_STYLES[name] || {});
  s.circle_size = intOr(s.circle_size, 96);
  return s;
}

function renderCategoryCircles() {
  const cw = $('#catsWrap'); const cs = $('#catsScroll');
  if (!cw || !cs) return;
  if (!CATEGORIES.length) { cw.style.display='none'; return; }
  cw.style.display = '';

  const html = CATEGORIES.map(cat => {
    const s = catStyle(cat);
    const icon = s.icon || iconForCategory(cat);
    const sz = s.circle_size;
    let inner, bg;
    if (s.use_image && s.image_path) {
      const imgSrc = fixImgSrc(s.image_path);
      inner = `<img src="${escapeAttr(imgSrc)}" alt="${escapeAttr(cat)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';"/>
               <span style="display:none;font-size:${Math.round(sz*0.46)}px;">${escapeHtml(icon)}</span>`;
      bg = `background:${s.circle_color};`;
    } else {
      inner = `<span style="font-size:${Math.round(sz*0.46)}px;">${escapeHtml(icon)}</span>`;
      bg = `background: radial-gradient(circle at 30% 30%, color-mix(in srgb, ${s.circle_color} 78%, white) 0%, ${s.circle_color} 78%);`;
    }
    return `<a class="am-cat-circle" href="?cat=${encodeURIComponent(cat)}" style="min-width:${Math.max(sz+20,80)}px;">
      <div class="bubble" style="width:${sz}px;height:${sz}px;${bg}display:flex;align-items:center;justify-content:center;overflow:hidden;">${inner}</div>
      <div class="label" style="color:${s.label_color};font-size:${s.label_size}px;">${escapeHtml(cat)}</div>
    </a>`;
  }).join('');
  cs.innerHTML = html;
}

function renderAnunciosBanner(container) {
  if (!container) return;
  const _cards = ANUNCIOS.cards || [];
  const hasCards = _cards.some(c => (c.img_b64 || c.title));

  let slides = (ANUNCIOS.banner_slides || [])
    .map(s => ({ b64: (s.img_b64||'').trim(), vid: (s.video_b64||'').trim(), url: (s.url||'').trim() }))
    .filter(s => s.b64 || s.vid);
  if (!slides.length) {
    const legacy = (ANUNCIOS.banner_img_b64 || '').trim();
    if (legacy) slides.push({ b64: legacy, url:'' });
  }
  if (!slides.length && !hasCards) return;

  const bh   = intOr(ANUNCIOS.banner_height, 320);
  const brt  = intOr(ANUNCIOS.banner_brightness, 100);
  const blur = intOr(ANUNCIOS.banner_blur, 0);
  const ovr  = intOr(ANUNCIOS.banner_overlay, 0);

  const slidesHtml = slides.map((s, i) => {
    const href = s.url || '#';
    const target = s.url ? 'target="_blank" rel="noopener"' : '';
    const media = s.vid
      ? `<video src="data:video/mp4;base64,${s.vid}" autoplay muted loop playsinline style="filter: brightness(${brt}%) blur(${blur}px);"></video>`
      : `<img src="data:image/png;base64,${s.b64}" style="filter: brightness(${brt}%) blur(${blur}px);"/>`;
    return `<a class="am-slide ${i===0?'active':''}" data-idx="${i}" href="${escapeAttr(href)}" ${target}>
      ${media}
    </a>`;
  }).join('');
  const heroStyle = `height:${bh}px;`;
  const ovrHtml = ovr>0 ? `<div class="ovr" style="background:rgba(0,0,0,${(ovr/100).toFixed(2)});"></div>` : '';

  let cardsHtml = '';
  if (hasCards) {
    cardsHtml = `<div class="am-ads-cards">` + _cards.map(c => {
      const title = (c.title||'').trim();
      const url = (c.url||'').trim() || '#';
      const b64 = (c.img_b64||'').trim();
      const target = url !== '#' ? 'target="_blank" rel="noopener"' : '';
      const img = b64
        ? `<img src="data:image/png;base64,${b64}"/>`
        : `<div style="color:#aaa;font-size:12px;">Sin imagen</div>`;
      return `<a class="am-ads-card" href="${escapeAttr(url)}" ${target}>
        <div class="t">${escapeHtml(title) || '&nbsp;'}</div>
        <div class="imgbox">${img}</div>
        <div class="lnk">Ver más ›</div>
      </a>`;
    }).join('') + `</div>`;
  }

  container.insertAdjacentHTML('beforeend', `
    <div class="am-ads-wrap">
      <div class="am-ads-hero" id="adsHero" style="${heroStyle}">
        ${slidesHtml}${ovrHtml}
        <img class="am-ads-cashea" src="./public/cashea.png" alt="Cashea"/>
      </div>
      ${cardsHtml}
    </div>
  `);

  if (slides.length > 1) {
    startAnunciosTick();
  }
}

// Tick global compartido para sincronizar banner principal y secundario
let __ANUNCIOS_TICK_STARTED = false;
let __ANUNCIOS_TICK_IDX = 0;
function startAnunciosTick() {
  if (__ANUNCIOS_TICK_STARTED) return;
  __ANUNCIOS_TICK_STARTED = true;
  setInterval(() => {
    __ANUNCIOS_TICK_IDX = (__ANUNCIOS_TICK_IDX + 1) % 4;
    ['#adsHero', '#adsSecondary', '#adsTertiary'].forEach(sel => {
      const el = document.querySelector(sel); if (!el) return;
      const items = el.querySelectorAll('.am-slide');
      if (!items.length) return;
      items.forEach(it => it.classList.remove('active'));
      items[__ANUNCIOS_TICK_IDX % items.length].classList.add('active');
    });
  }, 1800);
}

function thinBannerHtml(slides, domId) {
  const slidesHtml = slides.map((s, i) => {
    const href = s.url || '#';
    const target = s.url ? 'target="_blank" rel="noopener"' : '';
    const media = s.vid
      ? `<video src="data:video/mp4;base64,${s.vid}" autoplay muted loop playsinline></video>`
      : `<img src="data:image/png;base64,${s.b64}"/>`;
    return `<a class="am-slide ${i===0?'active':''}" data-idx="${i}" href="${escapeAttr(href)}" ${target}>
      ${media}
    </a>`;
  }).join('');
  return `
    <div class="am-secondary-banner-wrap">
      <div class="am-secondary-banner" id="${domId}">
        ${slidesHtml}
      </div>
    </div>
  `;
}

function thinBannerSlides(key) {
  return (ANUNCIOS[key] || [])
    .map(s => ({ b64: (s.img_b64||'').trim(), vid: (s.video_b64||'').trim(), url: (s.url||'').trim() }))
    .filter(s => s.b64 || s.vid);
}

function renderSecondaryBanner(container) {
  if (!container) return;
  const slides = thinBannerSlides('banner_secundario');
  if (!slides.length) return;
  container.insertAdjacentHTML('beforeend', thinBannerHtml(slides, 'adsSecondary'));
  if (slides.length > 1) startAnunciosTick();
}

// Tercer banner (fino, 1920x130) que va justo debajo del apartado Charcuteria.
// Si no se ha configurado banner_tercero, reutiliza las imagenes del secundario.
function tertiaryBannerHtml() {
  let slides = thinBannerSlides('banner_tercero');
  if (!slides.length) slides = thinBannerSlides('banner_secundario');
  if (!slides.length) return '';
  if (slides.length > 1) setTimeout(startAnunciosTick, 0);
  return thinBannerHtml(slides, 'adsTertiary');
}

function cap(s){ s=String(s||''); return s.charAt(0).toUpperCase()+s.slice(1).toLowerCase(); }

/* ---------------- VISTAS ---------------- */
function moveCatsBelowBanner(main) {
  const cw = document.getElementById('catsWrap');
  if (!cw || !main) return;
  const cards = main.querySelector('.am-ads-cards');
  const ads = main.querySelector('.am-ads-wrap');
  if (cards) cards.insertAdjacentElement('beforebegin', cw);
  else if (ads) ads.insertAdjacentElement('afterend', cw);
  else main.insertAdjacentElement('afterbegin', cw);
}

function viewHome(main) {
  renderAnunciosBanner(main);
  moveCatsBelowBanner(main);
  if (!CATEGORIES.length) {
    main.insertAdjacentHTML('beforeend', `<div class="am-empty">Aún no hay apartados.<br>Crea apartados desde la app de escritorio.</div>`);
    renderSecondaryBanner(main);
    return;
  }
  const terHtml = tertiaryBannerHtml();
  const out = CATEGORIES.map(cat => {
    const tile = `<div class="am-tiles-row">${buildHomeTile(cat)}</div>`;
    // Insertar el tercer banner justo debajo del apartado "Charcuteria"
    const norm = String(cat||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
    return (norm === 'charcuteria') ? tile + terHtml : tile;
  }).join('');
  main.insertAdjacentHTML('beforeend', out);
  renderSecondaryBanner(main);
}

function buildHomeTile(cat) {
  const catProds = PRODUCTS.filter(p => p.categoria === cat);
  const s = catStyle(cat);
  const emoji = s.icon || iconForCategory(cat);
  // Preferir los mosaicos de subcategoría definidos desde el editor (subcategorias.json).
  // Si no hay, caer al preview clásico con thumbnails de productos.
  const subs = Array.isArray(SUBCATS[cat]) ? SUBCATS[cat].slice(0, 4) : [];
  let grid;
  if (subs.length) {
    let items = subs.map(sub => {
      const nombre = sub.nombre || '';
      const imgSrc = sub.image_b64
        ? ('data:image/png;base64,' + String(sub.image_b64).trim())
        : fixImgSrc(sub.image_path || '');
      const href = `?cat=${encodeURIComponent(cat)}&sub=${encodeURIComponent(nombre)}`;
      const imgHtml = imgSrc
        ? `<img src="${escapeAttr(imgSrc)}" alt="${escapeAttr(nombre)}" loading="lazy"/>`
        : `<div style="color:#aaa;font-size:12px;display:flex;align-items:center;justify-content:center;height:100%;">Sin imagen</div>`;
      return `<a class="am-quad-item" data-cat="${escapeAttr(String(cat||'').toLowerCase())}" href="${escapeAttr(href)}">
        <div class="am-quad-imgwrap">${imgHtml}</div>
        <div class="am-quad-name">${escapeHtml(nombre)}</div>
      </a>`;
    }).join('');
    for (let k=subs.length; k<4; k++) items += `<div class="am-quad-item am-quad-empty"></div>`;
    grid = `<div class="am-quad-grid">${items}</div>`;
  } else {
    const preview = catProds.slice(0, 4);
    let items = preview.map(p => `
      <a class="am-quad-item" data-cat="${escapeAttr(String(cat||'').toLowerCase())}" href="?cat=${encodeURIComponent(cat)}">
        <div class="am-quad-imgwrap"><img src="${escapeAttr(fixImgSrc(p.imagen))}" alt="${escapeAttr(p.nombre||'')}" loading="lazy"/></div>
        <div class="am-quad-name">${escapeHtml(p.nombre || '')}</div>
      </a>
    `).join('');
    for (let k=preview.length; k<4; k++) items += `<div class="am-quad-item am-quad-empty"></div>`;
    grid = preview.length
      ? `<div class="am-quad-grid">${items}</div>`
      : `<div class="am-quad-grid"><div class="am-empty" style="grid-column:1/-1;margin:0;">Aún no hay productos.</div></div>`;
  }

  return `<div class="am-tile">
    <div class="am-tile-head">
      <div class="am-tile-title" style="color:${s.title_color};font-size:${s.title_size}px;">
        ${escapeHtml(cap(cat))}
      </div>

      <a class="am-tile-more" href="?cat=${encodeURIComponent(cat)}" style="color:${s.more_fg || s.more_bg};">Ver más →</a>
    </div>
    ${grid}
  </div>`;
}

function viewCategory(main, cat, subName) {
  // Si viene ?sub= filtramos por las keywords del mosaico correspondiente.
  let sub = null;
  if (subName) {
    const list = Array.isArray(SUBCATS[cat]) ? SUBCATS[cat] : [];
    sub = list.find(x => String(x.nombre||'').toLowerCase() === String(subName).toLowerCase()) || null;
  }
  const titleTxt = sub ? `${cap(cat)} · ${sub.nombre}` : cap(cat);
  main.insertAdjacentHTML('beforeend', `
    <div class="am-view-head">
      <div class="am-view-title">${escapeHtml(titleTxt)}</div>
      <a class="am-btn am-btn-ghost" href="${sub ? '?cat=' + encodeURIComponent(cat) : './'}">← ${sub ? cap(cat) : 'Apartados'}</a>
    </div>
  `);
  let prods = PRODUCTS.filter(p => p.categoria === cat);
  if (sub) {
    const kws = (sub.keywords || []).map(k => String(k||'').toLowerCase().trim()).filter(Boolean);
    if (kws.length) {
      prods = prods.filter(p => {
        const hay = (String(p.nombre||'') + ' ' + String(p.descripcion||'')).toLowerCase();
        return kws.some(k => hay.includes(k));
      });
    } else {
      // Sin palabras clave: intentar coincidir con el nombre del mosaico.
      const n = String(sub.nombre||'').toLowerCase();
      if (n) prods = prods.filter(p => String(p.nombre||'').toLowerCase().includes(n));
    }
  }
  if (!prods.length) {
    main.insertAdjacentHTML('beforeend', `<div class="am-empty">No hay productos${sub ? ' que coincidan con "'+escapeHtml(sub.nombre)+'"' : ''} todavía.</div>`);
    return;
  }
  renderProductGrid(main, prods);

}

function viewSearch(main, q) {
  main.insertAdjacentHTML('beforeend', `
    <div class="am-view-head">
      <div class="am-view-title">🔍 Resultados para: "<span style="color:var(--text);">${escapeHtml(q)}</span>"</div>
      <a class="am-btn am-btn-ghost" href="./">← Volver al inicio</a>
    </div>
  `);
  if (!q) { main.insertAdjacentHTML('beforeend',`<div class="am-empty">Escribe algo en la barra de búsqueda.</div>`); return; }
  const ql = q.toLowerCase();
  const results = PRODUCTS.filter(p =>
    String(p.nombre||'').toLowerCase().includes(ql) ||
    String(p.categoria||'').toLowerCase().includes(ql)
  );
  if (!results.length) { main.insertAdjacentHTML('beforeend',`<div class="am-empty">No se encontraron productos que coincidan.</div>`); return; }
  // (contador de resultados removido a pedido del usuario)

  renderProductGrid(main, results);
}

function normalizeCat(s){
  return String(s||'').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim();
}
// Categorias que se venden por peso (muestran el boton amarillo de Gramos)
const CATS_POR_GRAMOS = ['charcuteria', 'carniceria', 'vegetales'];
function isCharcuteria(cat){ return CATS_POR_GRAMOS.includes(normalizeCat(cat)); }

function renderProductGrid(main, prods) {
  const html = `<div class="am-grid">` + prods.map(p => {
    const charc = isCharcuteria(p.categoria);
    const buttons = charc
      ? `<div class="am-btns-row">
           <button class="am-add-btn am-btn-half" data-add="${escapeAttr(p.nombre||'')}">🛒 Agregar</button>
           <button class="am-add-btn am-btn-half am-grams-btn" data-grams="${escapeAttr(p.nombre||'')}">⚖️ Gramos</button>
         </div>`
      : `<button class="am-add-btn" data-add="${escapeAttr(p.nombre||'')}">🛒 Agregar</button>`;
    return `
    <div class="am-card" data-cat="${escapeAttr(String(p.categoria||'').toLowerCase())}">
      <img src="${escapeAttr(fixImgSrc(p.imagen))}" alt="${escapeAttr(p.nombre||'')}" loading="lazy" data-zoom="1"/>
      <div class="am-name">${escapeHtml(p.nombre||'')}</div>
      <div class="am-price-row">
        <span class="am-price">${escapeHtml(formatPrice(p.precio))}</span>
        <button class="am-share-btn" type="button" data-share="${escapeAttr(p.id||p.nombre||'')}" aria-label="Compartir producto" title="Compartir">
          <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path fill="currentColor" d="M3 12.5 21 4l-3.2 17-5.4-5.1 6.2-8.1-8.1 6.6z"/></svg>
        </button>
        <img class="am-cashea-inline" src="./public/cashea.png" alt="Cashea" loading="lazy"/>
      </div>
      ${buttons}
    </div>
  `;
  }).join('') + `</div>`;
  main.insertAdjacentHTML('beforeend', html);

  $$('.am-add-btn[data-add]', main).forEach(btn => {
    btn.addEventListener('click', () => {
      const name = btn.getAttribute('data-add');
      const prod = PRODUCTS.find(p => p.nombre === name);
      if (prod) openQtyModal(prod);
    });
  });

  $$('.am-share-btn[data-share]', main).forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const key = btn.getAttribute('data-share');
      const prod = PRODUCTS.find(p => String(p.id) === key) || PRODUCTS.find(p => p.nombre === key);
      if (prod) shareProduct(prod);
    });
  });

  $$('.am-grams-btn', main).forEach(btn => {
    btn.addEventListener('click', () => {
      const name = btn.getAttribute('data-grams');
      const prod = PRODUCTS.find(p => p.nombre === name);
      if (prod) openGramsModal(prod);
    });
  });

  // Click en la imagen del producto -> abrir lightbox con la imagen grande
  $$('.am-card img[data-zoom="1"]', main).forEach(img => {
    img.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      openImageLightbox(img.getAttribute('src'), img.getAttribute('alt') || '');
    });
  });
}

function openImageLightbox(src, alt) {
  // Cerrar cualquier lightbox previo
  document.querySelectorAll('.am-lightbox').forEach(el => el.remove());
  const box = document.createElement('div');
  box.className = 'am-lightbox';
  box.innerHTML = `
    <button class="close" aria-label="Cerrar">×</button>
    <img src="${escapeAttr(src)}" alt="${escapeAttr(alt)}"/>
  `;
  const close = () => box.remove();
  box.addEventListener('click', (e) => {
    // Cerrar si clican fuera de la imagen o en la X
    if (e.target === box || e.target.classList.contains('close')) close();
  });
  document.addEventListener('keydown', function esc(ev) {
    if (ev.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
  });
  document.body.appendChild(box);
}

/* ---------------- CARRITO ---------------- */
function viewCart(main) {
  const cart = loadCart();
  const items = Object.entries(cart);
  main.insertAdjacentHTML('beforeend', `
    <div class="am-view-head">
      <div class="am-view-title">🛒 Tu carrito</div>
      <a class="am-btn am-btn-ghost" href="./">← Seguir comprando</a>
    </div>
  `);
  if (!items.length) {
    main.insertAdjacentHTML('beforeend', `<div class="am-empty">Tu carrito está vacío.</div>`);
    return;
  }

  const rows = items.map(([name, it]) => `
    <div class="am-cart-row" data-name="${escapeAttr(name)}">
      <img src="${escapeAttr(fixImgSrc(it.imagen))}" alt="${escapeAttr(name)}"/>
      <div class="am-cart-info">
        <div class="am-cart-name">${escapeHtml(name)}</div>
        <div class="am-cart-price">${escapeHtml(formatPrice(it.precio))} c/u</div>
      </div>
      <div class="am-cart-qty">
        <button data-op="minus">−</button>
        <input type="number" min="1" value="${it.qty}" data-op="input"/>
        <button data-op="plus">+</button>
      </div>
      <div class="am-cart-linewrap"><span class="am-cart-line">${escapeHtml(formatPrice(it.precio * it.qty))}</span></div>
      <button class="am-cart-del" data-op="del" title="Quitar">🗑️</button>
    </div>
  `).join('');

  main.insertAdjacentHTML('beforeend', `
    <div class="am-cart-page">
      ${rows}
      <div class="am-cart-actions">
        <a class="am-btn am-btn-primary" href="./">＋ Añadir más productos</a>
        <button class="am-btn am-btn-danger" id="btnCartClear">🗑 Vaciar carrito</button>
        <a class="am-btn am-btn-success" id="btnCartWhatsapp" href="#">📲 Enviar pedido por WhatsApp</a>
      </div>
      <div class="am-cart-total-box">
        <div class="am-cart-total-label">Total:</div>
        <div class="am-cart-total">${escapeHtml(formatPrice(cartTotal()))}</div>
      </div>
    </div>
  `);

  // Interacciones
  $$('.am-cart-row', main).forEach(row => {
    const name = row.getAttribute('data-name');
    const inp = $('input[data-op="input"]', row);
    $('button[data-op="minus"]', row).addEventListener('click', () => { cartSet(name, (Number(inp.value)||1) - 1); rerenderCart(); });
    $('button[data-op="plus"]',  row).addEventListener('click', () => { cartSet(name, (Number(inp.value)||1) + 1); rerenderCart(); });
    inp.addEventListener('change', () => { cartSet(name, Math.max(1, Number(inp.value)||1)); rerenderCart(); });
    $('button[data-op="del"]', row).addEventListener('click', () => { cartSet(name, 0); rerenderCart(); });
  });
  const btnClear = $('#btnCartClear');
  if (btnClear) btnClear.addEventListener('click', () => {
    if (confirm('¿Vaciar el carrito?')) { cartClear(); rerenderCart(); }
  });

  const wa = $('#btnCartWhatsapp');
  if (wa) wa.addEventListener('click', (e) => {
    e.preventDefault();
    const phone = '584246687700';
    const items = Object.values(loadCart());
    const lines = items.map(it => `* ${it.qty}x ${String(it.nombre||'').toUpperCase()} - ${formatPrice(it.precio*it.qty)}`);
    const msg =
      `🛒 ¡HOLA! QUIERO CONFIRMAR MI PEDIDO:\n\n` +
      `${lines.join('\n')}\n\n` +
      `💰 TOTAL A PAGAR: ${formatPrice(cartTotal())}\n\n` +
      `-----------------------------------\n\n` +
      `Por favor indíquenme los datos para concretar el pago y el envío. 📦`;
    const url = `https://wa.me/${phone}?text=${encodeURIComponent(msg)}`;
    window.open(url, '_blank');
  });
}

function rerenderCart() {
  const main = $('#mainContent'); if (!main) return;
  main.innerHTML = ''; viewCart(main); updateCartBadge();
}

/* ---------------- MODAL cantidad ---------------- */
let _qtyProd = null;
function openQtyModal(prod) {
  _qtyProd = prod;
  $('#qtyImg').src = fixImgSrc(prod.imagen);
  $('#qtyName').textContent = prod.nombre;
  $('#qtyPrice').textContent = formatPrice(prod.precio);
  $('#qtyInput').value = 1;
  $('#qtyModal').hidden = false;
}
function closeQtyModal() { $('#qtyModal').hidden = true; _qtyProd = null; }
function wireQtyModal() {
  const modal = $('#qtyModal'); if (!modal) return;
  $('#qtyMinus').addEventListener('click', () => { const i=$('#qtyInput'); i.value = Math.max(1, (Number(i.value)||1)-1); });
  $('#qtyPlus').addEventListener('click',  () => { const i=$('#qtyInput'); i.value = Math.max(1, (Number(i.value)||1)+1); });
  $('#qtyCancel').addEventListener('click', closeQtyModal);
  $('#qtyConfirm').addEventListener('click', () => {
    if (!_qtyProd) return closeQtyModal();
    const q = Math.max(1, Number($('#qtyInput').value)||1);
    cartAdd(_qtyProd, q);
    toast(`✔ ${q} x ${_qtyProd.nombre} añadido al carrito`);
    closeQtyModal();
  });
  modal.addEventListener('click', (e) => { if (e.target === modal) closeQtyModal(); });
}

/* ---------------- MODAL por gramos (solo CHARCUTERIA) ---------------- */
let _gramsProd = null;
function computeGramsPrice(pricePerKilo, grams){
  const g = Math.max(0, Number(grams)||0);
  return (Number(pricePerKilo)||0) * (g/1000);
}
function refreshGramsPrice(){
  if (!_gramsProd) return;
  const g = Math.max(1, Number($('#gramsInput').value)||1);
  $('#gramsPrice').textContent = formatPrice(computeGramsPrice(_gramsProd.precio, g));
}
function openGramsModal(prod){
  _gramsProd = prod;
  $('#gramsImg').src = fixImgSrc(prod.imagen);
  $('#gramsName').textContent = prod.nombre;
  $('#gramsInput').value = 100;
  refreshGramsPrice();
  $('#gramsModal').hidden = false;
}
function closeGramsModal(){ $('#gramsModal').hidden = true; _gramsProd = null; }
function wireGramsModal(){
  const modal = $('#gramsModal'); if (!modal) return;
  const inp = $('#gramsInput');
  $('#gramsMinus').addEventListener('click', () => {
    inp.value = Math.max(1, (Number(inp.value)||1) - 50);
    refreshGramsPrice();
  });
  $('#gramsPlus').addEventListener('click', () => {
    inp.value = Math.max(1, (Number(inp.value)||1) + 50);
    refreshGramsPrice();
  });
  inp.addEventListener('input', refreshGramsPrice);
  inp.addEventListener('change', () => {
    inp.value = Math.max(1, Number(inp.value)||1);
    refreshGramsPrice();
  });
  $('#gramsCancel').addEventListener('click', closeGramsModal);
  $('#gramsConfirm').addEventListener('click', () => {
    if (!_gramsProd) return closeGramsModal();
    const g = Math.max(1, Number(inp.value)||1);
    const unitPrice = computeGramsPrice(_gramsProd.precio, g);
    const label = `${_gramsProd.nombre} (${g}g)`;
    cartAdd({
      id: (_gramsProd.id || '') + '_g' + g,
      nombre: label,
      precio: unitPrice,
      imagen: _gramsProd.imagen,
      categoria: _gramsProd.categoria,
    }, 1);
    toast(`✔ ${g}g de ${_gramsProd.nombre} añadido al carrito`);
    closeGramsModal();
  });
  modal.addEventListener('click', (e) => { if (e.target === modal) closeGramsModal(); });
}

/* ---------------- ORDEN ALFABÉTICO CON AGRUPACIÓN POR PRODUCTO ----------------
   Ordena todos los productos alfabéticamente, pero manteniendo juntos (uno al
   lado del otro) todos los que comparten el mismo nombre base, ignorando el
   tamaño/presentación (400G, 1KG, 900ML, X12, etc.).
   Ej: MAIZINA AMERICANA 400G / 200G / 90G  ->  luego CREMA DE ARROZ PRIMOR ...
   Al agregar un producto nuevo desde la app de escritorio, la web lo coloca
   automáticamente en su lugar: no hace falta tocar el archivo de Python.      */
function normText(s) {
  return String(s || '')
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/[^A-Z0-9.,%\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

// Quita del nombre las medidas/presentaciones para obtener el "nombre base".
const _SIZE_RE = /\b\d+(?:[.,]\d+)?\s*(?:G|GR|GRS|GRAMOS|KG|KGS|K|ML|L|LT|LTS|LITRO|LITROS|CC|OZ|LB|LBS|UND|UNDS|UNID|UNIDADES|U|PZA|PZAS|CM|MM|MTS|M|PACK|ROLLOS|HOJAS)?\b/g;
function productBaseName(nombre) {
  let t = normText(nombre);
  t = t.replace(/\bX\s*\d+(?:[.,]\d+)?\b/g, ' ');   // X12, X 6
  t = t.replace(_SIZE_RE, ' ');                     // 400G, 1.5LT, 90, ...
  t = t.replace(/\s+/g, ' ').trim();
  return t || normText(nombre);
}

// Valor numérico de la presentación (para desempatar dentro de un mismo grupo).
function productSizeValue(nombre) {
  const t = normText(nombre);
  const m = t.match(/\b(\d+(?:[.,]\d+)?)\s*(KG|K|G|GR|GRS|L|LT|LTS|ML|CC|OZ|LB)\b/);
  if (!m) return null;
  const n = parseFloat(m[1].replace(',', '.'));
  const u = m[2];
  if (u === 'KG' || u === 'K' || u === 'L' || u === 'LT' || u === 'LTS') return n * 1000;
  if (u === 'LB') return n * 453.6;
  if (u === 'OZ') return n * 28.35;
  return n; // G, GR, GRS, ML, CC
}

function sortProductsAlpha(list) {
  const coll = new Intl.Collator('es', { sensitivity: 'base', numeric: true });
  return (Array.isArray(list) ? list.slice() : []).map((p, i) => ({ p, i }))
    .sort((a, b) => {
      const ba = productBaseName(a.p.nombre), bb = productBaseName(b.p.nombre);
      const c = coll.compare(ba, bb);              // 1) grupo alfabético
      if (c !== 0) return c;
      const sa = productSizeValue(a.p.nombre), sb = productSizeValue(b.p.nombre);
      if (sa != null && sb != null && sa !== sb) return sb - sa;  // 2) mayor a menor
      if (sa != null && sb == null) return -1;
      if (sa == null && sb != null) return 1;
      const n = coll.compare(normText(a.p.nombre), normText(b.p.nombre));
      if (n !== 0) return n;
      return a.i - b.i;
    })
    .map(x => x.p);
}

/* ---------------- ROUTER ---------------- */

function route() {
  const main = $('#mainContent'); if (!main) return;
  main.innerHTML = '';
  const params = new URLSearchParams(location.search);
  const view = (params.get('view')||'').toLowerCase();
  const cat  = params.get('cat');
  const sub  = params.get('sub');
  const q    = params.get('q');
  if (view === 'cart') return viewCart(main);
  if (cat) return viewCategory(main, cat, sub);
  if (q !== null) return viewSearch(main, q);
  viewHome(main);
}

function wireSearch() {
  const f = $('#searchForm'); const i = $('#searchInput');
  if (!f || !i) return;
  f.addEventListener('submit', (e) => {
    e.preventDefault();
    const q = (i.value||'').trim();
    location.href = './?q=' + encodeURIComponent(q);
  });
}

/* ---------------- BOOT ---------------- */
async function boot() {
  const base = './public/';
  [SETTINGS, PRODUCTS, CATEGORIES, CAT_STYLES, ANUNCIOS] = await Promise.all([
    fetchJSON(base + 'site_settings.json', {}),
    fetchJSON(base + 'products.json', []),
    fetchJSON(base + 'categories.json', []),
    fetchJSON(base + 'category_styles.json', {}),
    fetchJSON(base + 'anuncios.json', {}),
  ]);
  SUBCATS = await fetchJSON(base + 'subcategorias.json', {});

  // Orden alfabético agrupado (se aplica a inicio, apartados y búsqueda).
  PRODUCTS = sortProductsAlpha(PRODUCTS);

  applyTheme();          // <- primero el tema, para que la barra se vea correcta
  renderDeliveryBanner();
  renderBrand();
  renderSocials();
  renderMenuPanel();
  renderCategoryCircles();
  wireSearch();
  wireQtyModal();
  wireGramsModal();
  updateCartBadge();
  route();
}


/* ---- Fallback automático: si una imagen no existe en una carpeta,
        se prueban las demás carpetas del repo (cat_images, subcat_images,
        product_images, product_images2, banner_images, ads_images) ---- */
document.addEventListener('error', function (ev) {
  const el = ev.target;
  if (!el || el.tagName !== 'IMG') return;
  const src = el.getAttribute('src') || '';
  if (!src || src.startsWith('data:')) return;

  let list = el._imgTry;
  if (!list) {
    list = imgCandidates(src);
    el._imgTry = list;
    el._imgIdx = Math.max(0, list.indexOf(src));
  }
  el._imgIdx = (el._imgIdx == null ? 0 : el._imgIdx) + 1;
  if (el._imgIdx < list.length) {
    el.src = list[el._imgIdx];
  }
}, true);

document.addEventListener('DOMContentLoaded', boot);

/* ====== Compartir producto ====== */
function productShareUrl(prod) {
  try {
    const u = new URL(window.location.href);
    u.hash = '';
    u.searchParams.set('producto', String(prod.id || prod.nombre || ''));
    return u.toString();
  } catch (_) { return window.location.href; }
}

function shareProduct(prod) {
  const url = productShareUrl(prod);
  const text = `${String(prod.nombre || '').toUpperCase()} - ${formatPrice(prod.precio)}`;
  if (navigator.share) {
    navigator.share({ title: prod.nombre || 'Producto', text, url }).catch(() => openShareModal(prod, url, text));
    return;
  }
  openShareModal(prod, url, text);
}

function openShareModal(prod, url, text) {
  const enc = encodeURIComponent;
  const links = [
    ['WhatsApp', `https://api.whatsapp.com/send?text=${enc(text + ' ' + url)}`],
    ['Facebook', `https://www.facebook.com/sharer/sharer.php?u=${enc(url)}`],
    ['Telegram', `https://t.me/share/url?url=${enc(url)}&text=${enc(text)}`],
    ['X (Twitter)', `https://twitter.com/intent/tweet?url=${enc(url)}&text=${enc(text)}`],
    ['Correo', `mailto:?subject=${enc(text)}&body=${enc(url)}`],
  ];
  const prev = document.getElementById('amShareOverlay');
  if (prev) prev.remove();
  const ov = document.createElement('div');
  ov.id = 'amShareOverlay';
  ov.className = 'am-share-overlay';
  ov.innerHTML = `
    <div class="am-share-modal" role="dialog" aria-modal="true">
      <div class="am-share-title">Compartir ${escapeHtml(prod.nombre || '')}</div>
      <div class="am-share-links">
        ${links.map(([n, h]) => `<a class="am-share-link" href="${escapeAttr(h)}" target="_blank" rel="noopener">${escapeHtml(n)}</a>`).join('')}
        <button type="button" class="am-share-link am-share-copy">Copiar enlace</button>
      </div>
      <button type="button" class="am-share-close">Cerrar</button>
    </div>`;
  document.body.appendChild(ov);
  const close = () => ov.remove();
  ov.addEventListener('click', (e) => { if (e.target === ov) close(); });
  ov.querySelector('.am-share-close').addEventListener('click', close);
  ov.querySelector('.am-share-copy').addEventListener('click', (e) => {
    const btn = e.currentTarget;
    const done = () => { btn.textContent = 'Enlace copiado'; setTimeout(close, 800); };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(done).catch(done);
    } else {
      const ta = document.createElement('textarea');
      ta.value = url; document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); } catch (_) {}
      ta.remove(); done();
    }
  });
}

})();
