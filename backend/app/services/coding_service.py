"""
Coding Problem Service & Test-Case Evaluator (FEAT-063..FEAT-086).
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from backend.app.models.coding import (
    CodingProblem, ProblemTestCase, CodeSubmission, StudentCodingStats
)
from sandbox.worker import ProcessIsolatedSandbox

DEFAULT_PROBLEMS = [
    {
        "slug": "two-sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Arrays",
        "tags": "Array, Hash Table",
        "companies": "Google, Amazon, Microsoft, Meta",
        "description_markdown": """Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

### Example 1:
```
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
```""",
        "constraints": "2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\nOnly one valid answer exists.",
        "starter_code_python": """def twoSum(nums: list[int], target: int) -> list[int]:
    # Write your solution here
    seen = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in seen:
            return [seen[diff], i]
        seen[num] = i
    return []
""",
        "starter_code_java": """class Solution {
    public int[] twoSum(int[] nums, int target) {
        // Solution implementation
        return new int[]{};
    }
}""",
        "starter_code_cpp": """class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // Solution implementation
        return {};
    }
};""",
        "starter_code_c": """int* twoSum(int* nums, int numsSize, int target, int* returnSize) {
    // Solution implementation
    return 0;
}""",
        "sample_cases": [
            {"stdin": "[2,7,11,15]\n9", "expected": "[0, 1]", "explanation": "2 + 7 = 9", "is_sample": True},
            {"stdin": "[3,2,4]\n6", "expected": "[1, 2]", "explanation": "2 + 4 = 6", "is_sample": True}
        ],
        "hidden_cases": [
            {"stdin": "[3,3]\n6", "expected": "[0, 1]", "is_sample": False},
            {"stdin": "[1,5,8,12]\n13", "expected": "[1, 2]", "is_sample": False}
        ]
    },
    {
        "slug": "valid-parentheses",
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "category": "Stacks",
        "tags": "String, Stack",
        "companies": "Amazon, Microsoft, Bloomberg",
        "description_markdown": """Given a string `s` containing just the characters `'('`, `')'`, `'{'`, `'}'`, `'['` and `']'`, determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.""",
        "constraints": "1 <= s.length <= 10^4\ns consists of parentheses only '()[]{}'.",
        "starter_code_python": """def isValid(s: str) -> bool:
    stack = []
    mapping = {")": "(", "}": "{", "]": "["}
    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)
    return not stack
""",
        "sample_cases": [
            {"stdin": "()", "expected": "true", "is_sample": True},
            {"stdin": "()[]{}", "expected": "true", "is_sample": True}
        ],
        "hidden_cases": [
            {"stdin": "(]", "expected": "false", "is_sample": False},
            {"stdin": "([)]", "expected": "false", "is_sample": False}
        ]
    },
    {
        "slug": "longest-substring-without-repeating-characters",
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "Medium",
        "category": "Sliding Window",
        "tags": "Hash Table, String, Sliding Window",
        "companies": "Google, Meta, Apple",
        "description_markdown": """Given a string `s`, find the length of the longest substring without repeating characters.

### Example 1:
```
Input: s = "abcabcbb"
Output: 3
Explanation: The answer is "abc", with the length of 3.
```""",
        "constraints": "0 <= s.length <= 5 * 10^4\ns consists of English letters, digits, symbols and spaces.",
        "starter_code_python": """def lengthOfLongestSubstring(s: str) -> int:
    char_map = {}
    left = max_len = 0
    for right, char in enumerate(s):
        if char in char_map and char_map[char] >= left:
            left = char_map[char] + 1
        char_map[char] = right
        max_len = max(max_len, right - left + 1)
    return max_len
