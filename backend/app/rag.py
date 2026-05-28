"""RAG pipeline — ingest documents and retrieve via ChromaDB.

Uses two separate ChromaDB collections to handle dimension mismatch:
- text_chunks: text-only content, embedded via Nemotron text mode
- image_chunks: images embedded natively via Nemotron VL (multimodal)

Images are validated via magic bytes in pdf_extractor. Invalid images are skipped.
Images are stored in metadata as reference text only (no base64 — too large for ChromaDB).
"""

import uuid
from typing import Any

from app.config import settings
from app.chunker import chunk_text, clean_text
from app.openrouter import client
from app.db import get_collection


class RAGPipeline:
    def __init__(self):
        self.text_collection = get_collection("text_chunks")
        self.image_collection = get_collection("image_chunks")
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

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for i, (text_chunk, start, end) in enumerate(raw_chunks):
            if not text_chunk.strip():
                continue
            chunk_id = str(uuid.uuid4())
            page_approx = int((start / max(len(cleaned), 1)) * 100) + 1

            ids.append(chunk_id)
            documents.append(text_chunk)
            metadatas.append({
                "course_code": course_code,
                "source_title": document_title,
                "topic": topic,
                "page": page_approx,
                "section": "",
                "difficulty": "",
                "content_type": "text",
                **(metadata or {}),
            })

        self.text_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return {
            "chunks_ingested": len(chunk_texts),
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
            print(f"  Limiting to {self.image_max_per_pdf} images (had {len(valid_items)})")
            valid_items = valid_items[:self.image_max_per_pdf]

        result = await client.embed_images(valid_items, max_batch_size=self.image_max_batch)

        embeddings = result["embeddings"]
        skipped = len(image_items) - len(valid_items) + result["skipped"]

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for i, (item, embedding) in enumerate(zip(valid_items, embeddings)):
            ids.append(str(uuid.uuid4()))
            text_desc = item.get("text", f"Image from {document_title}")
            documents.append(text_desc)
            metadatas.append({
                "course_code": course_code,
                "source_title": document_title,
                "topic": topic,
                "page": item.get("page", 1),
                "content_type": "image",
                "mime_type": item.get("mime_type", "image/png"),
                "image_size_kb": len(item["image_b64"]) // 1024,
                "difficulty": "",
                **(metadata or {}),
            })

        self.image_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return {
            "chunks_ingested": len(embeddings),
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
        from app.pdf_extractor import (
            extract_all_pages,
            count_images_in_pdf,
        )

        stats = count_images_in_pdf(filepath)
        print(f"  PDF: {stats['total_pages']} pages, "
              f"{stats['valid_images']} valid images, "
              f"{stats['invalid_images']} skipped (format), "
              f"{stats['pages_with_images']} pages with images")

        pages_content = await extract_all_pages(filepath)

        text_parts: list[str] = []
        all_image_items: list[dict[str, Any]] = []

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
            text_result = await self.ingest(
                course_code=course_code,
                document_title=document_title,
                text=full_text,
                topic=topic,
                metadata=metadata,
            )

        if all_image_items:
            try:
                image_result = await self.ingest_images(
                    course_code=course_code,
                    document_title=document_title,
                    image_items=all_image_items,
                    topic=topic,
                    metadata=metadata,
                )
            except Exception as e:
                print(f"  ⚠ Image embedding error (text chunks still stored): {e}")
                image_result = {"chunks_ingested": 0, "skipped": len(all_image_items)}

        print(f"  ✓ {text_result['chunks_ingested']} text chunks + "
              f"{image_result['chunks_ingested']} image chunks ingested"
              + (f" ({image_result.get('skipped', 0)} skipped)" if image_result.get("skipped", 0) > 0 else ""))

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

        query_embedding = await client.embed_text(query)

        where_filter: dict[str, Any] = {"course_code": course_code}
        if topic:
            where_filter["topic"] = topic

        seen_ids: set[str] = set()
        all_chunks: list[dict[str, Any]] = []

        # 1. Vector Search (Text)
        if content_type is None or content_type == "text":
            text_results = self.text_collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
            self._process_results(text_results, all_chunks, seen_ids, "text")

        # 2. Keyword Search (Text) - Simple fallback for better recall on specific terms
        # Only do this if we have few results or for text
        if (content_type is None or content_type == "text") and len(query.split()) < 10:
            # We take the first 3 words of the query as keywords
            keywords = [w.lower() for w in query.split() if len(w) > 3][:3]
            for kw in keywords:
                kw_results = self.text_collection.get(
                    where={"$and": [where_filter, {"course_code": course_code}]},
                    where_document={"$contains": kw},
                    limit=5,
                    include=["documents", "metadatas"],
                )
                if kw_results and kw_results["ids"]:
                    # Convert GET results format to match QUERY results format for processing
                    formatted_kw = {
                        "ids": [kw_results["ids"]],
                        "documents": [kw_results["documents"]],
                        "metadatas": [kw_results["metadatas"]],
                        "distances": [[0.1] * len(kw_results["ids"])] # Artificial distance for keyword matches
                    }
                    self._process_results(formatted_kw, all_chunks, seen_ids, "text")

        # 3. Vector Search (Image)
        if content_type is None or content_type == "image":
            image_results = self.image_collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
            self._process_results(image_results, all_chunks, seen_ids, "image")

        all_chunks.sort(key=lambda x: x["distance"])

        if content_type is None and len(all_chunks) > k * 2:
            all_chunks = all_chunks[: k * 2]

        return all_chunks

    def _process_results(self, results, all_chunks, seen_ids, default_type):
        if results and results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                chunk_id = results["ids"][0][i]
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                all_chunks.append({
                    "chunk_id": chunk_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "source_title": meta.get("source_title", "Unknown"),
                    "page": meta.get("page", 1),
                    "topic": meta.get("topic", ""),
                    "content_type": meta.get("content_type", default_type),
                    "distance": results["distances"][0][i] if results["distances"] else 0.5,
                })

    def count_chunks(self, course_code: str) -> int:
        text_count = 0
        img_count = 0

        text_data = self.text_collection.get(where={"course_code": course_code}, include=[])
        text_count = len(text_data.get("ids", [])) if text_data else 0

        img_data = self.image_collection.get(where={"course_code": course_code}, include=[])
        img_count = len(img_data.get("ids", [])) if img_data else 0

        return text_count + img_count

    def delete_course(self, course_code: str) -> int:
        deleted = 0
        for coll in [self.text_collection, self.image_collection]:
            results = coll.get(where={"course_code": course_code})
            ids_to_delete = results.get("ids", []) if results else []
            if ids_to_delete:
                coll.delete(ids=ids_to_delete)
                deleted += len(ids_to_delete)
        return deleted

    def list_courses(self) -> list[str]:
        course_codes: set[str] = set()
        for coll in [self.text_collection, self.image_collection]:
            all_data = coll.get(include=["metadatas"])
            for meta in (all_data.get("metadatas") or []):
                cc = meta.get("course_code", "") if meta else ""
                if cc:
                    course_codes.add(cc)
        return sorted(list(course_codes))

    def get_course_stats(self, course_code: str) -> dict[str, Any]:
        topic_counts: dict[str, int] = {}
        doc_counts: dict[str, int] = {}
        image_chunks = 0
        text_chunks = 0

        for coll in [self.text_collection, self.image_collection]:
            all_data = coll.get(where={"course_code": course_code}, include=["metadatas"])
            for meta in (all_data.get("metadatas", []) or []):
                if not meta: continue
                
                t = meta.get("topic", "")
                if t:
                    topic_counts[t] = topic_counts.get(t, 0) + 1
                
                d = meta.get("source_title", "Unknown")
                doc_counts[d] = doc_counts.get(d, 0) + 1
                
                ct = meta.get("content_type", "text")
                if ct == "image":
                    image_chunks += 1
                else:
                    text_chunks += 1

        return {
            "course_code": course_code,
            "total_chunks": text_chunks + image_chunks,
            "text_chunks": text_chunks,
            "image_chunks": image_chunks,
            "topics": [
                {"topic": t, "chunks": c}
                for t, c in sorted(topic_counts.items(), key=lambda x: -x[1])
            ],
            "documents": [
                {"name": d, "chunks": c}
                for d, c in sorted(doc_counts.items(), key=lambda x: -x[1])
            ],
        }