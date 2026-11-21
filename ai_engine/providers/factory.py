from ai_engine.providers.base import BaseAIProvider
from ai_engine.providers.local import LocalDeterministicFallbackProvider
from ai_engine.providers.mock import MockAIProvider
from ai_engine.providers.gemini import GeminiAIProvider
from backend.app.core.config import settings
from backend.app.core.logging import logger

def get_ai_provider(provider_name: str = None) -> BaseAIProvider:
    name = (provider_name or settings.AI_PROVIDER).lower()
    
    if name == "mock":
        return MockAIProvider()
    elif name == "local":
        return LocalDeterministicFallbackProvider()
    elif name == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not configured; falling back to local deterministic provider.")
            return LocalDeterministicFallbackProvider()
        return GeminiAIProvider(api_key=settings.GEMINI_API_KEY)
    else:
        logger.warning(f"Unknown AI provider '{name}'; defaulting to local deterministic provider.")
        return LocalDeterministicFallbackProvider()
