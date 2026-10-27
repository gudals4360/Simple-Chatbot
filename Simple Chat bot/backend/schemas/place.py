"""식당·카페 데이터 형식."""
from __future__ import annotations

from pydantic import BaseModel, Field


class MenuItem(BaseModel):
    name: str
    price: int = 0  # 0이면 가격 정보 없음


class Place(BaseModel):
    id: int | None = None
    name: str
    category: str = ""
    distance_m: int
    rating: float = 0
    rating_count: int = 0
    menu: list[MenuItem] = Field(default_factory=list)
    menu_updated: str = ""

    @property
    def walk_minutes(self) -> int:
        """직선거리를 실제 걷는 시간으로 대략 환산 (우회 1.2배, 분당 80m)."""
        return max(1, round(self.distance_m * 1.2 / 80))


class PlaceHit(BaseModel):
    place: Place
    score: float
    matched_menu: list[MenuItem]


class PlaceSearchResponse(BaseModel):
    query: str
    total_places: int
    results: list[PlaceHit]
