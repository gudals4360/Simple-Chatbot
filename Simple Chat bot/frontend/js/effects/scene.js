// 배경 장면: 다크 모드는 반짝이는 행성, 라이트 모드는 떠다니는 꽃.
// 대화 스크롤보다 느리게 움직이는 패럴랙스 스크롤을 적용한다.
import { $ } from '../core/dom.js';
import { state, activeScroll } from '../core/state.js';
import { root, currentTheme, syncThemeBtn } from './theme.js';

export function initScene() {
  const cv = $('scene'), ctx = cv.getContext('2d');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let W = 0, H = 0, dpr = 1, items = [], stars = [], mode = '';
  const rnd = (a, b) => a + Math.random() * (b - a);
  const PLANETS = [
    ['#B9A6FF', '#5B3FD1', '#1E1252'], ['#8FF3E4', '#1C9C9A', '#06363F'], ['#FFD59A', '#E2852F', '#4A2208'],
    ['#FFB3C7', '#D2457A', '#40102A'], ['#BFD8FF', '#3E6FD8', '#0C1E4D'], ['#E9F7A8', '#8DB33A', '#233210']
  ];
  const FLOWERS = [
    ['#FFD1DC', '#FF9EB5', '#FFE27A'], ['#FFFFFF', '#F2F2F7', '#FFC94D'], ['#FFE8A3', '#FFD25C', '#B9772A'],
    ['#E6D9FF', '#C6B0FF', '#FFE27A'], ['#FFC7B8', '#FF9F86', '#FFF0B3']
  ];

  function resize() {
    const r = cv.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = r.width; H = r.height;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function build() {
    mode = currentTheme();
    items = []; stars = [];
    const span = H + 400; // 위아래로 이어지는 가상 공간
    if (mode === 'dark') {
      const n = Math.max(8, Math.round(W / 45));
      for (let i = 0; i < n; i++) {
        const depth = rnd(0.12, 0.55);
        items.push({
          x: rnd(0, 1), y: rnd(0, span), depth,
          r: 8 + depth * 46 + rnd(-4, 6),
          pal: PLANETS[i % PLANETS.length],
          ring: Math.random() < 0.35, tilt: rnd(-0.5, 0.5),
          phase: rnd(0, Math.PI * 2), speed: rnd(0.15, 0.35), amp: rnd(6, 16)
        });
      }
      const sn = Math.round((W * H) / 2600);
      for (let i = 0; i < sn; i++) stars.push({ x: rnd(0, 1), y: rnd(0, span), depth: rnd(0.04, 0.12), s: rnd(0.5, 1.6), phase: rnd(0, 6.3), tw: rnd(0.8, 2.4) });
    } else {
      const n = Math.max(14, Math.round(W / 24));
      for (let i = 0; i < n; i++) {
        const depth = rnd(0.12, 0.6);
        items.push({
          x: rnd(0, 1), y: rnd(0, span), depth,
          r: 9 + depth * 30 + rnd(-2, 5),
          pal: FLOWERS[i % FLOWERS.length],
          petals: Math.random() < 0.7 ? 5 : 6,
          rot: rnd(0, 6.3), spin: rnd(-0.25, 0.25) || 0.1,
          phase: rnd(0, Math.PI * 2), speed: rnd(0.2, 0.4), amp: rnd(8, 20)
        });
      }
      // 작은 꽃잎 조각
      const pn = Math.round(W / 18);
      for (let i = 0; i < pn; i++) stars.push({ x: rnd(0, 1), y: rnd(0, span), depth: rnd(0.08, 0.2), s: rnd(2.5, 5), rot: rnd(0, 6.3), phase: rnd(0, 6.3), tw: rnd(0.3, 0.8), col: FLOWERS[i % FLOWERS.length][1] });
    }
    items.sort((a, b) => a.depth - b.depth);
  }

  function wrapY(y, scroll, depth) {
    const span = H + 400;
    let v = (y - scroll * depth) % span;
    if (v < 0) v += span;
    return v - 200;
  }

  function drawPlanet(p, x, y, t) {
    const { r, pal } = p;
    const glow = 0.55 + 0.25 * Math.sin(t * 1.3 + p.phase);
    // 바깥 빛
    const g0 = ctx.createRadialGradient(x, y, r * 0.6, x, y, r * 2.4);
    g0.addColorStop(0, pal[0] + Math.round(glow * 70).toString(16).padStart(2, '0'));
    g0.addColorStop(1, pal[0] + '00');
    ctx.fillStyle = g0; ctx.beginPath(); ctx.arc(x, y, r * 2.4, 0, 7); ctx.fill();
    if (p.ring) drawRing(p, x, y, true);
    // 구 본체
    const g = ctx.createRadialGradient(x - r * 0.4, y - r * 0.45, r * 0.1, x, y, r);
    g.addColorStop(0, pal[0]); g.addColorStop(0.55, pal[1]); g.addColorStop(1, pal[2]);
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
    // 반짝이는 하이라이트
    ctx.fillStyle = `rgba(255,255,255,${0.25 + 0.35 * glow})`;
    ctx.beginPath(); ctx.ellipse(x - r * 0.38, y - r * 0.42, r * 0.22, r * 0.12, -0.6, 0, 7); ctx.fill();
    if (p.ring) drawRing(p, x, y, false);
    // 반짝 별빛
    if (r > 22) {
      const k = Math.max(0, Math.sin(t * 2 + p.phase * 3));
      if (k > 0.85) sparkle(x + r * 0.55, y - r * 0.7, (k - 0.85) * 60);
    }
  }
  function drawRing(p, x, y, back) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(p.tilt);
    ctx.beginPath();
    if (back) ctx.ellipse(0, 0, p.r * 1.75, p.r * 0.45, 0, Math.PI, Math.PI * 2);
    else ctx.ellipse(0, 0, p.r * 1.75, p.r * 0.45, 0, 0, Math.PI);
    ctx.strokeStyle = p.pal[0] + (back ? '66' : 'B3'); ctx.lineWidth = Math.max(1.5, p.r * 0.12); ctx.stroke();
    ctx.restore();
  }
  function sparkle(x, y, s) {
    ctx.save(); ctx.translate(x, y); ctx.fillStyle = 'rgba(255,255,255,.9)';
    ctx.beginPath(); ctx.moveTo(0, -s); ctx.lineTo(s * 0.18, 0); ctx.lineTo(0, s); ctx.lineTo(-s * 0.18, 0); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(-s, 0); ctx.lineTo(0, s * 0.18); ctx.lineTo(s, 0); ctx.lineTo(0, -s * 0.18); ctx.closePath(); ctx.fill();
    ctx.restore();
  }

  function drawFlower(f, x, y, t) {
    const { r, pal, petals } = f;
    ctx.save(); ctx.translate(x, y); ctx.rotate(f.rot + t * f.spin);
    ctx.globalAlpha = 0.55 + f.depth * 0.6;
    for (let i = 0; i < petals; i++) {
      ctx.save(); ctx.rotate((i / petals) * Math.PI * 2);
      const g = ctx.createLinearGradient(0, 0, 0, -r);
      g.addColorStop(0, pal[1]); g.addColorStop(1, pal[0]);
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.bezierCurveTo(r * 0.55, -r * 0.25, r * 0.45, -r * 0.95, 0, -r);
      ctx.bezierCurveTo(-r * 0.45, -r * 0.95, -r * 0.55, -r * 0.25, 0, 0);
      ctx.fill();
      ctx.restore();
    }
    ctx.fillStyle = pal[2]; ctx.beginPath(); ctx.arc(0, 0, r * 0.22, 0, 7); ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.beginPath(); ctx.arc(-r * 0.07, -r * 0.07, r * 0.08, 0, 7); ctx.fill();
    ctx.restore();
  }

  let last = 0;
  function frame(ms) {
    const t = reduce ? 0 : ms / 1000;
    if (currentTheme() !== mode) build();
    const scroll = activeScroll() - state.OS.off * 0.3;
    ctx.clearRect(0, 0, W, H);
    if (mode === 'dark') {
      for (const s of stars) {
        const y = wrapY(s.y, scroll, s.depth);
        if (y < -5 || y > H + 5) continue;
        const a = 0.35 + 0.45 * (0.5 + 0.5 * Math.sin(t * s.tw + s.phase));
        ctx.fillStyle = `rgba(255,255,255,${a})`;
        ctx.fillRect(s.x * W, y, s.s, s.s);
      }
      for (const p of items) {
        const y = wrapY(p.y, scroll, p.depth) + Math.sin(t * p.speed + p.phase) * p.amp;
        if (y < -p.r * 3 || y > H + p.r * 3) continue;
        const x = p.x * W + Math.cos(t * p.speed * 0.7 + p.phase) * p.amp * 0.8;
        drawPlanet(p, x, y, t);
      }
    } else {
      for (const s of stars) {
        const y = wrapY(s.y + t * 6, scroll, s.depth);
        if (y < -10 || y > H + 10) continue;
        ctx.save(); ctx.translate(s.x * W + Math.sin(t * s.tw + s.phase) * 10, y); ctx.rotate(s.rot + t * s.tw);
        ctx.fillStyle = s.col + 'AA'; ctx.beginPath(); ctx.ellipse(0, 0, s.s, s.s * 0.55, 0, 0, 7); ctx.fill();
        ctx.restore();
      }
      for (const f of items) {
        const y = wrapY(f.y, scroll, f.depth) + Math.sin(t * f.speed + f.phase) * f.amp;
        if (y < -f.r * 2 || y > H + f.r * 2) continue;
        const x = f.x * W + Math.cos(t * f.speed * 0.8 + f.phase) * f.amp;
        drawFlower(f, x, y, t);
      }
    }
    if (!reduce || ms - last > 0) requestAnimationFrame(frame);
    last = ms;
  }

  function rebuild() { resize(); build(); }
  new ResizeObserver(rebuild).observe(cv);
  rebuild();
  if (reduce) { $('chatView').addEventListener('scroll', () => frame(0), { passive: true, capture: true }); $('listScroll').addEventListener('scroll', () => frame(0), { passive: true }); frame(0); }
  else requestAnimationFrame(frame);
  matchMedia('(prefers-color-scheme: dark)').addEventListener?.('change', () => {
    let saved = null; try { saved = localStorage.getItem('gk_theme'); } catch {}
    if (!saved) { root.setAttribute('data-theme', matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); syncThemeBtn(); rebuild(); }
  });
  return { rebuild };
}
