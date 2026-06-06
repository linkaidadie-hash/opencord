# OpenCord Roadmap

[English](./ROADMAP.md) | [简体中文](./ROADMAP.zh-CN.md)

> This is a direction document, not a timeline. Each version's scope is a design target, not a commitment. Actual ordering may shift based on community feedback.

---

## v0.1 — Skeleton (current)

**Goal**: Make `git clone + docker compose up` produce a community that can register, post, run AI summaries, and export JSON.

**Included:**

- [x] Project skeleton (monorepo: apps + packages + services + db)
- [x] README / ROADMAP / VISION / ARCHITECTURE / API docs (bilingual)
- [x] PostgreSQL schema (11 tables + tenant_id reserved + pgvector)
- [x] FastAPI backend
  - [x] User: register, login, JWT, API Token
  - [x] Profile: view, edit
  - [x] Channels: create, list, detail
  - [x] Posts: create, list, detail, Markdown rendering
  - [x] Comments: create, list, nested
  - [x] Tags: bind, query
  - [x] Notifications: poll, mark read
  - [x] Admin: ban / unban / suspend / promote / demote / delete post / AI Provider config
- [x] AI Provider abstraction
  - [x] `AIProvider` interface: `chat` / `summarize` / `embed`
  - [x] `OpenAICompatibleProvider` (covers OpenAI / DeepSeek / Ollama / SiliconFlow / OpenRouter)
  - [x] `MiniMaxProvider` (OpenAI-compatible)
  - [x] `DeepSeekProvider` (OpenAI-compatible, v0.2 adds thinking mode)
  - [x] Provider config stored in DB, swappable from admin
- [x] AI post summary
  - [x] AI summary cached on the post row
  - [x] Synchronous call in v0.1 (async queue in v0.2)
  - [x] Usage log + per-provider rate limit
- [x] Next.js frontend
  - [x] Register / login pages
  - [x] Home: channel list + recent posts
  - [x] Channel page: post list
  - [x] Post detail (with AI summary display)
  - [x] User profile page
  - [x] Admin: AI Provider config
- [x] Data export
  - [x] `/api/export/me` — current user's full data as JSON
- [x] Docker Compose
  - [x] postgres + redis + api + web
  - [x] One-command `docker compose up -d`

**Not in v0.1:**

- Private messages / group chat
- WebSocket / real-time
- Webhook / Bot framework
- AI profile / matching / anti-spam
- Plugin hot-reload
- Federation protocols (ActivityPub / AT Protocol)
- Multi-tenant management UI

---

## v0.2 — Messaging & Bots

**Goal**: Let communities "do private chat + accept bots".

- [ ] Private messages (P2P, with optional E2E encryption)
- [ ] Group chat (multi-party, channelized)
- [ ] WebSocket / SSE real-time
- [ ] Read receipts, unread count, recall
- [ ] Bot API (token-based)
- [ ] Webhook events (`post.created` / `comment.added` / `user.joined` / ...)
- [ ] AI user profile (based on posts + behavior)
- [ ] AI matching (profile + vector retrieval)
- [ ] AI anti-spam (classification + behavior signals)

---

## v0.3 — Federation & Migration

**Goal**: Let communities "move house, federate".

- [ ] ActivityPub exploration (minimal read / write)
- [ ] Data import tool (compatible with v0.1 / v0.2 export format)
- [ ] Data migration tool (import from Discourse / Mastodon)
- [ ] Plugin system alpha
  - [ ] Service hot-reload
  - [ ] Plugin manifest spec
  - [ ] At least 2 example plugins
- [ ] Theme / skin system
- [ ] Community rule engine (configurable)

---

## v0.4 — Hosted / Multi-tenant

**Goal**: Let "people who don't know how to deploy" use it too.

- [ ] Multi-tenant management UI
- [ ] Tenant isolation (DB schema upgrade)
- [ ] Hosted version sign-up flow
- [ ] Billing module (optional integration)
- [ ] Plugin marketplace alpha
- [ ] Industry templates (trade communities / dev communities / factory internal / interest groups)
- [ ] Enterprise SSO (OIDC / SAML)

---

## v0.5+ — TBD

- Mobile PWA
- End-to-end encrypted DMs
- Full federation compatibility
- Federated AI (multiple communities' AIs collaborating)
- Decentralized identity (DID)

---

## Design Principles (all versions)

1. **Never lock to one platform**: any "must use X" constraint is an anti-pattern
2. **Data is portable**: users can export their complete data and leave at any time
3. **AI is swappable**: any LLM can be plugged in through the Provider abstraction
4. **Code is forkable**: core code is MIT, docs are CC BY 4.0
5. **Schema is backward-compatible**: upgrades never break old data (keep last 1 version of fields)

---

## Current Status

- v0.1 status: 🚧 In progress (code complete, deployment verification pending)
- Target completion: 2026 Q2
- Maintainer: solo + AI collaboration

Slow progress is fine; wrong direction is not.
