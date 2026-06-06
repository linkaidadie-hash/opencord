"""
MockAIProvider — 不需要任何 API key 的本地 fake LLM。

用于：
- 5 分钟快速 demo（git clone → docker compose up → 发帖 → AI 总结）
- CI 单元测试
- 离线开发

v0.1 默认推荐：seed 脚本会创建一个 mock provider 并设为 default，
所以"git clone + cp .env.example .env + docker compose up + seed" 之后
直接触发 AI 总结就有结果，零配置。
"""
from __future__ import annotations

import hashlib
from packages.ai import (
    AIProvider,
    ChatMessage,
    ChatOptions,
    ChatResult,
    SummarizeOptions,
    SummarizeResult,
)


class MockAIProvider(AIProvider):
    """
    本地 fake LLM。所有"AI"行为都是确定性 hash + 简单截取。

    设计原则：
    - 输入相同 → 输出相同（用 hash 做"随机性"）
    - 永远不抛异常
    - latency 模拟真实 LLM（10-50ms）
    - tokens 粗略估算（按字符数 / 4）
    """

    provider_type = "mock"

    async def chat(
        self,
        messages: list[ChatMessage],
        options: ChatOptions | None = None,
    ) -> ChatResult:
        options = options or ChatOptions()
        # 拼出所有 user 消息
        user_text = "\n".join(m.content for m in messages if m.role == "user")
        seed = int(hashlib.md5(user_text.encode()).hexdigest()[:8], 16)
        reply = (
            f"[Mock AI] 这是对您消息的模拟回复。\n\n"
            f"您说：「{user_text[:120]}{'...' if len(user_text) > 120 else ''}」\n\n"
            f"（这是 MockAIProvider 生成的占位回复，用于无 key 演示。"
            f"配置真实 AI Provider 后会替换为真实模型输出。）"
        )
        t0_in = sum(len(m.content) for m in messages) // 4
        t0_out = len(reply) // 4
        return ChatResult(
            content=reply,
            model="mock-chat-v1",
            provider=self.provider_type,
            tokens_in=t0_in,
            tokens_out=t0_out,
            latency_ms=20,
            raw={"mock": True, "seed": seed},
        )

    async def summarize(
        self,
        text: str,
        options: SummarizeOptions | None = None,
    ) -> SummarizeResult:
        options = options or SummarizeOptions()
        text_clean = " ".join(text.split())  # 折叠空白

        # 简单"总结"策略：取首段 + 关键句
        # 首段：到第一个空行
        first_para = text_clean.split("\n\n")[0].strip()
        # 关键句：取前半部分的一个中长句
        sentences = []
        for sep in ["。", "！", "?", "？", "!"]:
            first_para = first_para.replace(sep, sep + "|SPLIT|")
        for s in first_para.split("|SPLIT|"):
            s = s.strip()
            if 20 <= len(s) <= 200:
                sentences.append(s)
                if len(sentences) >= 2:
                    break

        if not sentences:
            summary = first_para[:options.max_length]
        else:
            summary = "。".join(sentences) + "。"

        if len(summary) > options.max_length:
            summary = summary[: options.max_length - 1] + "…"

        seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        return SummarizeResult(
            summary=summary,
            model="mock-summarizer-v1",
            provider=self.provider_type,
            tokens_in=len(text) // 4,
            tokens_out=len(summary) // 4,
            latency_ms=15,
            raw={"mock": True, "seed": seed, "style": options.style},
        )
