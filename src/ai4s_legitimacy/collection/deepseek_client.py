from __future__ import annotations

import json
import os
import ssl
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence
from urllib import error as urllib_error
from urllib import request as urllib_request


DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_CHAT_MODEL = "deepseek-chat"
DEFAULT_REASONER_MODEL = "deepseek-reasoner"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_MAX_RETRIES = 3


def _build_ssl_context() -> ssl.SSLContext:
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


@dataclass(slots=True)
class DeepSeekClient:
    api_key: str
    base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_MAX_RETRIES
    transport: Callable[..., Any] = field(default=urllib_request.urlopen, repr=False)
    ssl_context: ssl.SSLContext = field(default_factory=_build_ssl_context, repr=False)

    @classmethod
    def from_env(cls) -> DeepSeekClient:
        api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for DeepSeek API access")
        return cls(
            api_key=api_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_DEEPSEEK_BASE_URL).strip()
            or DEFAULT_DEEPSEEK_BASE_URL,
        )

    def complete_json(
        self,
        *,
        model: str,
        messages: Sequence[dict[str, str]],
    ) -> dict[str, Any]:
        url = self.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": model,
            "messages": list(messages),
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ai4s-legitimacy/0.1.0",
        }
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                request = urllib_request.Request(url, data=body, headers=headers, method="POST")
                with self.transport(
                    request,
                    timeout=self.timeout_seconds,
                    context=self.ssl_context,
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                message = payload["choices"][0]["message"]
                content = str(message.get("content") or "").strip()
                if not content:
                    raise ValueError("DeepSeek JSON output was empty")
                return {
                    "parsed": json.loads(content),
                    "model": str(payload.get("model") or model),
                }
            except urllib_error.HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504} or attempt == self.max_retries:
                    break
                time.sleep(1.5 * attempt)
            except (
                urllib_error.URLError,
                TimeoutError,
                json.JSONDecodeError,
                KeyError,
                ValueError,
            ) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                time.sleep(1.0 * attempt)
        detail = ""
        if isinstance(last_error, urllib_error.HTTPError):
            detail = f"HTTP {last_error.code}: {last_error.reason}"
        elif last_error is not None:
            detail = str(last_error).strip()
        suffix = f" ({detail})" if detail else ""
        raise RuntimeError(
            f"DeepSeek request failed after {self.max_retries} attempts{suffix}"
        ) from last_error
