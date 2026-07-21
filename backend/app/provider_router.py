"""Multi-provider LLM router with per-provider multi-key rotation.

Routes:
  - Chat completions (chat, stream, chat_with_schema) → Google Gemini
  - Embeddings (text, image) → OpenRouter

Each provider accepts multiple API keys. On 429, the key is put in cooldown
and the next key is tried automatically.
"""

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class KeyRing:
    """Round-robin key pool with per-key cooldown on 429."""

    def __init__(self, keys: list[str]):
        if not keys:
            logger.warning("KeyRing initialized with empty key list")
        self.keys = list(keys)
        self._index = 0
        self._cooldowns: dict[str, float] = {}
        self._backoffs: dict[str, float] = {}

    def get_key(self) -> str | None:
        if not self.keys:
            return None
        now = time.monotonic()
        for _ in range(len(self.keys)):
            key = self.keys[self._index]
            self._index = (self._index + 1) % len(self.keys)
            if key not in self._cooldowns or now >= self._cooldowns[key]:
                return key
        return min(self.keys, key=lambda k: self._cooldowns.get(k, now))

    def report_429(self, key: str):
        current = self._backoffs.get(key, 10.0)
        self._cooldowns[key] = time.monotonic() + current
        self._backoffs[key] = min(current * 2, 300.0)
        logger.info("Key %s in cooldown for %.0fs (all keys: %d)", key[:12] + "...", current, len(self.keys))

    def report_success(self, key: str):
        self._backoffs.pop(key, None)
        self._cooldowns.pop(key, None)


