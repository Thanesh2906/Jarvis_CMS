import json
from typing import Any
import httpx
from app.core.config import get_settings


class OllamaService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate(self, prompt: str, system: str | None = None) -> str:
        payload: dict[str, Any] = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1},
        }
        if system:
            payload["system"] = system
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.settings.ollama_base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()

    async def choose_route(self, user_message: str, available_tools: list[str]) -> dict[str, Any]:
        system = "You route clinic assistant questions. Return only valid JSON and no markdown."
        prompt = f"""
Available routes:
- normal: general clinic explanation with no live data.
- tool: live clinic data using one safe predefined function.
- rag: questions about uploaded clinic documents, policies, manuals, reports, or document explanations.

Available tool names: {available_tools}

Return JSON exactly like one of these:
{{"route":"normal"}}
{{"route":"rag","query":"question to search"}}
{{"route":"tool","tool_name":"get_today_appointment_count","arguments":{{}}}}

Tool argument rules:
- search_patient_by_name needs {{"name":"..."}}
- get_patient_summary needs {{"patient_id": 123}}
- get_doctor_schedule and get_lab_pending_by_date need {{"date":"YYYY-MM-DD"}}
- today tools need no arguments.

User question: {user_message}
"""
        raw = await self.generate(prompt, system=system)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"route": "normal"}
        if parsed.get("route") not in {"normal", "tool", "rag"}:
            return {"route": "normal"}
        return parsed
