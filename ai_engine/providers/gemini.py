import json
import httpx
import time
from typing import Optional, Dict, Any
from ai_engine.providers.base import BaseAIProvider, AIResponse
from backend.app.core.config import settings
from backend.app.core.logging import logger

class GeminiAIProvider(BaseAIProvider):
    """
    Provider integrating Google Gemini via official REST API endpoint.
    Uses free-tier compatible gemini-1.5-flash or gemini-2.0-flash.
    FEAT-001 implementation.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.name = "gemini"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def get_provider_name(self) -> str:
        return self.name

    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000
    ) -> AIResponse:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        # Construct payload
        contents = []
        if context:
            ctx_str = f"Context:\n{json.dumps(context, indent=2)}\n\n"
            prompt = ctx_str + prompt

        contents.append({"parts": [{"text": prompt}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": 0.3
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        headers = {"Content-Type": "application/json"}
        url = f"{self.base_url}?key={self.api_key}"

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=float(settings.AI_TIMEOUT_SECONDS)) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.perf_counter() - start) * 1000
        # Parse candidate
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned zero candidates.")

        text_content = ""
        parts = candidates[0].get("content", {}).get("parts", [])
        for p in parts:
            if "text" in p:
                text_content += p["text"]

        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", len(prompt) // 4)
        completion_tokens = usage.get("candidatesTokenCount", len(text_content) // 4)

        return AIResponse(
            content=text_content,
            provider=self.name,
            model=self.model,
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
            is_fallback=False,
            metadata={"latency_ms": latency_ms}
        )
