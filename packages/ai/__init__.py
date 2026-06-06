"""
OpenCord AI Provider 抽象层

设计原则：
1. 不绑定任何 LLM 平台
2. 所有 Provider 实现同一 Protocol
3. 配置存 DB，运行时可切换
4. 限流在调用前拦截
5. 用量记录到 ai_usage_log
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Literal


# =====================================================
# 数据结构
# =====================================================

@dataclass
class ChatMessage:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None
    tool_call_id: str | None = None


@dataclass
class ChatOptions:
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 1.0
    stop: list[str] | None = None
    timeout_s: float = 60.0


@dataclass
class ChatResult:
    content: str
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class SummarizeOptions:
    max_length: int = 300
    language: str = "zh"  # "zh" | "en"
    style: Literal["concise", "detailed", "bullets"] = "concise"


@dataclass
class SummarizeResult:
    summary: str
    model: str
    provider: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmbedResult:
    vector: list[float]
    model: str
    provider: str
    tokens_in: int
    latency_ms: int


# =====================================================
# Provider 抽象接口
# =====================================================

class AIProvider(ABC):
    """所有 AI Provider 必须实现这个接口。"""

    provider_type: str = "base"

    def __init__(
        self,
        *,
        name: str,
        api_key: str,
        base_url: str,
        model: str,
        provider_id: str | None = None,
        rpm_limit: int | None = None,
    ):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider_id = provider_id
        self.rpm_limit = rpm_limit

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        options: ChatOptions | None = None,
    ) -> ChatResult: ...

    @abstractmethod
    async def summarize(
        self,
        text: str,
        options: SummarizeOptions | None = None,
    ) -> SummarizeResult: ...

    async def embed(self, text: str) -> EmbedResult:
        raise NotImplementedError(
            f"{self.provider_type} does not implement embed() in v0.1"
        )

    # 内部工具：HTTP 请求 + 计时
    async def _timed(self, coro):
        t0 = time.perf_counter()
        result = await coro
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return result, latency_ms


# =====================================================
# OpenAI-compatible 实现（覆盖 OpenAI / DeepSeek / Ollama / 硅基流动 / OpenRouter）
# =====================================================

class OpenAICompatibleProvider(AIProvider):
    """
    通用 OpenAI 协议实现。

    用 httpx 直接调，避免引入 openai 库（减少依赖 + 方便扩展）。
    """
    provider_type = "openai-compatible"

    async def chat(
        self,
        messages: list[ChatMessage],
        options: ChatOptions | None = None,
    ) -> ChatResult:
        import httpx

        options = options or ChatOptions()
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [self._msg_to_dict(m) for m in messages],
            "temperature": options.temperature,
            "top_p": options.top_p,
        }
        if options.max_tokens is not None:
            payload["max_tokens"] = options.max_tokens
        if options.stop:
            payload["stop"] = options.stop

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=options.timeout_s) as client:
            resp, latency_ms = await self._timed(
                client.post(url, json=payload, headers=headers)
            )
        resp.raise_for_status()
        data = resp.json()

        return ChatResult(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.model),
            provider=self.provider_type,
            tokens_in=data.get("usage", {}).get("prompt_tokens", 0),
            tokens_out=data.get("usage", {}).get("completion_tokens", 0),
            latency_ms=latency_ms,
            raw=data,
        )

    async def summarize(
        self,
        text: str,
        options: SummarizeOptions | None = None,
    ) -> SummarizeResult:
        options = options or SummarizeOptions()
        lang_name = "Chinese" if options.language == "zh" else "English"
        style_prompt = {
            "concise": "Write a concise summary in 1-3 sentences.",
            "detailed": "Write a detailed summary covering main points.",
            "bullets": "Write the summary as 3-5 bullet points.",
        }[options.style]

        messages = [
            ChatMessage(
                role="system",
                content=(
                    f"You are a helpful assistant that summarizes text. "
                    f"Output in {lang_name}. {style_prompt} "
                    f"Keep the summary under {options.max_length} characters."
                ),
            ),
            ChatMessage(role="user", content=text),
        ]

        chat_result = await self.chat(
            messages,
            ChatOptions(temperature=0.3, max_tokens=options.max_length * 2),
        )

        return SummarizeResult(
            summary=chat_result.content,
            model=chat_result.model,
            provider=self.provider_type,
            tokens_in=chat_result.tokens_in,
            tokens_out=chat_result.tokens_out,
            latency_ms=chat_result.latency_ms,
            raw=chat_result.raw,
        )

    @staticmethod
    def _msg_to_dict(m: ChatMessage) -> dict:
        d: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.name:
            d["name"] = m.name
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        return d


# =====================================================
# MiniMax 实现（同样走 OpenAI-compatible，绝大多数国内 LLM 兼容）
# =====================================================

class MiniMaxProvider(OpenAICompatibleProvider):
    """
    MiniMax（基于 M2M 协议 / OpenAI 兼容）。
    实际上 MiniMax 自己就是 OpenAI-compatible，所以直接继承。
    如果未来有 MiniMax 特有参数（如 abab 系列的安全设置），再覆盖。
    """
    provider_type = "MiniMax"


# =====================================================
# DeepSeek 实现（OpenAI 兼容，支持 thinking mode）
# =====================================================

class DeepSeekProvider(OpenAICompatibleProvider):
    """
    DeepSeek（OpenAI 兼容）。
    v0.1 不实现 thinking mode（reasoning_content 字段），
    v0.2 再加。
    """
    provider_type = "deepseek"


# =====================================================
# Factory
# =====================================================

# Mock provider 不需要 import 在顶部，延迟到 __init__.py 末尾注册
# 避免循环 import（mock.py 也 import 本文件的数据结构）
from .mock import MockAIProvider  # noqa: E402


class AIProviderFactory:
    """根据 type 字符串创建 Provider 实例。"""

    _registry: dict[str, type[AIProvider]] = {
        "openai-compatible": OpenAICompatibleProvider,
        "MiniMax": MiniMaxProvider,
        "deepseek": DeepSeekProvider,
        "mock": MockAIProvider,
        # "ollama": OllamaProvider,  # v0.1 暂不单独实现，复用 openai-compatible + 不同 base_url
    }

    @classmethod
    def create(
        cls,
        provider_type: str,
        *,
        name: str,
        api_key: str,
        base_url: str,
        model: str,
        provider_id: str | None = None,
        rpm_limit: int | None = None,
    ) -> AIProvider:
        if provider_type not in cls._registry:
            raise ValueError(
                f"Unknown provider type: {provider_type}. "
                f"Available: {list(cls._registry.keys())}"
            )
        provider_cls = cls._registry[provider_type]
        return provider_cls(
            name=name,
            api_key=api_key,
            base_url=base_url,
            model=model,
            provider_id=provider_id,
            rpm_limit=rpm_limit,
        )

    @classmethod
    def available_types(cls) -> list[str]:
        return list(cls._registry.keys())


# =====================================================
# 限流（简单内存实现，v0.2 改 Redis）
# =====================================================

class SimpleRateLimiter:
    """按 provider_id 计数，每分钟清零。"""

    def __init__(self):
        self._buckets: dict[str, list[float]] = {}

    def check(self, provider_id: str, rpm_limit: int | None) -> bool:
        if rpm_limit is None or rpm_limit <= 0:
            return True
        now = time.time()
        window_start = now - 60
        bucket = self._buckets.setdefault(provider_id, [])
        # 清掉窗口外的
        self._buckets[provider_id] = [t for t in bucket if t > window_start]
        if len(self._buckets[provider_id]) >= rpm_limit:
            return False
        self._buckets[provider_id].append(now)
        return True


# 全局单例（够 v0.1 用）
_rate_limiter = SimpleRateLimiter()


def get_rate_limiter() -> SimpleRateLimiter:
    return _rate_limiter
