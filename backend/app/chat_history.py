import json
import os
from datetime import datetime
from app.config import settings
from app.validation import validate_course_code, sanitize_id

def get_history_path(course_code):
    course_code = validate_course_code(course_code)
    os.makedirs(settings.CHAT_HISTORY_DIR, exist_ok=True)
    return os.path.join(settings.CHAT_HISTORY_DIR, f"{course_code}_history.json")

def load_history(course_code):
    history_file = get_history_path(course_code)
    if not os.path.exists(history_file):
        return {}
    try:
        with open(history_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_history(course_code, history):
    with open(get_history_path(course_code), "w") as f:
        json.dump(history, f, indent=2)

def get_course_history(course_code, session_id):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    history = load_history(course_code)
    return history.get(session_id, [])

def add_message(course_code, session_id, role, content):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    
    history = load_history(course_code)
    if session_id not in history:
        history[session_id] = []
    
    history[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_history(course_code, history)

def clear_course_history(course_code, session_id):
    course_code = validate_course_code(course_code)
    session_id = sanitize_id(session_id)
    history = load_history(course_code)
    if session_id in history:
        del history[session_id]
        save_history(course_code, history)
