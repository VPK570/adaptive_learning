import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any

COURSES_FILE = "courses.json"

def get_all_courses_data() -> List[Dict[str, Any]]:
    if not os.path.exists(COURSES_FILE):
        return []
    try:
        with open(COURSES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_courses_data(courses: List[Dict[str, Any]]):
    with open(COURSES_FILE, "w") as f:
        json.dump(courses, f, indent=2)

def create_course(course_code: str, course_name: str, description: str, icon: str = "📚") -> Dict[str, Any]:
    courses = get_all_courses_data()
    
    # Check if course already exists
    for course in courses:
        if course["course_code"] == course_code:
            raise ValueError(f"Course with code {course_code} already exists")
    
    new_course = {
        "course_code": course_code,
        "course_name": course_name,
        "description": description,
        "icon": icon,
        "created_at": datetime.now().isoformat()
    }
    
    courses.append(new_course)
    save_courses_data(courses)
    return new_course

def update_course(course_code: str, course_name: Optional[str] = None, description: Optional[str] = None, icon: Optional[str] = None) -> Dict[str, Any]:
    courses = get_all_courses_data()
    updated = False
    updated_course = None
    
    for course in courses:
        if course["course_code"] == course_code:
            if course_name is not None:
                course["course_name"] = course_name
            if description is not None:
                course["description"] = description
            if icon is not None:
                course["icon"] = icon
            updated = True
            updated_course = course
            break
            
    if not updated:
        raise ValueError(f"Course with code {course_code} not found")
        
    save_courses_data(courses)
    return updated_course

def delete_course(course_code: str):
    courses = get_all_courses_data()
    initial_len = len(courses)
    courses = [c for c in courses if c["course_code"] != course_code]
    
    if len(courses) == initial_len:
        raise ValueError(f"Course with code {course_code} not found")
        
    save_courses_data(courses)
