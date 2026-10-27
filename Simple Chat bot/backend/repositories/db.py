"""SQLite 연결과 초기 데이터 넣기."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from models.tables import ALL_STATEMENTS


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection, data_dir: Path) -> None:
    """테이블을 만들고, 비어 있으면 data/ 폴더의 원본 데이터로 채운다."""
    for stmt in ALL_STATEMENTS:
        conn.execute(stmt)
    if conn.execute("SELECT COUNT(*) FROM places").fetchone()[0] == 0:
        seed_places(conn, data_dir / "kakao_places.tsv")
    if conn.execute("SELECT COUNT(*) FROM personas").fetchone()[0] == 0:
        seed_personas(conn, data_dir / "personas.json")
    conn.commit()


_MENU_RE = re.compile(r"^(?P<name>.+?):(?P<price>\d+)\s*(?:\((?P<note>.+)\))?$")


def parse_menu(text: str) -> list[list]:
    """"아메리카노:4500|라떼:4900 (24시간)" → [["아메리카노", 4500], ["라떼", 4900], ["24시간", 0]]"""
    items = []
    for part in filter(None, (p.strip() for p in (text or "").split("|"))):
        m = _MENU_RE.match(part)
        if m:
            items.append([m["name"].strip(), int(m["price"])])
            if m["note"]:
                items.append([m["note"].strip(), 0])
        else:  # 가격 없는 안내 문구 (예: "주문제작(픽업/택배)")
            items.append([part, 0])
    return items


def seed_places(conn: sqlite3.Connection, tsv_path: Path) -> None:
    rows = []
    for line in tsv_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        cols = (line.split("\t") + [""] * 7)[:7]
        name, cat, dist, rating, count, menu, upd = cols
        rows.append((name, cat, int(dist), float(rating or 0), int(count or 0),
                     json.dumps(parse_menu(menu), ensure_ascii=False), upd))
    conn.executemany(
        "INSERT INTO places (name, category, distance_m, rating, rating_count, menu_json, menu_updated) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)", rows)


def seed_personas(conn: sqlite3.Connection, json_path: Path) -> None:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    for i, p in enumerate(data):
        conn.execute(
            "INSERT INTO personas (id, name, age, sex, job, district, education, marital, family, housing, "
            "summary, status, style, hello, chips_json, avatar_json, company_json, bio, sort_order) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (p["id"], p["name"], p["age"], p["sex"], p["job"], p["district"], p["edu"], p["marital"],
             p["family"], p["housing"], p["summary"], p["status"], p["style"], p["hello"],
             json.dumps(p["chips"], ensure_ascii=False), json.dumps(p["av"], ensure_ascii=False),
             json.dumps(p["company"], ensure_ascii=False), p["bio"], i))
