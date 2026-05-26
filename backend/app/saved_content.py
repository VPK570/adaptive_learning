import json
import os
import uuid
from datetime import datetime
from app.config import settings
from app.validation import validate_course_code, sanitize_text, MAX_TOPIC_LENGTH

class SavedContentManager:
    def __init__(self):
        self.flashcards_file = os.path.join(settings.FLASHCARDS_DIR, "saved_flashcards.json")
        self.quizzes_file = os.path.join(settings.QUIZZES_DIR, "saved_quizzes.json")
        self._init_files()

    def _init_files(self):
        os.makedirs(settings.FLASHCARDS_DIR, exist_ok=True)
        os.makedirs(settings.QUIZZES_DIR, exist_ok=True)
        if not os.path.exists(self.flashcards_file):
            with open(self.flashcards_file, 'w') as f:
                json.dump([], f)
        if not os.path.exists(self.quizzes_file):
            with open(self.quizzes_file, 'w') as f:
                json.dump([], f)

    def _read_json(self, file):
        with open(file, 'r') as f:
            return json.load(f)

    def _write_json(self, file, data):
        with open(file, 'w') as f:
            json.dump(data, f, indent=2)

    def save_flashcards(self, course_code, topic, cards):
        course_code = validate_course_code(course_code)
        topic = sanitize_text(topic, MAX_TOPIC_LENGTH)
        data = self._read_json(self.flashcards_file)
        new_set = {
            "id": str(uuid.uuid4()),
            "course_code": course_code,
            "topic": topic,
            "cards": cards,
            "created_at": datetime.now().isoformat()
        }
        data.append(new_set)
        self._write_json(self.flashcards_file, data)
        return new_set

    def get_saved_flashcards(self, course_code):
        course_code = validate_course_code(course_code)
        data = self._read_json(self.flashcards_file)
        return [c for c in data if c["course_code"] == course_code]

    def delete_flashcards(self, set_id):
        data = self._read_json(self.flashcards_file)
        new_data = [c for c in data if c["id"] != set_id]
        if len(new_data) == len(data):
            return False
        self._write_json(self.flashcards_file, new_data)
        return True

    def save_quiz(self, course_code, topic, questions, score):
        course_code = validate_course_code(course_code)
        topic = sanitize_text(topic, MAX_TOPIC_LENGTH)
        data = self._read_json(self.quizzes_file)
        new_quiz = {
            "id": str(uuid.uuid4()),
            "course_code": course_code,
            "topic": topic,
            "questions": questions,
            "score": score,
            "total": len(questions),
            "created_at": datetime.now().isoformat()
        }
        data.append(new_quiz)
        self._write_json(self.quizzes_file, data)
        return new_quiz

    def get_saved_quizzes(self, course_code):
        course_code = validate_course_code(course_code)
        data = self._read_json(self.quizzes_file)
        return [q for q in data if q["course_code"] == course_code]

    def delete_quiz(self, quiz_id):
        data = self._read_json(self.quizzes_file)
        new_data = [q for q in data if q["id"] != quiz_id]
        if len(new_data) == len(data):
            return False
        self._write_json(self.quizzes_file, new_data)
        return True
