/* =========================================================
   AMAZONIA MARKET - app.js
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

// FUNCIÓN CORREGIDA PARA RUTAS DE IMÁGENES
function fixImgSrc(path) {
  if (!path) return 'https://via.placeholder.com/300?text=Sin+Imagen';
  let p = String(path).trim().replace(/\\/g, '/');
  
  if (p.startsWith('data:') || p.startsWith('http://') || p.startsWith('https://')) {
    return p;
  }
  
  // Limpiar diagonales iniciales
  p = p.replace(/^\/+/, '');
  
  // Extraer solo el nombre del archivo si contiene subrutas repetidas
  if (p.includes('product_images/')) {
    p = p.split('product_images/').pop();
  } else if (p.includes('public/')) {
    p = p.split('public/').pop();
  }
  
  return './public/product_images/' + p;
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

/* ---------------- TEMA ---------------- */
function applyTheme() {
  const s = SETTINGS || {};
  const root = document.documentElement.style;

  const setVar = (name, val) => { if (val !== undefined && val !== null && String(val).trim() !== '') root.setProperty(name, String(val).trim()); };

  setVar('--tb-bg',          s.topbar_bg_color || s.hero_bg_color);
  setVar('--tb-delivery-fg', s.delivery_text_color);
  setVar('--tb-menu-bg',     s.btn_menu_bg);
  setVar('--tb-menu-fg',     s.btn_menu_fg);
  setVar('--tb-search-bg',   s.btn_search_bg);
  setVar('--tb-search-fg',   s.btn_search_fg);
  setVar('--tb-cart-bg',     s.btn_cart_bg);
  setVar('--tb-cart-fg',     s.btn_cart_fg);

  setVar('--menu-bg', s.menu_panel_bg);
  setVar('--menu-fg', s.menu_panel_fg);

  setVar('--more-bg', s.section_more_bg);
  setVar('--more-fg', s.section_more_fg);

  setVar('--img-border-color', s.img_border_color);
  const bw = intOr(s.img_border_width, null);
  if (bw !== null) root.setProperty('--img-border-width', bw + 'px');

  setVar('--cart-card-bg',  s.cart_card_bg);
  setVar('--cart-name-fg',  s.cart_name_color);
  setVar('--cart-unit-fg',  s.cart_unit_color);
  setVar('--cart-price-bg', s.cart_price_bg);
  setVar('--cart-price-fg', s.cart_price_fg);

  const align = String(s.logo_align || 'left').toLowerCase();
  const justify = align === 'center' ? 'center' : (align === 'right' ? 'flex-end' : 'flex-start');
  root.setProperty('--brand-justify', justify);
  const off = intOr(s.logo_offset_x, 0);
  root.setProperty('--brand-offset-x', off + 'px');

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
      inner = `<img src="${escapeAttr(imgSrc)}" alt="${escapeAttr(cat)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" onerror="this.onerror=null; this.src='https://via.placeholder.com/150?text=Error';"/>`;
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
    .map(s => ({ b64: (s.img_b64||'').trim(), url: (s.url||'').trim() }))
    .filter(s => s.b64);
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
    return `<a class="am-slide ${i===0?'active':''}" data-idx="${i}" href="${escapeAttr(href)}" ${target}>
      <img src="data:image/png;base64,${s.b64}" style="filter: brightness(${brt}%) blur(${blur}px);"/>
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
      </div>
      ${cardsHtml}
    </div>
  `);

  if (slides.length > 1) {
    let idx = 0;
    setInterval(() => {
      const el = $('#adsHero'); if (!el) return;
      const items = $$('.am-slide', el); if (!items.length) return;
      items[idx].classList.remove('active');
      idx = (idx + 1) % items.length;
      items[idx].classList.add('active');
    }, 4000);
  }
}

function cap(s){ s=String(s||''); return s.charAt(0).toUpperCase()+s.slice(1).toLowerCase(); }

/* ---------------- VISTAS ---------------- */
function viewHome(main) {
  renderAnunciosBanner(main);
  if (!CATEGORIES.length) {
    main.insertAdjacentHTML('beforeend', `<div class="am-empty">Aún no hay apartados.<br>Crea apartados desde la app de escritorio.</div>`);
    return;
  }
  const PER_ROW = 4;
  let out = '';
  for (let i=0; i<CATEGORIES.length; i+=PER_ROW) {
    const row = CATEGORIES.slice(i, i+PER_ROW);
    let cards = row.map(cat => buildHomeTile(cat)).join('');
    for (let k=row.length; k<PER_ROW; k++) cards += `<div class="am-tile am-tile-empty"></div>`;
    out += `<div class="am-tiles-row">${cards}</div>`;
  }
  main.insertAdjacentHTML('beforeend', out);
}

