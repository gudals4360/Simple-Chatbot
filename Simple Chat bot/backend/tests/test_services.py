"""서비스(비즈니스 로직) 단위 테스트."""
from __future__ import annotations

import unittest
from unittest.mock import patch
from datetime import datetime

from helpers import FakeClient, fake_forecast, make_settings

from main import build_services
from schemas.chat import ChatRequest
from services.llm_service import LLMError
from services.place_service import is_food_question, price_limit
from services.weather_service import ACADEMY, find_location, pick_days


class PlaceServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svc = build_services(make_settings(), weather_fetcher=fake_forecast)

    @classmethod
    def tearDownClass(cls):
        cls.svc.conn.close()

    def test_seeded_places(self):
        self.assertGreaterEqual(self.svc.places.repo.count(), 600)

    def test_food_question_detection(self):
        self.assertTrue(is_food_question("근처 점심 맛집 추천해 주세요"))
        self.assertFalse(is_food_question("7기 언제 개강해요?"))

    def test_price_limit(self):
        self.assertEqual(price_limit("만원 이하 점심"), 10000)
        self.assertEqual(price_limit("8천원 이하"), 8000)
        self.assertEqual(price_limit("국밥 추천"), 0)

    def test_search_by_name(self):
        hits = self.svc.places.search("차이나쿡", 5)
        self.assertTrue(hits)
        self.assertIn("차이나쿡", hits[0].place.name)

    def test_search_respects_price(self):
        hits = self.svc.places.search("만원 이하 점심", 10)
        self.assertTrue(hits)
        for h in hits[:5]:
            prices = [m.price for m in h.place.menu if m.price]
            self.assertTrue(prices and min(prices) <= 10000, h.place.name)

    def test_food_context_only_for_food(self):
        self.assertEqual(self.svc.places.food_context(["커리큘럼이 궁금해요"]), "")
        self.assertIn("[카카오맵 검색 결과]", self.svc.places.food_context(["근처 국밥 맛집"]))


class WeatherServiceTest(unittest.TestCase):
    def test_find_location(self):
        self.assertEqual(find_location("내일 부산 우산 필요해?").name.startswith("부산"), True)
        self.assertIsNone(find_location("오늘 날씨 어때?"))

    def test_pick_days(self):
        days = [f"2026-10-{d}" for d in range(27, 32)] + ["2026-11-01", "2026-11-02"]
        self.assertEqual(pick_days("오늘 날씨", days), [0])
        self.assertEqual(pick_days("내일 뭐 입어?", days), [1])
        self.assertEqual(len(pick_days("이번 주 날씨 정리해 줘", days)), 7)
        weekend = pick_days("이번 주말 날씨는요?", days)  # 2026-10-31(토), 11-01(일)
        self.assertEqual(weekend, [4, 5])

    def test_report_uses_academy_by_default(self):
        from services.weather_service import WeatherService
        r = WeatherService(fetcher=fake_forecast).report("오늘 우산 필요해?", now=datetime(2026, 10, 27, 9))
        self.assertTrue(r.ok)
        self.assertEqual(r.location, ACADEMY)
        self.assertIn("우산", r.text)

    def test_report_remembers_earlier_location(self):
        from services.weather_service import WeatherService
        r = WeatherService(fetcher=fake_forecast).report("내일은?", ["부산 날씨 알려줘"])
        self.assertTrue(r.location.name.startswith("부산"))

    def test_report_handles_network_error(self):
        from services.weather_service import WeatherService

        def broken(_):
            raise OSError("offline")
        r = WeatherService(fetcher=broken).report("오늘 날씨")
        self.assertFalse(r.ok)
        self.assertIn("불러오기 실패", r.text)


class ChatServiceTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeClient()
        self.svc = build_services(make_settings(), client_factory=lambda p: self.fake, weather_fetcher=fake_forecast)

    def tearDown(self):
        self.svc.conn.close()

    def req(self, room, text, **kw):
        return ChatRequest(room_id=room, messages=[{"role": "user", "content": text}], **kw)

    def test_manager_prompt_has_bootcamp_and_food(self):
        out = "".join(self.svc.chat.stream_reply(self.req("gk", "근처 점심 맛집 추천해 주세요", notes="7기 정원 20명")))
        self.assertEqual(out, "안녕하세요!\n\n반가워요")
        call = self.fake.calls[0]
        self.assertIn("자부담금", call["system"])
        self.assertIn("7기 정원 20명", call["system"])
        self.assertIn("[카카오맵 검색 결과]", call["system"])
        self.assertEqual(call["temperature"], 0.6)

    def test_weather_prompt_has_forecast(self):
        "".join(self.svc.chat.stream_reply(self.req("sky", "오늘 날씨 어때요?")))
        self.assertIn("[날씨 데이터]", self.fake.calls[0]["system"])

    def test_persona_prompt(self):
        "".join(self.svc.chat.stream_reply(self.req("seondong", "요즘 어떻게 지내세요?")))
        call = self.fake.calls[0]
        self.assertIn("최선동", call["system"])
        self.assertIn("구직", call["system"])
        self.assertEqual(call["temperature"], 0.85)

    def test_donggyu_profile_and_followup_history(self):
        messages = [{"role": "user" if i % 2 == 0 else "assistant",
                     "content": "저는 계단 없는 길이 좋아요." if i == 0 else "점심 이야기"}
                    for i in range(38)]
        messages.append({"role": "user", "content": "그때 기분은요?"})
        req = ChatRequest(room_id="donggyu", messages=messages)
        "".join(self.svc.chat.stream_reply(req))
        call = self.fake.calls[0]
        self.assertEqual(call["messages"], req.messages)
        self.assertIn(self.svc.chat.personas.get("donggyu").bio, call["system"])
        self.assertIn("이동규의 대화 호흡", call["system"])
        self.assertIn("합성 페르소나", call["system"])
        other, _ = self.svc.chat.build_system_prompt(self.req("seondong", "안녕"))
        self.assertNotIn("이동규의 대화 호흡", other)

    def test_unknown_model_falls_back(self):
        "".join(self.svc.chat.stream_reply(self.req("gk", "안녕", model="not-a-model")))
        self.assertEqual(self.fake.calls[0]["model"], "openai/gpt-oss-120b")

    def test_unknown_room(self):
        with self.assertRaises(LLMError) as cm:
            "".join(self.svc.chat.stream_reply(self.req("nobody", "안녕")))
        self.assertEqual(cm.exception.status, 404)

    def test_photo_requires_gemini(self):
        req = self.req("donggyu", "사진", provider="groq", image="data:image/jpeg;base64,/9j/2Q==")
        with self.assertRaises(LLMError) as cm:
            "".join(self.svc.chat.stream_reply(req))
        self.assertEqual(cm.exception.code, "image_provider")

    def test_gemini_receives_photo_with_last_user_message(self):
        from services.llm_service import GeminiClient
        req = self.req("donggyu", "사진", image="data:image/jpeg;base64,/9j/2Q==")
        with patch("services.llm_service.requests.post") as post:
            post.return_value.status_code = 200
            post.return_value.iter_lines.return_value = iter([])
            list(GeminiClient("test-key", 10).stream("test-model", "지침", req.messages, 0.85, image=req.image))
        parts = post.call_args.kwargs["json"]["contents"][-1]["parts"]
        self.assertEqual(parts[0], {"text": "사진"})
        self.assertEqual(parts[1]["inlineData"], {"mimeType": "image/jpeg", "data": "/9j/2Q=="})

    def test_provider_without_key(self):
        with self.assertRaises(LLMError) as cm:
            "".join(self.svc.chat.stream_reply(self.req("gk", "안녕", provider="gemini")))
        self.assertEqual(cm.exception.code, "provider_unavailable")


if __name__ == "__main__":
    unittest.main()
