// 백엔드 API 호출. 화면은 AI 서비스(Groq·Gemini)에 직접 연결하지 않고 항상 이 서버를 거친다.
// 화면을 다른 주소에서 띄울 때는 index.html의 <meta name="api-base">에 서버 주소를 적는다.
const BASE = (document.querySelector('meta[name="api-base"]')?.content || '').replace(/\/$/, '') + '/api';

export class ApiError extends Error {
  constructor(message, { status = 0, code = 'network' } = {}) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request(path, options = {}, timeoutMs = 10000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(BASE + path, { ...options, signal: options.signal || ctrl.signal });
    if (!res.ok) {
      let body = {};
      try { body = await res.json(); } catch {}
      throw new ApiError(body.error || `서버 오류 (${res.status})`, { status: res.status, code: body.code || 'http_error' });
    }
    return res;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e.name === 'AbortError') throw new ApiError('서버 응답이 너무 오래 걸려요.', { code: 'timeout' });
    throw new ApiError('서버에 연결하지 못했어요.', { code: 'network' });
  } finally {
    clearTimeout(timer);
  }
}

export const getHealth = async () => (await request('/health')).json();
export const getRooms = async () => (await request('/rooms')).json();

/**
 * 답변을 글자 단위로 받는다.
 * @param {{room_id:string, messages:{role:string,content:string}[], provider?:string, model?:string, notes?:string}} body
 * @param {(fullText:string) => void} onText 지금까지 받은 전체 답변
 */
export async function streamChat(body, onText, { idleMs = 45000 } = {}) {
  const ctrl = new AbortController();
  let timer = setTimeout(() => ctrl.abort(), idleMs);
  try {
    const res = await request('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    }, idleMs + 1000);
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let full = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      clearTimeout(timer); timer = setTimeout(() => ctrl.abort(), idleMs);  // 글자가 오는 동안은 계속 기다림
      full += dec.decode(value, { stream: true });
      onText(full);
    }
    full += dec.decode();
    return full;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (e.name === 'AbortError') throw new ApiError('응답이 너무 오래 걸려요.', { code: 'timeout' });
    throw new ApiError('답변을 받는 중에 연결이 끊겼어요.', { code: 'network' });
  } finally {
    clearTimeout(timer);
  }
}
