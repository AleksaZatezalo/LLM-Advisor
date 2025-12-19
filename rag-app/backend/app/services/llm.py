import httpx
from typing import AsyncIterator

from app.config import get_settings


class LLMService:
    def __init__(self):
        settings = get_settings()
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_model

    async def generate(self, prompt: str, stream: bool = False) -> str | AsyncIterator[str]:
        """Generate a response from the LLM."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            if stream:
                return self._stream_response(client, prompt)
            else:
                response = await client.post(
                    f"{self._base_url}/api/generate",
                    json={"model": self._model, "prompt": prompt, "stream": False}
                )
                response.raise_for_status()
                return response.json()["response"]

    async def _stream_response(self, client: httpx.AsyncClient, prompt: str) -> AsyncIterator[str]:
        async with client.stream(
            "POST",
            f"{self._base_url}/api/generate",
            json={"model": self._model, "prompt": prompt, "stream": True}
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]

    async def check_health(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def pull_model(self) -> bool:
        """Pull the configured model if not present."""
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                f"{self._base_url}/api/pull",
                json={"name": self._model, "stream": False}
            )
            return response.status_code == 200


# Singleton
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
