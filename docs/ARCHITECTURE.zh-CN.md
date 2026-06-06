# OpenCord 架构

[English](./ARCHITECTURE.md) | [简体中文](./ARCHITECTURE.zh-CN.md)

> OpenCord v0.1 技术架构文档。
> 这份文档讲 OpenCord **怎么** 实现的。**为什么** 见 [VISION.zh-CN.md](./VISION.zh-CN.md)，**接下来做什么** 见 [ROADMAP.zh-CN.md](./ROADMAP.zh-CN.md)。

---

## 1. Monorepo 结构

```
opencord/
├── apps/
│   ├── web/                  Next.js 14 (App Router) 前端
│   └── api/                  FastAPI 后端
├── packages/
│   ├── ai/                   AI Provider 抽象层（独立 Python 包）
│   ├── core/                 （预留）领域模型
│   ├── export/               （预留）数据导出工具
│   └── database/             （预留）SQLAlchemy 模型 / Alembic 迁移
├── services/                 （顶层）跨应用的服务契约（未来）
├── db/
│   └── schema.sql            初始 schema（11 张表，tenant_id 预留，pgvector）
├── docs/                     所有文档（中英双语）
├── scripts/                  运维脚本（seed.py 等）
├── docker-compose.yml        Postgres + Redis + API + Web
├── .env.example              配置模板
└── README.md / README.zh-CN.md
```

### 为什么这样分层

- `apps/` 放可运行的应用（前端 + 后端）。以后加 `apps/worker/`、`apps/cli/` 自然
- `packages/` 放可在 app 之外复用的库。`packages/ai` 是独立 Python 包 —— v0.3+ 可以单独 `pip install` 或 `git submodule`
- 顶层 `services/` 留给跨应用契约。v0.1 是空的。v0.3+ 可以放插件 manifest 定义
- `db/schema.sql` 是数据库的事实来源。Docker Compose init 容器首次启动时加载。Alembic 迁移 v0.2 上

---

## 2. 数据库设计

11 张表。全部带可空 `tenant_id` 字段，为未来多租户预留。

### 核心表

| 表 | 用途 |
|---|---|
| `tenants` | 社区实例。v0.1 只有 1 行默认数据 |
| `users` | 成员。`role` 是 `member` / `moderator` / `admin`，`status` 是 `active` / `suspended` / `banned` |
| `api_tokens` | 长期 API Token（SHA-256 哈希存，明文只在创建时返回） |
| `channels` | 板块。`visibility` 是 `public` / `private` |
| `posts` | Markdown 内容。AI 总结缓存到这里，`embedding` 字段为 v0.2 向量搜索预留 |
| `comments` | 一级 + 嵌套回复（通过 `parent_id`） |
| `tags` + `post_tags` | 多对多标签 |
| `notifications` | 每用户收件箱。轮询，不推送 |
| `ai_providers` | 运行时 AI 配置（后台管理） |
| `ai_usage_log` | 每次调用日志：tokens、cost、latency、error |
| `audit_log` | 管理员操作审计 |

### Schema 不变量

1. **UUID 作主键** —— 跨实例可移植，为未来联邦做准备
2. **所有表可空 `tenant_id`** —— v0.1 单租户，v0.4 多租户
3. **时间戳用 `timestamptz`** —— 永远不丢时区信息
4. **`updated_at` 由 trigger 自动更新** —— 在 `schema.sql` 里设置
5. **`embedding` 是 `vector(1536)`** —— 对齐 OpenAI `text-embedding-3-small` 维度

### 为什么 v0.1 就上 pgvector

两个原因：

1. **pgvector 迁移很贵**：数据多了之后再加 pgvector 需要停机迁移。v0.1 装上，v0.2（加 AI 匹配）就不用停机
2. **v0.1 schema 真实地反映未来形状**：任何看 `schema.sql` 的人能立刻知道 v0.2 要往哪走

---

## 3. AI Provider 抽象层

`packages/ai/` 是独立 Python 包。它是项目里**唯一**知道具体 LLM 厂商细节的地方。

### 接口

```python
class AIProvider(ABC):
    async def chat(self, messages: list[ChatMessage], options: ChatOptions) -> ChatResult
    async def summarize(self, text: str, options: SummarizeOptions) -> SummarizeResult
    async def embed(self, text: str) -> EmbedResult  # v0.1 抛 NotImplementedError
```

