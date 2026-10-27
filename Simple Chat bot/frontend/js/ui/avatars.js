// 프로필 그림 (오리지널 캐릭터 SVG). 페르소나는 서버가 준 옵션(머리 모양·색)으로 그린다.
export const MANAGER_AVATAR = `<svg viewBox="0 0 40 40" aria-hidden="true">
  <rect width="40" height="40" fill="#FFD9A8"/>
  <path d="M7 40c1-8 6-12 13-12s12 4 13 12z" fill="#3C4A5C"/>
  <path d="M17 28l3 5 3-5" fill="#FEE500"/>
  <circle cx="20" cy="18" r="9.5" fill="#FFE8CC"/>
  <path d="M10.4 17c0-6 4.2-9.6 9.6-9.6s9.6 3.6 9.6 9.6c-2-3.4-5.4-4.8-9.6-4.6-2 .1-3.6-1-4.4-2.2-.4 2.8-2.6 5.4-5.2 6.8z" fill="#2B2B2B"/>
  <circle cx="16.6" cy="19" r="1.3" fill="#2B2B2B"/><circle cx="23.4" cy="19" r="1.3" fill="#2B2B2B"/>
  <path d="M17.4 22.8c1.6 1.4 3.6 1.4 5.2 0" stroke="#2B2B2B" stroke-width="1.2" fill="none" stroke-linecap="round"/>
  <circle cx="14.6" cy="21.6" r="1.4" fill="#FFB3A1" opacity=".8"/><circle cx="25.4" cy="21.6" r="1.4" fill="#FFB3A1" opacity=".8"/>
</svg>`;

export const WEATHER_AVATAR = `<svg viewBox="0 0 40 40" aria-hidden="true">
  <rect width="40" height="40" fill="#BFE3FF"/>
  <g stroke="#FFC23D" stroke-width="1.6" stroke-linecap="round"><path d="M28 5.5v2.4M33.6 7.8l-1.7 1.7M36 13.4h-2.4M22.4 7.8l1.7 1.7"/></g>
  <circle cx="28" cy="13.4" r="4.4" fill="#FFD25C"/>
  <path d="M10.5 31c-3.6 0-6-2.6-6-5.6 0-3 2.3-5.4 5.3-5.6.8-4 4.2-6.8 8.4-6.8 3.8 0 7 2.4 8.1 5.8 3.6.1 6.3 2.9 6.3 6.3 0 3.4-2.8 5.9-6.3 5.9z" fill="#FFFFFF"/>
  <circle cx="16.6" cy="24.4" r="1.25" fill="#2B2B2B"/><circle cx="23.4" cy="24.4" r="1.25" fill="#2B2B2B"/>
  <path d="M18.2 27.6c1.2 1 2.6 1 3.8 0" stroke="#2B2B2B" stroke-width="1.1" fill="none" stroke-linecap="round"/>
  <circle cx="14.4" cy="26.6" r="1.3" fill="#FFB3A1" opacity=".75"/><circle cx="25.6" cy="26.6" r="1.3" fill="#FFB3A1" opacity=".75"/>
  <path d="M30.5 33.5c0-2.6 2-4.6 4.5-4.6s4.5 2 4.5 4.6z" fill="#6C8CFF"/><path d="M35 33.5v3.2c0 .9-.6 1.4-1.3 1.4" stroke="#4A5BA8" stroke-width=".9" fill="none" stroke-linecap="round"/>
</svg>`;

export function makeAvatar(o) {
  const hair = {
    long: `<path d="M10.4 19c-.2-6.8 4.1-11.1 9.6-11.1s9.8 4.3 9.6 11.1c-1.6-3.8-4.4-6-7.6-6.4-1.2 2-4.6 3.6-8.6 3.8-1.4.7-2.4 1.6-3 2.6z" fill="${o.hair}"/>`,
    short: `<path d="M10.6 17.5c0-6 4.2-9.6 9.4-9.6s9.4 3.6 9.4 9.6c-1.8-3-5-4.4-9.4-4.4s-7.6 1.4-9.4 4.4z" fill="${o.hair}"/>`,
    ponytail: `<path d="M10.5 18c0-6.3 4.2-10.2 9.5-10.2S29.5 11.7 29.5 18c-2-3.6-5.4-5-9.5-5s-7.5 1.4-9.5 5z" fill="${o.hair}"/><path d="M28.5 12c4 1 5 6 3.4 10.5-1-2.6-2.4-4-4.3-4.6z" fill="${o.hair}"/>`,
    messy: `<path d="M10.4 18.5c-.6-6.6 3.8-10.8 9.6-10.8s10.2 4.2 9.6 10.8c-1-1.8-2.2-3-3.6-3.6l-1.2 2.2-1.6-3-2 2.6-1.4-3-2 2.8-1.6-2.6-1.6 2.6-1.4-2c-1.6.8-2.6 2.2-3 4z" fill="${o.hair}"/>`,
    bob: `<path d="M9.8 23c-1.2-9 3.4-15 10.2-15s11.4 6 10.2 15h-3c.6-5-.6-8.6-3-9.8-2 1.4-5.8 2.2-10 2-.8 2-1 4.6-.6 7.8z" fill="${o.hair}"/>`
  }[o.style] || '';
  const glasses = o.glasses ? `<g fill="none" stroke="#2B2B2B" stroke-width="1"><circle cx="16.4" cy="19.2" r="2.4"/><circle cx="23.6" cy="19.2" r="2.4"/><path d="M18.8 19.2h2.4"/></g>` : '';
  return `<svg viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" fill="${o.bg}"/>
    ${o.style === 'long' ? `<path d="M9.5 20 8.5 33h23l-1-13z" fill="${o.hair}"/>` : ''}
    <path d="M7 40c1-8 6-12 13-12s12 4 13 12z" fill="${o.shirt}"/>
    <circle cx="20" cy="18.5" r="9.5" fill="${o.skin}"/>${hair}
    <circle cx="16.6" cy="19.2" r="1.25" fill="#2B2B2B"/><circle cx="23.4" cy="19.2" r="1.25" fill="#2B2B2B"/>${glasses}
    <path d="M17.6 23.2c1.5 1.2 3.3 1.2 4.8 0" stroke="#2B2B2B" stroke-width="1.1" fill="none" stroke-linecap="round"/>
    <circle cx="14.8" cy="22" r="1.3" fill="#FFB3A1" opacity=".7"/><circle cx="25.2" cy="22" r="1.3" fill="#FFB3A1" opacity=".7"/></svg>`;
}

export function avatarFor(room) {
  if (room.kind === 'manager') return MANAGER_AVATAR;
  if (room.kind === 'weather') return WEATHER_AVATAR;
  return makeAvatar(room.avatar || {});
}
