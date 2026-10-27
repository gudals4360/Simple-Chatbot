"""테스트 공용 도구: 가짜 AI, 가짜 날씨, 임시 DB 설정, 실제 서버 띄우기."""
from __future__ import annotations

import socket
import sys
import tempfile
import threading
import time
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from config import Settings, get_settings  # noqa: E402
from schemas.chat import ChatMessage  # noqa: E402
from schemas.weather import Location  # noqa: E402
from services.llm_service import LLMError  # noqa: E402


def make_settings(**overrides) -> Settings:
    """실제 .env를 읽지 않고, 임시 폴더에 DB를 만드는 설정."""
    tmp = Path(tempfile.mkdtemp(prefix="gk-test-"))
    base = get_settings()
    values = dict(groq_api_key="test-groq", gemini_api_key="", default_provider="groq",
                  groq_model="openai/gpt-oss-120b", gemini_model="gemini-3.8-flash",
                  db_path=tmp / "test.db", cors_origins=(), llm_timeout=5, weather_timeout=1)
    values.update(overrides)
    return replace(base, **values)


class FakeClient:
    """AI 대신 정해진 답을 흘려보내고, 받은 프롬프트를 기록한다."""

    def __init__(self, chunks=("안녕하세요", "!\n\n", "반가워요"), error: LLMError | None = None):
        self.chunks = chunks
        self.error = error
        self.calls: list[dict] = []

    def stream(self, model: str, system: str, messages: list[ChatMessage], temperature: float):
        self.calls.append(dict(model=model, system=system, messages=messages, temperature=temperature))
        if self.error:
            raise self.error
        yield from self.chunks


def fake_forecast(loc: Location) -> dict:
    """Open-Meteo 응답과 같은 모양의 고정 예보 (7일, 매일 비 70%)."""
    start = date.today()
    days = [(start + timedelta(days=i)).isoformat() for i in range(7)]
    hours = [f"{d}T{h:02d}:00" for d in days for h in range(24)]
    n = len(days)
    return {
        "current": {"temperature_2m": 14.2, "apparent_temperature": 12.8, "relative_humidity_2m": 70,
                    "precipitation": 0.4, "weather_code": 61, "wind_speed_10m": 9.5},
        "hourly": {"time": hours, "temperature_2m": [12 + (i % 24) / 4 for i in range(len(hours))],
                   "apparent_temperature": [11] * len(hours), "precipitation_probability": [70] * len(hours),
                   "weather_code": [61] * len(hours)},
        "daily": {"time": days, "weather_code": [61] * n, "temperature_2m_max": [18.0] * n,
                  "temperature_2m_min": [9.0] * n, "apparent_temperature_max": [17.0] * n,
                  "apparent_temperature_min": [7.0] * n, "precipitation_sum": [6.5] * n,
                  "precipitation_probability_max": [70] * n, "uv_index_max": [3.1] * n,
                  "wind_speed_10m_max": [14.0] * n},
    }


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class LiveServer:
    """uvicorn을 별도 스레드로 띄워 실제 HTTP로 테스트한다 (httpx 없이도 동작)."""

    def __init__(self, app):
        import uvicorn

        self.port = free_port()
        config = uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="warning", lifespan="on")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def __enter__(self):
        self.thread.start()
        deadline = time.time() + 10
        while not self.server.started:
            if time.time() > deadline:
                raise RuntimeError("테스트 서버가 시작되지 않았어요.")
            time.sleep(0.05)
        return self

    def __exit__(self, *exc):
        self.server.should_exit = True
        self.thread.join(timeout=5)
