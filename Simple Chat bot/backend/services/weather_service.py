"""하늘깡 날씨 서비스 (Open-Meteo 예보, API 키 불필요)."""
from __future__ import annotations

import re
import time
from datetime import date, datetime
from typing import Callable

import requests

from schemas.weather import Location, WeatherReport

ACADEMY = Location(name="교육장(영등포 양평역 근처)", lat=37.5256, lon=126.8889)

# Open-Meteo의 지명 검색은 한글 정확도가 낮아서 주요 지역 좌표를 직접 정리했다.
_LOCS_RAW: list[tuple[str, str, float, float]] = [
    ("교육장", ACADEMY.name, ACADEMY.lat, ACADEMY.lon), ("학원", ACADEMY.name, ACADEMY.lat, ACADEMY.lon),
    ("양평역", ACADEMY.name, ACADEMY.lat, ACADEMY.lon), ("양평동", ACADEMY.name, ACADEMY.lat, ACADEMY.lon),
    ("영등포구청", ACADEMY.name, ACADEMY.lat, ACADEMY.lon),
    ("영등포", "서울 영등포", 37.5264, 126.8962), ("여의도", "서울 여의도", 37.5219, 126.9245),
    ("문래", "서울 문래동", 37.5172, 126.8962), ("당산", "서울 당산", 37.5345, 126.9020),
    ("선유도", "서울 선유도", 37.5434, 126.8996), ("마포", "서울 마포", 37.5663, 126.9019),
    ("망원", "서울 망원동", 37.5556, 126.9019), ("홍대", "서울 홍대", 37.5563, 126.9236),
    ("합정", "서울 합정", 37.5495, 126.9137), ("연남", "서울 연남동", 37.5622, 126.9252),
    ("성수", "서울 성수동", 37.5446, 127.0557), ("성동", "서울 성동구", 37.5634, 127.0369),
    ("강남", "서울 강남", 37.4979, 127.0276), ("서초", "서울 서초", 37.4837, 127.0324),
    ("송파", "서울 송파", 37.5145, 127.1059), ("잠실", "서울 잠실", 37.5133, 127.1001),
    ("종로", "서울 종로", 37.5730, 126.9794), ("광화문", "서울 광화문", 37.5759, 126.9768),
    ("명동", "서울 명동", 37.5636, 126.9827), ("용산", "서울 용산", 37.5326, 126.9905),
    ("이태원", "서울 이태원", 37.5345, 126.9946), ("은평", "서울 은평", 37.6027, 126.9291),
    ("불광", "서울 불광동", 37.6104, 126.9297), ("노원", "서울 노원", 37.6542, 127.0568),
    ("강서", "서울 강서", 37.5509, 126.8495), ("마곡", "서울 마곡", 37.5603, 126.8254),
    ("목동", "서울 목동", 37.5263, 126.8752), ("구로", "서울 구로", 37.4954, 126.8874),
    ("신림", "서울 신림", 37.4842, 126.9297), ("관악", "서울 관악", 37.4784, 126.9516),
    ("건대", "서울 건대입구", 37.5404, 127.0692), ("광진", "서울 광진", 37.5385, 127.0823),
    ("서울", "서울", 37.5665, 126.9780),
    ("판교", "성남 판교", 37.3947, 127.1112), ("분당", "성남 분당", 37.3827, 127.1189),
    ("성남", "성남", 37.4200, 127.1265), ("수원", "수원", 37.2636, 127.0286), ("용인", "용인", 37.2411, 127.1776),
    ("일산", "고양 일산", 37.6584, 126.7700), ("고양", "고양", 37.6584, 126.8320), ("부천", "부천", 37.5034, 126.7660),
    ("안양", "안양", 37.3943, 126.9568), ("광명", "광명", 37.4786, 126.8646),
    ("김포공항", "김포공항", 37.5587, 126.7945), ("김포", "김포", 37.6152, 126.7156),
    ("인천공항", "인천공항", 37.4602, 126.4407), ("송도", "인천 송도", 37.3826, 126.6566),
    ("인천", "인천", 37.4563, 126.7052), ("의정부", "의정부", 37.7381, 127.0337), ("평택", "평택", 36.9921, 127.1129),
    ("파주", "파주", 37.7599, 126.7802), ("가평", "가평", 37.8315, 127.5105), ("양평군", "경기 양평군", 37.4917, 127.4876),
    ("춘천", "춘천", 37.8813, 127.7298), ("강릉", "강릉", 37.7519, 128.8761), ("속초", "속초", 38.2070, 128.5918),
    ("원주", "원주", 37.3422, 127.9202), ("평창", "평창", 37.3705, 128.3900), ("양양", "양양", 38.0754, 128.6190),
    ("청주", "청주", 36.6424, 127.4890), ("천안", "천안", 36.8151, 127.1139), ("세종", "세종", 36.4800, 127.2890),
    ("대전", "대전", 36.3504, 127.3845), ("전주", "전주", 35.8242, 127.1480), ("군산", "군산", 35.9676, 126.7369),
    ("광주", "광주", 35.1595, 126.8526), ("목포", "목포", 34.8118, 126.3922), ("여수", "여수", 34.7604, 127.6622),
    ("순천", "순천", 34.9506, 127.4872), ("대구", "대구", 35.8714, 128.6014), ("경주", "경주", 35.8562, 129.2247),
    ("포항", "포항", 36.0190, 129.3435), ("안동", "안동", 36.5684, 128.7294), ("울산", "울산", 35.5384, 129.3114),
    ("해운대", "부산 해운대", 35.1631, 129.1635), ("광안리", "부산 광안리", 35.1532, 129.1187),
    ("서면", "부산 서면", 35.1578, 129.0600), ("부산", "부산", 35.1796, 129.0756), ("창원", "창원", 35.2280, 128.6811),
    ("통영", "통영", 34.8544, 128.4331), ("거제", "거제", 34.8806, 128.6211),
    ("서귀포", "제주 서귀포", 33.2541, 126.5600), ("제주", "제주", 33.4996, 126.5312), ("울릉", "울릉도", 37.4844, 130.9057),
]
LOCATIONS: list[tuple[str, Location]] = sorted(
    ((k, Location(name=n, lat=la, lon=lo)) for k, n, la, lo in _LOCS_RAW), key=lambda x: -len(x[0]))

