"""날씨 데이터 형식."""
from __future__ import annotations

from pydantic import BaseModel


class Location(BaseModel):
    name: str
    lat: float
    lon: float


class WeatherReport(BaseModel):
    location: Location
    ok: bool
    text: str  # 프롬프트에 넣는 [날씨 데이터] 요약
