# OpenCord Architecture

[English](./ARCHITECTURE.md) | [简体中文](./ARCHITECTURE.zh-CN.md)

> Technical architecture for OpenCord v0.1.
> This document explains *how* OpenCord is built. For *why*, see [VISION.md](./VISION.md). For *what's next*, see [ROADMAP.md](./ROADMAP.md).

---

## 1. Monorepo Layout

```
opencord/
├── apps/
│   ├── web/                  Next.js 14 (App Router) frontend
│   └── api/                  FastAPI backend
├── packages/
│   ├── ai/                   AI Provider abstraction (standalone Python package)
│   ├── core/                 (reserved) domain models
│   ├── export/               (reserved) data export utilities
│   └── database/             (reserved) SQLAlchemy models / Alembic migrations
├── services/                 (top-level) cross-app service contracts (future)
├── db/
│   └── schema.sql            Initial schema (11 tables, tenant_id reserved, pgvector)
├── docs/                     All documentation (bilingual)
├── scripts/                  Operational scripts (seed.py, etc.)
├── docker-compose.yml        Postgres + Redis + API + Web
├── .env.example              Configuration template
└── README.md / README.zh-CN.md
```

### Why this layout

- `apps/` holds runnable applications (frontend + backend). Easy to add `apps/worker/`, `apps/cli/`, etc.
- `packages/` holds libraries reusable outside the app context. `packages/ai` is a standalone Python package — could be `pip install`-ed or `git submodule`-ed in v0.3+
- `services/` (top-level) is for cross-app contracts. In v0.1 it's empty. In v0.3+ it can hold plugin manifest definitions
- `db/schema.sql` is the source of truth for the database. The Docker Compose init container loads it on first boot. Alembic migrations come in v0.2

---

## 2. Database Design

11 tables. All carry a nullable `tenant_id` for future multi-tenancy.

### Core tables

| Table | Purpose |
|---|---|
| `tenants` | Community instances. v0.1 has 1 default row. |
| `users` | Members. `role` is `member` / `moderator` / `admin`. `status` is `active` / `suspended` / `banned`. |
| `api_tokens` | Long-lived API tokens (SHA-256 hashed; raw shown only at creation). |
| `channels` | Forums. `visibility` is `public` / `private`. |
| `posts` | Markdown content. AI summary cached here. `embedding` reserved for v0.2 vector search. |
| `comments` | One-level + nested replies (via `parent_id`). |
| `tags` + `post_tags` | Many-to-many tagging. |
| `notifications` | Per-user inbox. Polled, not pushed. |
| `ai_providers` | Runtime AI config (admin-managed). |
| `ai_usage_log` | Per-call log: tokens, cost, latency, error. |
| `audit_log` | Admin action trail. |

### Schema invariants

1. **UUIDs as primary keys** — portable across instances, future federation
2. **All tables nullable `tenant_id`** — single-tenant v0.1, multi-tenant-ready v0.4
3. **Timestamps as `timestamptz`** — never lose timezone info
4. **`updated_at` auto-updated via trigger** — set in `schema.sql`
5. **`embedding` is `vector(1536)`** — matches OpenAI `text-embedding-3-small` dimension

### Why pgvector in v0.1 even though v0.1 doesn't use it

Two reasons:
1. `pgvector` migration is non-trivial once you have data. Installing it now means v0.2 (which adds AI matching) doesn't need a migration downtime.
2. Keeps the v0.1 schema honest about its future shape. Anyone reading `schema.sql` sees where v0.2 is going.

---

## 3. AI Provider Abstraction

`packages/ai/` is a standalone Python package. It is the only place that knows about specific LLM providers.

### Interface

```python
class AIProvider(ABC):
    async def chat(self, messages: list[ChatMessage], options: ChatOptions) -> ChatResult
    async def summarize(self, text: str, options: SummarizeOptions) -> SummarizeResult
    async def embed(self, text: str) -> EmbedResult  # v0.1 raises NotImplementedError
```

### Implementations

