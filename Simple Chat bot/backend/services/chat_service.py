"""대화 처리: 방 종류 확인 → 필요한 정보(맛집·날씨) 붙이기 → 프롬프트 → AI 스트리밍."""
from __future__ import annotations

from typing import Callable, Iterator

from config import Settings
from repositories.persona_repository import PersonaRepository
from schemas.chat import ChatRequest
from services.llm_service import PROVIDER_LABELS, PROVIDER_MODELS, GeminiClient, GroqClient, LLMClient, LLMError
from services.place_service import PlaceService
from services.prompt_service import PromptService
from services.room_service import RoomService
from services.weather_service import WeatherService

ClientFactory = Callable[[str], LLMClient]


class ChatService:
    def __init__(self, settings: Settings, rooms: RoomService, personas: PersonaRepository, prompts: PromptService,
                 places: PlaceService, weather: WeatherService, client_factory: ClientFactory | None = None):
        self.settings = settings
        self.rooms = rooms
        self.personas = personas
        self.prompts = prompts
        self.places = places
        self.weather = weather
        self.client_factory = client_factory or self._default_client

    def _default_client(self, provider: str) -> LLMClient:
        s = self.settings
        if provider == "groq":
            return GroqClient(s.groq_api_key, s.llm_timeout)
        return GeminiClient(s.gemini_api_key, s.llm_timeout)

    def resolve_provider(self, requested: str | None) -> str:
        configured = self.settings.configured_providers()
        if not configured:
            raise LLMError("서버에 AI API 키가 설정되지 않았어요. backend/.env에 GROQ_API_KEY 또는 GEMINI_API_KEY를 넣어 주세요.",
                           "no_provider", 503)
        if requested:
            if requested not in configured:
                raise LLMError(f"서버에 {PROVIDER_LABELS[requested]} 키가 없어요. 다른 서비스를 골라 주세요.", "provider_unavailable", 400)
            return requested
        return self.settings.default_provider if self.settings.default_provider in configured else configured[0]

    def resolve_model(self, provider: str, requested: str | None) -> str:
        allowed = [m for m, _ in PROVIDER_MODELS[provider]]
        if requested in allowed:
            return requested
        default = self.settings.groq_model if provider == "groq" else self.settings.gemini_model
        return default if default in allowed else allowed[0]

    def build_system_prompt(self, req: ChatRequest) -> tuple[str, float]:
        kind = self.rooms.kind_of(req.room_id)
        if kind is None:
            raise LLMError("없는 채팅방이에요.", "unknown_room", 404)
        user_texts = [m.content for m in req.messages if m.role == "user"]
        if kind == "manager":
            return self.prompts.manager(req.notes, self.places.food_context(user_texts)), 0.6
        if kind == "weather":
            report = self.weather.report(user_texts[-1], user_texts[:-1])
            return self.prompts.weather(report.text), 0.6
        persona = self.personas.get(req.room_id)
        return self.prompts.persona_prompt(persona), 0.85

    def stream_reply(self, req: ChatRequest) -> Iterator[str]:
        """첫 글자가 나오기 전의 오류(키, 모델, 방)는 LLMError로 올라간다."""
        provider = self.resolve_provider(req.provider)
        model = self.resolve_model(provider, req.model)
        system, temperature = self.build_system_prompt(req)
        client = self.client_factory(provider)
        yield from client.stream(model, system, req.messages[-20:], temperature)
