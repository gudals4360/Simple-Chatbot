// 설정 시트: AI 서비스·모델 선택, 과정 운영 메모, 대화 지우기.
// API 키는 서버(backend/.env)에만 있으므로 여기서는 입력받지 않는다.
import { $, esc } from '../core/dom.js';
import { state } from '../core/state.js';
import { store, KEYS } from '../core/storage.js';
import { resetRooms } from './rooms.js';

let sheetProv = null;
const providers = () => state.health?.providers || [];
const providerById = (id) => providers().find((p) => p.id === id);

// 저장해 둔 선택값을 서버가 실제로 지원하는 값으로 맞춘다.
export function applySavedChoices() {
  state.notes = store.get(KEYS.notes) || '';
  const saved = store.get(KEYS.provider);
  const usable = providers().filter((p) => p.configured).map((p) => p.id);
  state.provider = usable.includes(saved) ? saved : state.health?.default_provider || null;
  const P = providerById(state.provider);
  const m = P && store.get(KEYS.model(P.id));
  state.model = P ? (P.models.some(([id]) => id === m) ? m : P.default_model) : null;
}

function renderProviders() {
  const list = providers();
  const anyKey = list.some((p) => p.configured);
  $('sheetLead').textContent = anyKey
    ? '대화에 쓸 AI 서비스와 모델을 고를 수 있어요. 변경 사항은 이 브라우저에 저장돼요.'
    : '서버에 아직 AI 키가 없어요. 아래 안내대로 키를 넣고 서버를 다시 켜면 대화할 수 있어요.';
  $('serverInfo').innerHTML = !state.health
    ? '<b>서버에 연결하지 못했어요.</b><br>터미널에서 <code>python backend/main.py</code>로 서버를 켠 뒤 이 페이지를 새로 고쳐 주세요.'
    : `<div class="providers">${list.map((p) => `<div class="row-p"><span>${esc(p.label)}</span>${p.configured ? '<span class="on">서버에 연결됨</span>' : '<span class="off">키 없음</span>'}</div>`).join('')}</div>
       <div class="hint" style="margin-top:6px">API 키는 서버의 <code>backend/.env</code>에만 있고 브라우저로는 전달되지 않아요.${anyKey ? '' : ' <code>.env.example</code>을 복사해 <code>.env</code>를 만들고 GROQ_API_KEY 또는 GEMINI_API_KEY를 넣어 주세요.'}</div>`;
  document.querySelectorAll('#provSeg [data-prov]').forEach((b) => {
    const P = providerById(b.dataset.prov);
    b.disabled = !P?.configured;
    b.setAttribute('aria-checked', String(b.dataset.prov === sheetProv));
  });
  const P = providerById(sheetProv);
  $('model').disabled = !P?.configured;
  $('model').innerHTML = P ? P.models.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join('') : '<option>서버에 키가 필요해요</option>';
  if (P) $('model').value = sheetProv === state.provider && state.model ? state.model : (store.get(KEYS.model(P.id)) || P.default_model);
}

export function openSheet(message) {
  sheetProv = state.provider || providers().find((p) => p.configured)?.id || 'groq';
  renderProviders();
  $('notes').value = state.notes;
  showMsg(message || '', message ? 'bad' : '');
  $('scrim').hidden = false;
  setTimeout(() => $('saveBtn').focus(), 50);
}

function closeSheet() { $('scrim').hidden = true; if (state.view === 'chat') $('msg').focus(); }
function showMsg(t, cls) { const el = $('sheetMsg'); el.textContent = t; el.className = 'msg-line ' + (cls || ''); }

export function initSettings() {
  $('provSeg').addEventListener('click', (e) => {
    const b = e.target.closest('[data-prov]'); if (!b || b.disabled || b.dataset.prov === sheetProv) return;
    sheetProv = b.dataset.prov; renderProviders(); showMsg('', '');
  });
  $('closeSheet').addEventListener('click', closeSheet);
  $('scrim').addEventListener('click', (e) => { if (e.target === $('scrim')) closeSheet(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('scrim').hidden) closeSheet(); });

  $('saveBtn').addEventListener('click', () => {
    const P = providerById(sheetProv);
    if (P?.configured) {
      state.provider = P.id; state.model = $('model').value;
      store.set(KEYS.provider, P.id);
      store.set(KEYS.model(P.id), state.model);
    }
    state.notes = $('notes').value;
    store.set(KEYS.notes, state.notes);
    closeSheet();
  });
  $('clearChat').addEventListener('click', () => { resetRooms(); showMsg('대화를 모두 지웠어요.', 'good'); });
}
