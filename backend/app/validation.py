import re
import os

# --- Constants & Limits ---
MAX_COURSE_CODE_LENGTH = 20
MAX_SESSION_ID_LENGTH = 50
MAX_TOPIC_LENGTH = 100
MAX_QUESTION_LENGTH = 1000
MAX_COURSE_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500
MAX_LANGUAGE_LENGTH = 20
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB limit

# --- Regex Patterns ---
# Only allow alphanumeric, underscores, and hyphens for IDs and codes
# This prevents path traversal and ensures valid ChromaDB collection names
SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")

def sanitize_id(id_str: str) -> str:
    """
    Sanitizes a string to be used as an identifier (e.g., session ID, course code).
    
    Rules:
    1. If empty, returns "default".
    2. Replaces any character not alphanumeric, underscore, or hyphen with an underscore.
    3. If the result starts with a dot or underscore, prepends "id_" to prevent issues 
       with hidden files or certain database naming conventions.
    4. Truncates to MAX_SESSION_ID_LENGTH (50).
    """
    if not id_str:
        return "default"
    # Replace anything not in the pattern with an underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", id_str)
    # Ensure it doesn't start with a dot or slash (additional path traversal protection)
    if sanitized.startswith(".") or sanitized.startswith("_"):
        sanitized = "id_" + sanitized
    return sanitized[:MAX_SESSION_ID_LENGTH]

def validate_id(id_str: str) -> bool:
    if not id_str:
        raise ValueError("ID cannot be empty")
    if len(id_str) > MAX_SESSION_ID_LENGTH:
        raise ValueError(f"ID exceeds maximum length of {MAX_SESSION_ID_LENGTH}")
    if not SAFE_ID_PATTERN.match(id_str):
        raise ValueError("ID contains invalid characters. Only alphanumeric, underscores, and hyphens are allowed.")
    return True

def validate_course_code(course_code: str) -> str:
    """Validates and sanitizes course code."""
    if not course_code:
        return "BAECE102" # Default or raise error
    
    # Check length
    code = course_code.strip()[:MAX_COURSE_CODE_LENGTH]
    
    # Sanitize for ChromaDB and paths
    if not SAFE_ID_PATTERN.match(code):
        code = sanitize_id(code)
    
    return code

def sanitize_text(text: str, max_length: int) -> str:
    """Basic text sanitization: trim and truncate."""
    if not text:
        return ""
    return text.strip()[:max_length]
# Patterns that signal prompt-injection attempts in student input
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(the\s+)?(previous|prior|above|system)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your\s+instructions)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"new\s+(instructions|rules|system\s+prompt)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if|a|an)\s+", re.IGNORECASE),
    re.compile(r"</?(system|assistant|user)>", re.IGNORECASE),
    re.compile(r"\[/?(INST|SYS)\]", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|instructions)", re.IGNORECASE),
]


def sanitize_student_query(text: str, max_length: int = MAX_QUESTION_LENGTH) -> str:
    """
    Sanitize a student's question before it enters the LLM prompt.
    Strips role-injection tokens and neutralizes common override phrases.
    """
    if not text:
        return ""

    cleaned = text.strip()[:max_length]

    # Remove fake chat-role / template markers outright
    cleaned = re.sub(r"</?(system|assistant|user)>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[/?(INST|SYS)\]", "", cleaned, flags=re.IGNORECASE)

    # Neutralize override phrases (don't delete — flag them so the model sees they were attempted)
    for pat in INJECTION_PATTERNS:
        cleaned = pat.sub("[filtered]", cleaned)

    return cleaned.strip()

def validate_filename(filename: str) -> str:
    """Ensures a filename is safe and doesn't contain path traversal components."""
    # Use os.path.basename to strip any directories
    base = os.path.basename(filename)
    # Further sanitize the name
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
