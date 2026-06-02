from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    route: str
    tool_name: str | None = None
    tool_result: dict[str, Any] | list[dict[str, Any]] | None = None
