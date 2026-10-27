// 브라우저 저장소 (개인 설정만 저장. API 키는 서버에만 있고 여기에는 절대 저장하지 않는다)
// 사생활 보호 모드 등에서 저장소가 막혀도 앱이 멈추지 않도록 try/catch로 감싼다.
export const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  del(k) { try { localStorage.removeItem(k); } catch {} },
};

export const KEYS = { provider: 'gk_provider', model: (p) => `gk_model_${p}`, notes: 'gk_notes', theme: 'gk_theme' };

// 예전 한 파일 버전이 브라우저에 남긴 API 키는 더 이상 쓰지 않으므로 지운다.
export function forgetLegacyKeys() {
  for (const k of ['gk_groq_key', 'gk_gemini_key', 'gk_api_key']) {
    try { localStorage.removeItem(k); sessionStorage.removeItem(k); } catch {}
  }
}
