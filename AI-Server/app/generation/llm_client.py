"""OpenAI-compatible chat-completions client. Disabled unless configured."""
from __future__ import annotations
import os
import httpx

class LLMUnavailable(RuntimeError):
    pass

class OpenAICompatibleClient:
    def __init__(self):
        self.base_url = os.getenv("SATYA_LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.getenv("SATYA_LLM_API_KEY", "")
        self.model = os.getenv("SATYA_LLM_MODEL", "gpt-4o-mini")
        self.timeout = float(os.getenv("SATYA_LLM_TIMEOUT_SECONDS", "45"))

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        if not self.configured:
            raise LLMUnavailable("SATYA_LLM_API_KEY is not configured")
        payload = {"model": self.model, "temperature": 0, "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMUnavailable("LLM provider returned an unexpected response") from exc
