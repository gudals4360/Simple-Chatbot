"""앱 설정.

API 키 같은 비밀 값은 코드에 쓰지 않고 환경 변수나 backend/.env 파일에서 읽는다.
.env는 .gitignore에 들어 있어서 GitHub에 올라가지 않는다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


def _load_dotenv(path: Path) -> None:
    """간단한 .env 로더 (python-dotenv 없이). 이미 설정된 환경 변수는 덮어쓰지 않는다."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    gemini_api_key: str
    default_provider: str
    groq_model: str
    gemini_model: str
    db_path: Path
    data_dir: Path
    knowledge_dir: Path
    frontend_dir: Path
    cors_origins: tuple[str, ...]
    llm_timeout: float
    weather_timeout: float

    def configured_providers(self) -> list[str]:
        out = []
        if self.groq_api_key:
            out.append("groq")
        if self.gemini_api_key:
            out.append("gemini")
        return out


@lru_cache
def get_settings() -> Settings:
    _load_dotenv(BASE_DIR / ".env")
    origins = os.getenv("CORS_ORIGINS", "")
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        default_provider=os.getenv("DEFAULT_PROVIDER", "groq"),
        groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        db_path=Path(os.getenv("DB_PATH", str(BASE_DIR / "app.db"))),
        data_dir=BASE_DIR / "data",
        knowledge_dir=BASE_DIR / "knowledge",
        frontend_dir=Path(os.getenv("FRONTEND_DIR", str(PROJECT_DIR / "frontend"))),
        cors_origins=tuple(o.strip() for o in origins.split(",") if o.strip()),
        llm_timeout=float(os.getenv("LLM_TIMEOUT", "60")),
        weather_timeout=float(os.getenv("WEATHER_TIMEOUT", "8")),
    )
