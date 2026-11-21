import re
from typing import Tuple

# Common prompt injection patterns and jailbreak techniques
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s*prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"jailbreak",
    r"reveal\s+your\s+(secret|instructions|hidden|api\s+key)",
    r"disregard\s+(all\s+)?guidelines",
    r"bypass\s+(safety|content)\s+filters",
    r"forget\s+everything\s+you\s+(know|were\s+told)",
    r"new\s+system\s+directive",
    r"dan\s+mode",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

def sanitize_user_prompt(prompt: str) -> Tuple[bool, str, str]:
    """
    Sanitizes user input before passing it to any AI provider.
    Returns:
        (is_safe: bool, sanitized_prompt: str, reason: str)
    """
    if not prompt or not prompt.strip():
        return False, "", "Prompt cannot be empty."

    # Check for prompt injection attempts
    for pattern in COMPILED_PATTERNS:
        if pattern.search(prompt):
            return False, "", "Security Alert: Input contains prohibited prompt injection patterns or directives."

    # Normalize excessive control characters or null bytes
    sanitized = prompt.replace("\x00", "").strip()

    # Limit maximum character length to prevent context flooding (e.g. 4000 characters)
    if len(sanitized) > 4000:
        sanitized = sanitized[:4000]

    return True, sanitized, "Input is clean."
