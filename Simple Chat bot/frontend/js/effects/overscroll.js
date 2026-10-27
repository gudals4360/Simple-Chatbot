// 오버스크롤 · 러버 밴드 · 스트레치 · 바운스 (세로 스크롤 영역용)
// 끝까지 스크롤한 뒤 더 당기면 저항감 있게 늘어나고, 놓으면 스프링처럼 살짝 튕겨 돌아온다.
import { $, clearSelection } from '../core/dom.js';
import { state } from '../core/state.js';

const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const C = 0.55;                                            // 러버 밴드 저항 계수 (iOS와 비슷한 값)
const rubber = (x, d) => (1 - 1 / (x * C / d + 1)) * d;    // 당긴 거리 → 실제로 늘어나는 거리
const unrubber = (y, d) => { const r = Math.min(Math.abs(y) / d, 0.98); return (d * (1 / (1 - r) - 1)) / C; };

export function enableOverscroll(el) {
  if (reduceMotion) return;
  const sceneEl = $('scene');
  let raw = 0, off = 0, vel = 0, raf = 0, wheelTimer = 0;
  let touching = false, mouseDown = false, moved = 0, lastY = 0, lastT = 0, dragV = 0;
  let lastSt = el.scrollTop, lastStT = performance.now(), userAt = 0;
  const H = () => el.clientHeight || 1;
  const maxScroll = () => Math.max(0, el.scrollHeight - el.clientHeight);
  const atTop = () => el.scrollTop <= 0;
  const atBottom = () => el.scrollTop >= maxScroll() - 1;

  // 화면에 반영: 러버 밴드(이동) + 스트레치(늘어남) + 배경 스트레치
  function apply(o) {
    off = o;
    const a = Math.abs(o), h = H();
    if (a < 0.15) {
      el.style.transform = ''; sceneEl.style.transform = ''; state.OS.off = 0; return;
    }
    const origin = o > 0 ? '50% 0%' : '50% 100%';
    const k = Math.min(a / h, 0.6);
    el.style.transformOrigin = origin;
    el.style.transform = `translateY(${(o * 0.55).toFixed(2)}px) scaleY(${(1 + k * 0.16).toFixed(4)})`;
    sceneEl.style.transformOrigin = origin;
    sceneEl.style.transform = `scaleY(${(1 + k * 0.1).toFixed(4)})`;
    state.OS.off = o;
  }
  function setRaw(r) { raw = r; apply(Math.sign(r) * rubber(Math.abs(r), H())); }

  // 손을 놓으면 스프링으로 돌아오며 살짝 튕김(바운스)
  function release(v0 = 0) {
    raw = 0; vel = v0; cancelAnimationFrame(raf);
    const step = () => {
      vel += -0.085 * off;   // 스프링 복원력
      vel *= 0.7;            // 감쇠 (값이 작을수록 덜 튕김)
      const n = off + vel;
      if (Math.abs(n) < 0.25 && Math.abs(vel) < 0.25) { apply(0); vel = 0; return; }
      apply(n); raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }
  function grab() { cancelAnimationFrame(raf); raw = off ? Math.sign(off) * unrubber(off, H()) : 0; vel = 0; }

  // 공통 드래그 처리 (터치·마우스)
  function dragBy(dy, e) {
    const now = performance.now();
    dragV = dy / Math.max(1, now - lastT); lastT = now; userAt = now;
    if (raw !== 0 || (atTop() && dy > 0) || (atBottom() && dy < 0)) {
      let r = raw + dy;
      if ((raw > 0 && r < 0) || (raw < 0 && r > 0)) r = 0;
      setRaw(r);
      if (e && e.cancelable) e.preventDefault();
      return true;
    }
    return false;
  }

  // 터치
  el.addEventListener('touchstart', (e) => { touching = true; grab(); lastY = e.touches[0].clientY; lastT = performance.now(); userAt = lastT; }, { passive: true });
  el.addEventListener('touchmove', (e) => {
    if (!touching) return;
    const y = e.touches[0].clientY; const dy = y - lastY; lastY = y;
    dragBy(dy, e);
  }, { passive: false });
  const touchEnd = () => { if (!touching) return; touching = false; if (off) release(); };
  el.addEventListener('touchend', touchEnd); el.addEventListener('touchcancel', touchEnd);

  // 마우스 드래그 (데스크톱에서도 폰처럼 끌어서 스크롤)
  el.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'mouse' || e.button !== 0) return;
    if (e.target.closest('input, textarea, select, .bubble, .inline-btn')) return;
    e.preventDefault(); // 끌 때 새 글자 선택이 생기지 않도록
    clearSelection();   // 대신 기존 선택(파란색)은 직접 지움 — 브라우저가 해 주던 일
    mouseDown = true; moved = 0; grab(); lastY = e.clientY; lastT = performance.now(); userAt = lastT;
    el.style.scrollBehavior = 'auto'; el.classList.add('dragging');
  });
  window.addEventListener('pointermove', (e) => {
    if (!mouseDown) return;
    const dy = e.clientY - lastY; lastY = e.clientY; moved += Math.abs(dy);
    if (moved > 4 && !el.hasPointerCapture?.(e.pointerId)) { try { el.setPointerCapture(e.pointerId); } catch {} }
    if (!dragBy(dy, null)) el.scrollTop -= dy;
  });
  window.addEventListener('pointerup', () => {
    if (!mouseDown) return; mouseDown = false; el.style.scrollBehavior = ''; el.classList.remove('dragging');
    if (off) release();
    else if (Math.abs(dragV) > 0.4) flick(dragV);
  });
  // 드래그한 뒤에는 클릭으로 처리하지 않음
  el.addEventListener('click', (e) => { if (moved > 6) { e.stopPropagation(); e.preventDefault(); moved = 0; } }, true);

  // 마우스로 휙 던졌을 때 관성 스크롤
  function flick(v) {
    let speed = -v * 16; // px/frame
    const step = () => {
      if (mouseDown || touching) return;
      const before = el.scrollTop;
      el.scrollTop += speed; speed *= 0.94;
      if (el.scrollTop === before && Math.abs(speed) > 2) { release(Math.max(-14, Math.min(14, -speed * 0.3))); return; }
      if (Math.abs(speed) > 0.5) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  // 휠·트랙패드: 끝에서 더 굴리면 늘어나고, 멈추면 튕겨 돌아옴
  el.addEventListener('wheel', (e) => {
    userAt = performance.now();
    const dy = -e.deltaY * (e.deltaMode === 1 ? 16 : 1);
    if (raw !== 0 || (atTop() && dy > 0) || (atBottom() && dy < 0)) {
      e.preventDefault(); cancelAnimationFrame(raf);
      let r = raw + dy * 0.6;
      if ((raw > 0 && r < 0) || (raw < 0 && r > 0)) r = 0;
      setRaw(r);
      clearTimeout(wheelTimer); wheelTimer = setTimeout(() => release(), 90);
    }
  }, { passive: false });

  // 빠르게 스크롤하다 끝에 부딪히면 튕기기 (관성 바운스)
  el.addEventListener('scroll', () => {
    const now = performance.now(), st = el.scrollTop;
    const v = (st - lastSt) / Math.max(1, now - lastStT); // px/ms
    if (!touching && !mouseDown && off === 0 && now - userAt < 1500) {
      if (st <= 0 && v < -0.8) release(Math.min(-v * 5, 16));
      else if (st >= maxScroll() - 1 && v > 0.8) release(-Math.min(v * 5, 16));
    }
    lastSt = st; lastStT = now;
  }, { passive: true });
}
