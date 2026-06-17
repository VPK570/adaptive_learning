"""OpenRouter client — all LLM and embedding calls via OpenRouter.

Supports:
- Text embeddings (via OpenAI-compatible endpoint)
- Multimodal embeddings (text + images) via Nemotron VL (batched)
- Chat completions (with thinking model support)
"""

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
        # Single shared client — reuses connections (pooling) instead of
        # opening a new connection pool on every call.
        self._client = httpx.AsyncClient(
            timeout=120,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def aclose(self) -> None:
        """Close the shared client. Call on application shutdown."""
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

    async def health_check(self) -> bool:
        """Verify API connectivity by fetching available models."""
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
        try:
            response = await self._client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json={
                    "model": self.embedding_model,
                    "input": [text],
                },
                timeout=30,
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[embed_text] HTTP {e.response.status_code}: {e.response.text[:300]}")
            raise

        # Handle non-success response
        if not response.is_success:
            try:
                data = response.json()
                error_msg = data.get("error", {}).get("message", response.text)
            except Exception:
                error_msg = response.text
            logger.error(f"[embed_text] HTTP {response.status_code}: {error_msg}")
            raise ValueError(f"embed_text failed: {error_msg}")

        data = response.json()
        if "data" not in data:
            logger.error(f"[embed_text] Missing 'data' key: {str(data)[:300]}")
            raise ValueError(f"Missing 'data' key: {str(data)[:200]}")
        return data["data"][0]["embedding"]

    async def embed_text_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self._client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json={
                    "model": self.embedding_model,
                    "input": texts,
                },
                timeout=60,
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[embed_text_batch] HTTP {e.response.status_code}: {e.response.text[:300]}")
            logger.warning(f"Texts count: {len(texts)}, sizes: {[len(t) for t in texts[:5]]}")
            raise
        body = response.text
        if not response.is_success:
            logger.error(f"[embed_text_batch] HTTP {response.status_code}: {body[:300]}")
            logger.warning(f"Texts count: {len(texts)}, sizes: {[len(t) for t in texts[:5]]}")
            raise ValueError(f"embed_text_batch failed: {body[:200]}")
        try:
            data = response.json()
        except Exception:
            logger.error(f"[embed_text_batch] Non-JSON: {body[:300]}")
            raise ValueError(f"Non-JSON response: {body[:200]}")
        if "data" not in data:
            logger.error(f"[embed_text_batch] Missing 'data' key. Keys: {list(data.keys())}")
            logger.warning(f"Body: {str(data)[:500]}")
            raise ValueError(f"Missing 'data' key: {str(data)[:200]}")
        return [item["embedding"] for item in data["data"]]

    async def embed_images(
        self,
        items: list[dict[str, Any]],
        max_batch_size: int = 5,
    ) -> dict[str, Any]:
        """
        Embed images in batches, skipping failed batches gracefully.

        Each item should have:
          - "image_b64": str — base64-encoded image data
          - "mime_type": str — MIME type (image/jpeg, image/png, etc.)
          - "text": str — optional description

        Returns: {embeddings: list[list[float]], skipped: int, failed_batches: int}
        """
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
                msg = str(e)[:100]
                if failed_batches == 1:
                    logger.error(f"  [embed_images] Batch {batch_num} failed (skipping {len(batch)} images): {msg}")

        return {
            "embeddings": all_embeddings,
            "skipped": skipped,
            "failed_batches": failed_batches,
        }

    async def _embed_image_batch(self, items: list[dict[str, Any]]) -> list[list[float]]:
        """Embed a single batch of images. Raises on failure."""
        inputs: list[dict[str, Any]] = []
        for item in items:
            text = item.get("text", "")
            b64_str = item["image_b64"]
            mime = item.get("mime_type", "image/png")

            content: list[dict[str, Any]] = []
            if text:
                content.append({"type": "text", "text": text})
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64_str}"},
            })
            inputs.append({"content": content})

        try:
            response = await self._client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json={"model": self.embedding_model, "input": inputs},
                timeout=180,
            )
        except httpx.HTTPStatusError as e:
            raise ValueError(f"HTTP {e.response.status_code}: {e.response.text[:200]}")
        if not response.is_success:
            body = response.text
            try:
                data = response.json()
                if "error" in data:
                    msg = str(data["error"])
                    if "26214400" in msg or "payload" in msg.lower():
                        total_kb = sum(len(i["image_b64"]) // 1024 for i in items)
                        raise ValueError(f"Batch too large ({total_kb}KB): {msg[:100]}")
                    raise ValueError(f"API error: {msg[:200]}")
            except Exception:
                pass
            raise ValueError(f"HTTP {response.status_code}: {body[:200]}")

        data = response.json()
        if "data" not in data:
            raise ValueError(f"No 'data' in response: {str(data)[:200]}")
        return [item["embedding"] for item in data["data"]]

    async def embed_image(self, text: str) -> list[float]:
        """
        Embed a single text query for image search.
        Uses the multimodal format to ensure 1024-dim embeddings match stored image vectors.
        """
        inputs = [{"content": [{"type": "text", "text": text}]}]
        try:
            response = await self._client.post(
                f"{self.base_url}/embeddings",
                headers=self._headers(),
                json={
                    "model": self.embedding_model,
                    "input": inputs,
                },
                timeout=30,
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[embed_image] HTTP {e.response.status_code}: {e.response.text[:300]}")
            raise

        if not response.is_success:
            raise ValueError(f"embed_image failed: {response.text[:200]}")

        data = response.json()
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

        request_body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if disable_thinking:
            request_body["thinking"] = {"type": "disabled"}

        try:
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=request_body,
                timeout=120,
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[chat] HTTP {e.response.status_code}: {e.response.text[:300]}")
            raise
        if not response.is_success:
            logger.error(f"[chat] HTTP {response.status_code}: {response.text[:300]}")
            raise ValueError(f"chat failed: {response.text[:200]}")
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ):
        model = model or self.llm_model

        request_body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        async with self._client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self._headers(),
            json=request_body,
            timeout=120,
        ) as response:
            if not response.is_success:
                body = await response.aread()
                logger.error(f"[stream] HTTP {response.status_code}: {body.decode()[:300]}")
                raise ValueError(f"stream failed: {body.decode()[:200]}")

            import json
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

        try:
            response = await self._client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "response_format": {"type": "json_object", "schema": response_schema},
                    "temperature": 0.2,
                    "thinking": {"type": "disabled"},
                },
                timeout=120,
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"[chat_with_schema] HTTP {e.response.status_code}: {e.response.text[:300]}")
            raise
        if not response.is_success:
            logger.error(f"[chat_with_schema] HTTP {response.status_code}: {response.text[:300]}")
            raise ValueError(f"chat_with_schema failed: {response.text[:200]}")
        data = response.json()
        import json
        return json.loads(data["choices"][0]["message"]["content"])


_client_singleton: OpenRouterClient | None = None


def get_client() -> OpenRouterClient:
    global _client_singleton
    if _client_singleton is None:
        _client_singleton = OpenRouterClient()
    return _client_singleton


client = get_client()
