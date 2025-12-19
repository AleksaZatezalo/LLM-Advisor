"""
LLM Service.

Interfaces with Ollama for local LLM inference.
"""
from dataclasses import dataclass
import httpx
from django.conf import settings


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    model: str
    done: bool


class LLMService:
    """
    Client for Ollama API.
    
    Provides methods for text generation and chat completion
    using locally running LLMs.
    """
    
    def __init__(self, model: str = None):
        self.model = model or settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_HOST
        self._client = None
    
    @property
    def client(self) -> httpx.Client:
        """Lazy-load HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=120.0)
        return self._client
    
    def generate(self, prompt: str, system: str = None) -> LLMResponse:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The user prompt
            system: Optional system message
        
        Returns:
            LLMResponse with generated text
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        
        if system:
            payload["system"] = system
        
        response = self.client.post(
            f"{self.base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        
        data = response.json()
        
        return LLMResponse(
            content=data.get("response", ""),
            model=data.get("model", self.model),
            done=data.get("done", True),
        )
    
    def chat(self, messages: list[dict], system: str = None) -> LLMResponse:
        """
        Chat completion with message history.
        
        Args:
            messages: List of {"role": "user/assistant", "content": "..."}
            system: Optional system message
        
        Returns:
            LLMResponse with assistant reply
        """
        formatted_messages = []
        
        if system:
            formatted_messages.append({
                "role": "system",
                "content": system,
            })
        
        formatted_messages.extend(messages)
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
        }
        
        response = self.client.post(
            f"{self.base_url}/api/chat",
            json=payload,
        )
        response.raise_for_status()
        
        data = response.json()
        message = data.get("message", {})
        
        return LLMResponse(
            content=message.get("content", ""),
            model=data.get("model", self.model),
            done=data.get("done", True),
        )
    
    def is_available(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except httpx.RequestError:
            return False
    
    def list_models(self) -> list[str]:
        """List available models."""
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except httpx.RequestError:
            return []
    
    def pull_model(self, model_name: str = None) -> bool:
        """
        Pull a model from Ollama registry.
        
        Note: This is a blocking operation that can take several minutes.
        """
        model = model_name or self.model
        
        try:
            response = self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": False},
                timeout=600.0,  # 10 minute timeout for large models
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False
