// 빠른 질문 목록: 좌우 스크롤 + 약한 러버 밴드·바운스
import { $, clearSelection } from '../core/dom.js';

export function initChipsScroll() {
  const el = $('chips');
  const motion = !matchMedia('(prefers-reduced-motion: reduce)').matches;
  const C = 0.35;                                            // 세로보다 뻣뻣하게(덜 늘어나게)
  const rubber = (x, d) => (1 - 1 / (x * C / d + 1)) * d;
  const W = () => el.clientWidth || 1;
  const maxScroll = () => Math.max(0, el.scrollWidth - el.clientWidth);
  const atStart = () => el.scrollLeft <= 0;
  const atEnd = () => el.scrollLeft >= maxScroll() - 1;
  let raw = 0, off = 0, vel = 0, raf = 0, wheelTimer = 0;
  let down = false, touching = false, moved = 0, lastX = 0, lastY = 0, lastT = 0, dragV = 0, axis = '';
  let lastSl = 0, lastSlT = performance.now(), userAt = 0;

  function apply(o) {
    off = o;
    el.style.transform = Math.abs(o) < 0.15 ? '' : `translateX(${(o * 0.5).toFixed(2)}px)`;
  }
  function setRaw(r) { raw = r; if (motion) apply(Math.sign(r) * rubber(Math.abs(r), W() * 0.5)); }
  function release(v0 = 0) {
    raw = 0; vel = motion ? v0 : 0; cancelAnimationFrame(raf);
    if (!motion) { apply(0); return; }
    const step = () => {
      vel += -0.1 * off; vel *= 0.62;          // 강한 감쇠: 거의 튕기지 않고 부드럽게 복귀
      const n = off + vel;
      if (Math.abs(n) < 0.2 && Math.abs(vel) < 0.2) { apply(0); vel = 0; return; }
      apply(n); raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }
  function dragBy(dx) {
    const now = performance.now();
    dragV = dx / Math.max(1, now - lastT); lastT = now; userAt = now;
    if (raw !== 0 || (atStart() && dx > 0) || (atEnd() && dx < 0)) {
      let r = raw + dx;
      if ((raw > 0 && r < 0) || (raw < 0 && r > 0)) r = 0;
      setRaw(r); return true;
    }
    el.scrollLeft -= dx; return false;
  }
  function flick(v) {
    let speed = -v * 16;
    const step = () => {
      if (down || touching) return;
      const before = el.scrollLeft;
      el.scrollLeft += speed; speed *= 0.93;
      if (el.scrollLeft === before && Math.abs(speed) > 2) { release(Math.max(-6, Math.min(6, -speed * 0.2))); return; }
      if (Math.abs(speed) > 0.5) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // 마우스로 끌기
  el.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'mouse' || e.button !== 0) return;
    e.preventDefault(); clearSelection();
    down = true; moved = 0; cancelAnimationFrame(raf); raw = 0; lastX = e.clientX; lastT = performance.now();
  });
  window.addEventListener('pointermove', (e) => {
    if (!down) return;
    const dx = e.clientX - lastX; lastX = e.clientX; moved += Math.abs(dx);
    if (moved > 4) el.classList.add('dragging');
    dragBy(dx);
  });
  window.addEventListener('pointerup', () => {
    if (!down) return; down = false; el.classList.remove('dragging');
    if (raw || off) release(); else if (Math.abs(dragV) > 0.3) flick(dragV);
  });
  el.addEventListener('click', (e) => { if (moved > 6) { e.stopPropagation(); e.preventDefault(); moved = 0; } }, true);

  // 터치: 좌우로 움직일 때만 끝에서 늘어남
  el.addEventListener('touchstart', (e) => {
    touching = true; axis = ''; cancelAnimationFrame(raf); raw = 0;
    lastX = e.touches[0].clientX; lastY = e.touches[0].clientY; lastT = performance.now(); userAt = lastT;
  }, { passive: true });
  el.addEventListener('touchmove', (e) => {
    if (!touching) return;
    const x = e.touches[0].clientX, y = e.touches[0].clientY;
    const dx = x - lastX, dy = y - lastY; lastX = x; lastY = y;
    if (!axis) axis = Math.abs(dx) >= Math.abs(dy) ? 'x' : 'y';
    if (axis !== 'x') return;
    const now = performance.now(); dragV = dx / Math.max(1, now - lastT); lastT = now; userAt = now;
    if (raw !== 0 || (atStart() && dx > 0) || (atEnd() && dx < 0)) {
      let r = raw + dx;
      if ((raw > 0 && r < 0) || (raw < 0 && r > 0)) r = 0;
      setRaw(r); if (e.cancelable) e.preventDefault();
    }
  }, { passive: false });
  const tEnd = () => { if (!touching) return; touching = false; if (raw || off) release(); };
  el.addEventListener('touchend', tEnd); el.addEventListener('touchcancel', tEnd);

  // 휠: 세로 휠도 좌우 스크롤로, 끝에서는 살짝 늘어남
  el.addEventListener('wheel', (e) => {
    const d = (Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY) * (e.deltaMode === 1 ? 16 : 1);
    if (!d) return;
    e.preventDefault(); userAt = performance.now();
    if (raw !== 0 || (atStart() && d < 0) || (atEnd() && d > 0)) {
      cancelAnimationFrame(raf);
      let r = raw - d * 0.4;
      if ((raw > 0 && r < 0) || (raw < 0 && r > 0)) r = 0;
      setRaw(r);
      clearTimeout(wheelTimer); wheelTimer = setTimeout(() => release(), 90);
    } else {
      el.scrollLeft += d;
    }
  }, { passive: false });

  // 빠르게 밀다가 끝에 닿으면 아주 살짝 튕김
  el.addEventListener('scroll', () => {
    const now = performance.now(), sl = el.scrollLeft;
    const v = (sl - lastSl) / Math.max(1, now - lastSlT);
    if (!down && !touching && off === 0 && now - userAt < 1200) {
      if (sl <= 0 && v < -0.8) release(Math.min(-v * 3, 6));
      else if (sl >= maxScroll() - 1 && v > 0.8) release(-Math.min(v * 3, 6));
    }
    lastSl = sl; lastSlT = now;
  }, { passive: true });
}
