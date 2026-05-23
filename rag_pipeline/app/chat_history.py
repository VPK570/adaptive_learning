import json
import os
from datetime import datetime

HISTORY_FILE = "chat_history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def get_course_history(course_code, session_id):
    history = load_history()
    return history.get(course_code, {}).get(session_id, [])

def add_message(course_code, session_id, role, content):
    history = load_history()
    if course_code not in history:
        history[course_code] = {}
    if session_id not in history[course_code]:
        history[course_code][session_id] = []
    
    history[course_code][session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_history(history)

def clear_course_history(course_code, session_id):
    history = load_history()
    if course_code in history and session_id in history[course_code]:
        del history[course_code][session_id]
        save_history(history)
