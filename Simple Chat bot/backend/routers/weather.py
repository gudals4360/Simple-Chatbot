"""GET /api/weather?q=내일 부산 — 하늘깡이 쓰는 날씨 요약을 그대로 확인."""
from __future__ import annotations

from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.routing import Route

from routers.common import ok, services


async def weather(request: Request):
    q = (request.query_params.get("q") or "오늘").strip()
    report = await run_in_threadpool(services(request).weather.report, q)
    return ok(report, status=200 if report.ok else 502)


routes = [Route("/weather", weather)]
