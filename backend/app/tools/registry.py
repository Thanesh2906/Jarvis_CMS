from typing import Any, Awaitable, Callable
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rbac import TOOL_PERMISSIONS, can_call_tool
from app.tools import clinic_tools

ToolCallable = Callable[..., Awaitable[Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self.tools: dict[str, ToolCallable] = {
            "get_today_patient_count": clinic_tools.get_today_patient_count,
            "get_today_appointment_count": clinic_tools.get_today_appointment_count,
            "get_pending_lab_results": clinic_tools.get_pending_lab_results,
            "get_unpaid_invoice_count": clinic_tools.get_unpaid_invoice_count,
            "get_today_revenue": clinic_tools.get_today_revenue,
            "search_patient_by_name": clinic_tools.search_patient_by_name,
            "get_patient_summary": clinic_tools.get_patient_summary,
            "get_doctor_schedule": clinic_tools.get_doctor_schedule,
            "get_lab_pending_by_date": clinic_tools.get_lab_pending_by_date,
        }

    def available_tool_names(self, role: str) -> list[str]:
        return [name for name in self.tools if can_call_tool(role, name)]

    async def call(self, db: AsyncSession, role: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        if tool_name not in self.tools:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown tool")
        if not can_call_tool(role, tool_name):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your role cannot use this clinic tool")
        return await self.tools[tool_name](db=db, role=role, **arguments)


registry = ToolRegistry()
