# OpenCord AI Provider 抽象层

不绑定任何 LLM 平台。所有 Provider 实现同一接口。

## 接口

```python
class AIProvider(Protocol):
    async def chat(self, messages, options) -> ChatResult: ...
    async def summarize(self, text, options) -> SummarizeResult: ...
    async def embed(self, text) -> EmbedResult: ...
```

## 实现

- `OpenAICompatibleProvider` — 通用 OpenAI-compatible 协议（OpenAI / OpenRouter / 硅基流动 / DeepSeek / Ollama 都可）
- `MiniMaxProvider` — MiniMax（M2M-Protocol 协议）
- `DeepSeekProvider` — DeepSeek（OpenAI 兼容，独立 Provider 是为了支持 DeepSeek 特有的 thinking mode）
- `OllamaProvider` — 本地 Ollama（OpenAI 兼容，但 base_url 不同）

## 切换逻辑

`AIProviderFactory` 根据 DB `ai_providers.is_default = TRUE` 选一个。
后台可手动切换；切换不影响 in-flight 请求。

## v0.1 范围

只实现 `chat` 和 `summarize`。`embed` 接口预留但 v0.1 不用（pgvector 数据从 v0.2 开始写入）。

## 限流

`ai_usage_log` 表记录每次调用。`rpm_limit` 字段在调用前检查，简单的 token bucket（v0.1 内存实现，v0.2 改 Redis）。
