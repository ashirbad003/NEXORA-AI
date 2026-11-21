from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncIterator
from pydantic import BaseModel, Field

class AIResponse(BaseModel):
    content: str
    provider: str
    model: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    is_fallback: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000
    ) -> AIResponse:
        """Generate response from AI model with safety validation"""
        pass

    async def stream_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000
    ) -> AsyncIterator[str]:
        """Stream response tokens chunk-by-chunk for Realtime AI Streaming Support (FEAT-013)"""
        full_response = await self.generate_response(prompt, system_instruction, context, max_tokens)
        words = full_response.content.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the registered name of the provider"""
        pass