""",
        "sample_cases": [
            {"stdin": "abcabcbb", "expected": "3", "is_sample": True},
            {"stdin": "bbbbb", "expected": "1", "is_sample": True}
        ],
        "hidden_cases": [
            {"stdin": "pwwkew", "expected": "3", "is_sample": False}
        ]
    }
]

class CodingArenaService:

    @staticmethod
    async def ensure_problems_seeded(db: AsyncSession):
        """Auto-seed canonical problems into PostgreSQL if empty."""
        res = await db.execute(select(CodingProblem))
        if not res.scalars().first():
            for p_data in DEFAULT_PROBLEMS:
                prob = CodingProblem(
                    slug=p_data["slug"],
                    title=p_data["title"],
                    difficulty=p_data["difficulty"],
                    category=p_data["category"],
                    tags=p_data["tags"],
                    companies=p_data["companies"],
                    description_markdown=p_data["description_markdown"],
                    constraints=p_data["constraints"],
                    starter_code_python=p_data["starter_code_python"],
                    starter_code_java=p_data.get("starter_code_java"),
                    starter_code_cpp=p_data.get("starter_code_cpp"),
                    starter_code_c=p_data.get("starter_code_c")
                )
                db.add(prob)
                await db.flush()

                # Add sample test cases
                for idx, sc in enumerate(p_data["sample_cases"]):
                    db.add(ProblemTestCase(
                        problem_id=prob.id,
                        stdin_input=sc["stdin"],
                        expected_output=sc["expected"],
                        explanation=sc.get("explanation"),
                        is_sample=True,
                        order_index=idx
                    ))

                # Add hidden test cases
                for idx, hc in enumerate(p_data["hidden_cases"]):
                    db.add(ProblemTestCase(
                        problem_id=prob.id,
                        stdin_input=hc["stdin"],
                        expected_output=hc["expected"],
                        is_sample=False,
                        order_index=len(p_data["sample_cases"]) + idx
                    ))

            await db.commit()

    @staticmethod
    async def evaluate_submission(
        problem: CodingProblem,
        language: str,
        code: str,
        test_cases: List[ProblemTestCase],
        sandbox: ProcessIsolatedSandbox
    ) -> Dict[str, Any]:
        """
        Evaluates a student code submission against both sample and hidden test cases.
        Enforces strict execution security via ProcessIsolatedSandbox.
        """
        # If sandbox mode blocks execution (e.g. Docker unavailable), safely report verdict
        test_exec = sandbox.execute(language, code, "")
        if test_exec["status"].startswith("EXECUTION_BLOCKED"):
            return {
                "verdict": test_exec["status"],
                "passed_cases": 0,
                "total_cases": len(test_cases),
                "execution_time_ms": 0.0,
                "memory_used_mb": 0.0,
                "error_message": test_exec["stderr"]
            }

        # If container environment is active, iterate test cases
        passed = 0
        total = len(test_cases)
        max_time = 0.0
        max_mem = 0.0

        for tc in test_cases:
            run_res = sandbox.execute(language, code, tc.stdin_input)
            if run_res["is_timeout"]:
                return {
                    "verdict": "TIME_LIMIT_EXCEEDED",
                    "passed_cases": passed,
                    "total_cases": total,
                    "execution_time_ms": run_res["execution_time_ms"],
                    "memory_used_mb": run_res["memory_used_mb"],
                    "error_message": "Time Limit Exceeded"
                }
            if run_res["exit_code"] != 0:
                return {
                    "verdict": "RUNTIME_ERROR",
                    "passed_cases": passed,
                    "total_cases": total,
                    "execution_time_ms": run_res["execution_time_ms"],
                    "memory_used_mb": run_res["memory_used_mb"],
                    "error_message": run_res["stderr"]
                }
            # Compare output
            if run_res["stdout"].strip() == tc.expected_output.strip():
                passed += 1
                max_time = max(max_time, run_res["execution_time_ms"])
                max_mem = max(max_mem, run_res["memory_used_mb"])
            else:
                return {
                    "verdict": "WRONG_ANSWER",
                    "passed_cases": passed,
                    "total_cases": total,
                    "execution_time_ms": run_res["execution_time_ms"],
                    "memory_used_mb": run_res["memory_used_mb"],
                    "error_message": "Output did not match expected result."
                }

        return {
            "verdict": "ACCEPTED" if passed == total else "WRONG_ANSWER",
            "passed_cases": passed,
            "total_cases": total,
            "execution_time_ms": max_time,
            "memory_used_mb": max_mem,
            "error_message": None
        }
