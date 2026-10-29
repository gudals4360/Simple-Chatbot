// 채팅 목록·친구 목록·프로필·채팅방 전환과 뒤로 가기(주소 #chat-방이름).
import { $, esc, fmtTime } from '../core/dom.js';
import { state, roomById } from '../core/state.js';
import { avatarFor } from './avatars.js';
import { greetRoom, markRead } from './messages.js';
import { refreshStatus, updateSend } from './chat.js';
import { openSheet } from './settings.js';

const PLACEHOLDER = { manager: '메시지 입력', weather: '어디 날씨가 궁금하세요?' };
const TAG = { persona: '', weather: '<span class="ai-tag">날씨</span>', manager: '' };

// 서버가 준 방 정보(/api/rooms)로 채팅방 화면을 만든다.
export function buildRooms(defs) {
  const first = $('chat');
  state.rooms = defs.map((d, i) => {
    let el = i === 0 ? first : null;
    if (!el) {
      el = document.createElement('main');
      el.className = 'chat'; el.setAttribute('aria-live', 'polite'); el.hidden = true;
      $('chat').after(el);
    }
    el.dataset.room = d.id;
    const def = { ...d, avatarSvg: avatarFor(d) };
    return { def, el, history: [], lastDay: '', lastMe: null, unread: 0, busy: false, preview: { text: '', time: new Date(0) } };
  });
  state.rooms.forEach((R, i) => {
    greetRoom(R);
    R.preview.time = new Date(Date.now() - i * 60000);  // 처음 순서 유지
  });
  state.cur = state.rooms[0];
  state.chat = state.cur.el;
  updateLists();
}

export function resetRooms() {
  state.rooms.forEach((R) => { R.el.innerHTML = ''; R.history = []; R.lastDay = ''; R.lastMe = null; R.unread = 0; greetRoom(R); });
  updateLists();
}

export function setPreview(R, text) {
  R.preview = { text: String(text).replace(/\*\*/g, '').replace(/^[-*]\s+/gm, '').replace(/\s+/g, ' ').trim(), time: new Date() };
  updateLists();
}

function roomRow(R) {
  const n = R.unread > 99 ? '99+' : String(R.unread);
  return `<button type="button" class="room" data-room="${esc(R.def.id)}">
    <span class="avatar">${R.def.avatarSvg}</span>
    <span class="info"><span class="nm">${esc(R.def.name)}${TAG[R.def.kind]}</span><span class="pv">${esc(R.preview.text)}</span></span>
    <span class="side"><span>${R.preview.time.getTime() ? fmtTime(R.preview.time) : ''}</span><span class="badge"${R.unread ? '' : ' hidden'}>${n}</span></span>
  </button>`;
}

function friendRow(R) {
  return `<button type="button" class="room" data-profile="${esc(R.def.id)}">
    <span class="avatar">${R.def.avatarSvg}</span>
    <span class="info"><span class="nm">${esc(R.def.name)}${TAG[R.def.kind]}</span><span class="pv">${esc(R.def.status)}</span></span>
  </button>`;
}

export function updateLists() {
  if (!state.rooms.length) return;
  const sorted = [...state.rooms].sort((a, b) => b.preview.time - a.preview.time);
  $('roomList').innerHTML = sorted.map(roomRow).join('');
  $('friendGkWrap').innerHTML = state.rooms.filter((R) => R.def.kind !== 'persona').map(friendRow).join('');
  const ps = state.rooms.filter((R) => R.def.kind === 'persona');
  $('friendList').innerHTML = ps.map(friendRow).join('');
  $('friendCount').textContent = `친구 ${ps.length}`;
  const total = state.rooms.reduce((s, R) => s + R.unread, 0);
  $('tabBadge').textContent = total > 99 ? '99+' : String(total);
  $('tabBadge').hidden = !total;
}