### 实现

| 类 | 类型 | 说明 |
|---|---|---|
| `OpenAICompatibleProvider` | `openai-compatible` | 覆盖 OpenAI、DeepSeek、Ollama、硅基流动、OpenRouter、所有 OpenAI 兼容端点。直接用 `httpx`，不引 `openai` SDK |
| `MiniMaxProvider` | `MiniMax` | 继承 `OpenAICompatibleProvider`。为 MiniMax 特有功能预留 |
| `DeepSeekProvider` | `deepseek` | 继承 `OpenAICompatibleProvider`。v0.2 加 `reasoning_content`（thinking mode） |
| `OllamaProvider` | （走 openai-compatible） | 没有独立类 —— 把 `base_url` 指向 `http://host.docker.internal:11434/v1` 就行 |

### Factory

```python
AIProviderFactory.create(provider_type=..., name=..., api_key=..., base_url=..., model=...)
```

Factory 把 DB 里的 `provider_type` 字符串映射到具体类。

### 限流

`SimpleRateLimiter` 在 `packages/ai/` 里。v0.1 用进程内内存；v0.2 迁到 Redis。每 Provider 的 `rpm_limit` 后台可配。

### 选 Provider 算法

API 需要某个任务（比如 summarize）的 Provider 时：

1. 找 `is_default = true` 的 active Provider
2. 验证它支持该任务
3. 查限流
4. 限流了，fallback 到下一个支持该任务的 active Provider
5. 全都没空，返回 `503 No AI provider available`

---

## 4. 为什么 v0.1 不上 WebSocket

这是主动选择，不是技术限制。

### WebSocket 能给你什么

- 实时消息送达
- 在线状态
- 通知即时推送
- 输入中提示

### WebSocket 让你付出什么

- 连接状态管理（重连、心跳、僵尸连接检测）
- 横向扩容复杂度（粘性会话 / Redis pub/sub / 外部 broker）
- 部署复杂度（WebSocket 走反代、负载均衡、CDN）
- 移动端耗电
- 测试复杂度（时序依赖的测试）

### v0.1 的方案

对通知和帖子更新：

- **通知**：通过 `GET /api/notifications?unread_only=true` 轮询。前端默认 30 秒一次。成本：每个活跃用户每 30 秒一个小的 JSON 请求
- **帖子列表更新**：翻页时重新拉。v0.1 不需要无限滚动流
- **AI 总结**：手动触发（v0.1 admin，v0.2 任何用户）。结果缓存

部署故事就简单了。`docker compose up` 直接跑通。不用给 nginx 配 WebSocket。理论上不用 Redis 就能横向扩。不用踩粘性会话的坑。

### v0.2 的计划

私信上线时，就是加 WebSocket 的恰当时机。v0.2 大概率先上一薄层 **Server-Sent Events (SSE)**（还是 HTTP，更简单），再切完整 WebSocket。完整 WebSocket 迁移在 v0.2 私信真正需要时做。

---

## 5. 代码分层

```
api/          ← FastAPI 路由（HTTP、请求校验、响应整形）
  ↓
services/     ← 业务逻辑（编排 domain + DB + AI）
  ↓
domain/       ← （v0.2）纯领域模型，无 I/O
  ↓
database/     ← SQLAlchemy ORM（v0.2）/ v0.1 用 raw SQLAlchemy Core
```

### v0.1 的简化

v0.1 把 `domain/` 和 `services/` 合并成一个目录（`apps/api/services/`）。每个 service 文件（`user_service.py`、`post_service.py` 等）就是一组接收 `AsyncSession` 和 DTO 的扁平函数。

v0.1 表面积小，这样做没问题。当 v0.2 加入：

- 插件系统
- 联邦逻辑
- 后台 worker

……我们再正经拆出 `domain/`。`services/` 变成薄编排层。

### 插件边界

`services/` 层是 v0.3+ 的**插件替换边界**。插件可以：

1. 替换 service 函数（比如 `post_service.create_post` 换成"先过审"版本）
2. 加新的 service 函数（比如 `plugin.trade_radar.scan_posts`）
3. 加新的 API 路由（比如 `GET /api/plugins/trade-radar/results`）

