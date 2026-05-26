import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent.parent / "storage" / "query_log.json"

def log_query(question: str, course_code: str, response: str, cited_sources: list = None):
    refusal_phrase = "I don't have enough information in the course materials"
    out_of_scope = refusal_phrase in response
    
    log_entry = {
        "question": question,
        "course_code": course_code,
        "timestamp": datetime.now().isoformat(),
        "response_preview": response[:200],
        "out_of_scope": out_of_scope,
        "cited_sources": cited_sources or []
    }
    
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []
            
    logs.append(log_entry)
    
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def get_unanswered_questions(course_code: str):
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    
    return [log for log in logs if log.get("course_code") == course_code and log.get("out_of_scope", False)]

def get_coverage(course_code: str):
    if not os.path.exists(LOG_FILE):
        return {}
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}
        
    course_logs = [log for log in logs if log.get("course_code") == course_code]
    
    doc_hits = {}
    for log in course_logs:
        # Check source_title in cited_sources
        # We need to be careful how cited_sources is structured. 
        # If it's a list of strings (source titles) or list of dicts.
        # Assuming list of dicts with 'source_title' key based on QueryEngine.query
        for src in log.get("cited_sources", []):
            if isinstance(src, dict):
                title = src.get("source_title")
            else:
                title = str(src)
            
            if title:
                doc_hits[title] = doc_hits.get(title, 0) + 1
                
    return doc_hits

from app.curriculum import CurriculumManager

curriculum = CurriculumManager()

...

def get_analytics(course_code: str):
    if not os.path.exists(LOG_FILE):
        return {"top_questions": [], "questions_per_day": {}, "weak_topics": [], "suggested_revision": [], "recent_questions": []}
        
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"top_questions": [], "questions_per_day": {}, "weak_topics": [], "suggested_revision": [], "recent_questions": []}
        
    course_logs = [log for log in logs if log.get("course_code") == course_code]
    curriculum_topics = curriculum.get_curriculum_topics(course_code)
    
    topic_hits = {}
    for topic in curriculum_topics:
        # Count hits in question text
        hits = sum(1 for log in course_logs if topic.lower() in log["question"].lower())
        topic_hits[topic] = hits
    
    weak_topics = [t for t, h in topic_hits.items() if 0 < h < 2]
    suggested_revision = [t for t, h in topic_hits.items() if h == 0]
    
    # Top 10 questions
    questions = [log["question"] for log in course_logs]
    top_questions = Counter(questions).most_common(10)
    
    # Questions per day
    dates = [log["timestamp"].split("T")[0] for log in course_logs]
    questions_per_day = dict(Counter(dates))
    
    # Recent questions (last 10)
    recent_questions = sorted(course_logs, key=lambda x: x["timestamp"], reverse=True)[:10]
    
    return {
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "questions_per_day": questions_per_day,
        "weak_topics": weak_topics,
        "suggested_revision": suggested_revision,
        "recent_questions": recent_questions
    }

def get_all_questions(course_code: str):
    if not os.path.exists(LOG_FILE):
        return []
        
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
        
    return [log for log in logs if log.get("course_code") == course_code]
