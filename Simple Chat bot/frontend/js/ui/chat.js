import { deliverReply, initConversationTools } from './conversation-tools.js';
// 채팅방 동작: 메시지 보내기 → 서버에서 답변 스트리밍 → 말풍선 갱신, 입력창, 공지, 연결 상태 표시.
import { $ } from '../core/dom.js';
import { state } from '../core/state.js';
import { streamChat } from '../api/client.js';
import { addMe, botGroup, markRead } from './messages.js';
import { openSheet } from './settings.js';

const READY = { manager: '상담 가능', weather: '날씨 알림 가능', persona: '대화 가능' };
let tools;
let statusIssue = '서버 연결 확인 중…';  // 비어 있으면 대화 가능

export function setStatusIssue(text) { statusIssue = text || ''; refreshStatus(); }

export function refreshStatus() {
  const ok = !statusIssue;
  $('status').classList.toggle('off', !ok);
  $('statusText').textContent = ok ? READY[state.cur?.def.kind] || '대화 가능' : statusIssue;
}

export function updateSend() {
  const has = $('msg').value.trim().length > 0 || !!state.cur?.attachment;
  const busy = !!state.cur?.busy;
  $('sendBtn').disabled = !has || busy;
  $('sendBtn').classList.toggle('on', has && !busy);
}

// 서버가 돌려준 오류 코드를 사람이 읽을 수 있는 안내로 바꾼다.
function explain(e) {
  switch (e.code) {
    case 'no_provider': return ['서버에 AI 키가 아직 없어요.', ' backend/.env 파일에 GROQ_API_KEY 또는 GEMINI_API_KEY를 넣고 서버를 다시 켜 주세요.', true, '서버 키 설정 필요'];
    case 'provider_unavailable': return ['이 AI 서비스는 서버에 키가 없어요.', ` ${e.message}`, true];
    case 'bad_key': return ['서버의 API 키가 올바르지 않아요.', ` ${e.message} backend/.env의 키를 확인해 주세요.`, false, 'API 키 확인 필요'];
    case 'rate_limited': return ['요청이 너무 많아요.', ' AI 서비스 사용 한도에 걸렸어요. 잠시 후 다시 보내 주세요.'];
    case 'bad_model': return ['모델 설정을 확인해 주세요.', ` ${e.message} 설정에서 다른 모델을 골라 보세요.`, true];
    case 'timeout': return ['응답이 너무 오래 걸려요.', ' 다시 보내 보거나 설정에서 더 빠른 모델을 골라 보세요.'];
    case 'network': return ['서버에 연결하지 못했어요.', ' 백엔드 서버(python backend/main.py)가 켜져 있는지 확인해 주세요.', false, '서버 연결 안 됨'];
    default: return [e.status ? `서버 오류 (${e.status})` : '오류가 생겼어요.', ` ${e.message || '잠시 후 다시 시도해 주세요.'}`];
  }
}

export async function ask(userText) {
  const R = state.cur;
  if (!R || R.busy) return;
  const image=R.attachment || null;
  if(image && !state.health?.providers?.some(p=>p.id==='gemini'&&p.configured)){
    if(!$('msg').value) $('msg').value=userText;
    window.alert('사진과 대화하려면 설정에서 Gemini 연결을 먼저 확인해 주세요.');return;
  }
  R.attachment=null;tools?.refresh();
  R.busy = true; updateSend();
  addMe(R, userText, image);
  R.history.push({ role: 'user', content: userText });
  R.history = R.history.slice(-39);

  const g = botGroup(R);
  setTimeout(() => markRead(R), 400);
  g.typing();

  try {
    let full = await streamChat({
      room_id: R.def.id,
      messages: R.history,
      provider: image ? 'gemini' : state.provider || undefined,
      image: image || undefined,
      model: image ? undefined : state.model || undefined,
      notes: R.def.kind === 'manager' ? state.notes : '',
    }, () => {});
    if (!full.trim()) full = '앗, 답변이 비어서 왔어요. 한 번만 다시 물어봐 주실래요?';
    await deliverReply(full, g);
    R.history.push({ role: 'assistant', content: full });
    setStatusIssue('');
  } catch (e) {
    R.history.pop();
    if(image){R.attachment=image;tools?.refresh();}
    const [title, body, withBtn, issue] = explain(e);
    g.error(title, body, withBtn);
    if (issue) setStatusIssue(issue);
  } finally {
    R.busy = false; updateSend();
  }
}

function toggleNotice() {
  const n = $('notice');
  n.setAttribute('aria-expanded', n.getAttribute('aria-expanded') === 'true' ? 'false' : 'true');
}

export function initComposer() {
  const msg = $('msg');
  tools=initConversationTools(()=>state.cur,updateSend);
  document.addEventListener('room-change',()=>tools.refresh());
  msg.addEventListener('input', () => { msg.style.height = 'auto'; msg.style.height = Math.min(msg.scrollHeight, 110) + 'px'; updateSend(); });
  msg.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); $('composer').requestSubmit(); }
  });
  $('composer').addEventListener('submit', (e) => {
    e.preventDefault();
    const t = msg.value.trim();
    if ((!t && !state.cur?.attachment) || state.cur?.busy) return;
    msg.value = ''; msg.style.height = 'auto'; updateSend();
    ask(t || '이 사진 봐요.');
  });
  $('chips').addEventListener('click', (e) => { const c = e.target.closest('.chip'); if (c) ask(c.textContent); });
  $('toggleChips').addEventListener('click', () => { $('chips').hidden = !$('chips').hidden; });
  $('chatView').addEventListener('click', (e) => { if (e.target.closest('[data-open-settings]')) openSheet(); });
  $('openSettings').addEventListener('click', () => openSheet());
  $('notice').addEventListener('click', () => { if (!window.getSelection().toString()) toggleNotice(); });
  $('notice').addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleNotice(); } });
}
