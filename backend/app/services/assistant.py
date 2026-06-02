from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.services.audit import create_conversation_log, finish_conversation_log, log_tool_call
from app.services.ollama import OllamaService
from app.services.rag import rag_service
from app.tools.registry import registry


class AssistantService:
    def __init__(self) -> None:
        self.ollama = OllamaService()

    async def answer(self, db: AsyncSession, user: User, message: str) -> dict[str, Any]:
        log = await create_conversation_log(db, user.id, message)
        route = await self.ollama.choose_route(message, registry.available_tool_names(user.role))
        route_name = route.get("route", "normal")

        if route_name == "tool":
            tool_name = route.get("tool_name")
            arguments = route.get("arguments") or {}
            result = await registry.call(db, user.role, tool_name, arguments)
            await log_tool_call(db, user.id, tool_name, arguments, result)
            answer = await self._format_tool_answer(message, tool_name, result)
            await finish_conversation_log(db, log, answer, "tool")
            return {"answer": answer, "route": "tool", "tool_name": tool_name, "tool_result": result}

        if route_name == "rag":
            answer, _chunks = await rag_service.answer(route.get("query") or message)
            await finish_conversation_log(db, log, answer, "rag")
            return {"answer": answer, "route": "rag", "tool_name": None, "tool_result": None}

        answer = await self.ollama.generate(
            message,
            system="You are Jarvis, a clinic management assistant. Do not invent live clinic data. If live data is needed, say a clinic tool is required.",
        )
        await finish_conversation_log(db, log, answer, "normal")
        return {"answer": answer, "route": "normal", "tool_name": None, "tool_result": None}

    async def _format_tool_answer(self, question: str, tool_name: str, result: Any) -> str:
        prompt = f"""
User question: {question}
Clinic tool used: {tool_name}
Tool result JSON: {result}

Write a short human answer. Do not add facts not present in the tool result.
"""
        return await self.ollama.generate(prompt, system="You convert clinic tool JSON into simple human language.")


assistant_service = AssistantService()