接口故意是扁平函数集，不是抽象基类。Python 的鸭子类型 + manifest 比 Java 风格接口更简单。

---

## 6. 鉴权模型

### JWT（人类会话）

- 算法：HS256
- 过期：7 天
- 存储：前端用 HttpOnly cookie，`TokenResponse` 也返回一份给客户端
- Claims：`sub`（user id）、`exp`、`iat`、`type: "jwt"`

### API Token（机器人 / 集成）

- 格式：`oc_<32 url-safe 随机字节>`
- 存储：SHA-256 哈希（永不存明文）
- 识别前缀（8 字符）：在 `APITokenPublic.token_prefix` 用于 UI 展示
- Scopes（v0.1 声明但不强制）：`post:read`、`post:write`、`comment:write` 等

### 识别

`get_current_user` 依赖检查 token 格式：

- 以 `oc_` 开头 → API Token（按哈希查）
- 否则 → JWT（验签）

### 为什么要两套

- JWT 给人用。方便、按登录可吊销、能带自定义 claims
- API Token 给机器/集成用。长期、不默认过期、改密码不影响机器人

两套都能访问同一套 API。v0.2 加细粒度 scope 强制。

---

## 7. 前端架构

Next.js 14 App Router，server-first。

- **Server Components** 跑只读数据的页面（首页、频道、帖子详情、个人主页）
- **Client Components** 跑表单和交互 UI（登录、注册、评论、Provider 配置）
- **`lib/api.ts`** 是 server-only 的 fetch 客户端，对 FastAPI 后端发起请求
- **`lib/auth.ts`** 读 auth cookie 供 SSR 用

v0.1 前端故意做得很轻 —— 没状态管理库、没客户端路由（只 Next 自带）、没乐观更新。bundle 小、依赖浅。

`API_INTERNAL_URL` 环境变量让 web 容器能通过 Docker 服务名（`http://api:8000`）找 api 容器。本地非 Docker 跑就设成 `http://localhost:8000`。

---

## 8. 部署

Docker Compose，4 个服务：

| 服务 | 镜像 | 用途 |
|---|---|---|
| `postgres` | `postgres:16-alpine` | 主存储 |
| `redis` | `redis:7-alpine` | 缓存（v0.2 启用） |
| `api` | 自构建 `apps/api/Dockerfile` | FastAPI 后端 |
| `web` | 自构建 `apps/web/Dockerfile` | Next.js 前端 |

### Build context

Docker Compose 的 `build.context` 是项目根（不是 `apps/api/`）。这样 api 容器能 `import packages.ai`（抽象层在 `packages/ai/`，不在 `apps/api/` 内部）。

### 首次启动

1. Postgres init 容器加载 `db/schema.sql`（挂到 `/docker-entrypoint-initdb.d/`）
2. api 容器等 postgres 健康检查通过
3. 跑一次 `seed.py` 创建默认租户、管理员、示例频道
4. web 容器启动，把 `/api/*` 反代到 api 容器

### v0.2+ 部署考虑

- 反向代理（Caddy / nginx）+ HTTPS
- 对象存储（S3 兼容）存媒体
- 后台 worker 容器（`apps/worker/`）跑异步任务
- 迁移执行器（Alembic）

---

## 9. 故意没做的东西

你可能预期会有，但 v0.1 故意没有的：

- **Alembic 迁移** —— v0.1 是单 schema，fresh 部署。迁移增加复杂度但 v0.1 没价值
- **后台 worker / 异步队列** —— 同步调用对小负载 v0.1 够用。v0.2 加 Celery 或 RQ
- **图片上传** —— v0.1 纯文本。v0.2 本地存储，v0.3 S3
- **搜索** —— Postgres 全文搜索（TSVECTOR）v0.2 上。v0.1 没搜索框
- **邮件发送** —— 注册不验邮箱。v0.2 加 SMTP 配置
- **鉴权限流** —— v0.1 信部署网络边界。v0.2 加 Redis 限流
- **日志聚合** —— v0.1 只 stdout。v0.2 结构化 JSON 日志发到可配置 sink
- **监控指标** —— v0.1 没 Prometheus。v0.2

这是 v0.1 的契约：小、能跑、对"没做什么"诚实。
