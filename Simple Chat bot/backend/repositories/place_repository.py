"""식당·카페 데이터 접근."""
from __future__ import annotations

import json
import sqlite3

from schemas.place import MenuItem, Place


class PlaceRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._cache: list[Place] | None = None

    def all(self) -> list[Place]:
        """전체 목록 (664곳 정도라 메모리에 올려 두고 검색한다)."""
        if self._cache is None:
            rows = self.conn.execute(
                "SELECT id, name, category, distance_m, rating, rating_count, menu_json, menu_updated "
                "FROM places ORDER BY distance_m").fetchall()
            self._cache = [
                Place(id=r["id"], name=r["name"], category=r["category"], distance_m=r["distance_m"],
                      rating=r["rating"], rating_count=r["rating_count"], menu_updated=r["menu_updated"],
                      menu=[MenuItem(name=n, price=p) for n, p in json.loads(r["menu_json"])])
                for r in rows
            ]
        return self._cache

    def count(self) -> int:
        return len(self.all())
