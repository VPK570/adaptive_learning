"""OpenRouter client — all LLM and embedding calls via OpenRouter.

Supports:
- Text embeddings (via OpenAI-compatible endpoint)
- Multimodal embeddings (text + images) via Nemotron VL (batched)
- Chat completions (with thinking model support)
"""

import json
import logging
import os
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OpenRouterClient:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = settings.OPENROUTER_BASE_URL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.llm_model = settings.LLM_MODEL
        self._client = httpx.AsyncClient(
            timeout=120,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not set. Set OPENROUTER_API_KEY env var.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://adaptive-learning.local",
            "X-Title": "Adaptive Learning RAG Pipeline",
        }

    async def _api_post(self, path: str, json_body: dict, timeout: int = 30, context: str = "") -> dict:
        try:
            response = await self._client.post(
                f"{self.base_url}{path}",
                headers=self._headers(),
                json=json_body,
                timeout=timeout,
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[{context}] HTTP {e.response.status_code}: {e.response.text[:300]}")
            raise ValueError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        if not response.is_success:
            body = response.text
            logger.error(f"[{context}] HTTP {response.status_code}: {body[:300]}")
            raise ValueError(f"{context} failed: {body[:200]}")
        return response.json()

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(
                f"{self.base_url}/models",
                headers=self._headers(),
                timeout=10,
            )
            return response.is_success
        except Exception as e:
            logger.error(f"[health_check] OpenRouter connectivity error: {e}")
            return False

    async def embed_text(self, text: str) -> list[float]:
        data = await self._api_post("/embeddings", {"model": self.embedding_model, "input": [text]}, timeout=30, context="embed_text")
        if "data" not in data:
            raise ValueError(f"Missing 'data' key: {str(data)[:200]}")
        return data["data"][0]["embedding"]

    async def embed_text_batch(self, texts: list[str]) -> list[list[float]]:
        data = await self._api_post("/embeddings", {"model": self.embedding_model, "input": texts}, timeout=60, context="embed_text_batch")
        if "data" not in data:
            raise ValueError(f"Missing 'data' key: {str(data)[:200]}")
        return [item["embedding"] for item in data["data"]]

    async def embed_images(
        self,
        items: list[dict[str, Any]],
        max_batch_size: int = 5,
    ) -> dict[str, Any]:
        if not items:
            return {"embeddings": [], "skipped": 0, "failed_batches": 0}

        all_embeddings: list[list[float]] = []
        skipped = 0
        failed_batches = 0

        for i in range(0, len(items), max_batch_size):
            batch = items[i:i + max_batch_size]
            batch_num = i // max_batch_size + 1
            try:
                embeds = await self._embed_image_batch(batch)
                all_embeddings.extend(embeds)
            except Exception as e:
                failed_batches += 1
                skipped += len(batch)
                if failed_batches == 1:
                    logger.error(f"  [embed_images] Batch {batch_num} failed (skipping {len(batch)} images): {str(e)[:100]}")

        return {"embeddings": all_embeddings, "skipped": skipped, "failed_batches": failed_batches}

    async def _embed_image_batch(self, items: list[dict[str, Any]]) -> list[list[float]]:
        inputs: list[dict[str, Any]] = []
        for item in items:
            text = item.get("text", "")
            b64_str = item["image_b64"]
            mime = item.get("mime_type", "image/png")
            content: list[dict[str, Any]] = []
            if text:
                content.append({"type": "text", "text": text})
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64_str}"}})
            inputs.append({"content": content})

        try:
            data = await self._api_post("/embeddings", {"model": self.embedding_model, "input": inputs}, timeout=180, context="embed_image_batch")
        except ValueError as e:
            msg = str(e)
            if "26214400" in msg or "payload" in msg.lower():
                total_kb = sum(len(i["image_b64"]) // 1024 for i in items)
                raise ValueError(f"Batch too large ({total_kb}KB): {msg[:100]}")
            raise

        if "data" not in data:
            raise ValueError(f"No 'data' in response: {str(data)[:200]}")
        return [item["embedding"] for item in data["data"]]

    async def embed_image(self, text: str) -> list[float]:
        inputs = [{"content": [{"type": "text", "text": text}]}]
        data = await self._api_post("/embeddings", {"model": self.embedding_model, "input": inputs}, timeout=30, context="embed_image")
        if "data" not in data:
            raise ValueError(f"Missing 'data' key: {str(data)[:200]}")
        return data["data"][0]["embedding"]

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        disable_thinking: bool = True,
    ) -> str:
        model = model or self.llm_model
        request_body: dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        if disable_thinking:
            request_body["thinking"] = {"type": "disabled"}

        data = await self._api_post("/chat/completions", request_body, timeout=120, context="chat")
        return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        model = model or self.llm_model
        request_body: dict[str, Any] = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": True}

        async with self._client.stream(
            "POST", f"{self.base_url}/chat/completions", headers=self._headers(), json=request_body, timeout=120,
        ) as response:
            if not response.is_success:
                body = await response.aread()
                logger.error(f"[stream] HTTP {response.status_code}: {body.decode()[:300]}")
                raise ValueError(f"stream failed: {body.decode()[:200]}")

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    choice = data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    if "thinking" in delta:
                        yield {"type": "thinking", "content": delta["thinking"]}
                    if "content" in delta and delta["content"]:
                        yield {"type": "content", "content": delta["content"]}
                except json.JSONDecodeError:
                    continue

    async def chat_with_schema(
        self,
        messages: list[dict[str, str]],
        response_schema: dict[str, Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        model = model or self.llm_model
        data = await self._api_post("/chat/completions", {
            "model": model, "messages": messages,
            "response_format": {"type": "json_object", "schema": response_schema},
            "temperature": 0.2, "thinking": {"type": "disabled"},
        }, timeout=120, context="chat_with_schema")
        return json.loads(data["choices"][0]["message"]["content"])


_client_singleton: OpenRouterClient | None = None


def get_client() -> OpenRouterClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = OpenRouterClient()
    return _client_singleton


client = get_client()