class ProviderRouter:
    def __init__(self):
        gemini_keys = list(settings.GEMINI_API_KEYS)
        if not gemini_keys and settings.GEMINI_API_KEY:
            gemini_keys = [settings.GEMINI_API_KEY]
        self._gemini_keys = KeyRing(gemini_keys)
        self._gemini_base = settings.GEMINI_BASE_URL
        self._gemini_model = settings.GEMINI_MODEL
        self._gemini_vision_model = settings.GEMINI_VISION_MODEL

        or_keys = list(settings.OPENROUTER_API_KEYS)
        if not or_keys and settings.OPENROUTER_API_KEY:
            or_keys = [settings.OPENROUTER_API_KEY]
        self._or_keys = KeyRing(or_keys)
        self._or_base = settings.OPENROUTER_BASE_URL
        self._embedding_model = settings.EMBEDDING_MODEL

        self._client = httpx.AsyncClient(
            timeout=120,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def aclose(self):
        await self._client.aclose()

    # ── Key management ──

    def _or_headers(self, key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://adaptive-learning.local",
            "X-Title": "Adaptive Learning RAG Pipeline",
        }

    def _gemini_headers(self, key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    async def _api_post(
        self,
        base_url: str,
        path: str,
        headers_fn,
        keyring: KeyRing,
        json_body: dict,
        timeout: int = 30,
        context: str = "",
    ) -> dict:
        last_error: Exception | None = None
        for attempt in range(3):
            key = keyring.get_key()
            if key is None:
                raise ValueError(f"[{context}] All keys in cooldown, no key available")
            try:
                response = await self._client.post(
                    f"{base_url}{path}",
                    headers=headers_fn(key),
                    json=json_body,
                    timeout=timeout,
                )
                if response.is_success:
                    keyring.report_success(key)
                    return response.json()
                body = response.text[:200]
                if response.status_code == 429:
                    keyring.report_429(key)
                    logger.warning("[%s] 429 on key %s — rotating (attempt %d/3)", context, key[:12] + "...", attempt + 1)
                    last_error = ValueError(f"429: {body}")
                    await asyncio.sleep(1)
                    continue
                logger.error("[%s] attempt %d HTTP %d: %s", context, attempt + 1, response.status_code, body)
                if 400 <= response.status_code < 500:
                    raise ValueError(f"{context} HTTP {response.status_code}: {body}")
                raise httpx.HTTPStatusError(f"HTTP {response.status_code}", request=response.request, response=response)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_error = e
                if attempt < 2:
                    wait = 2 ** attempt
                    logger.info("[%s] retrying in %ds (attempt %d/3)", context, wait, attempt + 1)
                    await asyncio.sleep(wait)
                    continue
                raise ValueError(f"[{context}] failed after 3 retries: {e}")
            except ValueError:
                raise
        raise ValueError(f"[{context}] failed after 3 retries: {last_error}")

    async def _api_post_stream(
        self,
        base_url: str,
        path: str,
        headers_fn,
        keyring: KeyRing,
        json_body: dict,
        timeout: int = 120,
        context: str = "",
    ) -> AsyncGenerator[bytes, None]:
        key = keyring.get_key()
        if key is None:
            raise ValueError(f"[{context}] All keys in cooldown, no key available")
        async with self._client.stream(
            "POST",
            f"{base_url}{path}",
            headers=headers_fn(key),
            json=json_body,
            timeout=timeout,
        ) as response:
            if response.status_code == 429:
                keyring.report_429(key)
                logger.warning("[%s] 429 on key %s — streaming failed", context, key[:12] + "...")
                raise ValueError("429 rate limited")
            if not response.is_success:
                body = await response.aread()
                logger.error("[%s] HTTP %d: %s", context, response.status_code, body.decode()[:300])
                raise ValueError(f"{context} failed: {body.decode()[:200]}")
            keyring.report_success(key)
            async for chunk in response.aiter_bytes():
                yield chunk

    # ── Chat completions → Gemini ──

    @staticmethod
    def _build_content(text: str, images: list[dict] | None = None) -> str | list[dict]:
        if not images:
            return text
        parts: list[dict] = [{"type": "text", "text": text}]
        for img in images:
            parts.append({"type": "image_url", "image_url": {"url": f"data:{img['mime']};base64,{img['b64']}"}})
        return parts

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        disable_thinking: bool = True,
        images: list[dict] | None = None,
    ) -> str:
        model = model or self._gemini_model
        if images:
            model = self._gemini_vision_model
            messages = [dict(m) for m in messages]
            if messages and messages[-1].get("role") == "user":
                messages[-1]["content"] = self._build_content(messages[-1]["content"], images)
        request_body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = await self._api_post(
            self._gemini_base, "/v1/chat/completions",
            self._gemini_headers, self._gemini_keys,
            request_body, timeout=120, context="chat",
        )
        return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        images: list[dict] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        model = model or self._gemini_model
        if images:
            model = self._gemini_vision_model
            messages = [dict(m) for m in messages]
            if messages and messages[-1].get("role") == "user":
                messages[-1]["content"] = self._build_content(messages[-1]["content"], images)
        request_body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        buffer = ""
        async for raw in self._api_post_stream(
            self._gemini_base, "/v1/chat/completions",
            self._gemini_headers, self._gemini_keys,
            request_body, timeout=120, context="stream",
        ):
            buffer += raw.decode()
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    return
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
        model = model or self._gemini_model
        data = await self._api_post(
            self._gemini_base, "/v1/chat/completions",
            self._gemini_headers, self._gemini_keys,
            {
                "model": model,
                "messages": messages,
                "response_format": {"type": "json_object", "schema": response_schema},
                "temperature": 0.2,
            },
            timeout=120,
            context="chat_with_schema",
        )
        return json.loads(data["choices"][0]["message"]["content"])

    # ── Embeddings → OpenRouter ──

    async def embed_text(self, text: str) -> list[float]:
        data = await self._api_post(
            self._or_base, "/embeddings",
            self._or_headers, self._or_keys,
            {"model": self._embedding_model, "input": [text]},
            timeout=30, context="embed_text",
        )
        if "data" not in data:
            raise ValueError(f"Missing 'data' key: {str(data)[:200]}")
        return data["data"][0]["embedding"]

    async def embed_text_batch(self, texts: list[str]) -> list[list[float]]:
        data = await self._api_post(
            self._or_base, "/embeddings",
            self._or_headers, self._or_keys,
            {"model": self._embedding_model, "input": texts},
            timeout=60, context="embed_text_batch",
        )
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
                    logger.error("  [embed_images] Batch %d failed (skipping %d images): %s", batch_num, len(batch), str(e)[:100])
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
            data = await self._api_post(
                self._or_base, "/embeddings",
                self._or_headers, self._or_keys,
                {"model": self._embedding_model, "input": inputs},
                timeout=180, context="embed_image_batch",
            )
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
        data = await self._api_post(
            self._or_base, "/embeddings",
            self._or_headers, self._or_keys,
            {"model": self._embedding_model, "input": inputs},
            timeout=30, context="embed_image",
        )
        if "data" not in data:
            raise ValueError(f"Missing 'data' key: {str(data)[:200]}")
        return data["data"][0]["embedding"]

    # ── Health ──

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(
                f"{self._gemini_base}/v1/models",
                headers=self._gemini_headers(self._gemini_keys.get_key() or ""),
                timeout=10,
            )
            if response.is_success:
                return True
        except Exception as e:
            logger.error("[health_check] Gemini connectivity error: %s", e)
        try:
            response = await self._client.get(
                f"{self._or_base}/models",
                headers=self._or_headers(self._or_keys.get_key() or ""),
                timeout=10,
            )
            return response.is_success
        except Exception as e:
            logger.error("[health_check] OpenRouter connectivity error: %s", e)
            return False


_router_singleton: ProviderRouter | None = None


def get_router() -> ProviderRouter:
    global _router_singleton
    if _router_singleton is None:
        _router_singleton = ProviderRouter()
    return _router_singleton


router = get_router()
