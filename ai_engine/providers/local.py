import json
from typing import Optional, Dict, Any, List
from ai_engine.providers.base import BaseAIProvider, AIResponse

class LocalDeterministicFallbackProvider(BaseAIProvider):
    """
    Deterministic rule-based and template-driven fallback engine.
    Ensures that NEXORA AI remains operational even when completely offline
    or when external API rate limits / network partitions occur.
    Implements FEAT-003 and supports structured responses for all 40 features.
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
        
        # Check if structured JSON response is requested
        if "structured json" in prompt_lower or "json roadmap" in prompt_lower or "json" in prompt_lower and "roadmap" in prompt_lower:
            reply = self._generate_structured_roadmap_json(context)
        elif "daily sprint" in prompt_lower or "sprint tasks" in prompt_lower:
            reply = self._generate_daily_sprint_json(context)
        elif "weakness remediation" in prompt_lower or "study plan" in prompt_lower:
            reply = (
                "**7-Day Targeted Weakness Remediation Plan (Offline Mode):**\n\n"
                "- **Day 1–2 (Concept Mastery):** Review fundamental theorems and boundary invariants.\n"
                "- **Day 3–4 (Pattern Drills):** Solve 6 curated standard questions (2 Easy, 4 Medium).\n"
                "- **Day 5 (Timed Simulation):** Complete a 45-minute timed test with 2 unknown problems.\n"
                "- **Day 6 (Error Log Review):** Document root causes for any wrong answers or edge case misses.\n"
                "- **Day 7 (Verification):** Retake diagnostic quiz to measure score delta."
            )
        elif "roadmap" in prompt_lower or "career" in prompt_lower:
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
        elif "hindi" in prompt_lower or "translation" in prompt_lower:
            reply = (
                "**NEXORA करियर मार्गदर्शन (लोकल मोड):**\n\n"
                "1. **डेटा स्ट्रक्चर्स और एल्गोरिदम:** ट्री, ग्राफ, और डायनामिक प्रोग्रामिंग पर ध्यान दें।\n"
                "2. **सिस्टम्स समझ:** ऑपरेटिंग सिस्टम (प्रोसेस, थ्रेड्स) और DBMS को मजबूत करें।\n"
                "3. **प्रोजेक्ट्स:** एक मजबूत फुल-स्टैक प्रोजेक्ट बनाएं।"
            )
        else:
            reply = (
                "**NEXORA AI Assistant (Local Deterministic Mode):**\n\n"
                "Your request has been processed using the local deterministic intelligence engine. "
                "Core system guidelines are active to support your preparation without external dependencies."
            )

        return AIResponse(
            content=reply,
            provider=self.name,
            model="deterministic-rule-engine-v1",
            tokens_prompt=len(prompt) // 4,
            tokens_completion=len(reply) // 4,
            is_fallback=True,
            metadata={
                "fallback_reason": "deterministic_offline_mode",
                "rules_applied": 1
            }
        )

    def _generate_structured_roadmap_json(self, context: Optional[Dict[str, Any]]) -> str:
        role = (context or {}).get("target_role", "Software Development Engineer")
        weeks: List[Dict[str, Any]] = []
        milestones = [
            ("Week 1-2: Advanced Data Structures", "Arrays, Strings, Two Pointers & Sliding Window mastery.", ["Two Sum", "Longest Substring", "Trapping Rain Water"]),
            ("Week 3-4: Trees & Binary Search Trees", "Tree traversals, Lowest Common Ancestor, and BST properties.", ["Invert Tree", "LCA in BST", "Serialize/Deserialize Binary Tree"]),
            ("Week 5-6: Graphs & Shortest Path Algorithms", "BFS, DFS, Dijkstra, and Topological Sort implementations.", ["Course Schedule", "Number of Islands", "Network Delay Time"]),
            ("Week 7-8: Dynamic Programming Patterns", "Memoization, Tabulation, 0/1 Knapsack, and LCS.", ["Climbing Stairs", "Coin Change", "Longest Common Subsequence"]),
            ("Week 9-10: System Design & Low Level Architecture", "Database normalization, indexing, caching, and REST API modeling.", ["LRU Cache", "Rate Limiter", "URL Shortener"]),
            ("Week 11-12: Mock Interviews & Behavioral Mastery", "Full 60-min timed mocks and STAR leadership questions.", ["STAR Story Curation", "Live Coding Practice", "Resume Review"]),
        ]
        for idx, (title, focus, topics) in enumerate(milestones, start=1):
            weeks.append({
                "week_number": idx,
                "title": title,
                "focus_area": focus,
                "key_topics": topics,
                "target_problems_count": 8,
                "status": "in_progress" if idx == 1 else "pending"
            })
        data = {
            "target_role": role,
            "duration_weeks": 12,
            "weeks": weeks,
            "readiness_index_target": 85
        }
        return json.dumps(data)

    def _generate_daily_sprint_json(self, context: Optional[Dict[str, Any]]) -> str:
        tasks = [
            {"title": "Solve 2 Graph BFS/DFS Problems", "category": "coding", "estimated_minutes": 45, "completed": False},
            {"title": "Review OS Concurrency & Deadlock Notes", "category": "learning", "estimated_minutes": 30, "completed": False},
            {"title": "Complete 1 Daily Tech Trivia Quiz", "category": "quiz", "estimated_minutes": 5, "completed": False},
        ]
        return json.dumps({"date": "today", "tasks": tasks, "total_estimated_minutes": 80})
