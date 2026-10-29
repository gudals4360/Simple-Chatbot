// 말풍선 그리기: 날짜 구분선, 내 메시지, 상대 메시지(입력 중 표시·오류 포함), 읽음 표시.
import { esc, fmt, fmtDate, fmtTime, scrollDown, splitParas } from '../core/dom.js';
import { state } from '../core/state.js';
import { setPreview, updateLists } from './rooms.js';

function dayDivider(R, now) {
  const d = fmtDate(now);
  if (d !== R.lastDay) {
    R.lastDay = d;
    const el = document.createElement('div');
    el.className = 'divider'; el.textContent = d;
    R.el.appendChild(el);
  }
}

export function addMe(R, text, image = null) {
  const now = new Date(); dayDivider(R, now);
  const minute = fmtTime(now);
  // 같은 분에 연달아 보내면 시간은 마지막 말풍선에만 표시 (카카오톡처럼)
  if (R.lastMe && R.lastMe.minute === minute && R.el.lastElementChild === R.lastMe.row) {
    R.lastMe.row.querySelector('.time')?.remove();
  }
  const row = document.createElement('div');
  row.className = 'row me';
  row.innerHTML = `<div class="col"><div class="line"><div class="bubble">${fmt(text)}</div>
    <div class="meta"><span class="unread">1</span><span class="time">${minute}</span></div></div></div>`;
  R.el.appendChild(row);
  if(image){const photo=document.createElement('img');photo.src=image;photo.alt='보낸 사진';photo.className='chat-photo';row.querySelector('.bubble').prepend(photo);}
  R.lastMe = { row, minute };
  setPreview(R, text);
  scrollDown(R.el);
}

export function botGroup(R) {
  const now = new Date(); dayDivider(R, now);
  const row = document.createElement('div');
  row.className = 'row bot';
  row.innerHTML = `<div class="avatar">${R.def.avatarSvg}</div><div class="col"><div class="name">${esc(R.def.name)}</div><div class="bubbles"></div></div>`;
  R.el.appendChild(row);
  R.lastMe = null;
  const box = row.querySelector('.bubbles');
  box.style.display = 'flex'; box.style.flexDirection = 'column'; box.style.gap = '4px'; box.style.alignItems = 'flex-start';
  const seen = () => state.view === 'chat' && state.cur === R;
  return {
    typing() { if(box.querySelector('[data-typing]'))return; box.insertAdjacentHTML('beforeend', `<div class="line" data-typing><div class="bubble"><span class="typing" role="status" aria-label="입력 중"><span></span><span></span><span></span></span></div></div>`); scrollDown(R.el); },
    sendPart(text) {
      box.querySelector('[data-typing]')?.remove();
      const line=document.createElement('div');line.className='line';
      line.innerHTML=`<div class="bubble">${fmt(text)}</div><div class="meta"><span>${fmtTime(new Date())}</span></div>`;
      box.append(line);scrollDown(R.el);setPreview(R,text);
      if(!seen()){R.unread++;updateLists();}
    },
    render(text, done) {
      const paras = splitParas(text);
      if (!paras.length) return;
      box.innerHTML = paras.map((p, i) => {
        const last = i === paras.length - 1;
        return `<div class="line"><div class="bubble${i ? ' cont' : ''}">${fmt(p)}</div>${last && done ? `<div class="meta"><span>${fmtTime(new Date())}</span></div>` : ''}</div>`;
      }).join('');
      scrollDown(R.el);
      if (done) { setPreview(R, paras[paras.length - 1]); if (!seen()) { R.unread += paras.length; updateLists(); } }
    },
    error(title, body, withBtn) {
      box.innerHTML = `<div class="line"><div class="bubble error"><div class="err-title">${esc(title)}</div>${esc(body)}${withBtn ? '<br><button class="inline-btn" data-open-settings>설정 열기</button>' : ''}</div><div class="meta"><span>${fmtTime(new Date())}</span></div></div>`;
      scrollDown(R.el);
      setPreview(R, title); if (!seen()) { R.unread += 1; updateLists(); }
    },
  };
}

export function markRead(R) { R.el.querySelectorAll('.unread').forEach((u) => u.remove()); }

export function greetRoom(R) { if (R.def.kind === 'persona' || !R.def.hello) return; botGroup(R).render(R.def.hello, true); }
