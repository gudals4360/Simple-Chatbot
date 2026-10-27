"""교육장 근처 식당 검색 (질문에 맞는 가게를 골라 그럴깡 프롬프트에 넣는다)."""
from __future__ import annotations

import math
import re

from repositories.place_repository import PlaceRepository
from schemas.place import MenuItem, Place, PlaceHit

FOOD_RE = re.compile(
    r"(맛집|점심|저녁|아침|야식|밥|먹|식당|음식|메뉴|가격|얼마|카페|커피|라떼|빵|디저트|베이커리|회식|술|맥주|하이볼|"
    r"치킨|국밥|순대|해장|찌개|백반|분식|김밥|떡볶이|짜장|짬뽕|중식|중국집|일식|초밥|라멘|돈까스|돈가스|카츠|우동|소바|"
    r"국수|칼국수|냉면|고기|삼겹|갈비|곱창|막창|족발|보쌈|피자|버거|햄버거|샐러드|포케|쌀국수|마라|샤브|양꼬치|파스타|"
    r"브런치|샌드위치|혼밥|가성비|배고|간식)")

SYN: dict[str, list[str]] = {
    "중국집": ["중식", "중국요리", "짜장", "짬뽕"], "중식": ["중국요리", "짜장", "짬뽕"],
    "짜장": ["중식", "중국요리"], "짬뽕": ["중식", "중국요리"],
    "일식": ["일식", "초밥", "라멘", "돈까스", "덮밥", "소바", "우동"], "초밥": ["초밥", "스시"], "스시": ["초밥"],
    "돈가스": ["돈까스", "카츠"], "돈까스": ["돈까스", "카츠"], "카츠": ["돈까스", "카츠"],
    "국밥": ["국밥", "순대", "해장", "곰탕", "설렁탕"], "해장": ["해장", "국밥", "순대국"], "순대": ["순대"],
    "고기": ["고기", "삼겹", "갈비", "곱창", "막창", "한우"],
    "회식": ["고기", "삼겹", "갈비", "곱창", "주점", "포장마차", "양꼬치", "닭도리탕"],
    "한잔": ["주점", "호프", "포장마차", "술집", "하이볼"], "퇴근": ["주점", "호프", "포장마차", "술집"],
    "술": ["주점", "호프", "포장마차", "술집", "칵테일", "와인", "하이볼"], "맥주": ["호프", "주점", "치킨"],
    "2차": ["주점", "호프", "포장마차", "술집"],
    "카페": ["카페", "커피", "디저트", "베이커리"], "커피": ["카페", "커피"], "빵": ["베이커리", "빵", "베이글", "소금빵"],
    "디저트": ["디저트", "베이커리", "빙수"], "분식": ["분식", "김밥", "떡볶이"], "김밥": ["김밥", "분식"],
    "떡볶이": ["떡볶이", "분식"], "면": ["국수", "칼국수", "냉면", "라멘", "소바", "우동", "쌀국수"],
    "국수": ["국수", "칼국수"], "칼국수": ["칼국수", "수제비"], "찌개": ["찌개", "김치찌개", "부대찌개", "순두부"],
    "백반": ["백반", "한식", "정식"], "한식": ["한식", "백반", "찌개", "국밥"], "샐러드": ["샐러드", "포케"],
    "다이어트": ["샐러드", "포케", "오트밀"], "건강": ["샐러드", "포케", "두부"],
    "양식": ["양식", "파스타", "이탈리안", "스테이크", "피자"], "파스타": ["파스타", "이탈리안", "양식"],
    "베트남": ["베트남", "쌀국수"], "쌀국수": ["쌀국수", "베트남"], "치킨": ["치킨", "통닭", "닭강정"],
    "햄버거": ["햄버거", "버거"], "버거": ["햄버거", "버거"],
}
STOP = re.compile(r"^(점심|저녁|아침|맛집|추천|만원|천원|가격|얼마|어디|좋은|좋아|근처|가까운|가까|교육장|건물|식당|음식|"
                  r"메뉴|오늘|내일|먹을|먹고|먹기|싶어|알려|알려줘|해줘|있어|있나|있을|어때|가성비|저렴|이하|이내|정도|곳|"
                  r"사람|우리|같이|혼자|혼밥)")
GENERIC = re.compile(r"^(카페|커피|중식|분식|국밥|치킨|피자|국수|라멘|초밥|우동|스시|빵|김밥|순대|포차|식당|한식|일식|양식|술집|호프)$")
NON_MEAL = re.compile(r"(카페|커피|베이커리|디저트|빙수|주스|요거트|버블티|에스프레소|칵테일|와인|호프|술집|주점|포장마차|"
                      r"오뎅바|떡|꽈배기|전통찻집)")
