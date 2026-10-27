// 화면 다루기 공용 도구: 요소 찾기, 글자 안전 처리, 날짜·시간 표시.
export const $ = (id) => document.getElementById(id);

export const fmtTime = (d) => d.toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit' });
export const fmtDate = (d) => d.toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });

// HTML로 넣기 전에 특수문자를 바꿔서 글자가 코드로 실행되지 않게 한다.
export const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// AI 답변의 간단한 마크다운(**굵게**, 목록)을 말풍선용 HTML로 바꾼다.
export function fmt(text) {
  return esc(text.trim())
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .replace(/\n/g, '<br>');
}

// 빈 줄 하나 = 말풍선 하나
export const splitParas = (t) => t.split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean);

export const scrollDown = (el) => { el.scrollTop = el.scrollHeight; };

// 배경을 누르면 기존 글자 선택(파란색)을 지움.
// 끌어서 스크롤하려고 mousedown 기본 동작을 막은 곳에서는 브라우저가 대신 지워 주지 않기 때문.
export function clearSelection() {
  const sel = window.getSelection && window.getSelection();
  if (sel && !sel.isCollapsed) sel.removeAllRanges();
}
