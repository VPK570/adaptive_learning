from typing import Any
from app.db import get_db
from app.openrouter import client
from app.validation import validate_course_code
from surrealdb.errors import InternalError

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
                    "topic": "",
                    "content_type": "curriculum_text"
                })
        
        if chunks_to_insert:
            embeddings = await client.embed_text_batch(documents)
            for i, chunk in enumerate(chunks_to_insert):
                chunk["embedding"] = embeddings[i]
            
            try:
                await db.query("INSERT INTO curriculum_chunk $chunks", {"chunks": chunks_to_insert})
            except InternalError as e:
                # If the error is about missing fields, we alter the table to add the missing field
                if "Found field" in str(e) and "but no such field exists" in str(e):
                    # Extract the missing field name from the error message
                    # Error format: "Found field 'field_name', but no such field exists for table 'table_name'"
                    import re
                    match = re.search(r"Found field '([^']+)'", str(e))
                    if match:
                        missing_field = match.group(1)
                        # Alter the table to add the missing field
                        db = await get_db()
                        await db.query(f"ALTER TABLE curriculum_chunk FIELD {missing_field} TYPE string;")
                        # Retry the insert
                        await db.query("INSERT INTO curriculum_chunk $chunks", {"chunks": chunks_to_insert})
                    else:
                        raise
                else:
                    raise
        
        return {"status": "success", "chunks_ingested": len(chunks_to_insert)}

    async def list_curriculum(self, course_code: str) -> list[str]:
        course_code = validate_course_code(course_code)
        db = await get_db()
        res = await db.query("SELECT source_title FROM curriculum_chunk WHERE course_code = $code GROUP BY source_title", {"code": course_code})
        if res:
            return sorted([r["source_title"] for r in res])
        return []

    async def get_curriculum_topics(self, course_code: str) -> list[str]:
        course_code = validate_course_code(course_code)
        db = await get_db()
        res = await db.query("SELECT text FROM curriculum_chunk WHERE course_code = $code", {"code": course_code})
        
        topics = set()
        if res:
            for row in res:
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
            SELECT vector::similarity::cosine(embedding, $query_vec) AS similarity 
            FROM curriculum_chunk 
            WHERE course_code = $course 
            AND embedding <|3, 40|> $query_vec
        """
        res = await db.query(curr_query, {"query_vec": query_embedding, "course": course_code})
        
        if res:
            similarities = [r["similarity"] for r in res]
            if max(similarities) > 0.6:
                return True
        
        # 2. Fallback: Search Course Notes
        notes_query = """
            SELECT vector::similarity::cosine(embedding, $query_vec) AS similarity 
            FROM text_chunk 
            WHERE course_code = $course 
            AND embedding <|3, 40|> $query_vec
        """
        res_notes = await db.query(notes_query, {"query_vec": query_embedding, "course": course_code})
        if res_notes:
            similarities = [r["similarity"] for r in res_notes]
            if max(similarities) > 0.6:
                return True
                
        return False
