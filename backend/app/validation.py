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
    """Removes any characters that are not alphanumeric, underscores, or hyphens."""
    if not id_str:
        return "default"
    # Replace anything not in the pattern with an underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_\-]", "_", id_str)
    # Ensure it doesn't start with a dot or slash (additional path traversal protection)
    if sanitized.startswith(".") or sanitized.startswith("_"):
        sanitized = "id_" + sanitized
    return sanitized[:MAX_SESSION_ID_LENGTH]

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

def validate_filename(filename: str) -> str:
    """Ensures a filename is safe and doesn't contain path traversal components."""
    # Use os.path.basename to strip any directories
    base = os.path.basename(filename)
    # Further sanitize the name
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
