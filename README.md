# OpenCord

English | [简体中文](./README.zh-CN.md)

**An open-source, AI-native community system.**

It is not trying to become another walled garden. It is a self-hostable social layer for communities that want to own their rules, data, and AI workflows.

OpenCord starts small: channels, posts, comments, notifications, admin tools, API tokens, AI summaries, and JSON export.

The goal is not to clone existing social platforms.
The goal is to give communities a portable foundation.

---

## Current demo slice

The code on `main` is the v0.1 skeleton. The current demo slice is being built on a feature branch:

- **Open Topic Network** — topics become first-class; communities host topics; relations form a graph; follows bind users to communities/topics.
- **Open Plaza Signals** — a public square where users post lightweight signals: *"I'm looking for X / I'd love to talk about Y / I can help with Z"*.
- **Feature branch**: [`feature/open-plaza-c2-lite`](https://github.com/linkaidadie-hash/opencord/tree/feature/open-plaza-c2-lite) (pushed, not yet merged into `main`).

What this branch is **not**: it is not a chat app, not a Telegram / Discord clone, not a forum, not a project management tool. See [`AGENTS.md`](AGENTS.md) § 1 for the positioning rules.

The application narrative for this slice lives in [`docs/OPENAI_OSS_APPLICATION_NOTES.md`](docs/OPENAI_OSS_APPLICATION_NOTES.md).

---

## Why OpenCord

Today, many communities live inside closed platforms:

- Relationship graphs belong to the platform
- Data cannot be exported freely
- APIs are limited or paid-only
- Automation and AI integration are restricted
- Platform rules change without notice

OpenCord offers another path: a foundation that the community itself owns.

## Core Principles

- **Users own their data** — full JSON export, no lock-in
- **Communities own their rules** — moderation, channels, visibility all under your control
- **Self-hostable** — `git clone` and `docker compose up`
- **Data is portable** — import / export, future ActivityPub support
- **AI is provider-agnostic** — OpenAI / DeepSeek / MiniMax / Ollama / any OpenAI-compatible endpoint
- **Open by default** — REST API, future WebSocket / Webhook, future plugin system

---

## v0.1 Scope

This is the skeleton release. We deliberately cut scope to ship a working foundation.

**Included:**
- User registration / login (email + password)
- Personal profile pages
- API Tokens (for bots and integrations)
- Channels (public / private)
- Posts (Markdown)
- Comments (one-level + nested replies)
- Tags
- In-app notifications (polling, no WebSocket)
- Basic admin: ban / unban / suspend / promote / demote users, delete posts
- AI Provider abstraction layer (OpenAI-compatible + 国产 models)
- AI post summary
- PostgreSQL schema with `tenant_id` reserved
- JSON data export
- Docker Compose one-command deployment
- README / ROADMAP / VISION / ARCHITECTURE / API docs (bilingual)

**Not in v0.1 (deferred to v0.2+):**
- Private messages / group chat
- WebSocket / real-time
- Webhook / Bot API
- AI profile / matching / anti-spam
- Plugin hot-reload
- ActivityPub / federation

## v0.1 Principles

- **Single-tenant, multi-tenant-ready**: every core table carries a `tenant_id uuid nullable` field
- **No WebSocket**: notifications are served via `GET /api/notifications` polling
- **Provider-agnostic AI**: every LLM goes through the `AIProvider` abstraction layer
- **Plugin-shaped code from day 1**: domain / service / api layers are decoupled; services are the boundary for future plugin replacement

---

## Quick Start

**No API key needed.** A `MockAIProvider` is shipped and seeded as default. The full flow works offline.

```bash
git clone https://github.com/linkaidadie-hash/opencord.git
cd opencord
cp .env.example .env
# Edit .env — minimum: set POSTGRES_PASSWORD (any value).
# Other variables have safe defaults for local dev.
# AI provider key is OPTIONAL in v0.1 (Mock is the default).
docker compose up -d --build
```

After startup:
- Web frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

First-time setup — run the seed script to create the default tenant, admin user, sample channels, and the Mock AI provider:

```bash
docker compose exec api python seed.py
```

Default admin (set in `.env`):
- Email: `INITIAL_ADMIN_EMAIL` (default `admin@opencord.local`)
- Password: `INITIAL_ADMIN_PASSWORD` (default `change-me`)

Try the AI summary end-to-end (admin only in v0.1):

```bash
# Get a post id
curl http://localhost:8000/api/posts

# Login as admin
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_username":"admin","password":"change-me"}'
# Save .access_token from the response

# Trigger AI summary (uses Mock by default)
curl -X POST http://localhost:8000/api/ai/summarize-post/<POST_ID> \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
# Returns: {"post_id":"...","ai_summary":"[Mock] ..."}
```

When you're ready to use a real LLM, visit `/admin/ai` and add an OpenAI / DeepSeek / MiniMax / Ollama provider. Then set it as default. The Mock provider stays available as a fallback.

> For full deployment verification, see [DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md).

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind | SSR, mature ecosystem, easy self-host |
| Backend | FastAPI (Python 3.12) | Best AI ecosystem, type-friendly, auto docs |
| Database | PostgreSQL 16 + pgvector | Primary storage + vector search in one place |
| Cache | Redis 7 | Sessions / rate-limit / AI result cache |
| Real-time | **Not in v0.1** | SSE / WebSocket deferred to v0.2 |
| Object storage | Local (v0.1) → S3 (v0.2+) | Reduce deployment friction |
| AI | OpenAI-compatible abstraction | No platform lock-in |
| Deployment | Docker Compose | One command, zero config |

---

## Project Structure

```
opencord/
├── apps/
│   ├── web/                  # Next.js frontend
│   └── api/                  # FastAPI backend
├── packages/
│   ├── ai/                   # AI Provider abstraction layer (standalone Python package)
│   ├── core/                 # (reserved for v0.2) domain models
│   ├── export/               # (reserved for v0.2) data export utilities
│   └── database/             # (reserved for v0.2) SQLAlchemy models / Alembic
├── services/                 # (top-level) cross-app service contracts (future)
├── db/
│   └── schema.sql            # Initial schema (tenant_id reserved, pgvector)
├── docs/
│   ├── ROADMAP.md / ROADMAP.zh-CN.md
│   ├── ARCHITECTURE.md / ARCHITECTURE.zh-CN.md
│   ├── API.md / API.zh-CN.md
│   └── VISION.md / VISION.zh-CN.md
├── scripts/
│   └── seed.py
├── docker-compose.yml
├── .env.example
└── README.md / README.zh-CN.md
```

The boundary between app-internal code and top-level `services` is intentional:
- Domain logic lives close to the type definitions, with no I/O dependencies
- Services orchestrate domain + database + AI, and are the boundary for future plugin replacement

---

## Commercial Layer (not in v0.1)

Open source does not mean "no business model":

- Open-source community system: **free**
- Hosted version: v0.4
- Enterprise private deployment: v0.4+
- Plugin marketplace: v0.3+
- AI usage hosting: v0.4
- Custom development: available now

No monetization in v0.1. The first goal is a working, shippable foundation.

---

## Documentation

- [ROADMAP.md](docs/ROADMAP.md) / [ROADMAP.zh-CN.md](docs/ROADMAP.zh-CN.md) — version planning
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) / [ARCHITECTURE.zh-CN.md](docs/ARCHITECTURE.zh-CN.md) — technical architecture
- [API.md](docs/API.md) / [API.zh-CN.md](docs/API.zh-CN.md) — REST API reference
- [VISION.md](docs/VISION.md) / [VISION.zh-CN.md](docs/VISION.zh-CN.md) — why OpenCord exists

---

## License

- Code: [MIT](LICENSE)
- Documentation: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Data: owned by the user (export as JSON to leave)

---

## Maintainer

- @linkaidadie-hash

> Building a boat, not fishing in someone else's pond.
