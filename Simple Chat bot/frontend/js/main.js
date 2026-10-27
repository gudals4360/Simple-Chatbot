// 앱 시작점: 서버 상태와 채팅방 목록을 받아 화면을 만들고 각 기능을 연결한다.
import { $ } from './core/dom.js';
import { state } from './core/state.js';
import { forgetLegacyKeys } from './core/storage.js';
import { getHealth, getRooms } from './api/client.js';
import { initTheme } from './effects/theme.js';
import { initScene } from './effects/scene.js';
import { enableOverscroll } from './effects/overscroll.js';
import { initChipsScroll } from './effects/chips-scroll.js';
import { buildRooms, initRoomNavigation, routeFromHash, showView } from './ui/rooms.js';
import { initComposer, setStatusIssue } from './ui/chat.js';
import { applySavedChoices, initSettings, openSheet } from './ui/settings.js';

async function start() {
  forgetLegacyKeys();
  const scene = initScene();
  initTheme(() => scene.rebuild());
  initChipsScroll();
  enableOverscroll($('listScroll'));
  initRoomNavigation();
  initComposer();
  initSettings();

  try {
    const [health, rooms] = await Promise.all([getHealth(), getRooms()]);
    state.health = health;
    buildRooms(rooms);
    state.rooms.forEach((R) => enableOverscroll(R.el));
    applySavedChoices();
    routeFromHash();
    if (health.providers.some((p) => p.configured)) setStatusIssue('');
    else { setStatusIssue('서버 키 설정 필요'); openSheet(); }
  } catch {
    state.health = null;
    showView('list');
    $('roomList').innerHTML = `<div class="pane-label" style="line-height:1.6">서버에 연결하지 못했어요.<br>
      터미널에서 <b>python backend/main.py</b>를 실행한 뒤 <b>http://127.0.0.1:8000</b>으로 열어 주세요.</div>`;
    setStatusIssue('서버 연결 안 됨');
    openSheet();
  }
}

start();
