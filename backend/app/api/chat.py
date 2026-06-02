from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.assistant import assistant_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> ChatResponse:
    result = await assistant_service.answer(db, user, payload.message)
    return ChatResponse(**result)
