"""DB 테이블 구조 (SQLite).

- places:   교육장 근처 식당·카페 (카카오맵 2026-10-27 수집)
- personas: 대화 상대 페르소나 (합성 페르소나 데이터 기반)
"""

PLACES_TABLE = """
CREATE TABLE IF NOT EXISTS places (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    category      TEXT    NOT NULL DEFAULT '',
    distance_m    INTEGER NOT NULL,          -- 교육장에서 직선거리(m)
    rating        REAL    NOT NULL DEFAULT 0, -- 카카오맵 평점
    rating_count  INTEGER NOT NULL DEFAULT 0, -- 평가 수
    menu_json     TEXT    NOT NULL DEFAULT '[]', -- [["메뉴", 가격], ...]
    menu_updated  TEXT    NOT NULL DEFAULT ''    -- 메뉴판 갱신월 (YYYY-MM)
);
"""

PERSONAS_TABLE = """
CREATE TABLE IF NOT EXISTS personas (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    age           INTEGER NOT NULL,
    sex           TEXT NOT NULL,
    job           TEXT NOT NULL,
    district      TEXT NOT NULL,
    education     TEXT NOT NULL,
    marital       TEXT NOT NULL,
    family        TEXT NOT NULL,
    housing       TEXT NOT NULL,
    summary       TEXT NOT NULL,
    status        TEXT NOT NULL,
    style         TEXT NOT NULL,   -- 말투 설명 (프롬프트용, 화면에는 안 보냄)
    hello         TEXT NOT NULL,   -- 첫인사
    chips_json    TEXT NOT NULL,   -- 빠른 질문 목록
    avatar_json   TEXT NOT NULL,   -- 프로필 그림 옵션
    company_json  TEXT NOT NULL,   -- 회사 정보
    bio           TEXT NOT NULL,   -- 원본 데이터 프로필 (프롬프트용, 화면에는 안 보냄)
    sort_order    INTEGER NOT NULL DEFAULT 0
);
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_places_distance ON places(distance_m);",
]

ALL_STATEMENTS = [PLACES_TABLE, PERSONAS_TABLE, *INDEXES]
