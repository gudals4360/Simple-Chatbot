"""API(라우터) 테스트: 실제 서버를 띄워 HTTP로 요청한다."""
from __future__ import annotations

import unittest

import requests
from helpers import FakeClient, LiveServer, fake_forecast, make_settings

from main import create_app
from services.llm_service import LLMError


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fake = FakeClient()
        app = create_app(make_settings(), client_factory=lambda p: cls.fake, weather_fetcher=fake_forecast)
        cls.live = LiveServer(app).__enter__()
        cls.api = cls.live.url + "/api"

    @classmethod
    def tearDownClass(cls):
        cls.live.__exit__(None, None, None)

    def setUp(self):
        self.fake.error = None
        self.fake.calls.clear()

    def test_health(self):
        j = requests.get(self.api + "/health", timeout=5).json()
        self.assertEqual(j["default_provider"], "groq")
        by_id = {p["id"]: p for p in j["providers"]}
        self.assertTrue(by_id["groq"]["configured"])
        self.assertFalse(by_id["gemini"]["configured"])
        self.assertNotIn("test-groq", str(j))  # 키는 절대 응답에 담지 않는다

    def test_rooms(self):
        rooms = requests.get(self.api + "/rooms", timeout=5).json()
        ids = [r["id"] for r in rooms]
        self.assertEqual(ids[:2], ["gk", "sky"])
        self.assertEqual(len(ids), 8)
        self.assertIn("donggyu", ids)
        persona = next(r for r in rooms if r["id"] == "jia")
        self.assertEqual(persona["kind"], "persona")
        self.assertIn("company", persona)
        self.assertNotIn("bio", persona)

    def test_places_search(self):
        r = requests.get(self.api + "/places/search", params={"q": "국밥"}, timeout=5)
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertGreater(j["total_places"], 600)
        self.assertTrue(j["results"])

    def test_places_search_requires_query(self):
        r = requests.get(self.api + "/places/search", timeout=5)
        self.assertEqual(r.status_code, 400)

    def test_weather(self):
        j = requests.get(self.api + "/weather", params={"q": "내일 부산"}, timeout=5).json()
        self.assertTrue(j["ok"])
        self.assertTrue(j["location"]["name"].startswith("부산"))

    def test_chat_streams_text(self):
        body = {"room_id": "gk", "messages": [{"role": "user", "content": "안녕하세요"}]}
        r = requests.post(self.api + "/chat", json=body, stream=True, timeout=5)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.headers["content-type"].startswith("text/plain"))
        self.assertEqual(r.content.decode("utf-8"), "안녕하세요!\n\n반가워요")

    def test_chat_bad_key_maps_status(self):
        self.fake.error = LLMError("키가 올바르지 않아요.", "bad_key", 401)
        body = {"room_id": "gk", "messages": [{"role": "user", "content": "안녕"}]}
        r = requests.post(self.api + "/chat", json=body, timeout=5)
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()["code"], "bad_key")

    def test_chat_validation(self):
        bad = [
            {"room_id": "gk", "messages": []},
            {"room_id": "gk", "messages": [{"role": "assistant", "content": "hi"}]},
            {"room_id": "gk", "messages": [{"role": "user", "content": "x" * 5000}]},
            {"room_id": "gk", "messages": [{"role": "user", "content": "hi"}], "provider": "openai"},
        ]
        for body in bad:
            r = requests.post(self.api + "/chat", json=body, timeout=5)
            self.assertEqual(r.status_code, 422, body)

    def test_chat_unknown_room(self):
        body = {"room_id": "nobody", "messages": [{"role": "user", "content": "안녕"}]}
        self.assertEqual(requests.post(self.api + "/chat", json=body, timeout=5).status_code, 404)

    def test_chat_not_json(self):
        r = requests.post(self.api + "/chat", data="hello", timeout=5)
        self.assertEqual(r.status_code, 400)


class NoKeyTest(unittest.TestCase):
    def test_chat_without_any_key(self):
        app = create_app(make_settings(groq_api_key=""), weather_fetcher=fake_forecast)
        with LiveServer(app) as live:
            health = requests.get(live.url + "/api/health", timeout=5).json()
            self.assertIsNone(health["default_provider"])
            body = {"room_id": "gk", "messages": [{"role": "user", "content": "안녕"}]}
            r = requests.post(live.url + "/api/chat", json=body, timeout=5)
            self.assertEqual(r.status_code, 503)
            self.assertEqual(r.json()["code"], "no_provider")


if __name__ == "__main__":
    unittest.main()
