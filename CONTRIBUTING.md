# Contributing to OpenCord / 开弦

Thanks for your interest in contributing. OpenCord is an **open plaza for AI-native public collaboration**, not a chat app, not a forum, not a project management tool. Please read the [positioning in `AGENTS.md`](AGENTS.md#1-project-positioning-read-this-first) before opening an issue or PR — most "couldn't this be a Telegram clone" suggestions are out of scope.

---

## 1. Where to start

| Goal | Where to go |
|---|---|
| Understand the mission | [`docs/VISION.md`](docs/VISION.md) |
| See the roadmap | [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| Understand the architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| See the API surface | [`docs/API.md`](docs/API.md) |
| Run it locally | [`README.md`](README.md) + [`docs/DEPLOYMENT_CHECKLIST.md`](docs/DEPLOYMENT_CHECKLIST.md) |
| Working as an AI coding agent | [`AGENTS.md`](AGENTS.md) |

---

## 2. Filing issues

Use the GitHub issue templates. Pick the right one:

- **Bug report** — when something that's working in the latest `main` regressed.
- **Feature request** — when proposing something that fits the public-plaza positioning.
- **Documentation issue** — when docs are wrong, missing, or unclear.
- **Security issue** — **do not** open a public issue. Follow [`SECURITY.md`](SECURITY.md) instead.

A good issue includes:

- The version / commit hash you're testing against.
- A minimal reproduction (commands, curl, screenshot).
- What you expected vs what you got.
- Relevant logs (`docker compose logs api --tail 200` etc.).

Issues that request any of the **out-of-scope shapes** (private chat, Discord-style rooms, project management, etc.) will be closed with a link back to `AGENTS.md` § 1.

---

## 3. Branch naming

- **Feature work**: `feature/<short-kebab-name>-<stage>`
  Example: `feature/open-plaza-c2-lite`, `feature/relation-graph-c3`, `feature/agent-summaries-d1`.
- **Bug fixes**: `fix/<short-kebab-name>`
  Example: `fix/signal-intent-validation`, `fix/topic-status-patch-403`.
- **Docs only**: `docs/<short-kebab-name>`
  Example: `docs/contributing`, `docs/roadmap-c3`.

Never branch directly from `main` mid-PR. Always branch from `main` for new work, or from a feature branch if you're stacking small changes on top of an in-flight feature.

---

## 4. Pull request workflow

1. **Fork** the repo (or use a feature branch if you have write access).
2. **Branch** off `main` (or the agreed base branch) with a name from § 3.
3. **Read** [`AGENTS.md`](AGENTS.md) and the linked VISION / ROADMAP / ARCHITECTURE before writing code.
4. **Make the change.** Follow the hard rules in `AGENTS.md` § 3.
5. **Run all required checks** (`AGENTS.md` § 5). All must pass locally before opening the PR.
6. **Open the PR** against `main` (or the staging branch if the maintainer says so).
7. **Fill in the PR template.** Answer all 5 boundary-check questions (see `AGENTS.md` § 6). If any is "Yes", explain why in the PR body.
8. **Wait for review.** At least one human reviewer must approve. AI-authored PRs are welcome but a human must sign off.
9. **Squash-merge** is the default. The PR title becomes the commit subject.

### PR size

- Small, focused PRs merge faster. Aim for < 500 lines of diff.
- Larger changes (e.g. a new migration) are fine if the diff is **cohesive** and the PR description clearly partitions it.

### Review SLA

- Initial triage: 7 days.
- Substantive review: 14 days for features, 7 days for fixes.

If you need faster turnaround, mark the PR as `urgent:` in the title and explain why in the body.

---

## 5. Commit message style

We use **Conventional Commits**. Format:

```
<type>(<scope>): <short summary>

<optional body explaining why, not what>

<optional footer with refs / breaking-change notes>
```

Allowed `<type>` values:

| Type | When |
|---|---|
| `feat` | New user-visible feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or fixing tests |
| `chore` | Tooling, build, dependencies, CI |
| `perf` | Performance improvement |

`<scope>` is the area of the codebase (e.g. `open-topic`, `plaza`, `signals`, `auth`, `docs`). Keep the summary under 72 characters; no trailing period.

Examples:

```
feat(plaza): add open plaza signals skeleton
fix(signal): reject unknown intent_type with 400
docs(roadmap): add C / C2-lite summary
chore(deps): bump fastapi to 0.115.x
```

---

## 6. Static checks you must run locally

These all run in CI as well, but please don't make CI do the catching you can do at the desk:

```bash
# 1. SQL static assertion (one per migration that exists)
py -3 scripts/check_sql_0001.py
py -3 scripts/check_sql_0002.py
# add check_sql_NNNN.py for any new migration

# 2. Python AST + runtime import smoke
py -3 scripts/check_python_imports.py

# 3. Bytecode compile
py -3 -m compileall apps/api

# 4. Trailing whitespace / conflict markers
git diff --check

# 5. No secrets in staged content
git diff --cached --name-only | grep -E '\.env$|__pycache__|node_modules|\.venv'
# expected: empty
```

A CI green is required to merge. A local green is required to open the PR.

---

## 7. What we **do** accept (high-signal directions)

These are in scope and welcome. Pick one and dig in:

- **Open Topic Network** — topic CRUD, topic-relation graph queries, topic search, topic summarization
- **Open Plaza** — feed algorithms, signal types, signal threading, signal-to-encounter conversion rules
- **Public square UX** — `/plaza` page polish, follow graph visualization, signal publish flow
- **Portable data** — JSON / NDJSON / Atom export formats, import tooling, schema migration helpers
- **Static checks & dev tooling** — better check scripts, CI workflows, type hints, doc lint
- **i18n** — `README.zh-CN.md` parity, UI translations, locale-aware timestamps
- **Documentation** — anything that makes it easier for the next contributor or operator
- **OpenAI / Codex OSS application** — see `docs/OPENAI_OSS_APPLICATION_NOTES.md` for the directions that line up with the application

---

## 8. What we **do not** accept (out of scope)

These will be closed immediately with a link back to `AGENTS.md` § 1:

- "Add private chat" / "Add DM" / "Add group chat"
- "Add WebSocket / live cursors / presence"
- "Make it work like Discord / Telegram / Slack / Teams"
- "Add project management" / "Add kanban" / "Add task dependencies"
- "Introduce `agents` / `agent_runs` / `agent_actions`"
- "Integrate 杜工部 / any third-party agent platform"
- "Add ActivityPub / federation"
- "Add a plugin system"
- "Add hosted billing"
- "Rename `tenants` to `communities`" or any other "concept mapping" rename
- "Refactor everything in one mega-PR"

If your idea falls in this list but you still think it has merit, open an **issue** with the discussion tag and we can debate it. Don't open a PR.

---

## 9. Participating in the Open Topic / Open Plaza direction

If you want to contribute to the active stage (right now: C2-lite polish → C3 relation graph):

1. Read `docs/ROADMAP.md` to see the current stage scope.
2. Skim the related migration file under `db/migrations/` and the relevant `apps/api/api/open_topic_*.py` and `apps/api/services/*_service.py` files.
3. Look at open issues tagged with the stage name.
4. Open a draft PR early. We'd rather see a 200-line draft than a 2,000-line surprise.

For Plaza UI work specifically, the `apps/web/app/plaza/page.tsx` page is the canonical entry. Anything that expands the plaza is welcome, as long as it doesn't drift into "private chat in disguise" (DMs hidden behind a "ticket" label, etc.).

---

## 10. Coding style

- **Python**: PEP 8, type hints on new code, snake_case, async/await for IO. Run `py -3 -m py_compile` on changed files locally.
- **TypeScript**: existing Next.js / React style in `apps/web/`. No new dependencies without PR review.
- **SQL**: lowercase keywords, snake_case identifiers, schema qualified (`public.communities`), explicit `IF NOT EXISTS` on every CREATE in migrations.
- **Commits**: one logical change per commit. Do not bundle unrelated edits.

---

## 11. License

By contributing, you agree your contributions are licensed under the project's [MIT License](./LICENSE). Do not submit code copied from GPL / AGPL / commercial / non-permissive sources.

---

## 12. Code of conduct (short version)

- Be kind. Assume good faith. Argue ideas, not people.
- No harassment, no doxxing, no discrimination.
- Disagreement is welcome; rudeness is not.

The full CoC will be in `CODE_OF_CONDUCT.md` (pending). In the meantime, follow the spirit above.
