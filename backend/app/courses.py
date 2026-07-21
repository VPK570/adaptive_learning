from typing import List, Optional, Dict, Any
from app.validation import (
    validate_course_code, 
    sanitize_text, 
    MAX_COURSE_NAME_LENGTH, 
    MAX_DESCRIPTION_LENGTH
)
from app.db import get_db

async def get_all_courses_data() -> List[Dict[str, Any]]:
    db = await get_db()
    result = await db.query("SELECT * FROM course ORDER BY created_at DESC")
    return result if isinstance(result, list) else []

async def create_course(course_code: str, course_name: str, description: str, icon: str = "📚") -> Dict[str, Any]:
    course_code = validate_course_code(course_code)
    course_name = sanitize_text(course_name, MAX_COURSE_NAME_LENGTH)
    description = sanitize_text(description, MAX_DESCRIPTION_LENGTH)
    icon = sanitize_text(icon, 10)
    
    db = await get_db()
    
    # Check if course already exists
    existing = await db.query("SELECT * FROM course WHERE course_code = $code", {"code": course_code})
    if existing and len(existing) > 0:
        raise ValueError(f"Course with code {course_code} already exists")
    
    new_course = {
        "course_code": course_code,
        "course_name": course_name,
        "description": description,
        "icon": icon,
    }
    await db.query("CREATE course CONTENT $content", {"content": new_course})
    return new_course

async def update_course(course_code: str, course_name: Optional[str] = None, description: Optional[str] = None, icon: Optional[str] = None) -> Dict[str, Any]:
    course_code = validate_course_code(course_code)
    db = await get_db()
    
    update_data = {}
    if course_name is not None:
        update_data["course_name"] = sanitize_text(course_name, MAX_COURSE_NAME_LENGTH)
    if description is not None:
        update_data["description"] = sanitize_text(description, MAX_DESCRIPTION_LENGTH)
    if icon is not None:
        update_data["icon"] = sanitize_text(icon, 10)
    
    if not update_data:
        res = await db.query("SELECT * FROM course WHERE course_code = $code", {"code": course_code})
        if not res:
            raise ValueError(f"Course with code {course_code} not found")
        return res[0]

    res = await db.query(
        "UPDATE course MERGE $data WHERE course_code = $code RETURN AFTER",
        {"data": update_data, "code": course_code}
    )
    
    if not res:
        raise ValueError(f"Course with code {course_code} not found")
        
    return res[0]

async def delete_course(course_code: str):
    course_code = validate_course_code(course_code)
    db = await get_db()
    
    await db.query("DELETE course WHERE course_code = $code", {"code": course_code})
    # Also delete related chunks in other tables
    await db.query("DELETE text_chunk WHERE course_code = $code", {"code": course_code})
    await db.query("DELETE image_chunk WHERE course_code = $code", {"code": course_code})
    await db.query("DELETE curriculum_chunk WHERE course_code = $code", {"code": course_code})
