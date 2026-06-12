from typing import Any
from app.config import settings
from app.chunker import chunk_text, clean_text
from app.openrouter import client
from app.db import get_db

class RAGPipeline:
    def __init__(self):
        self.top_k = settings.RAG_TOP_K
        self.chunk_size = settings.CHUNK_SIZE
        self.overlap = settings.CHUNK_OVERLAP_TOKENS
        self.image_max_batch = getattr(settings, "IMAGE_MAX_BATCH_SIZE", 5)
        self.image_max_per_pdf = getattr(settings, "IMAGE_MAX_PER_PDF", 50)

    async def ingest(
        self,
        course_code: str,
        document_title: str,
        text: str,
        topic: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cleaned = clean_text(text)
        raw_chunks = chunk_text(cleaned, self.chunk_size, self.overlap)

        if not raw_chunks:
            return {"chunks_ingested": 0, "error": "No content to chunk"}

        chunk_texts = [ct for ct, _, _ in raw_chunks if ct.strip()]

        if not chunk_texts:
            return {"chunks_ingested": 0, "error": "No non-empty chunks to embed"}

        embeddings = await client.embed_text_batch(chunk_texts)
        db = await get_db()

        chunks_to_insert = []
        for i, (text_chunk, start, end) in enumerate(raw_chunks):
            if not text_chunk.strip():
                continue
            page_approx = int((start / max(len(cleaned), 1)) * 100) + 1

            chunk_data = {
                "course_code": course_code,
                "source_title": document_title,
                "topic": topic,
                "page": page_approx,
                "text": text_chunk,
                "embedding": embeddings[i],
                "content_type": "text",
                **(metadata or {}),
            }
            chunks_to_insert.append(chunk_data)

        if chunks_to_insert:
            await db.query("INSERT INTO text_chunk $chunks", {"chunks": chunks_to_insert})

        return {
            "chunks_ingested": len(chunks_to_insert),
            "course_code": course_code,
            "document_title": document_title,
        }

    async def ingest_images(
        self,
        course_code: str,
        document_title: str,
        image_items: list[dict[str, Any]],
        topic: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not image_items:
            return {"chunks_ingested": 0, "skipped": 0}

        valid_items = []
        for item in image_items:
            b64 = item["image_b64"]
            if not isinstance(b64, str) or len(b64) < 100:
                continue
            valid_items.append(item)

        if not valid_items:
            return {"chunks_ingested": 0, "skipped": len(image_items)}

        if len(valid_items) > self.image_max_per_pdf:
            valid_items = valid_items[:self.image_max_per_pdf]

        result = await client.embed_images(valid_items, max_batch_size=self.image_max_batch)
        embeddings = result["embeddings"]
        skipped = len(image_items) - len(valid_items) + result["skipped"]

        db = await get_db()
        chunks_to_insert = []
        for item, embedding in zip(valid_items, embeddings):
            text_desc = item.get("text", f"Image from {document_title}")
            chunk_data = {
                "course_code": course_code,
                "source_title": document_title,
                "topic": topic,
                "page": item.get("page", 1),
                "text": text_desc,
                "embedding": embedding,
                "content_type": "image",
                "mime_type": item.get("mime_type", "image/png"),
                "image_size_kb": len(item["image_b64"]) // 1024,
                **(metadata or {}),
            }
            chunks_to_insert.append(chunk_data)

        if chunks_to_insert:
            await db.query("INSERT INTO image_chunk $chunks", {"chunks": chunks_to_insert})

        return {
            "chunks_ingested": len(chunks_to_insert),
            "skipped": skipped,
            "course_code": course_code,
            "document_title": document_title,
        }

    async def ingest_pdf(
        self,
        course_code: str,
        document_title: str,
        filepath: str,
        topic: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from app.pdf_extractor import extract_all_pages
        pages_content = await extract_all_pages(filepath)

        text_parts = []
        all_image_items = []

        for page in pages_content:
            if page.text.strip():
                text_parts.append(f"[Page {page.page_num}]\n{page.text}")
            for img in page.images:
                all_image_items.append({
                    "image_b64": img.b64_str,
                    "mime_type": img.mime_type,
                    "page": page.page_num,
                    "text": f"Diagram from {document_title}, Page {page.page_num}",
                })

        text_result = {"chunks_ingested": 0}
        image_result = {"chunks_ingested": 0, "skipped": 0}

        if text_parts:
            full_text = "\n\n".join(text_parts)
            text_result = await self.ingest(course_code, document_title, full_text, topic, metadata)

        if all_image_items:
            image_result = await self.ingest_images(course_code, document_title, all_image_items, topic, metadata)

        return {
            "text_chunks": text_result["chunks_ingested"],
            "image_chunks": image_result["chunks_ingested"],
            "total_chunks": text_result["chunks_ingested"] + image_result["chunks_ingested"],
            "course_code": course_code,
            "document_title": document_title,
        }

    async def retrieve(
        self,
        query: str,
        course_code: str,
        top_k: int | None = None,
        topic: str | None = None,
        content_type: str | None = None,
    ) -> list[dict[str, Any]]:
        k = top_k or self.top_k
        db = await get_db()

        text_results = []
        image_results = []

        # 1. Hybrid Search (Text)
        if content_type is None or content_type == "text":
            query_embedding = await client.embed_text(query)
            
            # A. Vector Search
            vector_query = f"""
                SELECT *, vector::similarity::cosine(embedding, $query_vec) AS similarity 
                FROM text_chunk 
                WHERE course_code = $course 
                AND embedding <|{k}, 40|> $query_vec
            """
            v_params = {"query_vec": query_embedding, "course": course_code}
            if topic:
                vector_query += " AND topic = $topic"
                v_params["topic"] = topic
            
            vector_hits = await db.query(vector_query, v_params)
            if not isinstance(vector_hits, list):
                vector_hits = []
            
            for hit in vector_hits:
                hit["distance"] = 1.0 - hit.get("similarity", 0.0)

            # B. BM25 Search
            bm25_query = f"""
                SELECT *, search::score(0) AS bm25_score 
                FROM text_chunk 
                WHERE course_code = $course 
                AND text @0@ $query
                LIMIT {k}
            """
            b_params = {"query": query, "course": course_code}
            if topic:
                bm25_query += " AND topic = $topic"
                b_params["topic"] = topic
            
            bm25_hits = await db.query(bm25_query, b_params)
            if not isinstance(bm25_hits, list):
                bm25_hits = []

            # C. Reciprocal Rank Fusion (RRF)
            rrf_k = 60
            scores = {}
            doc_map = {}

            for rank, doc in enumerate(vector_hits):
                doc_id = str(doc["id"])
                doc_map[doc_id] = doc
                scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)
            
            for rank, doc in enumerate(bm25_hits):
                doc_id = str(doc["id"])
                if doc_id not in doc_map:
                    doc_map[doc_id] = doc
                scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)

            sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
            text_results = [doc_map[doc_id] for doc_id in sorted_ids[:k]]
            for doc in text_results:
                doc["chunk_id"] = str(doc["id"])

        # 2. Vector Search (Image)
        if content_type is None or content_type == "image":
            query_embedding = await client.embed_image(query)
            img_query = f"""
                SELECT *, vector::similarity::cosine(embedding, $query_vec) AS similarity 
                FROM image_chunk 
                WHERE course_code = $course 
                AND embedding <|{k}, 40|> $query_vec
            """
            image_hits = await db.query(img_query, {"query_vec": query_embedding, "course": course_code})
            if isinstance(image_hits, list):
                for row in image_hits:
                    row["chunk_id"] = str(row["id"])
                    row["distance"] = 1.0 - row.get("similarity", 0.0)
                    image_results.append(row)

        if content_type == "text":
            return text_results
        if content_type == "image":
            image_results.sort(key=lambda x: x.get("distance", 1.0))
            return image_results
        
        # Combined results
        all_results = text_results + image_results
        # Simple heuristic to interleave or sort combined
        return all_results[:k*2]

    async def get_course_stats(self, course_code: str) -> dict[str, Any]:
        db = await get_db()
        
        # Count chunks
        text_count_res = await db.query("SELECT count() FROM text_chunk WHERE course_code = $code GROUP ALL", {"code": course_code})
        img_count_res = await db.query("SELECT count() FROM image_chunk WHERE course_code = $code GROUP ALL", {"code": course_code})
        
        text_chunks = text_count_res[0]["count"] if isinstance(text_count_res, list) and len(text_count_res) > 0 else 0
        image_chunks = img_count_res[0]["count"] if isinstance(img_count_res, list) and len(img_count_res) > 0 else 0
        
        # Topics and documents
        topics_res = await db.query("SELECT topic, count() as count FROM (SELECT topic FROM text_chunk WHERE course_code = $code) GROUP BY topic", {"code": course_code})
        
        docs_text = await db.query("SELECT source_title FROM text_chunk WHERE course_code = $code GROUP BY source_title", {"code": course_code})
        docs_img = await db.query("SELECT source_title FROM image_chunk WHERE course_code = $code GROUP BY source_title", {"code": course_code})
        
        all_doc_names = set()
        if isinstance(docs_text, list):
            for r in docs_text:
                all_doc_names.add(r["source_title"])
        if isinstance(docs_img, list):
            for r in docs_img:
                all_doc_names.add(r["source_title"])
        
        return {
            "course_code": course_code,
            "total_chunks": text_chunks + image_chunks,
            "text_chunks": text_chunks,
            "image_chunks": image_chunks,
            "topics": [{"topic": r["topic"], "chunks": r["count"]} for r in (topics_res if isinstance(topics_res, list) else []) if r.get("topic")],
            "documents": [{"name": name} for name in all_doc_names],
        }

    async def delete_course(self, course_code: str) -> int:
        db = await get_db()
        res1 = await db.query("DELETE text_chunk WHERE course_code = $code", {"code": course_code})
        res2 = await db.query("DELETE image_chunk WHERE course_code = $code", {"code": course_code})
        return len(res1 if res1 else []) + len(res2 if res2 else [])

    async def count_chunks(self, course_code: str) -> int:
        stats = await self.get_course_stats(course_code)
        return stats["total_chunks"]

    async def list_courses(self) -> list[str]:
        db = await get_db()
        res_text = await db.query("SELECT course_code FROM text_chunk GROUP BY course_code")
        res_img = await db.query("SELECT course_code FROM image_chunk GROUP BY course_code")
        
        all_courses = set()
        if isinstance(res_text, list):
            for r in res_text:
                all_courses.add(r["course_code"])
        if isinstance(res_img, list):
            for r in res_img:
                all_courses.add(r["course_code"])
                
        return sorted(list(all_courses))