function enterRoom(R) {
  state.cur = R; state.chat = R.el;
  state.rooms.forEach((x) => { x.el.hidden = x !== R; });
  $('roomName').textContent = R.def.name;
  $('roomSub').textContent = R.def.sub;
  $('notice').hidden = R.def.kind !== 'manager';
  $('chips').hidden = R.def.kind === 'persona';
  $('toggleChips').hidden = R.def.kind === 'persona';
  $('chips').innerHTML = R.def.kind === 'persona' ? '' : R.def.chips.map((c) => `<button class="chip">${esc(c)}</button>`).join('');
  $('chips').scrollLeft = 0;
  $('chatView').setAttribute('aria-label', `${R.def.name} 채팅방`);
  $('msg').placeholder = PLACEHOLDER[R.def.kind] || `${R.def.name}님에게 메시지 보내기`;
  R.unread = 0; markRead(R); updateLists(); updateSend(); refreshStatus();
}

export function showView(v, push) {
  state.view = v;
  $('listView').hidden = v !== 'list';
  $('chatView').hidden = v !== 'chat';
  if (v === 'chat') {
    $('profile').hidden = true;
    state.cur.unread = 0; updateLists();
    const el = state.chat;
    requestAnimationFrame(() => { el.style.scrollBehavior = 'auto'; el.scrollTop = el.scrollHeight; el.style.scrollBehavior = ''; });
    if (push) { try { window.history.pushState({ v: 'chat', room: state.cur.def.id }, '', '#chat-' + state.cur.def.id); } catch {} }
  }
}

export function openRoom(id, push = true) {
  const R = roomById(id); if (!R) return;
  enterRoom(R); showView('chat', push);
}

function openProfile(id) {
  const R = roomById(id); if (!R) return;
  const d = R.def;
  $('profAvatar').innerHTML = d.avatarSvg;
  $('profName').textContent = d.name;
  $('profStatus').textContent = d.status;
  $('profMeta').textContent = d.kind === 'weather' ? '날씨·옷차림 도우미 · Open-Meteo 예보 사용\nAI 챗봇'
    : d.kind === 'persona' ? `${d.age}세 · ${d.district}\n${d.company.company} · ${d.company.role}`
    : '한국경제아카데미 UXUI·PM 부트캠프 매니저 · AI 챗봇';
  $('profMeta').style.whiteSpace = 'pre-line';
  $('profChat').dataset.room = id;
  $('profile').hidden = false;
}

function showTab(t) {
  $('tabChats').setAttribute('aria-selected', String(t === 'chats'));
  $('tabFriends').setAttribute('aria-selected', String(t === 'friends'));
  $('paneChats').hidden = t !== 'chats';
  $('paneFriends').hidden = t !== 'friends';
  $('listTitle').textContent = t === 'chats' ? '채팅' : '친구';
}

export function routeFromHash() {
  const m = location.hash.match(/^#chat-([a-z0-9_-]+)$/);
  if (m && roomById(m[1])) openRoom(m[1], false); else showView('list');
}

export function initRoomNavigation() {
  $('listScroll').addEventListener('click', (e) => {
    const r = e.target.closest('[data-room]'); if (r) { openRoom(r.dataset.room); return; }
    const f = e.target.closest('[data-profile]'); if (f) openProfile(f.dataset.profile);
  });
  $('profChat').addEventListener('click', () => openRoom($('profChat').dataset.room));
  $('profileClose').addEventListener('click', () => { $('profile').hidden = true; });
  $('tabChats').addEventListener('click', () => showTab('chats'));
  $('tabFriends').addEventListener('click', () => showTab('friends'));
  $('openSettings2').addEventListener('click', () => openSheet());
  $('backBtn').addEventListener('click', () => {
    if (window.history.state && window.history.state.v === 'chat') window.history.back();
    else showView('list');
  });
  window.addEventListener('popstate', routeFromHash);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('profile').hidden) $('profile').hidden = true; });
}
