"""대화 요청 형식."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    room_id: str = Field(min_length=1, max_length=40)
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)
    provider: Literal["groq", "gemini"] | None = None
    model: str | None = Field(default=None, max_length=80)
    notes: str = Field(default="", max_length=2000)  # 그럴깡 [추가 운영 정보]

    @field_validator("messages")
    @classmethod
    def last_must_be_user(cls, v: list[ChatMessage]) -> list[ChatMessage]:
        if v[-1].role != "user":
            raise ValueError("마지막 메시지는 사용자 메시지여야 해요.")
        return v


class ErrorResponse(BaseModel):
    error: str
    code: str
