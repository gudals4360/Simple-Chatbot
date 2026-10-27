"""채팅방·페르소나 데이터 형식."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Company(BaseModel):
    company: str
    about: str
    role: str
    place: str
    note: str = ""


class Persona(BaseModel):
    """DB에 저장된 페르소나 전체 정보 (프롬프트 생성용)."""
    id: str
    name: str
    age: int
    sex: str
    job: str
    district: str
    education: str
    marital: str
    family: str
    housing: str
    summary: str
    status: str
    style: str
    hello: str
    chips: list[str]
    avatar: dict
    company: Company
    bio: str


class RoomInfo(BaseModel):
    """화면에 보내는 채팅방 정보. 말투·원본 프로필처럼 화면에 필요 없는 건 빼고 보낸다."""
    id: str
    kind: Literal["manager", "weather", "persona"]
    name: str
    sub: str
    status: str
    hello: str
    chips: list[str] = Field(default_factory=list)
    avatar: dict | None = None  # 페르소나 프로필 그림 옵션 (도우미는 화면에 고정 그림)
    age: int | None = None
    job: str | None = None
    district: str | None = None
    company: Company | None = None


class ProviderInfo(BaseModel):
    id: Literal["groq", "gemini"]
    label: str
    configured: bool
    models: list[tuple[str, str]]
    default_model: str


class HealthResponse(BaseModel):
    ok: bool = True
    providers: list[ProviderInfo]
    default_provider: str | None