function buildHomeTile(cat) {
  const catProds = PRODUCTS.filter(p => p.categoria === cat);
  const s = catStyle(cat);
  const emoji = s.icon || iconForCategory(cat);
  const preview = catProds.slice(0, 4);
  let items = preview.map(p => `
    <a class="am-quad-item" href="?cat=${encodeURIComponent(cat)}">
      <div class="am-quad-imgwrap">
        <img src="${escapeAttr(fixImgSrc(p.imagen))}" alt="${escapeAttr(p.nombre||'')}" loading="lazy" onerror="this.onerror=null; this.src='https://via.placeholder.com/150?text=Sin+Imagen';"/>
      </div>
      <div class="am-quad-name">${escapeHtml(p.nombre || '')}</div>
    </a>
  `).join('');
  for (let k=preview.length; k<4; k++) items += `<div class="am-quad-item am-quad-empty"></div>`;

  const grid = preview.length
    ? `<div class="am-quad-grid">${items}</div>`
    : `<div class="am-quad-grid"><div class="am-empty" style="grid-column:1/-1;margin:0;">Aún no hay productos.</div></div>`;

  return `<div class="am-tile">
    <div class="am-tile-title" style="color:${s.title_color};font-size:${s.title_size}px;">
      ${escapeHtml(emoji)} ${escapeHtml(cap(cat))}
      <span class="am-tile-count">· ${catProds.length} producto(s)</span>
    </div>
    ${grid}
    <a class="am-tile-more" href="?cat=${encodeURIComponent(cat)}" style="background:${s.more_bg};color:${s.more_fg};">Ver más →</a>
  </div>`;
}

function viewCategory(main, cat) {
  const emoji = iconForCategory(cat);
  main.insertAdjacentHTML('beforeend', `
    <div class="am-view-head">
      <div class="am-view-title">${escapeHtml(emoji)} ${escapeHtml(cap(cat))}</div>
      <a class="am-btn am-btn-ghost" href="./">← Apartados</a>
    </div>
  `);
  const prods = PRODUCTS.filter(p => p.categoria === cat);
  if (!prods.length) {
    main.insertAdjacentHTML('beforeend', `<div class="am-empty">No hay productos en este apartado todavía.</div>`);
    return;
  }
  renderProductGrid(main, prods);
  main.insertAdjacentHTML('beforeend', `<p style="color:var(--muted);font-size:13px;">Mostrando ${prods.length} producto(s).</p>`);
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
  main.insertAdjacentHTML('beforeend', `<p style="color:var(--muted);font-size:13px;">${results.length} resultado(s) en toda la tienda.</p>`);
  renderProductGrid(main, results);
}

function renderProductGrid(main, prods) {
  const html = `<div class="am-grid">` + prods.map(p => `
    <div class="am-card">
      <img src="${escapeAttr(fixImgSrc(p.imagen))}" alt="${escapeAttr(p.nombre||'')}" loading="lazy" onerror="this.onerror=null; this.src='https://via.placeholder.com/300?text=Sin+Imagen';"/>
      <div class="am-name">${escapeHtml(p.nombre||'')}</div>
      <div><span class="am-price">${escapeHtml(formatPrice(p.precio))}</span></div>
      <button class="am-add-btn" data-add="${escapeAttr(p.nombre||'')}">🛒 Agregar</button>
    </div>
  `).join('') + `</div>`;
  main.insertAdjacentHTML('beforeend', html);

  $$('.am-add-btn', main).forEach(btn => {
    btn.addEventListener('click', () => {
      const name = btn.getAttribute('data-add');
      const prod = PRODUCTS.find(p => p.nombre === name);
      if (prod) openQtyModal(prod);
    });
  });
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
      <img src="${escapeAttr(fixImgSrc(it.imagen))}" alt="${escapeAttr(name)}" onerror="this.onerror=null; this.src='https://via.placeholder.com/150?text=Sin+Imagen';"/>
      <div class="am-cart-name">${escapeHtml(name)}</div>
      <div class="am-cart-price"><span class="am-cart-unit">${escapeHtml(formatPrice(it.precio))}</span></div>
      <div class="am-cart-qty">
        <button data-op="minus">−</button>
        <input type="number" min="1" value="${it.qty}" data-op="input"/>
        <button data-op="plus">+</button>
      </div>
      <div><span class="am-cart-line">${escapeHtml(formatPrice(it.precio * it.qty))}</span></div>
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
    const phone = (SETTINGS.whatsapp_phone || '').replace(/[^\d]/g,'');
    const lines = Object.values(loadCart()).map(it => `• ${it.qty} x ${it.nombre} — ${formatPrice(it.precio*it.qty)}`);
    const msg = `Hola, quisiera pedir:\n${lines.join('\n')}\n\nTotal: ${formatPrice(cartTotal())}`;
    const url = phone
      ? `https://wa.me/${phone}?text=${encodeURIComponent(msg)}`
      : `https://wa.me/?text=${encodeURIComponent(msg)}`;
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
  const imgEl = $('#qtyImg');
  imgEl.src = fixImgSrc(prod.imagen);
  imgEl.onerror = function() { this.src = 'https://via.placeholder.com/300?text=Sin+Imagen'; };
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

/* ---------------- ROUTER ---------------- */
function route() {
  const main = $('#mainContent'); if (!main) return;
  main.innerHTML = '';
  const params = new URLSearchParams(location.search);
  const view = (params.get('view')||'').toLowerCase();
  const cat  = params.get('cat');
  const q    = params.get('q');
  if (view === 'cart') return viewCart(main);
  if (cat) return viewCategory(main, cat);
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

  applyTheme();
  renderDeliveryBanner();
  renderBrand();
  renderSocials();
  renderMenuPanel();
  renderCategoryCircles();
  wireSearch();
  wireQtyModal();
  updateCartBadge();
  route();
}

document.addEventListener('DOMContentLoaded', boot);
})();
