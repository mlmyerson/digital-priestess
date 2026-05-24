from dataclasses import dataclass

import httpx

from app.core.config import Settings


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class LMStudioClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def complete(self, messages: list[ChatMessage]) -> str:
        if not self.settings.lm_studio_is_local:
            raise ValueError("LM Studio base URL must point to localhost for local-only mode.")

        url = f"{str(self.settings.lm_studio_base_url).rstrip('/')}/chat/completions"
        payload = {
            "model": self.settings.lm_studio_model,
            "messages": [message.__dict__ for message in messages],
            "temperature": 0.4,
            "stream": False,
        }
        timeout = httpx.Timeout(self.settings.lm_studio_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()