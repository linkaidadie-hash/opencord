# AGENTS.md

> Working rules for AI coding agents (Codex, Claude Code, Cursor, etc.) contributing to **OpenCord / 开弦**.

## 1. Project positioning (read this first)

**OpenCord is an open plaza for AI-native public collaboration.**

It is **not** a chat app, **not** a Telegram clone, **not** a Discord clone, **not** a forum, **not** a project management tool.

The current demo slices in this branch (`feature/open-plaza-c2-lite`) are:

- **C1 — Open Topic Network**: 6 new tables (`communities`, `topics`, `threads`, `topic_summaries`, `relations`, `follows`) + `/api/open-topic/*` + minimal `/open-topic` UI.
- **C2-lite — Open Plaza + Signals**: 1 new table (`signals`) + `/api/plaza` aggregate + `/api/open-topic/signals` CRUD + minimal `/plaza` UI.

If a proposed change would push the project toward any of the **forbidden shapes** below, **refuse or escalate** — do not implement.

### Forbidden shapes (do not implement without explicit human override)

- **Private chat / group chat / DMs** (not yet in scope)
- **WebSocket / SSE / push notifications** (not yet in scope)
- **Encounter matching / 棋友匹配 / 同城 / 地图** (not in scope)
- **Project / Task / Acceptance Criteria** (not in scope)
- **Agent / AgentRun / AgentAction** (the `agents` table is **not** introduced; `topic_summaries.generated_by` is a string defaulting to `'system'`)
- **杜工部 / any third-party agent platform** (not integrated)
- **ActivityPub / AT Protocol federation** (out of scope)
- **Plugin hot-reload** (out of scope)
- **Hosted billing / multi-tenant management UI** (out of scope)

## 2. Read these before changing anything

Always read (in this order) before opening a PR or writing code:

1. [`docs/VISION.md`](docs/VISION.md)
2. [`docs/ROADMAP.md`](docs/ROADMAP.md)
3. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
4. [`docs/API.md`](docs/API.md)
5. [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md)
6. The current `db/schema.sql` (v0.1 baseline) and any `db/migrations/*.sql` (C / C2-lite increments)
7. This file (`AGENTS.md`)

## 3. Hard rules for every change

### 3.1 Database

- **Do not** mutate any **old** table (`tenants`, `users`, `api_tokens`, `channels`, `posts`, `comments`, `tags`, `post_tags`, `notifications`, `ai_providers`, `ai_usage_log`, `audit_log`). Do not rename. Do not migrate data out of them.
- **Do not** rename `tenants` → `communities` or `ai_usage_log` → `agent_runs` or any other "concept mapping" rename. The new `communities` and `signals` tables are **additions**, not replacements.
- **Do not** introduce `agents` / `agent_runs` / `agent_actions` tables. If the change requires it, escalate to a human.
- New tables in C / C2-lite / future increments **must** have `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE`.
- Migrations **must**:
  - Live under `db/migrations/NNNN_*.sql` (zero-padded sequence number).
  - Use `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` (idempotent).
  - Use **VARCHAR** for type fields, **never** PG ENUM. Application-layer constants in `apps/api/core/open_topic.py` are the source of truth.
  - Be explicit and reviewable. **No** auto-migrations on production startup, **no** silent schema changes.
- Do **not** add Alembic.

### 3.2 Application code

- Do not introduce WebSocket / SSE endpoints.
- Do not introduce private-chat / DM / group-chat endpoints.
- Do not call into 杜工部 or any third-party agent platform.
- `tenant_id` is **never** accepted from the request body or query string. It is resolved from `current_user` via `resolve_tenant_id(user)` and validated via `ensure_tenant_exists(db, tenant_id)`. Both functions live in `apps/api/core/open_topic.py`.
- For any new model, also add the corresponding `*Create` / `*Public` Pydantic schema in `apps/api/schemas.py`. The `*Create` schema **must not** include `tenant_id`.

### 3.3 Frontend

