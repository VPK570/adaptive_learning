import json
import logging

from fastapi import APIRouter, Depends, Query, HTTPException

from app.deps import get_rag, get_saved_content
from app.rag import RAGPipeline
from app.saved_content import SavedContentManager
from app.schemas import FlashcardRequest, SaveFlashcardRequest
from app.validation import validate_course_code, sanitize_text, MAX_TOPIC_LENGTH
from app.openrouter import client

logger = logging.getLogger(__name__)
router = APIRouter()


def safe_json_parse(response_str: str):
    if not response_str:
        return None
    try:
        json_str = response_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif json_str.startswith("```"):
            json_str = json_str.split("```")[1].split("```")[0].strip()
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}\nResponse: {response_str}")
        return None


@router.post("/flashcards")
async def generate_flashcards(
    body: FlashcardRequest,
    rag: RAGPipeline = Depends(get_rag),
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)

    chunks = await rag.retrieve(query=topic, course_code=course_code, top_k=10)
    if not chunks:
        raise HTTPException(404, "No materials found to generate flashcards.")

    context = "\n".join([c["text"] for c in chunks if c.get("text")])

    prompt = f"""Based on the following course materials, generate {body.count} flashcards for the topic: {topic}.
Return ONLY a JSON array of objects, each with 'question' and 'answer' fields.
Ensure the JSON is complete and valid. Do not truncate the output.

MATERIALS:
{context}
"""
    response = await client.chat(
        [{"role": "user", "content": prompt}], temperature=0.3, max_tokens=2048
    )

    result = safe_json_parse(response)
    if result is None:
        raise HTTPException(500, "Failed to generate valid JSON for flashcards.")
    return result


@router.post("/flashcards/save")
async def save_flashcards(
    body: SaveFlashcardRequest,
    saved_content: SavedContentManager = Depends(get_saved_content),
):
    course_code = validate_course_code(body.course_code)
    topic = sanitize_text(body.topic, MAX_TOPIC_LENGTH)
    return await saved_content.save_flashcards(course_code, topic, body.cards)


@router.get("/flashcards/saved")
async def get_saved_flashcards(
    course: str = Query(...),
    saved_content: SavedContentManager = Depends(get_saved_content),
):
    course = validate_course_code(course)
    return await saved_content.get_saved_flashcards(course)


@router.delete("/flashcards/saved/{set_id}")
async def delete_saved_flashcards(
    set_id: str,
    saved_content: SavedContentManager = Depends(get_saved_content),
):
    try:
        if not await saved_content.delete_flashcards(set_id):
            raise HTTPException(404, "Flashcard set not found.")
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(400, str(e))