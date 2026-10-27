// 라이트·다크 모드 전환 (처음 값은 index.html 맨 위의 짧은 스크립트가 깜빡임 없이 정한다)
import { store, KEYS } from '../core/storage.js';

export const root = document.documentElement;

export function currentTheme() { return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }

export function syncThemeBtn() {
  document.querySelectorAll('.theme-btn').forEach((b) =>
    b.setAttribute('aria-label', currentTheme() === 'dark' ? '라이트 모드로 바꾸기' : '다크 모드로 바꾸기'));
}

export function initTheme(onChange) {
  document.querySelectorAll('.theme-btn').forEach((b) => b.addEventListener('click', () => {
    const next = currentTheme() === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    store.set(KEYS.theme, next);
    syncThemeBtn();
    onChange?.();
  }));
  syncThemeBtn();
}