PARTICLE = re.compile(r"(이랑|에서|으로|이나|에요|해요|은|는|이|가|을|를|도|만|집|요|좀)$")


def is_food_question(text: str) -> bool:
    return bool(FOOD_RE.search(text))


def price_limit(q: str) -> int:
    """'만원 이하', '8천원 이내' 같은 표현에서 가격 상한을 뽑는다. 없으면 0."""
    if re.search(r"만\s*원\s*(이하|이내|아래|미만|안쪽|대)", q) and not re.search(r"[0-9]\s*만", q):
        return 10000
    m = re.search(r"([0-9]+(?:[.,][0-9]+)?)\s*(천|만)?\s*원?\s*(이하|이내|아래|미만|안쪽|대|까지)", q)
    if not m:
        return 10000 if re.search(r"가성비|싼|저렴", q) else 0
    v = float(m.group(1).replace(",", ""))
    if m.group(2) == "만":
        v *= 10000
    elif m.group(2) == "천" or v < 100:
        v *= 1000
    return int(v)


def _terms(q: str) -> set[str]:
    terms: set[str] = set()
    for t in re.findall(r"[가-힣A-Za-z0-9]{2,}", q):
        base = PARTICLE.sub("", t)
        if len(base) >= 2 and not STOP.search(base):
            terms.add(base)
        for k, syns in SYN.items():
            if k in t:
                terms.update(syns)
    return terms


class PlaceService:
    def __init__(self, repo: PlaceRepository):
        self.repo = repo

    def search(self, q: str, limit: int = 15) -> list[PlaceHit]:
        terms = _terms(q)
        limit_price = price_limit(q)
        near = bool(re.search(r"가까|바로|코앞|같은 건물|1층", q))
        meal_only = bool(re.search(r"(점심|저녁|아침|밥|식사|한 끼|맛집|배고)", q)) and not re.search(
            r"(카페|커피|빵|디저트|술|맥주|호프|2차|하이볼|와인|칵테일)", q)

        scored: list[tuple[float, int, Place, list[MenuItem]]] = []
        for p in self.repo.all():
            head = p.name.split(" ")[0]
            name_hit = len(head) >= 2 and not GENERIC.match(head) and head in q
            s = 1000.0 if name_hit else 0.0
            hit = 0
            for t in terms:
                if t in p.category:
                    hit += 3
                elif t in p.name:
                    hit += 2
                elif any(t in m.name for m in p.menu):
                    hit += 2
            s += (150 if hit else 0) + min(hit, 6) * 5
            if meal_only and NON_MEAL.search(p.category):
                s -= 400
            menu = p.menu
            if limit_price:
                menu = [m for m in p.menu if m.price and m.price <= limit_price]
                if not menu and not name_hit:
                    s -= 500
            s += p.rating * math.log2(p.rating_count + 1) * 4
            s -= p.distance_m / (6 if near else 20)
            if not p.menu and not p.rating_count:
                s -= 30
            scored.append((s, hit, p, menu))

        any_hit = any(h > 0 for _, h, _, _ in scored)
        picked = [x for x in scored if not any_hit or x[1] > 0 or x[0] >= 1000]
        picked.sort(key=lambda x: x[0], reverse=True)
        return [PlaceHit(place=p, score=round(s, 1), matched_menu=menu) for s, _, p, menu in picked[:limit]]

    def context(self, q: str) -> str:
        """프롬프트에 넣을 [카카오맵 검색 결과] 텍스트."""
        hits = self.search(q)
        if not hits:
            return ""
        rows = []
        for h in hits:
            p = h.place
            rating = f"카카오맵 평점 {p.rating:g} ({p.rating_count}명)" if p.rating_count else "카카오맵 평점 없음"
            menu = ", ".join(f"{m.name} {m.price:,}원" if m.price else m.name for m in h.matched_menu) or "메뉴판 정보 없음"
            upd = f" (메뉴판 {p.menu_updated} 기준)" if p.menu_updated else ""
            rows.append(f"- {p.name} | {p.category} | 도보 약 {p.walk_minutes}분(직선 {p.distance_m}m) | {rating} | 메뉴: {menu}{upd}")
        return (f"[카카오맵 검색 결과] 이번 질문과 관련된 교육장 근처 가게 {len(hits)}곳 "
                f"(카카오맵 2026년 10월 27일 수집, 반경 800m 안 {self.repo.count()}곳 중)\n" + "\n".join(rows))

    def food_context(self, user_texts: list[str]) -> str:
        """마지막 질문(또는 최근 대화)이 음식 이야기일 때만 검색 결과를 만든다."""
        if not user_texts:
            return ""
        last = user_texts[-1]
        recent = " ".join(user_texts[-3:])
        if is_food_question(last):
            q = last
        elif is_food_question(recent):
            q = recent
        else:
            return ""
        return self.context(q)
