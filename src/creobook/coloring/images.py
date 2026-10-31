"""OpenAI image generation with retries. Tests inject their own caller."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import Any, Callable

from creobook.coloring.models import ColoringError


class RetryableImageError(ColoringError):
    """Timeouts, rate limits, and transient server errors."""


class ImageAPIError(ColoringError):
    """The image API refused the request or returned nothing usable."""


@dataclass
class GeneratedImage:
    png: bytes
    usage: dict[str, Any] = field(default_factory=dict)
    model: str = ""
    size: str = ""
    quality: str = ""


def call_with_retry(
    call: Callable[[], Any],
    *,
    attempts: int = 4,
    sleeper: Callable[[float], None] | None = None,
) -> Any:
    """Retry ``call`` on RetryableImageError with exponential backoff."""
    import time

    sleep = sleeper or time.sleep
    last: RetryableImageError | None = None
    for attempt in range(attempts):
        try:
            return call()
        except RetryableImageError as exc:
            last = exc
            if attempt == attempts - 1:
                break
            sleep(float(2**attempt))
    assert last is not None
    raise last


def require_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise ColoringError(
            "OPENAI_API_KEY is not set. Export it in the environment; do not put it in the repository."
        )
    return key


def _usage_dict(result: Any) -> dict[str, Any]:
    usage = getattr(result, "usage", None)
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        dumped = usage.model_dump()
        return {key: value for key, value in dumped.items() if value is not None}
    if isinstance(usage, dict):
        return dict(usage)
    return {}


def _as_retryable(exc: Exception) -> Exception:
    try:
        from openai import (
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            RateLimitError,
        )
    except ImportError:
        return exc
    if isinstance(exc, (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)):
        return RetryableImageError(str(exc))
    return exc


class OpenAIColoringClient:
    """Thin Images API and Responses API wrapper. Construct only when a paid call is intended."""

    def __init__(self, *, api_key: str | None = None, timeout: float = 180.0) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key or require_api_key(), timeout=timeout, max_retries=0)
        self._sleeper = None

    def complete_text(self, prompt: str, *, model: str) -> str:
        def once() -> str:
            try:
                response = self._client.responses.create(model=model, input=prompt)
            except Exception as exc:
                mapped = _as_retryable(exc)
                if mapped is not exc:
                    raise mapped from exc
                raise ImageAPIError(str(exc)) from exc
            text = getattr(response, "output_text", None) or ""
            if not str(text).strip():
                raise ImageAPIError("Text model returned an empty plan")
            return str(text)

        return call_with_retry(once)

    def generate_image(self, *, prompt: str, model: str, size: str, quality: str) -> GeneratedImage:
        def once() -> GeneratedImage:
            try:
                result = self._client.images.generate(
                    model=model,
                    prompt=prompt,
                    size=size,
                    quality=quality,
                    output_format="png",
                    background="opaque",
                    n=1,
                )
            except Exception as exc:
                mapped = _as_retryable(exc)
                if mapped is not exc:
                    raise mapped from exc
                raise ImageAPIError(str(exc)) from exc
            data = getattr(result, "data", None) or []
            if not data or not getattr(data[0], "b64_json", None):
                raise ImageAPIError("Image API returned no PNG")
            try:
                png = base64.b64decode(data[0].b64_json)
            except (ValueError, TypeError) as exc:
                raise ImageAPIError("Image API returned invalid base64") from exc
            return GeneratedImage(
                png=png,
                usage=_usage_dict(result),
                model=model,
                size=size,
                quality=quality,
            )

        return call_with_retry(once)
