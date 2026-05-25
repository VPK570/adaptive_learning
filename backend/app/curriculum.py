import uuid
from typing import Any
from app.db import get_collection
from app.rag import RAGPipeline

from app.validation import validate_course_code

class CurriculumManager:
    def __init__(self):
        # We store curriculum in a separate collection per course
        # but keep it within the same RAG pipeline logic
        self.rag = RAGPipeline()

    def _get_curriculum_collection(self, course_code: str):
        course_code = validate_course_code(course_code)
        return get_collection(f"curriculum_{course_code}")

    async def ingest_curriculum(
        self,
        course_code: str,
        document_title: str,
        filepath: str,
    ) -> dict[str, Any]:
        course_code = validate_course_code(course_code)
        from app.pdf_extractor import extract_all_pages
        from app.openrouter import client
        
        collection = self._get_curriculum_collection(course_code)
        pages_content = await extract_all_pages(filepath)
        
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []
        
        for page in pages_content:
            if page.text.strip():
                chunk_id = str(uuid.uuid4())
                ids.append(chunk_id)
                documents.append(page.text)
                metadatas.append({
                    "course_code": course_code,
                    "source_title": document_title,
                    "page": page.page_num,
                    "content_type": "curriculum_text"
                })
        
        if ids:
            embeddings = await client.embed_text_batch(documents)
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
        return {"status": "success", "chunks_ingested": len(ids)}

    def list_curriculum(self, course_code: str) -> list[str]:
        try:
            collection = self._get_curriculum_collection(course_code)
            all_data = collection.get(include=["metadatas"])
            sources = set()
            for meta in (all_data.get("metadatas", []) or []):
                if meta:
                    sources.add(meta.get("source_title", "Unknown"))
            return sorted(list(sources))
        except Exception:
            return []

    def get_curriculum_topics(self, course_code: str) -> list[str]:
        try:
            collection = self._get_curriculum_collection(course_code)
            # Fetch all curriculum text
            all_data = collection.get(include=["documents"])
            documents = all_data.get("documents", []) or []
            
            # Simple extraction of potential "topics" (lines/sentences)
            # In a real app, this would use an LLM or NLP library. 
            # For now, extract potential headers or key terms (e.g., words capitalized or phrases)
            topics = set()
            for doc in documents:
                # Basic heuristic: lines that might be headers
                lines = [line.strip() for line in doc.split('\n') if len(line.strip()) < 50 and len(line.strip()) > 3]
                for line in lines:
                    topics.add(line)
            
            return sorted(list(topics))
        except Exception:
            return []

    async def check_topic_in_curriculum(self, course_code: str, query: str) -> bool:
        course_code = validate_course_code(course_code)
        """
        Checks if the query is relevant to the course curriculum or notes.
        Uses semantic similarity against both.
        """
        from app.openrouter import client
        from app.rag import RAGPipeline
        
        try:
            # 1. Search Curriculum
            curr_collection = self._get_curriculum_collection(course_code)
            # Check if collection exists and has data
            curr_data = curr_collection.get(limit=1)
            
            # If curriculum has content, perform semantic search
            if curr_data.get("ids"):
                query_embedding = await client.embed_text(query)
                results = curr_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=3,
                    include=["distances"]
                )
                
                # Check distances (lower is better, assuming cosine distance)
                # Adjust threshold based on embedding model (0.3-0.5 is usually good for cosine distance)
                if results["distances"] and results["distances"][0]:
                    if min(results["distances"][0]) < 0.4: 
                        return True
            
            # 2. Fallback: Search Course Notes (RAGPipeline)
            rag = RAGPipeline()
            # If search in RAG notes finds something, consider it in-scope
            note_results = await rag.retrieve(query, course_code, top_k=3)
            if note_results:
                # If the best match distance is very good, it's definitely related
                if note_results[0].get("distance", 1.0) < 0.4:
                    return True
            
            return False
        except Exception:
            return False
