# OpenAI / Codex OSS Application Notes — Draft

> Application notes draft for requesting OpenAI / Codex open-source support.
> This is a working document, not a final submission. It will be tightened once the maintainer reviews the language.
>
> Maintainer: the team behind [OpenCord / 开弦](https://github.com/linkaidadie-hash/opencord).

---

## 1. Project mission

**OpenCord / 开弦 is an open plaza for AI-native public collaboration.**

It is **not**:

- A chat app
- A Telegram / Discord / Slack clone
- A forum
- A project management tool

It **is**:

- A self-hostable social layer for communities that want to own their rules, data, and AI workflows.
- An **open plaza** where topics, signals, and (later) public encounters happen.
- A portable foundation: full JSON export, no lock-in, MIT-licensed.

The full vision is in [`docs/VISION.md`](VISION.md). The short version: today's communities live inside closed platforms whose relationship graphs, data, and AI integration are owned by the platform. OpenCord is a different shape — public, portable, and AI-native.

---

## 2. Where the code is right now

| Stage | Status | Branch | Notes |
|---|---|---|---|
| **v0.1 — Skeleton** | Shipped | `main` (commit `f6ceda5`) | `git clone + docker compose up` → register, post, AI summary, JSON export. |
| **C1 — Open Topic Network** | Shipped | `feature/open-topic-network-c1` (commit `63b3e92`) | 6 new tables, `/api/open-topic/*`, minimal `/open-topic` UI. |
| **C2-lite — Open Plaza + Signals** | Shipped, pushed | `feature/open-plaza-c2-lite` (commit `18c1e8f`) | `signals` table, `/api/plaza` aggregate, `/api/open-topic/signals` CRUD, `/plaza` UI. |
| **C3 — Relation graph query** | Next | (not yet branched) | graph traversal, topic recommendations. |
| **D1 — Plaza UI polish** | Planned | (not yet branched) | `/plaza` interactivity, signal threading. |
| **v0.2 — Hosted & multi-tenant** | Not in scope of OSS slice | n/a | would require paid infra. |

Code volume (as of `feature/open-plaza-c2-lite`):

- ~2,300 lines added in C, ~700 lines added in C2-lite.
- 7 new tables in `db/migrations/` (C: 6 + C2-lite: 1).
- 12 new HTTP endpoints under `/api/open-topic/*` + 1 under `/api/plaza`.
- Zero changes to v0.1's 11-table schema. No renames. No data migrations.
- All static checks pass: SQL assertions, Python AST + import smoke, bytecode compile, no trailing whitespace, no conflict markers.
- **No** Docker / PostgreSQL runtime verification yet (the maintainer's local environment lacks Docker). This is the gap OSS support would help close.

---

## 3. Why OpenCord is a good fit for Codex

Codex is the right partner for OpenCord because:

- **The codebase is small and growing**. ~3,000 lines of new code across 2 stages. Easy to onboard an AI agent that needs the whole repo in context.
- **The shape is well-bounded**. AGENTS.md / VISION.md / ROADMAP.md / ARCHITECTURE.md define a hard "do not cross" line (no private chat, no Discord clone, no agent tables). This makes Codex's "stay in scope" tractable.
- **The tests are static-and-checklist**. The current CI surface is SQL assertions + Python import smoke + git diff `--check`. Codex fits this style of work naturally.
- **The documentation surface is large relative to code**. README, ROADMAP, VISION, ARCHITECTURE, API, AGENTS, CONTRIBUTING, SECURITY, OPENAI_OSS_APPLICATION_NOTES — that's a lot of writing. Codex is well-suited for keeping docs in sync with code.
- **The community is small and intent on staying small**. There is no expectation that Codex must scale to a 10,000-PR-a-day project. The work is high-trust, high-judgment, low-volume.

---

## 4. Specific maintenance tasks Codex would help with

The following are concrete, ongoing, well-scoped tasks that would benefit from Codex assistance. None of them are "make OpenCord into a chat app".

### 4.1 Issue triage

- Read incoming issues, classify against [`AGENTS.md` § 1](AGENTS.md#1-project-positioning-read-this-first) (in-scope / out-of-scope / security).
- For out-of-scope issues, draft a polite close-with-link response.
- For in-scope bugs, suggest a label and a likely file to look at.

### 4.2 PR review

- Verify the 5 boundary questions in `AGENTS.md` § 6 are answered.
- Verify the static checks in `AGENTS.md` § 5 are listed in the PR description.
- Spot-check that no secrets are committed (`git diff --cached --name-only | grep '\.env$' || true`).
- Check for accidental schema changes to v0.1 old tables.

### 4.3 Documentation updates

- Keep `README.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md` in sync with the code as the project grows.
- Translate new content into the `*.zh-CN.md` siblings when the maintainer asks.
- Generate `docs/API.md` snippets from the FastAPI `/openapi.json` once it's stable.

### 4.4 Static checks

- Add new `scripts/check_sql_NNNN.py` when a new migration lands.
- Add new ORM / schema presence assertions to `scripts/check_python_imports.py`.
- Triage failures in CI.

### 4.5 Test generation

- Write pytest-based smoke tests for each new endpoint, following the structure of `scripts/verify_open_topic.sh`.
- Add edge cases for the `core/open_topic.py` validators (invalid `subject_type`, missing tenant, etc.).
- Add a test that `db/schema.sql` has not been mutated (a `git diff` of the file in CI is the easiest version).

### 4.6 Migration review

- For each new `db/migrations/NNNN_*.sql`, verify:
  - `CREATE TABLE IF NOT EXISTS` (idempotent)
  - `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE`
  - No PG ENUM
  - Indexes match the query patterns in the corresponding service file
- Verify no rename / no alteration of v0.1 old tables.

### 4.7 Security review

- Per-PR review of `SECURITY.md` compliance: secrets, AI provider key handling, audit log writes, CORS, JWT defaults.
- Per-PR diff scan for new endpoints that might leak tenant boundaries or accept user-supplied `tenant_id`.
- Triage of any `security` labelled issues.

### 4.8 What Codex should **not** do

- **Do not** implement private chat / DM / group chat. This is the #1 out-of-scope category.
- **Do not** introduce WebSocket / SSE.
- **Do not** introduce `agents` / `agent_runs` / `agent_actions` tables or call 杜工部.
- **Do not** bump dependency major versions without a separate PR.
- **Do not** force-push to `main` or rewrite history.
- When in doubt, **ask the maintainer** before merging. The maintainer is the human reviewer of record.

---

## 5. 3-month roadmap (the work the application would unlock)

The application is anchored in the **public, open, AI-native** shape. The 3-month plan assumes Codex assistance is available:

### Month 1 — C2 polish + Plaza UX

- Polish `/plaza` page (signal form actually wired to `POST /api/open-topic/signals`).
- Add pagination to `list_signals` and `list_topics`.
- Add `view signal detail` route.
- Add 3 follow-up migrations: topic view counts, signal reply count (if we go that way), audit log for plaza events.
- Bring static checks into a GitHub Actions workflow.

### Month 2 — Relation graph query (C3)

- New endpoints for `relations`: `GET /api/open-topic/relations/graph?root_type=&root_id=&depth=3`.
- BFS / DFS over the relation table with cycle detection.
- Use this to power a "nearby topics" widget on `/plaza` (purely public, no encounter).
- NDJSON export of the relation graph for a community.

### Month 3 — Export format + AGENTS workflow

- NDJSON export alongside JSON (`/api/export/me.ndjson`).
- Self-test `AGENTS.md` compliance: a small repo-internal "Codex" pass that reads `AGENTS.md` and checks the boundary questions for an in-flight PR.
- Public docs site: convert `docs/` to a static site with an "AI agent onboarding" entry point.

After 3 months the project should have:

- A first public deploy by a third party.
- ≥ 5 outside contributors.
- Stable API + export format.
- A clear "what's next after C3" doc in `docs/ROADMAP.md`.

---

## 6. Resources requested from OpenAI

We are applying for the **OpenAI / Codex Open Source support** track. The resources we are requesting:

### 6.1 Code access

- **ChatGPT Pro** for the maintainer and up to 2 active contributors (12 months). This unlocks Codex-backed IDE workflows for the people doing the maintenance work.
- **Codex** (current generation) access for CI / headless use. The static-check + migration-review + PR-triage workflows in § 4 are Codex-shaped.

### 6.2 API credits

- **API credits** for development and CI:
  - `gpt-4o` or equivalent for the topic-summarization pipeline (C2+ feature: a `/api/open-topic/topics/{id}/summarize` endpoint, with provider pluggability already in v0.1's `AIProvider` abstraction).
  - `text-embedding-3-small` for relation-graph semantic similarity (C3).
  - Estimated usage: ~5M tokens/month during active development, dropping to ~1M/month after stabilization.
- The credits would be used **through the project's `ai_providers` table** — not as a side channel. This means every call lands in `ai_usage_log` and is auditable, fitting the project's data-portability commitment.

### 6.3 Security review support

- A **one-shot security review** by OpenAI's security team (or a designated vendor) of the C / C2-lite / C3 code, focused on:
  - JWT / API token handling
  - AI provider key storage and rotation
  - Tenant boundary enforcement
  - CORS / authentication defaults
  - Audit log completeness
- The output would feed back into `SECURITY.md` and any follow-up PRs.

### 6.4 Community support (non-financial)

- A **listing in OpenAI's open-source directory** for discoverability, once the project is stable enough.
- A **co-streamed demo session** at the maintainer's discretion, if OpenAI's developer-relations team is interested in showcasing Codex + Codex-shaped projects.

### 6.5 What we are **not** asking for

- Equity, investment, or commercial partnership.
- Hardware.
- Trademark or branding rights.
- A guarantee of acceptance — this is an application, not a contract.

---

## 7. Why now

Three converging pressures:

1. **The agent ecosystem is growing fast.** Without an open, portable, agent-friendly community layer, the next decade of social will be even more locked-in than the last. OpenCord is trying to keep a public-shaped option alive.
2. **The maintainer has capacity.** The project has had two clean static-acceptance cycles (C, C2-lite) with disciplined branch hygiene. The next stage is the most code-heavy yet, and external help unlocks it.
3. **The shape is already chosen.** OpenCord has explicitly chosen "public plaza" over "Telegram clone". A public plaza needs AI-agent help to build out, because the surface area (export formats, schema migrations, relation graphs) is large and the maintainer is one person.

---

## 8. Closing

OpenCord is small, opinionated, and intentionally slow. It is the project equivalent of "make a small public square and keep it open". The maintainer would rather ship 200 lines of high-judgment code per week than 2,000 lines of generic social-platform features.

If this application lands well, the next 3 months would be: C2 polish, C3 relation graph, NDJSON export, GitHub Actions CI, and a public demo. None of that is "make it a chat app". All of it is the boring, important work of making the open shape actually usable.

Thanks for reading. Contact: see the maintainer in the repository's `MAINTAINERS.md` or the GitHub handle of the project owner.