| Class | Type | Notes |
|---|---|---|
| `OpenAICompatibleProvider` | `openai-compatible` | Covers OpenAI, DeepSeek, Ollama, SiliconFlow, OpenRouter, any OpenAI-compatible endpoint. Uses raw `httpx` (no `openai` SDK). |
| `MiniMaxProvider` | `MiniMax` | Inherits from `OpenAICompatibleProvider`. Reserved for MiniMax-specific features. |
| `DeepSeekProvider` | `deepseek` | Inherits from `OpenAICompatibleProvider`. v0.2 will add `reasoning_content` (thinking mode). |
| `OllamaProvider` | (via openai-compatible) | No dedicated class — just point `base_url` to `http://host.docker.internal:11434/v1`. |

### Factory

```python
AIProviderFactory.create(provider_type=..., name=..., api_key=..., base_url=..., model=...)
```

The factory maps `provider_type` (string from DB) to a class.

### Rate limiting

`SimpleRateLimiter` in `packages/ai/`. v0.1 uses in-process memory; v0.2 will move to Redis. Per-provider `rpm_limit` is configurable in the admin panel.

### Selection algorithm

When the API needs a provider for a task (e.g. summarize):
1. Find the active provider with `is_default = true`
2. Verify it supports the task
3. Check rate limit
4. If rate-limited, fall back to the next active provider that supports the task
5. If none available, return `503` with `No AI provider available`

---

## 4. Why No WebSocket in v0.1

This is a deliberate choice, not a technical limitation.

### What WebSocket gives you

- Real-time message delivery
- Live presence indicators
- Instant notification push
- Typing indicators

### What WebSocket costs you

- Connection state management (reconnect logic, heartbeat, dead connection detection)
- Horizontal scaling complexity (sticky sessions, Redis pub/sub, or external broker)
- Deployment complexity (WebSocket through reverse proxies, load balancers, CDNs)
- Mobile client battery drain (long-lived connections)
- Testing complexity (timing-dependent tests)

### v0.1's answer

For notifications and post updates:
- **Notifications**: polled via `GET /api/notifications?unread_only=true`. Default frontend interval: 30s. Costs: 1 small JSON request every 30 seconds per active user.
- **Post list updates**: re-fetched on page navigation. No infinite scroll streaming needed.
- **AI summary**: triggered manually (admin in v0.1, any user in v0.2). Result cached.

This keeps the deployment story simple. `docker compose up` and it works. No nginx config for WebSocket. No Redis required for horizontal scale (in theory). No sticky-session gotchas.

### v0.2's plan

When private messages ship, the right time to add WebSocket arrives. We'll likely use a thin server-sent-events (SSE) layer first (still HTTP, simpler) before going full WebSocket. The full WebSocket migration is in v0.2 if v0.2 messaging needs it.

---

## 5. Code Layering

```
api/          ← FastAPI routers (HTTP, request validation, response shaping)
  ↓
services/     ← Business logic (orchestrates domain + DB + AI)
  ↓
domain/       ← (v0.2) Pure domain models with no I/O
  ↓
database/     ← SQLAlchemy ORM (v0.2) / raw SQLAlchemy Core in v0.1
```

### v0.1 simplification

We collapsed `domain/` and `services/` into one folder (`apps/api/services/`) for v0.1. Each service file (`user_service.py`, `post_service.py`, etc.) is a flat collection of functions that take an `AsyncSession` and a DTO.

This is fine for v0.1 because the surface area is small. When v0.2 adds:
- Plugin system
- Federation logic
- Background workers

…we'll split `domain/` out properly. The `services/` folder will become a thin orchestration layer.

### Plugin boundary

The `services/` layer is the **plugin replacement boundary** in v0.3+. A plugin will be able to:

1. Replace a service function (e.g. replace `post_service.create_post` with one that sends to a moderation queue first)
2. Add new service functions (e.g. `plugin.trade_radar.scan_posts`)
3. Add new API routes (e.g. `GET /api/plugins/trade-radar/results`)

