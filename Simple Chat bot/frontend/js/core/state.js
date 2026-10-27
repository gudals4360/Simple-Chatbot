// 여러 화면 모듈이 함께 쓰는 현재 상태.
import { $ } from './dom.js';

export const state = {
  rooms: [],          // { def, el, history, lastDay, lastMe, unread, busy, preview }
  cur: null,          // 지금 열린 채팅방
  chat: null,         // 지금 열린 채팅방의 스크롤 요소
  view: 'list',       // 'list' | 'chat'
  OS: { off: 0 },     // 현재 오버스크롤 양(px). +는 위에서 당김, -는 아래에서 당김
  health: null,       // 서버 상태 (/api/health)
  provider: null,     // 'groq' | 'gemini'
  model: null,
  notes: '',
};

export const roomById = (id) => state.rooms.find((R) => R.def.id === id);

// 배경 패럴랙스가 따라갈 스크롤 위치
export function activeScroll() {
  return state.view === 'chat' && state.chat ? state.chat.scrollTop : $('listScroll').scrollTop;
}
