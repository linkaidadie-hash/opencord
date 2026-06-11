# Demo Walkthrough — Open Plaza + Open Topic Network

> This is the **demo narration** for the C2-polish slice of OpenCord / 开弦.
> It is what an applicant, an OpenAI Codex reviewer, or a curious visitor would read to understand what the project is, what is real today, and what is not.
>
> It is **not** a release. It is **not** a feature spec. It is a walkthrough that doubles as a boundary statement.

---

## 1. The shape in one sentence

**OpenCord is an open plaza for AI-native public collaboration.** People, topics, and signals share public space first; private or agentic surfaces come later, only when the public shape holds up.

What it is **not**:

- A chat app
- A Telegram / Discord / Slack clone
- A forum (threads under channels, top-down moderation)
- A project management tool
- A private social network

If any of those better describes the feature you are about to add, **stop and re-read [`AGENTS.md` § 1](AGENTS.md#1-project-positioning-read-this-first)**.

---

## 2. What is the Open Topic Network?

The Open Topic Network is the data + API skeleton of the project. It treats **topics** as first-class objects that the rest of the system hangs off.

| Concept | What it is | Why it matters |
|---|---|---|
| **Community** | A container for topics. The closest analog is a forum category, but it is not a "channel" you post in. | Communities are the second-level scope. You follow a community, the topics inside it surface. |
| **Topic** | An open question / subject / area of attention. Has a title, a body, a status (`open` / `resolved` / `archived`). | Topics are what gets discussed. They outlive any single thread. |
| **Thread** | A specific conversation inside a topic. C2-lite does not yet attach posts / comments to threads; threads are atomic discussion entries on their own. | Threads are where actual back-and-forth happens. They are not the unit of "the topic". |
| **Relation** | A typed edge in a graph. `topic --hosts--> community`, `topic --relates_to--> topic`, `user --follows--> topic`, etc. | The network is the part that makes OpenCord interesting — it is a graph, not a list of posts. |
| **Follow** | A user-side bookmark. Target is a community / topic / project / user. | What you follow is what shows up in your plaza. |
| **Topic summary** | A cached AI summary of a topic. `generated_by` is a string defaulting to `'system'`. | Where agent-generated content will eventually live, but **no agent table is introduced in C2-lite**. |

The 6 tables for the Open Topic Network live in [`db/migrations/0001_open_topic_network.sql`](../db/migrations/0001_open_topic_network.sql). They are **additions** to the v0.1 schema; nothing in v0.1 was renamed or migrated out.

---

## 3. What are Open Plaza Signals?

A **Signal** is a public, lightweight, intent-bearing post in the plaza. It is the smallest unit of "I'm here, and here's what I want".

Six intent types (defined as VARCHAR in the DB, with application-layer constants in [`apps/api/core/open_topic.py`](../apps/api/core/open_topic.py)):

| Machine | Human (UI label) | Hint |
|---|---|---|
| `looking_for_person` | **Looking for people** | I want to find someone to work / think with |
| `looking_for_help` | **Looking for help** | I need a hand on a specific problem |
| `looking_for_project` | **Looking for projects** | I want to join or start something |
| `offering_help` | **Offering help** | I can lend a hand; here is what I can do |
| `open_to_chat` | **Open to talk** | Around a topic, no specific ask |
| `seeking_feedback` | **Seeking feedback** | I made something; I want honest reactions |

A Signal has:

- A `title` (one-line, human-readable, max 200 chars)
- An optional `body` (longer context)
- Optional `tags` (JSONB array)
- Optional `topic_id` (a Signal can hang in the plaza without a topic, or attach to one)
- A `visibility` (public / unlisted / private) — but the plaza feed only shows `public`
- An optional `expires_at` (the schema supports it; UI doesn't yet expose it)

The 1 table for signals lives in [`db/migrations/0002_open_plaza_signals.sql`](../db/migrations/0002_open_plaza_signals.sql). Again: pure addition. No old table touched.

---

## 4. How a user would see this

This is the demo flow, as it would play out on a properly-deployed instance.

### Step 1 — Land on `/plaza`

`https://<your-host>/plaza` shows:

- A header banner: "Open Plaza · 开放广场 — A public square for topics, signals, and open encounters."
- A two-column feed: **recent topics** (left) and **recent signals** (right).
- A small signal publish form at the bottom (C2-polish: UI-only; submit wires up in a later stage).

If the backend is down, a yellow banner explains the most likely causes (no migration, default tenant missing, etc.).

### Step 2 — Browse a topic

Clicking a topic title takes the user to `/open-topic/<topic-id>`, which shows:

- The topic's title, status, and body
- A list of related topics (via the `relations` table, with `relation_type` filterable)
- A thread list (each thread is a discussion entry; the C2-lite version is a thin line of body text)

There is **no** "reply" button in the C2-lite view, because threads are not yet wired to a comment form. That comes after Plaza polish.

### Step 3 — Publish a Signal

In a future C-stage, the form at the bottom of `/plaza` will POST to `POST /api/open-topic/signals`. Today the form is rendered with `disabled` inputs; the API exists and is fully tested at the static-check level. The user experience is: form, intent type, title, body, tags, submit → the signal appears at the top of the right column.

### Step 4 — Why you can also see what you follow

`GET /api/open-topic/follows/me` returns the signals-and-topics the current user has followed, scoped to their tenant. The plaza feed and the follow feed are the same data, filtered two different ways.

---

## 5. What this is **not** (recap)

- **Not** a chat app. No DMs, no group chat, no threads-as-DMs-in-disguise.
- **Not** a Discord clone. No "server + role + room" model.
- **Not** a forum. There is no "post → comment → comment" pyramid. Topics are top-level.
- **Not** a project management tool. There is no kanban, no task, no acceptance criteria.
- **Not** an agent platform. There is **no** `agents` / `agent_runs` / `agent_actions` table. `topic_summaries.generated_by` is a string defaulting to `'system'`.
- **Not** integrated with 杜工部. Period.
- **Not** an ActivityPub node. No federation.
- **Not** a plugin host. No hot-reload.
- **Not** a hosted-billing product. Self-host only.

The 5-boundary check from [`AGENTS.md` § 6](AGENTS.md#6-boundary-check-required-in-every-pr-description) is the canonical way to ask "is this PR in scope". If any of the 5 questions answers "Yes", the PR is out of scope.

---

## 6. What has been validated (and how)

### 6.1 What **has** been validated

Static-only checks, run in this order (all green at `a9a4465`):

| Check | Command | Result |
|---|---|---|
| SQL 0001 static | `py -3 scripts/check_sql_0001.py` | **ALL SQL CHECKS PASSED** |
| SQL 0002 static | `py -3 scripts/check_sql_0002.py` | **ALL SQL 0002 CHECKS PASSED** |
| Python AST | `py -3 scripts/check_python_imports.py` (part 1) | **all 44 .py files parsed by AST** |
| Python runtime import | `py -3 scripts/check_python_imports.py` (part 2) | **ALL PYTHON IMPORT CHECKS PASSED** (7 new ORM, 12 open_topic subroutes, `/api/plaza/*` mounted) |
| Bytecode compile | `py -3 -m compileall apps/api` | **exit=0** |
| Trailing whitespace / conflict markers | `git diff --check` | **exit=0** |
| Staged secrets scan | `git diff --cached --name-only \| grep -E '\.env$\|__pycache__\|node_modules\|\.venv'` | empty |
| v0.1 tables unchanged | `git diff -- db/schema.sql` | empty |
| Old routers still importable | import smoke | `auth / users / channels / posts / comments / ai / admin / export / notifications` all present |

### 6.2 What has **not** been validated (yet)

The maintainer's local environment lacks Docker and PostgreSQL CLI. **The following have not been run end-to-end:**

- ❌ Real PostgreSQL execution of migration 0001 (Open Topic Network)
- ❌ Real PostgreSQL execution of migration 0002 (Signals)
- ❌ `docker compose up`
- ❌ The 6 new tables physically existing in a real database
- ❌ The 1 new `signals` table physically existing in a real database
- ❌ `GET /api/plaza` returning a real 200 with a real DB behind it
- ❌ `POST /api/open-topic/signals` returning a real 201
- ❌ `GET /api/open-topic/signals/{id}` returning a real 200
- ❌ Old endpoints (`/api/channels`, `/api/posts`, etc.) returning real 200/201
- ❌ Frontend `/plaza` rendered by a real browser
- ❌ Frontend `/open-topic` rendered by a real browser
- ❌ `tsc --noEmit` / `next lint` for the frontend
- ❌ The 14-step curl smoke in `scripts/verify_open_topic.sh` against a live stack

This is the most important gap. A future stage (or a separate CI job) must close it before any "release" claim is made.

---

## 7. How to do the runtime validation locally

The intended next step. Anyone with Docker + PostgreSQL can close the § 6.2 gap in ~10 minutes.

```bash
# 1. Start the stack
docker compose up -d postgres redis
docker compose up -d api web
docker compose logs -f api    # wait for "connected to ..."

# 2. Apply both migrations (C + C2-lite)
cat db/migrations/0001_open_topic_network.sql \
  | docker compose exec -T postgres psql -U opencord -d opencord
cat db/migrations/0002_open_plaza_signals.sql \
  | docker compose exec -T postgres psql -U opencord -d opencord

# 3. Confirm 7 new tables exist and tenant_id NOT NULL
docker compose exec postgres psql -U opencord -d opencord -c "\dt" | \
  grep -E "^\s*public\s+\|\s+(communities|topics|threads|topic_summaries|relations|follows|signals)\b"
# expect: 7 rows
for t in communities topics threads topic_summaries relations follows signals; do
  docker compose exec postgres psql -U opencord -d opencord -c "\d $t" | grep tenant_id
done
# expect: every table shows "tenant_id | uuid | not null"

# 4. Get a JWT
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@opencord.local","username":"demo","password":"correct-horse-battery-staple","display_name":"Demo"}' \
  | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
# fallback: /api/auth/login if user already exists

# 5. Hit the plaza + signals
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/plaza
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/open-topic/signals
# expect: 200, JSON body, no 5xx

# 6. Run the 14-step curl smoke
bash scripts/verify_open_topic.sh
# expect: [ALL 14 STEPS PASSED]

# 7. Browse the plaza in a real browser
#   http://localhost:3000/plaza
#   http://localhost:3000/open-topic
```

If any of the above fails:

```bash
# Dump everything for triage
docker compose logs --tail 200 > /tmp/opencord.log
docker compose exec postgres psql -U opencord -d opencord -c "\d+ signals"
```

---

## 8. What comes after C2-polish

This walkthrough is for C2-polish. The 8 follow-up issues (created in this round) are the candidate next steps, in roughly this order:

1. **Polish Open Plaza UI** — wire the publish form, add pagination, add a "view signal detail" page.
2. **Add relation graph query** — `GET /api/open-topic/relations/graph?root_type=&root_id=&depth=3`.
3. **Add export format for topics and signals** — NDJSON alongside JSON.
4. **Add runtime Docker / PostgreSQL smoke tests** — close the § 6.2 gap.
5. **Add topic summary workflow** — system-triggered or user-triggered, still without an `agents` table.
6. **Add signal discovery filters** — by intent type, by tag, by recency.
7. **Add AGENTS workflow for Codex issue triage** — the boundary check from `AGENTS.md` § 6 as a first pass.
8. **Add security review checklist** for AI provider keys and data portability.

The deliberate non-features (private chat, WebSocket, Encounter, 杜工部, ActivityPub, plugin system, hosted billing) are **not** in any of those 8 issues. They are explicitly parked.

---

## 9. Closing

If you read this far and your reaction is "this is way too small to matter", that's the right reaction. OpenCord is intentionally small. The aim of the C / C2-lite / C2-polish stages is to make the **shape** of an open plaza legible and demoable, not to ship a feature-complete social platform.

The next stage is bigger — relation graph queries, runtime validation, a first public deploy — but it's still small on the "shapes" axis. The project will not become a chat app. It will become a slightly fuller plaza.

If you have feedback, open an issue. If you want to run it, follow § 7. If you want to review the PR boundary check, it's [`AGENTS.md` § 6](AGENTS.md#6-boundary-check-required-in-every-pr-description).