The interface is intentionally a flat function set, not an abstract base class. Python duck-typing + manifest makes the plugin model simpler than Java-style interfaces.

---

## 6. Auth Model

### JWT (interactive users)

- Algorithm: HS256
- Expiration: 7 days
- Storage: HttpOnly cookie on the frontend, also returned in `TokenResponse` for clients
- Claims: `sub` (user id), `exp`, `iat`, `type: "jwt"`

### API Token (bots / integrations)

- Format: `oc_<32 url-safe random bytes>`
- Stored as: SHA-256 hash (raw never persisted)
- Recognizable prefix (8 chars): used in `APITokenPublic.token_prefix` for UI display
- Scopes (v0.1: declared but not enforced): `post:read`, `post:write`, `comment:write`, etc.

### Detection

The `get_current_user` dependency checks the token format:
- Starts with `oc_` → API token (lookup by hash)
- Otherwise → JWT (verify signature)

### Why two mechanisms

- JWT is for human sessions. Convenient, revocable per-login, can include custom claims.
- API Token is for bots and integrations. Long-lived, no expiry by default, easier to rotate, no need to re-issue for password changes.

Both can hit the same endpoints. v0.2 will add fine-grained scope enforcement.

---

## 7. Frontend Architecture

Next.js 14 App Router, server-first.

- **Server Components** for pages that just read data (home, channel, post detail, user profile)
- **Client Components** for forms and interactive UI (login, register, comment form, AI provider config)
- **`lib/api.ts`** is a server-only fetch client that talks to the FastAPI backend
- **`lib/auth.ts`** reads the auth cookie for server-side rendering

The frontend is deliberately minimal in v0.1 — no state management library, no client-side router beyond Next's, no optimistic updates. This keeps the bundle small and the dependency tree shallow.

The `API_INTERNAL_URL` env var lets the web container talk to the api container by Docker service name (`http://api:8000`). For local dev outside Docker, set it to `http://localhost:8000`.

---

## 8. Deployment

Docker Compose, 4 services:

| Service | Image | Purpose |
|---|---|---|
| `postgres` | `postgres:16-alpine` | Primary storage |
| `redis` | `redis:7-alpine` | Cache (reserved for v0.2) |
| `api` | built from `apps/api/Dockerfile` | FastAPI backend |
| `web` | built from `apps/web/Dockerfile` | Next.js frontend |

### Build context

The Docker Compose `build.context` is the project root (not `apps/api/`). This is so the api container can `import packages.ai` (the abstraction lives in `packages/ai/`, not inside `apps/api/`).

### First boot

1. Postgres init container loads `db/schema.sql` (mounted at `/docker-entrypoint-initdb.d/`)
2. API container waits for postgres health check
3. Run `seed.py` once to create default tenant, admin user, sample channels
4. Web container starts, proxies `/api/*` to the api container

### v0.2+ deployment concerns

- Reverse proxy (Caddy / nginx) with HTTPS
- Object storage (S3-compatible) for media uploads
- Background worker container (`apps/worker/`) for async tasks
- Migration runner (Alembic)

---

## 9. What's Deliberately Missing

Things you might expect, that v0.1 doesn't have, on purpose:

- **Alembic migrations** — v0.1 is a single schema, deployed fresh. Migrations add complexity without value here.
- **Service worker / async queue** — sync calls are fine for the small workloads v0.1 has. v0.2 brings Celery or RQ.
- **Image upload** — text-only v0.1. Image upload in v0.2 with local storage; S3 in v0.3.
- **Search** — Postgres full-text search (TSVECTOR) lands in v0.2. v0.1 has no search box.
- **Email sending** — registration doesn't verify email yet. v0.2 adds SMTP config.
- **Rate limiting on auth** — v0.1 trusts the deployment's network boundary. v0.2 adds Redis-backed rate limits.
- **Logging aggregation** — stdout only in v0.1. v0.2 ships structured JSON logs to a configurable sink.
- **Metrics** — no Prometheus yet. v0.2.

This is the v0.1 contract: small, working, honest about what it doesn't do.
