"""채팅방 목록 (도우미 2명 + DB의 페르소나)."""
from __future__ import annotations

from repositories.persona_repository import PersonaRepository
from schemas.room import RoomInfo

MANAGER = RoomInfo(
    id="gk", kind="manager", name="그럴깡", sub="UXUI·PM 부트캠프 매니저",
    status="UXUI·PM 부트캠프 7기 모집 중 · 편하게 물어보세요",
    hello=("안녕하세요! 한국경제아카데미 UXUI·PM 부트캠프 매니저 그럴깡이에요 😊\n\n"
           "지금 **7기**를 모집하고 있어요. 12월 17일에 개강하고, 자부담금은 40만원이고, 교육 기간 동안 노트북도 빌려드려요.\n\n"
           "일정, 비용, 커리큘럼, 지원 방법, 취업 준비까지 궁금한 건 뭐든 편하게 물어봐 주세요.\n\n"
           "아래 빠른 질문을 눌러도 바로 답해 드릴게요!"),
    chips=["7기 언제 개강해요?", "자부담금이 얼마예요?", "커리큘럼이 궁금해요", "비전공자도 들을 수 있나요?",
           "노트북이랑 툴도 지원돼요?", "어떻게 지원해요?", "수업 시간과 장소는요?", "근처 점심 맛집 추천해 주세요",
           "오늘 점심 뭐 드셨어요?", "주말에 뭐 하세요?"],
)

WEATHER = RoomInfo(
    id="sky", kind="weather", name="하늘깡", sub="날씨·옷차림 알려주는 친구",
    status="우산 챙길지 고민될 땐 물어보세요 ☂️",
    hello=('안녕하세요! 날씨 담당 하늘깡이에요 🌤️\n\n"오늘 날씨 어때?", "내일 부산 우산 필요해?"처럼 물어보면 '
           "옷차림이랑 우산까지 챙겨 드릴게요 ☂️\n\n지역을 말하지 않으면 교육장(양평역 근처) 기준으로 알려 드려요."),
    chips=["오늘 날씨 어때요?", "퇴근길에 우산 필요해요?", "내일 뭐 입고 나가요?", "이번 주말 날씨는요?",
           "부산 날씨 알려줘", "이번 주 날씨 정리해 줘"],
)


class RoomService:
    def __init__(self, personas: PersonaRepository):
        self.personas = personas

    def list_rooms(self) -> list[RoomInfo]:
        rooms = [MANAGER, WEATHER]
        for p in self.personas.list():
            rooms.append(RoomInfo(
                id=p.id, kind="persona", name=p.name, sub=f"{p.age}세 · {p.job}", status=p.status, hello=p.hello,
                chips=p.chips, avatar=p.avatar, age=p.age, job=p.job, district=p.district, company=p.company))
        return rooms

    def kind_of(self, room_id: str) -> str | None:
        if room_id == MANAGER.id:
            return "manager"
        if room_id == WEATHER.id:
            return "weather"
        return "persona" if self.personas.get(room_id) else None
