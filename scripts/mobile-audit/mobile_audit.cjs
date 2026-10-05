const fs = require('fs');
// Run from the repository root: node scripts/mobile-audit/mobile_audit.cjs
// Optional: AUDIT_BASE (site URL), AUDIT_OUT (output folder), AUDIT_USER / AUDIT_PASSWORD (account for the signed-in pass)
// or AUDIT_SESSION (an existing sessionid cookie, for a site whose origin the API does not trust, such as localhost).
const { chromium } = require('playwright');
const BASE = process.env.AUDIT_BASE || 'https://save-point-orpin.vercel.app';
const OUT = process.env.AUDIT_OUT || './mobile-audit-out';
fs.mkdirSync(OUT, { recursive: true });

const VIEWPORTS = [{ w: 360, h: 740 }, { w: 390, h: 844 }, { w: 430, h: 932 }];
const PUBLIC = ['/es', '/es/catalogue', '/es/games/the-witcher-3-wild-hunt', '/es/login', '/es/register', '/es/sources'];
const PRIVATE = ['/es', '/es/catalogue', '/es/collection', '/es/collection?status=completed', '/es/recommendations', '/es/friends', '/es/profile', '/es/games/the-witcher-3-wild-hunt'];

// Runs inside the page: objective layout problems.
function audit() {
  const vw = window.innerWidth;
  const out = { vw, docWidth: document.documentElement.scrollWidth, bodyScrollW: document.body.scrollWidth, pageScrollsX: document.documentElement.scrollWidth > vw + 1 };
  const sel = (e) => (e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/\s+/).slice(0, 2).join('.') : ''));
  const txt = (e) => (e.innerText || e.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 40);
  const visible = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && Number(cs.opacity) > 0.05; };
  const all = [...document.querySelectorAll('body *')].filter(visible);

  // 1) elements sticking out of the viewport
  out.overflowing = all.filter((e) => { const r = e.getBoundingClientRect(); return r.right > vw + 2 && !e.closest('[aria-hidden="true"]') && getComputedStyle(e).position !== 'fixed'; })
    .map((e) => ({ el: sel(e), right: Math.round(e.getBoundingClientRect().right), text: txt(e) })).slice(0, 8);

  // 2) tap targets under 44px
  const tappable = all.filter((e) => e.matches('a[href], button, input:not([type=hidden]), select, textarea, [role=button], [role=menuitem]'));
  out.tapTotal = tappable.length;
  out.smallTaps = tappable.filter((e) => { const r = e.getBoundingClientRect(); return (r.width < 40 || r.height < 40) && !e.closest('.visually-hidden'); })
    .map((e) => { const r = e.getBoundingClientRect(); return { el: sel(e), w: Math.round(r.width), h: Math.round(r.height), text: txt(e) }; }).slice(0, 12);

  // 3) tiny text
  const fonts = {};
  all.forEach((e) => { if ([...e.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) { const f = parseFloat(getComputedStyle(e).fontSize); if (f < 12) { const k = sel(e); fonts[k] = Math.min(fonts[k] ?? 99, f); } } });
  out.tinyText = Object.entries(fonts).slice(0, 8).map(([el, size]) => ({ el, size }));

  // 4) headings and titles wrapping on many lines
  out.wrappedTitles = [...document.querySelectorAll('h1, h2, h3, .sp-h1, .sp-card-title, .sp-tile-title, .sp-pf-name, [class*="title"]')].filter(visible).map((e) => {
    const cs = getComputedStyle(e); const lh = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.25; const lines = Math.round(e.getBoundingClientRect().height / lh);
    return { el: sel(e), lines, h: Math.round(e.getBoundingClientRect().height), fs: cs.fontSize, text: txt(e) };
  }).filter((x) => x.lines >= 3).slice(0, 10);

  // 5) text/controls overlapping each other
  const leaf = all.filter((e) => e.matches('a[href], button, input, select, h1, h2, h3, p, label, span') && ![...e.children].some((c) => visible(c) && c.matches('a[href], button, input, select, h1, h2, h3, p, label, span')) && (txt(e) || e.matches('input, select')));
  const overlaps = [];
  for (let i = 0; i < leaf.length && overlaps.length < 12; i++) {
    const a = leaf[i].getBoundingClientRect();
    for (let j = i + 1; j < leaf.length && overlaps.length < 12; j++) {
      if (leaf[i].contains(leaf[j]) || leaf[j].contains(leaf[i])) continue;
      const b = leaf[j].getBoundingClientRect();
      const w = Math.min(a.right, b.right) - Math.max(a.left, b.left); const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (w > 4 && h > 4 && (w * h) / Math.min(a.width * a.height, b.width * b.height) > 0.25) overlaps.push({ a: sel(leaf[i]) + ' "' + txt(leaf[i]) + '"', b: sel(leaf[j]) + ' "' + txt(leaf[j]) + '"' });
    }
  }
  out.overlaps = overlaps;

  // 6) content clipped by a fixed-height container
  out.clipped = all.filter((e) => { const cs = getComputedStyle(e); return (cs.overflowY === 'hidden') && e.scrollHeight > e.clientHeight + 6 && e.clientHeight > 0; })
    .map((e) => ({ el: sel(e), clientH: e.clientHeight, scrollH: e.scrollHeight })).slice(0, 6);
  out.pageHeight = document.documentElement.scrollHeight;
  return out;
}

