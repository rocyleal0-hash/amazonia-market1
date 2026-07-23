/* =========================================================
   AMAZONIA MARKET - app.js
   Replica de tienda.py en HTML/JS estatico para GitHub Pages
   ========================================================= */
(() => {
'use strict';

const $  = (s, r=document) => r.querySelector(s);
const $$ = (s, r=document) => Array.from(r.querySelectorAll(s));
const escapeHtml = s => String(s ?? '')
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
const escapeAttr = escapeHtml;

// Helper para corregir rutas de imágenes apuntando a public/
// Helper para corregir rutas de imágenes apuntando siempre a public/
function fixImgSrc(path) {
  if (!path) return '';
  let p = String(path).trim();
  if (p.startsWith('data:') || p.startsWith('http://') || p.startsWith('https://')) {
    return p;
  }
  // Limpiar slashes iniciales
  p = p.replace(/^\/+/, '');
  
  // Si no empieza con public/, se lo anteponemos
  if (!p.startsWith('public/')) {
    p = 'public/' + p;
  }
  return p;
}
  return 'public/' + p.replace(/^\//, '');
}

// -------- helpers de datos --------
async function fetchJSON(path, fallback) {
  try {
    const r = await fetch(path, { cache: 'no-store' });
    if (!r.ok) throw new Error('http ' + r.status);
    return await r.json();
  } catch (e) {
    console.warn('No se pudo cargar', path, e);
    return fallback;
  }
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

// -------- cart en localStorage --------
const CART_KEY = 'amazonia_cart_v1';
function loadCart() {
  try { return JSON.parse(localStorage.getItem(CART_KEY) || '{}'); }
  catch { return {}; }
}
function saveCart(c) { localStorage.setItem(CART_KEY, JSON.stringify(c)); updateCartBadge(); }
function cartCount() {
  const c = loadCart();
  return Object.values(c).reduce((s, it) => s + (Number(it.qty)||0), 0);
}
function cartTotal() {
  const c = loadCart();
  return Object.values(c).reduce((s, it) => s + (Number(it.precio)||0) * (Number(it.qty)||0), 0);
}
function cartAdd(prod, qty=1) {
  const c = loadCart();
  const name = prod.nombre;
  if (!c[name]) {
    c[name] = { id: prod.id, nombre: prod.nombre, precio: Number(prod.precio)||0,
                imagen: prod.imagen, categoria: prod.categoria, qty: 0 };
  }
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
  const n = cartCount();
  const b = $('#cartBadge');
  if (n > 0) { b.textContent = n; b.hidden = false; }
  else       { b.hidden = true; }
}

// -------- toast --------
let toastTimer = null;
function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 1800);
}

// =========================================================
// STATE
// =========================================================
let SETTINGS = {};
let PRODUCTS = [];
let CATEGORIES = [];
let CAT_STYLES = {};
let ANUNCIOS = {};

// =========================================================
// TOPBAR
// =========================================================
function renderDeliveryBanner() {
  const text = SETTINGS.delivery_text || '🚚 Delivery GRATIS en toda la zona de Coro';
  const one = `<span>${escapeHtml(text)}</span>`;
  const group = one.repeat(6);
  $('#deliveryTrack').innerHTML = group + group;
}

function renderBrand() {
  const siteName   = SETTINGS.site_name   || 'Amazonia';
  const siteMarket = SETTINGS.site_market || 'MARKET';

  const logoB64 = (SETTINGS.site_logo_b64 || '').trim();
  const logoEl = $('#brandLogo');
  const hideLogo = String(SETTINGS.hide_logo || '0').match(/^(1|true|yes)$/i);
  if (logoB64 && !hideLogo) {
    logoEl.src = 'data:image/png;base64,' + logoB64;
    logoEl.style.display = 'block';
    const sz = parseInt(SETTINGS.logo_size || 54, 10) || 54;
    logoEl.style.height = sz + 'px';
  }

  const hideTitles = String(SETTINGS.hide_titles || '0').match(/^(1|true|yes)$/i);
  const titlesHtml = hideTitles ? '' : `
    <div class="am-brand-name">${escapeHtml(siteName)}</div>
    <div class="am-brand-market">${escapeHtml(siteMarket)}</div>
  `;
  $('#brandTitles').innerHTML = titlesHtml;
}

function renderSocials() {
  const fb = (SETTINGS.social_facebook_url || '').trim();
  const ig = (SETTINGS.social_instagram_url || '').trim();
  const tk = (SETTINGS.social_tiktok_url || '').trim();
  const svg = {
    fb: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="#fff"><path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"/></svg>`,
    ig: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="#fff"><path d="M12 2.163c3.204 0 3.584.012 4.849.07 1.366.062 2.633.336 3.608 1.311.975.975 1.249 2.242 1.311 3.608.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.062 1.366-.336 2.633-1.311 3.608-.975.975-2.242 1.249-3.608 1.311-1.265.058-1.645.07-4.849.07-3.205 0-3.584-.012-4.849-.07-1.366-.062-2.633-.336-3.608-1.311-.975-.975-1.249-2.242-1.311-3.608C2.175 15.647 2.163 15.268 2.163 12s.012-3.584.07-4.849c.062-1.366.336-2.633 1.311-3.608.975-.975 2.242-1.249 3.608-1.311C8.416 2.175 8.796 2.163 12 2.163zm0 1.802c-3.148 0-3.523.011-4.767.068-1.006.046-1.554.213-1.918.353-.482.187-.827.41-1.188.771-.361.361-.584.706-.771 1.188-.14.364-.307.912-.353 1.918C2.976 8.477 2.965 8.852 2.965 12s.011 3.523.068 4.767c.046 1.006.213 1.554.353 1.918.187.482.41.827.771 1.188.361.361.706.584 1.188.771.364.14.912.307 1.918.353 1.244.057 1.619.068 4.767.068s3.523-.011 4.767-.068c1.006-.046 1.554-.213 1.918-.353.482-.187.827-.41 1.188-.771.361-.361.706-.584.771-1.188.14-.364.307-.912.353-1.918.057-1.244.068-1.619.068-4.767s-.011-3.523-.068-4.767c-.046-1.006-.213-1.554-.353-1.918-.187-.482-.41-.827-.771-1.188-.361-.361-.706-.584-1.188-.771-.364-.14-.912-.307-1.918-.353C15.523 3.976 15.148 3.965 12 3.965zm0 3.063A4.972 4.972 0 1 1 12 16.972 4.972 4.972 0 0 1 12 7.028zm0 8.203A3.231 3.231 0 1 0 12 8.769a3.231 3.231 0 0 0 0 6.462zm5.171-8.406a1.163 1.163 0 1 1-2.326 0 1.163 1.163 0 0 1 2.326 0z"/></svg>`,
    tk: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="#fff"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5.8 20.1a6.34 6.34 0 0 0 10.86-4.43V8.66a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1.84-.09z"/></svg>`,
  };
  const items = [];
  if (fb) items.push(`<a href="${escapeAttr(fb)}" target="_blank" rel="noopener" title="Facebook" style="border-radius:50%;background:#1877F2;">${svg.fb}</a>`);
  if (ig) items.push(`<a href="${escapeAttr(ig)}" target="_blank" rel="noopener" title="Instagram" style="border-radius:10px;background:radial-gradient(circle at 30% 110%,#FEDA75 0%,#FA7E1E 25%,#D62976 50%,#962FBF 75%,#4F5BD5 100%);">${svg.ig}</a>`);
  if (tk) items.push(`<a href="${escapeAttr(tk)}" target="_blank" rel="noopener" title="TikTok" style="border-radius:50%;background:#000;">${svg.tk}</a>`);
  $('#amSocials').innerHTML = items.join('');
}

function renderMenuPanel() {
  const items = CATEGORIES.map(c =>
    `<a href="?cat=${encodeURIComponent(c)}">${escapeHtml(cap(c))}</a>`
  ).join('');
  $('#menuPanel').innerHTML =
    `<div class="am-menu-head">Apartados</div>` +
    (items || `<div style="padding:14px 18px;opacity:.85;font-size:13px;">Aún no hay apartados.</div>`);
}

// =========================================================
// CIRCULOS DE CATEGORIAS
// =========================================================
function catStyle(name) {
  const defaults = {
    icon:'', circle_color:'#2A2A9C', circle_size:96,
    label_color:'#0F172A', label_size:14,
    title_color:'#2A2A9C', title_size:22,
    more_bg:'#2A2A9C', more_fg:'#FFFFFF',
    use_image:false, image_path:''
  };
  const s = Object.assign({}, defaults, CAT_STYLES[name] || {});
  s.circle_size = parseInt(s.circle_size || 96, 10) || 96;
  return s;
}

function renderCategoryCircles() {
  if (!CATEGORIES.length) { $('#catsWrap').style.display='none'; return; }
  const html = CATEGORIES.map(cat => {
    const s = catStyle(cat);
    const icon = s.icon || iconForCategory(cat);
    const sz = s.circle_size;
    let inner, bg;
    if (s.use_image && s.image_path) {
      inner = `<img src="${escapeAttr(fixImgSrc(s.image_path))}" alt="${escapeAttr(cat)}"/>`;
      bg = `background:${s.circle_color};`;
    } else {
      inner = escapeHtml(icon);
      bg = `background: radial-gradient(circle at 30% 30%, color-mix(in srgb, ${s.circle_color} 78%, white) 0%, ${s.circle_color} 78%); font-size:${Math.round(sz*0.46)}px;`;
    }
    return `<a class="am-cat-circle" href="?cat=${encodeURIComponent(cat)}" style="min-width:${Math.max(sz+20,80)}px;">
      <div class="bubble" style="width:${sz}px;height:${sz}px;${bg}">${inner}</div>
      <div class="label" style="color:${s.label_color};font-size:${s.label_size}px;">${escapeHtml(cat)}</div>
    </a>`;
  }).join('');
  $('#catsScroll').innerHTML = html;
}

// =========================================================
// BANNER DE ANUNCIOS (hero slideshow + 4 cards)
// =========================================================
function renderAnunciosBanner(container) {
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

  const bh   = parseInt(ANUNCIOS.banner_height, 10) || 320;
  const brt  = parseInt(ANUNCIOS.banner_brightness, 10) || 100;
  const blur = parseInt(ANUNCIOS.banner_blur, 10) || 0;
  const ovr  = parseInt(ANUNCIOS.banner_overlay, 10) || 0;

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

  // Slideshow cada 1.5s
  if (slides.length > 1) {
    let idx = 0;
    setInterval(() => {
      const el = $('#adsHero');
      if (!el) return;
      const items = $$('.am-slide', el);
      items[idx].classList.remove('active');
      idx = (idx + 1) % items.length;
      items[idx].classList.add('active');
    }, 1500);
  }
}

// =========================================================
// VISTAS
// =========================================================
function cap(s){ s=String(s||''); return s.charAt(0).toUpperCase()+s.slice(1).toLowerCase(); }

function viewHome(main) {
  renderAnunciosBanner(main);
  if (!CATEGORIES.length) {
    main.insertAdjacentHTML('beforeend',
      `<div class="am-empty">Aún no hay apartados.<br>Crea apartados desde la app de escritorio.</div>`);
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
      <div class="am-quad-imgwrap"><img src="${escapeAttr(fixImgSrc(p.imagen))}" alt="${escapeAttr(p.nombre||'')}" loading="lazy"/></div>
      <div class="am-quad-name">${escapeHtml(p.nombre || '')}</div>
    </a>
  `).join('');
  for (let k=preview.length; k<4; k++) items += `<div class="am-quad-item am-quad-empty"></div>`;

  const grid = preview.length
    ? `<div class="am-quad-grid">${items}</div>`
    : `<div class="am-quad-grid"><div class="am-empty" style="grid-column:1/-1;margin:0;">Aún no hay productos.</div></div>`;

  return `<div class="am-tile">
    <div class="am-tile-title" style="color:${s.title_color};">
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
    main.insertAdjacentHTML('beforeend',
      `<div class="am-empty">No hay productos en este apartado todavía.</div>`);
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
  if (!q) {
    main.insertAdjacentHTML('beforeend',`<div class="am-empty">Escribe algo en la barra de búsqueda.</div>`);
    return;
  }
  const ql = q.toLowerCase();
  const results = PRODUCTS.filter(p =>
    String(p.nombre||'').toLowerCase().includes(ql) ||
    String(p.categoria||'').toLowerCase().includes(ql)
  );
  if (!results.length) {
    main.insertAdjacentHTML('beforeend',`<div class="am-empty">No se encontraron productos que coincidan.</div>`);
    return;
  }
  main.insertAdjacentHTML('beforeend', `<p style="color:var(--muted);font-size:13px;">${results.length} resultado(s) en toda la tienda.</p>`);
  renderProductGrid(main, results);
}

function renderProductGrid(main, prods) {
  const html = `<div class="am-grid">` + prods.map(p => `
    <div class="am-card">
      <img src="${escapeAttr(fixImgSrc(p.imagen))}" alt="${escapeAttr(p.nombre||'')}" loading="lazy"/>
      <div class="am-name">${escapeHtml(p.nombre||'')}</div>
      <div><span class="am-price">${escapeHtml(formatPrice(p.precio))}</span></div>
      <button class="am-add-btn" data-add="${escapeAttr(p.nombre||'')}">🛒 Agregar</button>
    </div>
  `).join('') + `</div>`;
  main.insertAdjacentHTML('beforeend', html);

  // handlers
  $$('.am-add-btn', main).forEach(btn => {
    btn.addEventListener('click', () => {
      const name = btn.getAttribute('data-add');
      const prod = PRODUCTS.find(p => p.nombre === name);
      if (prod) openQtyModal(prod);
    });
  });
}

// =========================================================
// CARRITO
// =========================================================
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
      <div class="am-cart-name">${escapeHtml(name)}</div>
      <div class="am-cart-price">${escapeHtml(formatPrice(it.precio))}</div>
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
      </div>
      <div class="am-cart-total-box">
        <div>
          <div class="am-cart-total-label">Total a pagar:</div>
          <div class="am-cart-total">${escapeHtml(formatPrice(cartTotal()))}</div>
        </div>
        <button class="am-btn am-btn-success" id="btnCartPay" style="font-size:18px;padding:14px 28px;">💳  Pagar ahora</button>
      </div>
    </div>
  `);

  // handlers
  $$('.am-cart-row', main).forEach(row => {
    const name = row.getAttribute('data-name');
    row.querySelector('[data-op="minus"]').onclick = () => { const c=loadCart(); if(!c[name])return; cartSet(name, c[name].qty-1); rerender(); };
    row.querySelector('[data-op="plus"]').onclick  = () => { const c=loadCart(); if(!c[name])return; cartSet(name, c[name].qty+1); rerender(); };
    row.querySelector('[data-op="del"]').onclick   = () => { cartSet(name, 0); rerender(); };
    row.querySelector('[data-op="input"]').onchange = (e) => {
      const q = Math.max(0, parseInt(e.target.value,10)||0);
      cartSet(name, q); rerender();
    };
  });
  $('#btnCartClear').onclick = () => { if(confirm('¿Vaciar el carrito?')){ cartClear(); rerender(); } };
  $('#btnCartPay').onclick = () => alert('¡Gracias por tu compra! (Aquí conectas tu pasarela de pago).');
}

// =========================================================
// MODAL CANTIDAD
// =========================================================
let PENDING_PROD = null;
function openQtyModal(prod) {
  PENDING_PROD = prod;
  $('#qtyImg').src = fixImgSrc(prod.imagen);
  $('#qtyImg').alt = prod.nombre || '';
  $('#qtyName').textContent = prod.nombre || '';
  $('#qtyPrice').textContent = formatPrice(prod.precio);
  $('#qtyInput').value = 1;
  $('#qtyModal').hidden = false;
}
function closeQtyModal() {
  $('#qtyModal').hidden = true;
  PENDING_PROD = null;
}

// =========================================================
// ROUTER + INIT
// =========================================================
function currentParams() {
  const p = new URLSearchParams(location.search);
  return { view: p.get('view')||'', cat: p.get('cat')||'', q: p.get('q')||'' };
}

function rerender() {
  updateCartBadge();
  const main = $('#mainContent');
  main.innerHTML = '';
  const { view, cat, q } = currentParams();
  if (view === 'cart') viewCart(main);
  else if (view === 'search') viewSearch(main, q);
  else if (cat) viewCategory(main, cat);
  else viewHome(main);
}

async function init() {
  // Cargar todos los JSON en paralelo desde la carpeta public
  [SETTINGS, PRODUCTS, CATEGORIES, CAT_STYLES, ANUNCIOS] = await Promise.all([
    fetchJSON('public/site_settings.json', {}),
    fetchJSON('public/products.json', []),
    fetchJSON('public/categories.json', []),
    fetchJSON('public/category_styles.json', {}),
    fetchJSON('public/anuncios.json', { cards: [] }),
  ]);

  // Si categories.json está vacío, deducir desde CAT_STYLES o productos
  if (!Array.isArray(CATEGORIES) || !CATEGORIES.length) {
    CATEGORIES = Object.keys(CAT_STYLES);
    if (!CATEGORIES.length) {
      const seen = new Set();
      PRODUCTS.forEach(p => { if (p.categoria && !seen.has(p.categoria)) { seen.add(p.categoria); CATEGORIES.push(p.categoria); } });
    }
  }

  // Topbar
  renderDeliveryBanner();
  renderBrand();
  renderSocials();
  renderMenuPanel();

  // Círculos
  renderCategoryCircles();

  // Contenido
  rerender();

  // Handlers globales
  $('#btnMenu').onclick = () => {
    const p = $('#menuPanel');
    p.hidden = !p.hidden;
  };
  $('#searchForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const q = ($('#searchInput').value||'').trim();
    if (q) location.href = '?view=search&q=' + encodeURIComponent(q);
    else location.href = './';
  });
  // Precargar buscador con q actual
  const { q } = currentParams();
  if (q) $('#searchInput').value = q;

  // Modal
  $('#qtyMinus').onclick = () => { const i=$('#qtyInput'); i.value = Math.max(1, (parseInt(i.value,10)||1)-1); };
  $('#qtyPlus').onclick  = () => { const i=$('#qtyInput'); i.value = (parseInt(i.value,10)||1)+1; };
  $('#qtyCancel').onclick = closeQtyModal;
  $('#qtyConfirm').onclick = () => {
    if (!PENDING_PROD) return;
    const qty = Math.max(1, parseInt($('#qtyInput').value,10)||1);
    cartAdd(PENDING_PROD, qty);
    toast(`Añadido ${qty} × ${PENDING_PROD.nombre}`);
    closeQtyModal();
  };
  $('#qtyModal').addEventListener('click', (e) => {
    if (e.target.id === 'qtyModal') closeQtyModal();
  });

  updateCartBadge();
}

document.addEventListener('DOMContentLoaded', init);

})();
