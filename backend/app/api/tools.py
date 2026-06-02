from typing import Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.services.audit import log_tool_call
from app.tools.registry import registry

router = APIRouter(prefix="/tools", tags=["tools"])


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = {}


@router.get("")
async def list_tools(user: User = Depends(get_current_user)) -> dict[str, list[str]]:
    return {"tools": registry.available_tool_names(user.role)}


@router.post("/call")
async def call_tool(payload: ToolCallRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)) -> Any:
    result = await registry.call(db, user.role, payload.tool_name, payload.arguments)
    await log_tool_call(db, user.id, payload.tool_name, payload.arguments, result)
    return result