- The frontend is **Next.js 14 App Router** under `apps/web/app/`. Do not introduce Pages Router. Do not introduce a different router paradigm.
- Do not add new UI dependencies (component libraries, CSS frameworks) without a human-reviewed PR.
- Do not modify old pages (e.g. `app/c/[slug]/page.tsx`, `app/u/[username]/page.tsx`, `app/p/[id]/page.tsx`) when adding new features; create new routes instead.

### 3.4 Secrets

- **Never** commit API keys, JWT secrets, database passwords, GitHub tokens, `.env` files, or any credential.
- AI provider keys live in the `ai_providers` table (DB), not in `.env`. Encryption-at-rest for those keys is a v0.2+ item; v0.1 stores them plaintext with the understanding that the DB is the security boundary.
- The local `.env.example` is the template. Real `.env` must stay out of git (already in `.gitignore`).
- If a secret accidentally lands in a commit, **revoke it immediately** and rotate. Do not try to rewrite history without human approval.

## 4. Required artefacts for every change

Before you mark a change "done", make sure all of these exist and are up to date:

- **Migration file** (if schema changed): `db/migrations/NNNN_*.sql`, idempotent, VARCHAR not ENUM.
- **ORM model** in `apps/api/models.py` (append, never replace; old classes byte-identical).
- **Pydantic schema** in `apps/api/schemas.py` (append; `*Create` must not expose `tenant_id`).
- **Core constants** in `apps/api/core/open_topic.py` if new type / status / visibility values were added.
- **Service** in `apps/api/services/` (one file per aggregate).
- **Router** in `apps/api/api/` (one file per aggregate; mount under `/api/<prefix>/*`).
- **`main.py` mount**: one new `app.include_router(...)` line.
- **Frontend route** if user-visible: `apps/web/app/<segment>/page.tsx`; do not edit `lib/api.ts` types in a way that drifts from the Pydantic schema.
- **Nav entry** in `apps/web/components/Nav.tsx` if a new top-level entry is added.

## 5. Required pre-commit checks

Run these locally before opening the PR:

```bash
# 1. SQL static assertion (one script per migration)
py -3 scripts/check_sql_0001.py
py -3 scripts/check_sql_0002.py
# add a new check_sql_NNNN.py if you added a new migration

# 2. Python AST + runtime import smoke
py -3 scripts/check_python_imports.py

# 3. Bytecode compile
py -3 -m compileall apps/api

# 4. Trailing whitespace / conflict markers
git diff --check

# 5. Staged content scan
git diff --cached --name-only | grep -E '\.env$|__pycache__|node_modules|\.venv'
# expected: empty
```

CI will rerun these on the PR. If any of them fail, the change is **not** ready.

## 6. Boundary check (required in every PR description)

In the PR body, answer:

1. Did this change touch `tenants` / `users` / any v0.1 old table? **No** (otherwise justify + escalate).
2. Did this change rename `tenants` → `communities` or `ai_usage_log` → `agent_runs`? **No**.
3. Did this change introduce `agents` / `agent_runs` / `agent_actions`? **No**.
4. Did this change add private chat / WebSocket / Encounter / 杜工部? **No**.
5. Did this change leak any secret? **No**.

If any answer is "Yes", the PR is **out of scope** for the current stage and must be redesigned or escalated.

## 7. Branch / commit conventions

- Branch naming: `feature/<short-name>-<stage>` for new work, `fix/<short-name>` for fixes. Examples: `feature/open-topic-network-c1`, `feature/open-plaza-c2-lite`, `fix/signal-intent-validation`.
- Commit messages: Conventional Commits style. `<type>(<scope>): <short summary>`. Allowed types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`.
- One commit per logical change. Do not bundle unrelated edits.
- Do **not** push directly to `main`. Always go through a PR + human review.

## 8. What to do when uncertain

If a request is ambiguous or conflicts with the positioning above, **ask the human** before writing code. Do not guess silently. Cite this file (`AGENTS.md`) and the relevant section when you ask.

## 9. License reminder

OpenCord is MIT-licensed. By contributing, you agree your contributions are MIT-licensed as well. Do not submit code copied from GPL / AGPL / commercial / non-permissive sources.
