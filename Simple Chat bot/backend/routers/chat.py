"""POST /api/chat — AI 답변을 글자 단위로 흘려보낸다 (text/plain 스트리밍)."""
from __future__ import annotations

import json
from itertools import chain

from pydantic import ValidationError
from starlette.concurrency import iterate_in_threadpool, run_in_threadpool
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.routing import Route

from routers.common import error, services, validation_error
from schemas.chat import ChatRequest
from services.llm_service import LLMError


async def chat(request: Request):
    try:
        req = ChatRequest.model_validate(await request.json())
    except json.JSONDecodeError:
        return error("JSON 본문이 필요해요.", "invalid_request", 400)
    except ValidationError as e:
        return validation_error(e)

    gen = services(request).chat.stream_reply(req)
    # 첫 조각을 먼저 받아서, 키·모델 오류를 알맞은 HTTP 상태 코드로 돌려준다.
    try:
        first = await run_in_threadpool(next, gen, "")
    except LLMError as e:
        return error(str(e), e.code, e.status)

    def rest():
        try:
            yield from gen
        except LLMError as e:  # 답변 도중 끊긴 경우
            yield f"\n\n(연결이 끊겼어요: {e})"

    body = iterate_in_threadpool(chain([first], rest()))
    return StreamingResponse(body, media_type="text/plain; charset=utf-8",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


routes = [Route("/chat", chat, methods=["POST"])]
