from pydantic import BaseModel, Field


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class DocumentChunk(BaseModel):
    text: str
    source: str
    score: float | None = None


class DocumentSearchResponse(BaseModel):
    answer: str
    chunks: list[DocumentChunk]
