"""Groq·Gemini 호출 (스트리밍). API 키는 서버 설정에서만 읽는다."""
from __future__ import annotations

import json
from typing import Iterator, Protocol

import requests

from schemas.chat import ChatMessage

PROVIDER_MODELS: dict[str, list[tuple[str, str]]] = {
    "groq": [
        ("openai/gpt-oss-120b", "GPT-OSS 120B (추천, 한국어 품질 좋음)"),
        ("llama-3.3-70b-versatile", "Llama 3.3 70B"),
        ("openai/gpt-oss-20b", "GPT-OSS 20B (빠름)"),
        ("llama-3.1-8b-instant", "Llama 3.1 8B (가장 빠름)"),
    ],
    "gemini": [
        ("gemini-3.8-flash", "Gemini 3.8 Flash (추천)"),
        ("gemini-3.5-flash-lite", "Gemini 3.5 Flash-Lite (가장 빠름)"),
        ("gemini-3.6-flash", "Gemini 3.6 Flash"),
        ("gemini-4-argon", "Gemini 4 Argon (가장 똑똑함, 느림)"),
    ],
}
PROVIDER_LABELS = {"groq": "Groq", "gemini": "Gemini"}


class LLMError(Exception):
    """AI 서비스 오류. code는 화면에서 안내 문구를 고르는 데 쓴다."""

    def __init__(self, message: str, code: str, status: int = 502):
        super().__init__(message)
        self.code = code
        self.status = status


class LLMClient(Protocol):
    def stream(self, model: str, system: str, messages: list[ChatMessage], temperature: float) -> Iterator[str]: ...


def _raise_for_status(r: requests.Response, label: str) -> None:
    if r.ok:
        return
    try:
        body = r.json()
        body = body[0] if isinstance(body, list) else body
        detail = body.get("error", {}).get("message", "")
    except Exception:
        detail = r.text[:200]
    s = r.status_code
    if s in (401, 403) or (s == 400 and "api key" in detail.lower()):
        raise LLMError(f"{label}에서 서버의 API 키를 거부했어요. backend/.env의 키를 확인해 주세요.", "bad_key", 502)
    if s == 429:
        raise LLMError(f"{label} 사용 한도에 걸렸어요. 잠시 후 다시 보내 주세요.", "rate_limited", 429)
    if s in (400, 404):
        raise LLMError(f"{label}에서 이 모델을 쓸 수 없어요. 설정에서 다른 모델을 골라 보세요. ({detail[:120]})", "bad_model", 400)
    raise LLMError(f"{label} 서버 오류 ({s}). 잠시 후 다시 시도해 주세요.", "upstream_error", 502)


def _sse_data(lines: Iterator[bytes]) -> Iterator[dict]:
    for raw in lines:
        line = raw.decode("utf-8", "replace").strip() if isinstance(raw, bytes) else raw.strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            return
        try:
            yield json.loads(data)
        except json.JSONDecodeError:
            continue


class GroqClient:
    URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str, timeout: float):
        self.api_key, self.timeout = api_key, timeout

    def stream(self, model: str, system: str, messages: list[ChatMessage], temperature: float) -> Iterator[str]:
        body = {
            "model": model, "stream": True, "temperature": temperature, "max_tokens": 1024,
            "messages": [{"role": "system", "content": system}] + [m.model_dump() for m in messages],
        }
        if model.startswith("openai/gpt-oss"):
            body["reasoning_effort"] = "low"
        try:
            r = requests.post(self.URL, json=body, stream=True, timeout=self.timeout,
                              headers={"Authorization": f"Bearer {self.api_key}"})
        except requests.RequestException as e:
            raise LLMError("Groq 서버에 연결하지 못했어요.", "network", 502) from e
        _raise_for_status(r, "Groq")
        for j in _sse_data(r.iter_lines()):
            text = (j.get("choices") or [{}])[0].get("delta", {}).get("content")
            if text:
                yield text


class GeminiClient:
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse"

    def __init__(self, api_key: str, timeout: float):
        self.api_key, self.timeout = api_key, timeout

    def stream(self, model: str, system: str, messages: list[ChatMessage], temperature: float) -> Iterator[str]:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
                         for m in messages],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 4096},
        }
        try:
            r = requests.post(self.URL.format(model=requests.utils.quote(model, safe="")), json=body, stream=True,
                              timeout=self.timeout, headers={"x-goog-api-key": self.api_key})
        except requests.RequestException as e:
            raise LLMError("Gemini 서버에 연결하지 못했어요.", "network", 502) from e
        _raise_for_status(r, "Gemini")
        for j in _sse_data(r.iter_lines()):
            parts = ((j.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
            text = "".join(p.get("text", "") for p in parts if not p.get("thought"))  # 생각 과정은 빼고
            if text:
                yield text
