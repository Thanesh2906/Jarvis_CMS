import json
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import AiConversationLog, AiToolCallLog


async def create_conversation_log(db: AsyncSession, user_id: int, question: str) -> AiConversationLog:
    log = AiConversationLog(user_id=user_id, question=question)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def finish_conversation_log(db: AsyncSession, log: AiConversationLog, response: str, route: str) -> None:
    log.response = response
    log.route = route
    await db.commit()


async def log_tool_call(db: AsyncSession, user_id: int, tool_name: str, arguments: dict[str, Any], result: Any) -> None:
    db.add(
        AiToolCallLog(
            user_id=user_id,
            tool_name=tool_name,
            arguments_json=json.dumps(arguments, default=str),
            result_json=json.dumps(result, default=str),
        )
    )
    await db.commit()
