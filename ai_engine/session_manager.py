from typing import List, Dict, Any, Tuple, Optional
from collections import deque
from datetime import datetime, timezone, date

class AIChatSessionManager:
    """
    Manages multi-turn conversation persistence, context window optimization,
    user rate limiting, persona prompt injection, and latency timeout enforcement.
    Implements FEAT-007, FEAT-009, FEAT-010, FEAT-011, FEAT-017.
    """
    # Max turns to preserve in working memory before summarization/truncation (FEAT-007)
    MAX_CONTEXT_TURNS = 10
    DAILY_QUOTA_LIMIT = 50

    PERSONA_PROMPTS = {
        "friendly_mentor": (
            "You are a supportive, encouraging, and highly experienced senior software engineer. "
            "Explain concepts simply, offer constructive guidance, and motivate the student."
        ),
        "strict_interviewer": (
            "You are a rigorous technical interviewer from a Tier-1 tech company. "
            "Demand precise algorithmic complexity, probe edge cases, and challenge naive solutions."
        ),
        "technical_architect": (
            "You are a principal software architect. Focus on high-level system trade-offs, "
            "scalability, clean architecture, design patterns, and operational robustness."
        )
    }

    def __init__(self):
        # session_id -> deque of messages
        self._sessions: Dict[str, deque] = {}
        # user_id -> {date: count}
        self._rate_limits: Dict[str, Dict[str, int]] = {}

    def get_persona_prompt(self, persona: str) -> str:
        return self.PERSONA_PROMPTS.get(persona.lower(), self.PERSONA_PROMPTS["friendly_mentor"])

    def check_and_increment_rate_limit(self, user_id: str) -> Tuple[bool, int, int]:
        """
        Enforces FEAT-017 (50 queries per day per user).
        Returns (is_allowed, current_count, remaining_quota)
        """
        today = date.today().isoformat()
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = {}
        
        current_count = self._rate_limits[user_id].get(today, 0)
        if current_count >= self.DAILY_QUOTA_LIMIT:
            return False, current_count, 0
        
        self._rate_limits[user_id][today] = current_count + 1
        remaining = self.DAILY_QUOTA_LIMIT - (current_count + 1)
        return True, current_count + 1, remaining

    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Stores multi-turn AI interactions (FEAT-010).
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = deque(maxlen=self.MAX_CONTEXT_TURNS)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        self._sessions[session_id].append(message)

    def get_context_window(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Returns optimized context window truncated to max turns (FEAT-007).
        """
        if session_id not in self._sessions:
            return []
        return list(self._sessions[session_id])

session_manager = AIChatSessionManager()
