from typing import Dict, Any, List
from datetime import datetime

class TokenTelemetryTracker:
    """
    Tracks prompt tokens, completion tokens, latency, and estimated cost per call.
    FEAT-004 implementation.
    """
    # Estimated pricing per 1K tokens (Gemini 1.5 Flash reference rate: $0.000075 / 1K input, $0.0003 / 1K output)
    COST_PER_1K_INPUT_USD = 0.000075
    COST_PER_1K_OUTPUT_USD = 0.0003

    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def log_call(
        self,
        provider: str,
        model: str,
        tokens_prompt: int,
        tokens_completion: int,
        latency_ms: float,
        is_fallback: bool = False,
        user_id: str = "anonymous",
        action: str = "general_query"
    ) -> Dict[str, Any]:
        cost_usd = (
            (tokens_prompt / 1000.0) * self.COST_PER_1K_INPUT_USD +
            (tokens_completion / 1000.0) * self.COST_PER_1K_OUTPUT_USD
        )
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "provider": provider,
            "model": model,
            "tokens_prompt": tokens_prompt,
            "tokens_completion": tokens_completion,
            "total_tokens": tokens_prompt + tokens_completion,
            "latency_ms": round(latency_ms, 2),
            "estimated_cost_usd": round(cost_usd, 6),
            "is_fallback": is_fallback
        }
        self._history.append(record)
        # Keep last 1000 records in memory
        if len(self._history) > 1000:
            self._history.pop(0)
        return record

    def get_summary(self) -> Dict[str, Any]:
        total_tokens = sum(r["total_tokens"] for r in self._history)
        total_cost = sum(r["estimated_cost_usd"] for r in self._history)
        calls_count = len(self._history)
        fallback_count = sum(1 for r in self._history if r["is_fallback"])
        return {
            "total_calls": calls_count,
            "total_tokens": total_tokens,
            "total_estimated_cost_usd": round(total_cost, 6),
            "fallback_calls": fallback_count,
            "fallback_rate_pct": round((fallback_count / calls_count * 100), 2) if calls_count > 0 else 0.0
        }

telemetry_tracker = TokenTelemetryTracker()
