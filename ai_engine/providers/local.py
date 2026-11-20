from typing import Optional, Dict, Any
from ai_engine.providers.base import BaseAIProvider, AIResponse

class LocalDeterministicFallbackProvider(BaseAIProvider):
    """
    Deterministic rule-based and template-driven fallback engine.
    Ensures that NEXORA AI remains operational even when completely offline
    or when external API rate limits / network partitions occur.
    """
    def __init__(self):
        self.name = "local_deterministic_fallback"

    def get_provider_name(self) -> str:
        return self.name

    async def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000
    ) -> AIResponse:
        prompt_lower = prompt.lower()
        
        # Domain heuristic routing
        if "roadmap" in prompt_lower or "career" in prompt_lower:
            reply = (
                "**NEXORA Offline Career Advisor Guidance:**\n\n"
                "1. **Core CS Foundations:** Prioritize Data Structures & Algorithms (Trees, Graphs, DP).\n"
                "2. **Systems Knowledge:** Review Operating Systems (Processes, Concurrency) and DBMS (Indexing, Normalization).\n"
                "3. **Practical Projects:** Build a complete full-stack portfolio application with unit test coverage.\n"
                "4. **Weekly Target:** Complete 5 medium LeetCode/GFG problems and 1 mock assessment."
            )
        elif "code review" in prompt_lower or "complexity" in prompt_lower:
            reply = (
                "**NEXORA Deterministic Code Analysis:**\n\n"
                "- **Complexity:** Analyze loops and recursion depth for Time: O(N) and Space: O(1) bounds.\n"
                "- **Edge Cases:** Verify handling of empty collections, single elements, and integer overflow.\n"
                "- **Style:** Maintain consistent naming and avoid mutable default arguments."
            )
        elif "interview" in prompt_lower:
            reply = (
                "**NEXORA Interview Preparation Guideline:**\n\n"
                "- Frame behavioral responses strictly using the **STAR methodology** (Situation, Task, Action, Result).\n"
                "- For technical questions, state time/space complexity before writing code."
            )
        else:
            reply = (
                "**NEXORA AI Assistant (Local Mode):**\n\n"
                "Your request has been processed using the local deterministic intelligence engine. "
                "All educational guidelines, practice problems, and diagnostic scoring remain fully available."
            )

        return AIResponse(
            content=reply,
            provider=self.name,
            model="deterministic-heuristic-v1",
            tokens_prompt=len(prompt.split()),
            tokens_completion=len(reply.split()),
            is_fallback=True,
            metadata={"offline_mode": True, "context_attached": bool(context)}
        )
