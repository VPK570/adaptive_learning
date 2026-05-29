import uuid
from typing import Any
from app.db import get_db
from app.openrouter import client
from app.validation import validate_course_code

class CurriculumManager:
    async def ingest_curriculum(
        self,
        course_code: str,
        document_title: str,
        filepath: str,
    ) -> dict[str, Any]:
        course_code = validate_course_code(course_code)
        from app.pdf_extractor import extract_all_pages
        
        pages_content = await extract_all_pages(filepath)
        
        db = await get_db()
        chunks_to_insert = []
        documents = []
        
        for page in pages_content:
            if page.text.strip():
                documents.append(page.text)
                chunks_to_insert.append({
                    "course_code": course_code,
                    "source_title": document_title,
                    "page": page.page_num,
                    "text": page.text,
                    "content_type": "curriculum_text"
                })
        
        if chunks_to_insert:
            embeddings = await client.embed_text_batch(documents)
            for i, chunk in enumerate(chunks_to_insert):
                chunk["embedding"] = embeddings[i]
            
            await db.query("INSERT INTO curriculum_chunk $chunks", {"chunks": chunks_to_insert})
            
        return {"status": "success", "chunks_ingested": len(chunks_to_insert)}

    async def list_curriculum(self, course_code: str) -> list[str]:
        course_code = validate_course_code(course_code)
        db = await get_db()
        res = await db.query("SELECT source_title FROM curriculum_chunk WHERE course_code = $code GROUP BY source_title", {"code": course_code})
        if res and res[0]["result"]:
            return sorted([r["source_title"] for r in res[0]["result"]])
        return []

    async def get_curriculum_topics(self, course_code: str) -> list[str]:
        course_code = validate_course_code(course_code)
        db = await get_db()
        res = await db.query("SELECT text FROM curriculum_chunk WHERE course_code = $code", {"code": course_code})
        
        topics = set()
        if res and res[0]["result"]:
            for row in res[0]["result"]:
                doc = row["text"]
                lines = [line.strip() for line in doc.split('\n') if 3 < len(line.strip()) < 50]
                for line in lines:
                    topics.add(line)
        return sorted(list(topics))

    async def check_topic_in_curriculum(self, course_code: str, query: str) -> bool:
        course_code = validate_course_code(course_code)
        query_embedding = await client.embed_text(query)
        db = await get_db()
        
        # 1. Search Curriculum
        curr_query = """
            SELECT vector::distance::cosine(embedding, $query_vec) AS distance 
            FROM curriculum_chunk 
            WHERE course_code = $course 
            AND embedding <| 3, MTREE |> $query_vec
        """
        res = await db.query(curr_query, {"query_vec": query_embedding, "course": course_code})
        
        if res and res[0]["result"]:
            distances = [r["distance"] for r in res[0]["result"]]
            if min(distances) < 0.4:
                return True
        
        # 2. Fallback: Search Course Notes
        notes_query = """
            SELECT vector::distance::cosine(embedding, $query_vec) AS distance 
            FROM text_chunk 
            WHERE course_code = $course 
            AND embedding <| 3, MTREE |> $query_vec
        """
        res_notes = await db.query(notes_query, {"query_vec": query_embedding, "course": course_code})
        if res_notes and res_notes[0]["result"]:
            distances = [r["distance"] for r in res_notes[0]["result"]]
            if min(distances) < 0.4:
                return True
                
        return False