WMO = {
    0: "맑음", 1: "대체로 맑음", 2: "구름 조금", 3: "흐림", 45: "안개", 48: "짙은 안개",
    51: "약한 이슬비", 53: "이슬비", 55: "강한 이슬비", 56: "어는 이슬비", 57: "강한 어는 이슬비",
    61: "약한 비", 63: "비", 65: "강한 비", 66: "어는 비", 67: "강한 어는 비",
    71: "약한 눈", 73: "눈", 75: "강한 눈", 77: "싸락눈", 80: "약한 소나기", 81: "소나기", 82: "강한 소나기",
    85: "약한 눈 소나기", 86: "강한 눈 소나기", 95: "뇌우", 96: "우박을 동반한 뇌우", 99: "강한 우박 뇌우",
}
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]  # date.weekday() 순서


def is_snow(c: int) -> bool:
    return c in (71, 73, 75, 77, 85, 86)


def is_rain(c: int) -> bool:
    return 51 <= c <= 67 or 80 <= c <= 82 or c >= 95


def find_location(text: str) -> Location | None:
    for key, loc in LOCATIONS:
        if key in text:
            return loc
    return None


def outfit(t: float) -> str:
    """기온별 옷차림 (일반적으로 많이 쓰는 기준)."""
    if t >= 28: return "민소매, 반팔, 반바지, 린넨 옷"
    if t >= 23: return "반팔, 얇은 셔츠, 반바지나 면바지"
    if t >= 20: return "얇은 가디건, 긴팔 티, 면바지, 청바지"
    if t >= 17: return "얇은 니트, 맨투맨, 가디건, 청바지"
    if t >= 12: return "자켓, 가디건, 야상, 청바지, 스타킹"
    if t >= 9: return "트렌치코트, 자켓, 니트, 야상"
    if t >= 5: return "코트, 가죽자켓, 히트텍, 니트"
    return "패딩, 두꺼운 코트, 목도리, 장갑, 기모 옷"


def umbrella(prob: float, total: float, codes: list[int]) -> str:
    if any(is_snow(c) for c in codes) and (prob >= 40 or total >= 0.5):
        return "눈 예보 → 우산 챙기고 미끄러운 길 조심"
    if prob >= 60 or total >= 1:
        return "우산 꼭 챙기기"
    if prob >= 30 or any(is_rain(c) for c in codes):
        return "접이식 우산 하나 가방에 넣어 두기"
    return "우산 필요 없음"


def pick_days(text: str, days: list[str]) -> list[int]:
    if re.search(r"이번 ?주(?!말)|일주일|주간|다음 ?주(?!말)", text):
        return list(range(len(days)))
    idx: list[int] = []
    if "모레" in text:
        idx.append(2)
    elif "내일" in text:
        idx.append(1)
    if re.search(r"주말|토요일|일요일", text):
        for i, d in enumerate(days):
            wd = date.fromisoformat(d).weekday()
            if ((wd == 5 and "일요일" not in text) or (wd == 6 and "토요일" not in text)) and len(idx) < 2 and i not in idx:
                idx.append(i)
    return idx or [0]


ForecastFetcher = Callable[[Location], dict]


