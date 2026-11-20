from typing import Optional, Dict, Any
from ai_engine.providers.base import BaseAIProvider, AIResponse

class MockAIProvider(BaseAIProvider):
    def __init__(self, name: str = "mock_provider"):
        self.name = name

    def get_provider_name(self) -> str:
        return self.name

    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000
    ) -> AIResponse:
        return AIResponse(
            content=f"MOCK_RESPONSE: {prompt[:30]}...",
            provider=self.name,
            model="mock-testing-model",
            tokens_prompt=10,
            tokens_completion=15,
            is_fallback=False,
            metadata={"test_mode": True}
        )
