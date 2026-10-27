"""페르소나 데이터 접근."""
from __future__ import annotations

import json
import sqlite3

from schemas.room import Company, Persona


class PersonaRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    @staticmethod
    def _to_model(r: sqlite3.Row) -> Persona:
        return Persona(
            id=r["id"], name=r["name"], age=r["age"], sex=r["sex"], job=r["job"], district=r["district"],
            education=r["education"], marital=r["marital"], family=r["family"], housing=r["housing"],
            summary=r["summary"], status=r["status"], style=r["style"], hello=r["hello"],
            chips=json.loads(r["chips_json"]), avatar=json.loads(r["avatar_json"]),
            company=Company(**json.loads(r["company_json"])), bio=r["bio"])

    def list(self) -> list[Persona]:
        rows = self.conn.execute("SELECT * FROM personas ORDER BY sort_order").fetchall()
        return [self._to_model(r) for r in rows]

    def get(self, persona_id: str) -> Persona | None:
        r = self.conn.execute("SELECT * FROM personas WHERE id = ?", (persona_id,)).fetchone()
        return self._to_model(r) if r else None