class WeatherService:
    URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout: float = 8.0, fetcher: ForecastFetcher | None = None):
        self.timeout = timeout
        self._fetch = fetcher or self._fetch_open_meteo
        self._cache: dict[tuple[float, float], tuple[float, dict]] = {}

    def _fetch_open_meteo(self, loc: Location) -> dict:
        params = {
            "latitude": loc.lat, "longitude": loc.lon, "timezone": "Asia/Seoul", "forecast_days": 7,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "hourly": "temperature_2m,apparent_temperature,precipitation_probability,weather_code",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,"
                     "precipitation_sum,precipitation_probability_max,uv_index_max,wind_speed_10m_max",
        }
        r = requests.get(self.URL, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def forecast(self, loc: Location) -> dict:
        key = (loc.lat, loc.lon)
        hit = self._cache.get(key)
        if hit and time.time() - hit[0] < 600:  # 10분 캐시
            return hit[1]
        data = self._fetch(loc)
        self._cache[key] = (time.time(), data)
        return data

    def report(self, text: str, earlier_texts: list[str] | None = None, now: datetime | None = None) -> WeatherReport:
        """질문 문장에서 지역·날짜를 찾아 [날씨 데이터] 요약을 만든다.
        지역이 없으면 이전 질문에서 말한 지역, 그것도 없으면 교육장 기준."""
        loc = find_location(text)
        if loc is None:
            for t in reversed(earlier_texts or []):
                loc = find_location(t)
                if loc:
                    break
        loc = loc or ACADEMY
        now = now or datetime.now()
        try:
            f = self.forecast(loc)
        except Exception:  # 네트워크 오류 등
            return WeatherReport(location=loc, ok=False, text=(
                f"[날씨 데이터]\n불러오기 실패 ({loc.name}). 인터넷 연결 문제일 수 있어. "
                "지금은 날씨를 알 수 없다고 솔직하게 말해."))
        return WeatherReport(location=loc, ok=True, text=self._summarize(f, loc, text, now))

    @staticmethod
    def _summarize(f: dict, loc: Location, text: str, now: datetime) -> str:
        d, h = f["daily"], f["hourly"]
        days = pick_days(text, d["time"])
        lines = [f"[날씨 데이터] 지역: {loc.name} / Open-Meteo 예보 / 조회 시각: {now.month}월 {now.day}일 {now:%H:%M}"]
        c = f.get("current")
        if 0 in days and c:
            lines.append(f"- 지금: {WMO.get(c['weather_code'], '정보 없음')}, 기온 {c['temperature_2m']}°C "
                         f"(체감 {c['apparent_temperature']}°C), 습도 {c['relative_humidity_2m']}%, 바람 {c['wind_speed_10m']}km/h")
        for i in days:
            day = d["time"][i]
            dd = date.fromisoformat(day)
            label = {0: "오늘", 1: "내일", 2: "모레"}.get(i, f"{dd.month}월 {dd.day}일")
            codes: list[int] = []

            def part(frm: int, to: int, name: str) -> str:
                xs = [k for k, t in enumerate(h["time"]) if t.startswith(day) and frm <= int(t[11:13]) <= to]
                if not xs:
                    return ""
                temps = [h["temperature_2m"][k] for k in xs]
                pp = max((h["precipitation_probability"][k] or 0) for k in xs)
                cs = [h["weather_code"][k] for k in xs]
                codes.extend(cs)
                main = WMO.get(max(set(cs), key=cs.count), "")
                return f"{name} {round(min(temps))}~{round(max(temps))}°C {main} 강수확률 {pp}%"

            parts = [p for p in (part(6, 9, "출근길(6~9시)"), part(12, 15, "낮(12~15시)"), part(18, 21, "퇴근길(18~21시)")) if p]
            tmax, tmin = d["temperature_2m_max"][i], d["temperature_2m_min"][i]
            prob = d["precipitation_probability_max"][i] or 0
            total = d["precipitation_sum"][i] or 0
            codes.append(d["weather_code"][i])
            avg, gap = (tmax + tmin) / 2, tmax - tmin
            uv, wind = d["uv_index_max"][i], d["wind_speed_10m_max"][i]
            lines.append(f"- {label} ({WEEKDAYS[dd.weekday()]}요일): {WMO.get(d['weather_code'][i], '정보 없음')}, "
                         f"최저 {tmin}°C / 최고 {tmax}°C (체감 {d['apparent_temperature_min'][i]}~{d['apparent_temperature_max'][i]}°C), "
                         f"강수확률 최대 {prob}%, 예상 강수량 {total}mm, 자외선 지수 {uv}, 최대 풍속 {wind}km/h")
            if parts:
                lines.append("  · " + " / ".join(parts))
            gap_note = f" / 일교차 {gap:.0f}°C로 커서 아침저녁용 겉옷 필수" if gap >= 10 else ""
            lines.append(f"  · 옷차림 기준(평균 {avg:.1f}°C): {outfit(avg)}{gap_note}")
            extra = (" / 자외선 강함 → 선크림·모자" if uv >= 6 else "") + (" / 바람 강함" if wind >= 30 else "")
            lines.append(f"  · 우산: {umbrella(prob, total, codes)}{extra}")
        return "\n".join(lines)
