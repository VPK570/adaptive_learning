import hashlib
import logging
from typing import Any

from app.chunker import chunk_text, clean_text
from app.config import settings
from app.db import get_db
from app.provider_router import router as client

logger = logging.getLogger(__name__)


def calculate_file_hash(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


class RAGPipeline:
    def __init__(self):
        self.top_k = settings.RAG_TOP_K
        self.chunk_size = settings.CHUNK_SIZE
        self.overlap = settings.CHUNK_OVERLAP_TOKENS
        self.image_max_batch = getattr(settings, "IMAGE_MAX_BATCH_SIZE", 5)
        self.image_max_per_pdf = getattr(settings, "IMAGE_MAX_PER_PDF", 50)
        self.rrf_k = settings.RRF_K
        self.ef_search = settings.HNSW_EF_SEARCH

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

        valid_chunks = [(ct, s, e) for ct, s, e in raw_chunks if ct.strip()]

        if not valid_chunks:
            return {"chunks_ingested": 0, "error": "No non-empty chunks to embed"}

        chunk_texts = [ct for ct, _, _ in valid_chunks]
        embeddings = await client.embed_text_batch(chunk_texts)
        db = await get_db()

        import re

        from app.chunker import extract_page_for_chunk

        chunks_to_insert = []
        for (text_chunk, start, end), emb in zip(valid_chunks, embeddings):
            page_num = extract_page_for_chunk(text_chunk, cleaned, start)

            # Clean markers from the chunk text before storing
            text_chunk_clean = re.sub(r"\[Page \d+\]", "", text_chunk).strip()
            if not text_chunk_clean:
                continue

            chunk_data = {
                "course_code": course_code,
                "source_title": document_title,
                "topic": topic,
                "page": page_num,
                "text": text_chunk_clean,
                "embedding": emb,
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
        file_size: int = 0,
        file_url: str = "",
    ) -> dict[str, Any]:
        db = await get_db()
        content_hash = calculate_file_hash(filepath)

        # Check if already ingested
        existing = await db.query(
            "SELECT id FROM document WHERE course_code = $course AND content_hash = $hash",
            {"course": course_code, "hash": content_hash}
        )
        if existing:
            existing_id = existing[0]["id"]
            await db.query(
                "UPDATE $id SET file_path = $fp, file_url = $fu, file_size = $fs",
                {"id": existing_id, "fp": filepath, "fu": file_url, "fs": file_size}
            )
            return {
                "text_chunks": 0, "image_chunks": 0, "total_chunks": 0,
                "course_code": course_code, "document_title": document_title,
                "status": "already_ingested", "doc_id": str(existing_id),
            }

        from app.chunker import chunk_by_topic_regions
        from app.pdf_extractor import detect_sections, extract_all_pages
        from app.topics import (
            classify_sections_embedding,
            classify_sections_fallback,
            classify_sections_llm,
            extract_extra_topics_llm,
            get_course_topics,
            resolve_topic_boundaries,
        )

        pages_content = await extract_all_pages(filepath)

        # Collect image items separately (unchanged path)
        all_image_items = []
        for page in pages_content:
            for img in page.images:
                all_image_items.append({
                    "image_b64": img.b64_str, "mime_type": img.mime_type,
                    "page": page.page_num,
                    "text": f"Diagram from {document_title}, Page {page.page_num}",
                })

        # ── Late chunking pipeline: detect sections → classify → chunk within topics ──
        sections = detect_sections(pages_content) if pages_content else []

        classifications = None
        if sections:
            try:
                classifications = await classify_sections_llm(sections, course_code)
            except Exception:
                logger.warning("classify_sections_llm failed", exc_info=True)
            if classifications is None:
                try:
                    classifications = await classify_sections_embedding(sections, course_code)
                except Exception:
                    logger.warning("classify_sections_embedding failed", exc_info=True)
            if classifications is None:
                try:
                    classifications = await classify_sections_fallback(sections, course_code)
                except Exception:
                    logger.warning("classify_sections_fallback failed", exc_info=True)

        if classifications:
            topic_regions = resolve_topic_boundaries(sections, classifications)
        elif sections:
            topic_regions = [{
                "topic": "uncategorized", "heading": document_title,
                "page_start": sections[0].page_start,
                "page_end": sections[-1].page_end,
                "text": "\n\n".join(s.text for s in sections),
            }]
        else:
            topic_regions = []

        all_chunks = chunk_by_topic_regions(topic_regions, self.chunk_size, self.overlap)

        # Embed and store text chunks (grouped by topic for batch embedding)
        text_chunks_ingested = 0
        chunks_to_insert = []
        if all_chunks:
            topic_groups = {}
            for chunk in all_chunks:
                topic_groups.setdefault(chunk.topic, []).append(chunk)

            for topic_name, chunk_group in topic_groups.items():
                valid_chunks = [c for c in chunk_group if c.text.strip()]
                texts = [c.text for c in valid_chunks]
                if not texts:
                    continue
                try:
                    embeddings = await client.embed_text_batch(texts)
                except Exception:
                    logger.warning("embed_text_batch failed — per-chunk fallback", exc_info=True)
                    embeddings = []
                    for t in texts:
                        try:
                            embeddings.append(await client.embed_text(t))
                        except Exception:
                            embeddings.append(None)

                for chunk, emb in zip(valid_chunks, embeddings):
                    if emb is None:
                        continue
                    chunks_to_insert.append({
                        "course_code": course_code,
                        "source_title": document_title,
                        "topic": chunk.topic,
                        "page": chunk.page,
                        "section_heading": chunk.section_heading,
                        "text": chunk.text,
                        "embedding": emb,
                        "content_type": "text",
                    })

            if chunks_to_insert:
                await db.query("INSERT INTO text_chunk $chunks", {"chunks": chunks_to_insert})
                text_chunks_ingested = len(chunks_to_insert)

        # Images (unchanged)
        image_result = {"chunks_ingested": 0, "skipped": 0}
        if all_image_items:
            image_result = await self.ingest_images(course_code, document_title, all_image_items, topic, metadata)

        # ── Coverage calculation ──
        total_chunks = len(chunks_to_insert)
        course_topics = await get_course_topics(course_code)

        topic_data = {}
        for chunk in chunks_to_insert:
            t = chunk["topic"]
            topic_data.setdefault(t, {"count": 0, "pages": set()})
            topic_data[t]["count"] += 1
            topic_data[t]["pages"].add(chunk["page"])

        topics_coverage = []
        for t in course_topics:
            name = t["topic_name"]
            data = topic_data.get(name, {"count": 0, "pages": set()})
            pct = (data["count"] / total_chunks * 100) if total_chunks > 0 else 0
            pages = sorted(data["pages"])
            topics_coverage.append({
                "topic_name": name, "chunk_count": data["count"],
                "coverage_pct": round(pct, 1),
                "page_min": pages[0] if pages else None,
                "page_max": pages[-1] if pages else None,
                "depth": "mention" if pct < 15 else "moderate" if pct < 40 else "comprehensive",
            })

        # Module-level coverage (gap-based grouping by order_index)
        modules = []
        current_module = {"topics": []}
        last_idx = None
        for t in sorted(course_topics, key=lambda x: x.get("order_index", 0)):
            idx = t.get("order_index", 0)
            if last_idx is not None and idx - last_idx > 2:
                modules.append(current_module)
                current_module = {"topics": []}
            current_module["topics"].append(t["topic_name"])
            last_idx = idx
        if current_module["topics"]:
            modules.append(current_module)

        module_coverage = []
        for i, m in enumerate(modules, 1):
            covered = sum(1 for t in m["topics"] if topic_data.get(t, {}).get("count", 0) > 0)
            module_coverage.append({
                "module": f"Module {i}", "topics_total": len(m["topics"]),
                "topics_covered": covered,
                "coverage_pct": round(covered / len(m["topics"]) * 100, 1) if m["topics"] else 0,
            })

        # Extra topics from uncategorized chunks
        uncategorized_chunks = [
            {"text": c.text, "page_start": c.page, "page_end": c.page}
            for c in all_chunks if c.topic == "uncategorized"
        ] if all_chunks else []
        extra_topics = []
        if uncategorized_chunks:
            try:
                extra_topics = await extract_extra_topics_llm(uncategorized_chunks[:10], course_code)
            except Exception:
                logger.warning("extract_extra_topics_llm failed", exc_info=True)

        topic_analysis = {
            "topics": topics_coverage,
            "module_coverage": module_coverage,
            "extra_topics": extra_topics,
            "total_chunks": total_chunks,
            "uncategorized_chunks": len(uncategorized_chunks),
        }

        # Store document record
        from datetime import datetime
        try:
            result = await db.query(
                "INSERT INTO document $doc RETURN id",
                {"doc": {
                    "course_code": course_code, "filename": document_title,
                    "content_hash": content_hash, "doc_type": "material",
                    "created_at": datetime.now().isoformat(),
                    "file_path": filepath, "file_url": file_url,
                    "file_size": file_size, "topic_analysis": topic_analysis,
                }}
            )
        except Exception:
            # Cleanup orphaned chunks on failure
            await db.query(
                "DELETE text_chunk WHERE course_code = $code AND source_title = $title",
                {"code": course_code, "title": document_title},
            )
            await db.query(
                "DELETE image_chunk WHERE course_code = $code AND source_title = $title",
                {"code": course_code, "title": document_title},
            )
            raise
        doc_id = str(result[0]["id"]) if result and len(result) > 0 else None

        return {
            "text_chunks": text_chunks_ingested,
            "image_chunks": image_result["chunks_ingested"],
            "total_chunks": text_chunks_ingested + image_result["chunks_ingested"],
            "course_code": course_code, "document_title": document_title,
            "topic_analysis": topic_analysis, "doc_id": doc_id,
        }

    async def retrieve(
        self,
        query: str,
        course_code: str,
        top_k: int | None = None,
        topic: str | None = None,
        content_type: str | None = None,
        source_titles: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        k = top_k or self.top_k
        db = await get_db()

        text_results = []

        # 1. Hybrid Search (Text)
        if content_type is None or content_type == "text":
            query_embedding = await client.embed_text(query)

            # A. Vector Search
            vector_query = f"""
                SELECT *, vector::similarity::cosine(embedding, $query_vec) AS similarity 
                FROM text_chunk 
                WHERE course_code = $course 
                AND embedding <|{k}, {self.ef_search}|> $query_vec
            """
            v_params = {"query_vec": query_embedding, "course": course_code}
            if topic:
                vector_query += " AND topic = $topic"
                v_params["topic"] = topic
            if source_titles:
                vector_query += " AND source_title IN $sources"
                v_params["sources"] = source_titles
            if topics:
                vector_query += " AND topic IN $topics_list"
                v_params["topics_list"] = topics

            vector_hits = await db.query(vector_query, v_params)
            if not isinstance(vector_hits, list):
                vector_hits = []

            # Apply similarity threshold
            vector_hits = [h for h in vector_hits if h.get("similarity", 0) >= settings.RAG_MIN_SIMILARITY]

            for hit in vector_hits:
                hit["distance"] = 1.0 - hit.get("similarity", 0.0)

            # C. Vector Search (Curriculum)
            curr_hits = []
            if content_type is None:
                curr_query = f"""
                    SELECT *, vector::similarity::cosine(embedding, $query_vec) AS similarity 
                    FROM curriculum_chunk 
                    WHERE course_code = $course 
                    AND embedding <|{k}, {self.ef_search}|> $query_vec
                """
                c_params = {"query_vec": query_embedding, "course": course_code}
                if topic:
                    curr_query += " AND topic = $topic"
                    c_params["topic"] = topic
                if source_titles:
                    curr_query += " AND source_title IN $sources"
                    c_params["sources"] = source_titles
                if topics:
                    curr_query += " AND topic IN $topics_list"
                    c_params["topics_list"] = topics

                curr_hits = await db.query(curr_query, c_params)
                if not isinstance(curr_hits, list):
                    curr_hits = []
                curr_hits = [h for h in curr_hits if h.get("similarity", 0) >= settings.RAG_MIN_SIMILARITY]
                for hit in curr_hits:
                    hit["distance"] = 1.0 - hit.get("similarity", 0.0)
                    hit["source_type"] = "curriculum"

            # D. Reciprocal Rank Fusion (RRF)
            rrf_k = self.rrf_k
            scores = {}
            doc_map = {}

            for rank, doc in enumerate(vector_hits):
                doc_id = str(doc["id"])
                doc_map[doc_id] = doc
                scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)

            for rank, doc in enumerate(curr_hits):
                doc_id = str(doc["id"])
                if doc_id not in doc_map:
                    doc_map[doc_id] = doc
                scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (rrf_k + rank + 1)

            sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
            text_results = [doc_map[doc_id] for doc_id in sorted_ids[:k]]
            for doc in text_results:
                doc["chunk_id"] = str(doc["id"])

        return text_results

    async def get_course_stats(self, course_code: str) -> dict[str, Any]:
        db = await get_db()

        text_count_res = await db.query("SELECT count() FROM text_chunk WHERE course_code = $code GROUP ALL", {"code": course_code})
        img_count_res = await db.query("SELECT count() FROM image_chunk WHERE course_code = $code GROUP ALL", {"code": course_code})

        text_chunks = text_count_res[0]["count"] if isinstance(text_count_res, list) and len(text_count_res) > 0 else 0
        image_chunks = img_count_res[0]["count"] if isinstance(img_count_res, list) and len(img_count_res) > 0 else 0

        topics_res = await db.query("SELECT topic, count() as count FROM (SELECT topic FROM text_chunk WHERE course_code = $code) GROUP BY topic", {"code": course_code})

        docs_text = await db.query("SELECT source_title FROM text_chunk WHERE course_code = $code GROUP BY source_title", {"code": course_code})
        docs_img = await db.query("SELECT source_title FROM image_chunk WHERE course_code = $code GROUP BY source_title", {"code": course_code})
        docs_curr = await db.query("SELECT source_title FROM curriculum_chunk WHERE course_code = $code GROUP BY source_title", {"code": course_code})

        all_doc_names = set()
        if isinstance(docs_text, list):
            for r in docs_text:
                all_doc_names.add(r["source_title"])
        if isinstance(docs_img, list):
            for r in docs_img:
                all_doc_names.add(r["source_title"])

        curr_doc_names = set()
        if isinstance(docs_curr, list):
            for r in docs_curr:
                curr_doc_names.add(r["source_title"])

        doc_rows = await db.query(
            "SELECT filename, file_url, file_size, doc_type, topic_analysis FROM document WHERE course_code = $code",
            {"code": course_code},
        ) or []
        documents = [{
            "name": r["filename"],
            "file_url": r.get("file_url"),
            "file_size": r.get("file_size"),
            "doc_type": r.get("doc_type"),
            "topic_analysis": r.get("topic_analysis"),
        } for r in doc_rows if r.get("filename")]
        if not documents:
            documents = [{"name": name} for name in sorted(all_doc_names)]

        return {
            "course_code": course_code,
            "total_chunks": text_chunks + image_chunks,
            "text_chunks": text_chunks,
            "image_chunks": image_chunks,
            "topics": [{"topic": r["topic"], "chunks": r["count"]} for r in (topics_res if isinstance(topics_res, list) else []) if r.get("topic")],
            "documents": documents,
            "curriculum_docs": [{"name": name} for name in curr_doc_names],
        }

    async def get_batch_stats(self, course_codes: list[str]) -> dict[str, dict[str, Any]]:
        if not course_codes:
            return {}
        db = await get_db()
        text_res = await db.query(
            "SELECT course_code, count() as total FROM text_chunk WHERE course_code IN $codes GROUP BY course_code",
            {"codes": course_codes},
        ) or []
        img_res = await db.query(
            "SELECT course_code, count() as total FROM image_chunk WHERE course_code IN $codes GROUP BY course_code",
            {"codes": course_codes},
        ) or []
        text_counts = {r["course_code"]: r["total"] for r in text_res}
        img_counts = {r["course_code"]: r["total"] for r in img_res}
        result = {}
        for cc in course_codes:
            tc = text_counts.get(cc, 0)
            ic = img_counts.get(cc, 0)
            # Query document table for actual document counts
            doc_res = await db.query(
                "SELECT course_code, count() as doc_count FROM document WHERE course_code = $code GROUP BY course_code",
                {"code": cc},
            ) or []
            dc = doc_res[0]["doc_count"] if doc_res else 0
            qres = await db.query(
                "SELECT count() AS c FROM query_log WHERE course_code = $code GROUP ALL",
                {"code": cc},
            ) or []
            total_queries = qres[0]["c"] if qres else 0
            uids = set()
            for tbl, col in (("query_log", "user_id"), ("quiz", "user_id"), ("knowledge_state", "student_id")):
                r = await db.query(
                    f"SELECT {col} AS uid FROM {tbl} WHERE course_code = $code GROUP BY {col}",
                    {"code": cc},
                ) or []
                uids |= {row["uid"] for row in r if row.get("uid")}
            result[cc] = {"total_chunks": tc + ic, "chunk_count": tc + ic, "doc_count": dc,
                          "student_count": len(uids), "total_queries": total_queries}
        return result

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
