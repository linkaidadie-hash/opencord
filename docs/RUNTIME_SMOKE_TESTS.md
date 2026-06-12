# Runtime smoke tests — Open Plaza / Open Topic Network

> Status: authored on `feature/runtime-smoke-tests`, **not yet merged**.
> Scope: closes the gap described in `docs/DEMO_WALKTHROUGH.md` § 6.2
> and in [issue #7](https://github.com/linkaidadie-hash/opencord/issues/7).

This document explains how the runtime smoke surface is wired up, who runs
what, and how to interpret failures. Read it once before opening a PR that
touches `db/`, `apps/api/`, or `scripts/`.

---

## 1. What "runtime smoke" actually checks

The static checks in `AGENTS.md` § 5 (`check_sql_0001.py`,
`check_sql_0002.py`, `check_python_imports.py`, `git diff --check`) are
necessary but **not sufficient**. They tell you the SQL parses, the Python
imports, and the diff is clean. They do **not** tell you:

1. PostgreSQL can actually execute the migrations end-to-end.
2. The 7 new tables (`communities`, `topics`, `threads`, `topic_summaries`,
   `relations`, `follows`, `signals`) physically exist after migration.
3. `tenant_id` is `NOT NULL` on every one of them, on a real Postgres.
4. The v0.1 baseline (`tenants`, `users`, `api_tokens`, `channels`,
   `posts`, `comments`, `tags`, `post_tags`, `notifications`,
   `ai_providers`, `ai_usage_log`, `audit_log`) is still intact.
5. The FastAPI app boots, `/health` returns 200, and the Open Topic /
   Open Plaza routers respond.

The runtime smoke surface covers all five. It runs **two equivalent ways**:

| Path | Where it runs | When |
|---|---|---|
| `.github/workflows/runtime-smoke.yml` | GitHub Actions runner | Every PR that touches `db/`, `apps/api/`, `apps/web/`, `scripts/`, `docker-compose.yml`, or this workflow file. Also on push to `main` and on `workflow_dispatch`. |
| `scripts/runtime_smoke_open_plaza.sh` | A developer machine with Docker | Manual reproduction of the same checks locally. |

Both paths share the same exit-code semantics and the same SQL contract.

---

## 2. What it does NOT do (yet)

- It does **not** boot the Next.js web frontend. Issue #7 scope is the
  API + database half.
- It does **not** exercise `apps/web/app/plaza/page.tsx` in a real
  browser. That's tracked separately.
- It does **not** run `tsc --noEmit` for the frontend.
- It does **not** replace `scripts/check_python_imports.py` /
  `check_sql_0001.py` / `check_sql_0002.py`. Those still run first
  inside the workflow and are required for merge.
- It does **not** mutate `db/schema.sql` or any existing migration. The
  contract is: existing files unchanged, new tables only.

---

## 3. Running it on a developer machine

You need a Docker daemon (Docker Desktop 4.x+, or any recent
docker-engine with the `compose` plugin). Postgres / Redis clients
on the host are **not** required.

### 3.1 Quickest path (DB-only contract)

```bash
bash scripts/runtime_smoke_open_plaza.sh
```

What this does:

1. Verifies `docker` and `docker compose` are present and the daemon
   is reachable.
2. Brings up `postgres` + `redis` from `docker-compose.yml` (project
   name `opencord-smoke`, isolated volume).
3. Waits for Postgres healthcheck.
4. Applies `db/migrations/0001_open_topic_network.sql`.
5. Applies `db/migrations/0002_open_plaza_signals.sql`.
6. Asserts the 7 new tables exist with `tenant_id uuid NOT NULL`.
7. Asserts the 12 v0.1 baseline tables are still present.
8. Best-effort: if an API is already up at `OPENCORD_API`, hits
   `/health`, `/api/plaza`, `/api/open-topic/signals`,
   `/api/open-topic/communities`. If not, prints a hint.
9. Tears the stack down on exit.

The script returns a specific exit code per failure class (see the
script header for the full table). A green run ends with
`[ALL SMOKE CHECKS PASSED]`.

### 3.2 Full path (DB + live API)

```bash
# Bring up everything
docker compose -p opencord-smoke up -d postgres redis
docker compose -p opencord-smoke up -d --build api

# Re-run the smoke against the running api
bash scripts/runtime_smoke_open_plaza.sh --skip-docker
```

The script then runs the 14-step curl smoke from
`scripts/verify_open_topic.sh` against the live API and exits non-zero
if any step fails.

### 3.3 Skip mode (assert against an existing instance)

```bash
OPENCORD_API=https://my-staging.example.com \
  bash scripts/runtime_smoke_open_plaza.sh --skip-docker
```

This is the path for an already-deployed staging instance. The script
will skip the docker half and only exercise the API surface.

### 3.4 Useful env vars

| Variable | Default | Meaning |
|---|---|---|
| `OPENCORD_API` | `http://localhost:8000` | Where the API listens. |
| `COMPOSE_FILE` | `<repo>/docker-compose.yml` | Compose file used. |
| `COMPOSE_PROJECT_NAME` | `opencord-smoke` | Compose project name (controls volume / network names). |
| `PG_READY_TIMEOUT` | `30` | Seconds to wait for Postgres healthcheck. |
| `HEALTH_TIMEOUT` | `60` | Seconds to wait for `/health`. |
| `TEARDOWN=0` | `1` | Don't tear the stack down on exit. |

---

## 4. Running it in CI

`.github/workflows/runtime-smoke.yml` runs automatically on:

- Any PR that touches `db/**`, `apps/api/**`, `apps/web/**`,
  `scripts/**`, `docker-compose.yml`, or itself.
- Pushes to `main`.
- Manual dispatch via the Actions tab.

A failure means: **the PR regressed the runtime contract**. Open the
workflow run, scroll to the failing step, and read the output:

- `apply migration 0001` / `apply migration 0002` failed → the
  migration doesn't parse on a real Postgres. Re-run locally with
  `bash scripts/runtime_smoke_open_plaza.sh`.
- `assert 7 new tables + tenant_id NOT NULL` failed → one of the new
  tables is missing or `tenant_id` is wrong. Read the
  `::error file=...` annotation.
- `assert v0.1 baseline tables still present` failed → the change
  accidentally dropped a v0.1 table. This is a hard regression per
  `AGENTS.md` § 3.1.
- `wait for /health` failed → the api didn't start. The `uvicorn-log`
  artifact (uploaded on failure) has the traceback.
- `scripts/verify_open_topic.sh` failed → the 14-step curl smoke
  hit an unexpected 4xx/5xx. Read which step printed `[FAIL]`.

The workflow uses `concurrency.cancel-in-progress: true` on the same
ref so a stale push doesn't block the next one.

---

## 5. Adding a new migration? Update both paths.

If you add `db/migrations/0003_*.sql`:

1. Add a `check_sql_0003.py` mirroring the 0001 / 0002 scripts.
   Wire it into `.github/workflows/runtime-smoke.yml` next to the
   existing static-check steps, and into `AGENTS.md` § 5.
2. Add a new expected table name to the `EXPECTED` array in
   `.github/workflows/runtime-smoke.yml` *only* if 0003 introduces a
   new top-level table (not for ALTERs / new indexes).
3. Add a corresponding `psql -f ...` step to apply 0003 in the
   workflow, after 0002.
4. If you add a new top-level table, mirror it in
   `scripts/runtime_smoke_open_plaza.sh`'s `EXPECTED_TABLES` array
   so the local flow stays equivalent.
5. If you intend to keep `tenant_id NOT NULL REFERENCES tenants(id)`
   on every new table — and you must, per `AGENTS.md` § 3.1 — the
   assertion in step 4 of `runtime-smoke_open_plaza.sh` will catch
   a regression automatically.

---

## 6. Boundaries respected by this surface

- `db/schema.sql`, `db/migrations/0001_open_topic_network.sql`,
  `db/migrations/0002_open_plaza_signals.sql` are **read-only inputs**
  to this workflow / script. They are not modified by the smoke.
- `apps/api/models.py`, `apps/api/schemas.py`, `apps/api/api/**`,
  `apps/api/services/**`, `apps/web/**` are **not modified** by this
  PR. The smoke calls them, it doesn't change them.
- The smoke is fail-loud. If a migration can't apply, the workflow
  step exits 1 immediately; no silent fallback.
- No secrets are injected by the smoke. Postgres password is
  `change_me`, matching `docker-compose.yml` defaults. CI uses
  GitHub Actions `env:` (not secrets) because nothing sensitive is
  involved at this layer.

---

## 7. Relationship to existing docs

- [`docs/DEMO_WALKTHROUGH.md`](DEMO_WALKTHROUGH.md) § 6.2 / § 7 — the
  human-walked version of the same checks. This file is the
  automated / CI counterpart.
- [`docs/DEPLOYMENT_CHECKLIST.md`](DEPLOYMENT_CHECKLIST.md) — operator-
  facing deploy checklist. References this file under the "post-deploy
  smoke" section.
- [`AGENTS.md`](../AGENTS.md) § 5 — static-only pre-commit checks.
  This file is what runtime adds on top of them.

---

## 8. Open follow-ups (not part of #7)

- Browser-level smoke of `/plaza` and `/open-topic` (Playwright).
- `tsc --noEmit` for `apps/web/` on the same runner.
- Caching pip / Next.js build in the workflow for faster PR feedback.
- A nightly run that exercises the 14-step smoke against a fresh
  seed (admin user + a sample community) so the assertion surface
  grows beyond "schema + routers respond".

None of these block #7 from being merged.