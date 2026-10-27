"""라우터 공통 도우미."""
from __future__ import annotations

from pydantic import BaseModel, ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse


def services(request: Request):
    return request.app.state.services


def ok(model: BaseModel | list, status: int = 200) -> JSONResponse:
    if isinstance(model, list):
        return JSONResponse([m.model_dump(mode="json") for m in model], status_code=status)
    return JSONResponse(model.model_dump(mode="json"), status_code=status)


def error(message: str, code: str, status: int) -> JSONResponse:
    return JSONResponse({"error": message, "code": code}, status_code=status)


def validation_error(e: ValidationError) -> JSONResponse:
    first = e.errors()[0] if e.errors() else {}
    where = ".".join(str(x) for x in first.get("loc", []))
    return error(f"요청 형식이 올바르지 않아요: {where} {first.get('msg', '')}".strip(), "invalid_request", 422)