(async () => {
  const browser = await chromium.launch();
  const results = [];
  async function pass(label, routes, creds) {
    for (const vp of VIEWPORTS) {
      const ctx = await browser.newContext({ viewport: { width: vp.w, height: vp.h }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: 'es-ES', colorScheme: 'dark',
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1' });
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', (e) => errors.push(String(e).slice(0, 120)));
      if (creds && creds.session) {
        await ctx.addCookies([{ name: 'sessionid', value: creds.session, domain: new URL(BASE).hostname, path: '/' }]);
      } else if (creds) {
        await page.goto(BASE + '/es/login', { waitUntil: 'networkidle' });
        await page.fill('#username', creds.u); await page.fill('#password', creds.p);
        await page.click('button[type=submit]'); await page.waitForURL((u) => !u.pathname.endsWith('/login'), { timeout: 45000 });
      }
      for (const route of routes) {
        try {
          await page.goto(BASE + route, { waitUntil: 'networkidle', timeout: 60000 });
          await page.waitForTimeout(700);
          const name = `${label}_${vp.w}_${route.replace(/[^a-z0-9]+/gi, '_')}`;
          const metrics = await page.evaluate(audit);
          if (vp.w === 390) { await page.screenshot({ path: `${OUT}/${name}.png` }); await page.screenshot({ path: `${OUT}/${name}_full.png`, fullPage: true }); }
          results.push({ label, vp: vp.w, route, errors: errors.splice(0), ...metrics });
        } catch (e) { results.push({ label, vp: vp.w, route, failed: String(e).slice(0, 150) }); }
      }
      // interactions at 390 only
      if (vp.w === 390) {
        try {
          await page.goto(BASE + '/es', { waitUntil: 'networkidle' });
          await page.locator('header button[aria-controls="mobile-menu"]').click();
          await page.waitForTimeout(500);
          await page.screenshot({ path: `${OUT}/${label}_390_menu_open.png` });
          results.push({ label, vp: 390, route: 'menu-open', ...(await page.evaluate(audit)) });
        } catch (e) { results.push({ label, vp: 390, route: 'menu-open', failed: String(e).slice(0, 150) }); }
        if (creds) {
          try {
            await page.goto(BASE + '/es', { waitUntil: 'networkidle' });
            await page.locator('header [aria-haspopup]').first().click();
            await page.waitForTimeout(500);
            await page.screenshot({ path: `${OUT}/${label}_390_account_menu.png` });
            await page.goto(BASE + '/es/catalogue', { waitUntil: 'networkidle' });
            const dd = page.locator('.sp-dropdown > button, .sp-dropdown summary').first();
            if (await dd.count()) { await dd.click(); await page.waitForTimeout(400); await page.screenshot({ path: `${OUT}/${label}_390_filter_open.png` }); }
          } catch (e) { results.push({ label, vp: 390, route: 'interactions', failed: String(e).slice(0, 150) }); }
        }
      }
      await ctx.close();
    }
  }
  await pass('out', PUBLIC, null);
  if (process.env.AUDIT_SESSION) await pass('in', PRIVATE, { session: process.env.AUDIT_SESSION });
  else if (process.env.AUDIT_PASSWORD) await pass('in', PRIVATE, { u: process.env.AUDIT_USER || 'demo_user', p: process.env.AUDIT_PASSWORD });
  fs.writeFileSync(`${OUT}/results.json`, JSON.stringify(results, null, 1));
  console.log('done', results.length, 'measurements');
  await browser.close();
})();
