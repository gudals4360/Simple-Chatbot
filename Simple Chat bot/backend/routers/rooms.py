"""GET /api/rooms — 채팅방 목록, GET /api/health — 서버·AI 서비스 상태."""
from __future__ import annotations

from starlette.requests import Request
from starlette.routing import Route

from routers.common import ok, services
from schemas.room import HealthResponse, ProviderInfo
from services.llm_service import PROVIDER_LABELS, PROVIDER_MODELS


async def list_rooms(request: Request):
    return ok(services(request).rooms.list_rooms())


async def health(request: Request):
    svc = services(request)
    configured = svc.settings.configured_providers()
    providers = [
        ProviderInfo(id=pid, label=PROVIDER_LABELS[pid], configured=pid in configured,
                     models=PROVIDER_MODELS[pid], default_model=svc.chat.resolve_model(pid, None))
        for pid in ("groq", "gemini")
    ]
    default = None
    if configured:
        default = svc.settings.default_provider if svc.settings.default_provider in configured else configured[0]
    return ok(HealthResponse(providers=providers, default_provider=default))


routes = [Route("/rooms", list_rooms), Route("/health", health)]
