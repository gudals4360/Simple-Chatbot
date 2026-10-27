"""GET /api/places/search?q=만원 이하 점심 — 교육장 근처 식당 검색."""
from __future__ import annotations

from starlette.requests import Request
from starlette.routing import Route

from routers.common import error, ok, services
from schemas.place import PlaceSearchResponse


async def search(request: Request):
    q = (request.query_params.get("q") or "").strip()
    if not q:
        return error("검색어(q)를 넣어 주세요.", "invalid_request", 400)
    try:
        limit = max(1, min(30, int(request.query_params.get("limit", "15"))))
    except ValueError:
        return error("limit은 숫자여야 해요.", "invalid_request", 400)
    svc = services(request).places
    return ok(PlaceSearchResponse(query=q, total_places=svc.repo.count(), results=svc.search(q, limit)))


routes = [Route("/places/search", search)]
