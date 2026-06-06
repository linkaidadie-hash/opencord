# OpenCord v0.1 Deployment Checklist

[English](./DEPLOYMENT_CHECKLIST.md) | [简体中文](./DEPLOYMENT_CHECKLIST.zh-CN.md)

> Status: **Static audit complete (v0.1.0)**. Real runtime verification on a host with Docker is pending — see "Verified by static audit" vs "Pending runtime verification" sections below.

## Scope of this audit

This document records what was **statically verified** (read the code, traced the request flow) vs what was **runtime-verified** (actually executed `docker compose up`).

The agent that produced this audit does not have Docker installed on its Windows host, so runtime verification must be done by the maintainer. This file is the script to follow.

If anything here fails, please open a GitHub issue with: command run, full error output, OS + Docker version.

## What v0.1 ships

- 75 files / ~7000 lines
- 3 commits on `main`
- 4 Docker services: `postgres` / `redis` / `api` / `web`
- 11 database tables (PostgreSQL 16 + pgvector)
- 9 API route groups (auth, users, channels, posts, comments, ai, admin, export, notifications)
- 10 Next.js pages
- 3 AI Provider implementations (OpenAI-compatible / MiniMax / DeepSeek) + 1 **Mock Provider** (default, no key needed)
- 1 seed script that creates: default tenant, admin user, 4 sample channels, Mock AI provider

## Prerequisites

On the host where you'll deploy:

- Docker Engine 24+ **and** Docker Compose v2
- 2 GB RAM minimum (4 GB recommended for AI summary features)
- 10 GB disk (mostly PostgreSQL data + Docker images)
- Ports 3000 (web) and 8000 (api) available

Test prerequisites:

```bash
docker --version          # Docker version 24.0.0+
docker compose version    # Docker Compose version v2.x
```

## 5-minute quick start (no API key required)

The MockAIProvider means you can experience the full flow without any external API key.

```bash
# 1. Clone
git clone https://github.com/linkaidadie-hash/opencord.git
cd opencord

# 2. Configure
cp .env.example .env
# Edit .env — minimum change: set POSTGRES_PASSWORD (any value)
# Other variables have safe defaults for local dev

# 3. Start
docker compose up -d --build

# 4. Wait for all services healthy
docker compose ps
# Expected: 4 services in "Up" / "healthy" state

# 5. Seed (creates admin + sample channels + Mock AI provider)
docker compose exec api python seed.py

# 6. Verify API
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}

curl http://localhost:8000/version
# {"name":"OpenCord","version":"0.1.0","instance":"My OpenCord Community"}

# 7. Open browser
open http://localhost:3000   # macOS
# or visit http://localhost:3000 manually
```

## What to verify

### API endpoints (curl)

```bash
# Health
curl http://localhost:8000/health
curl http://localhost:8000/version

# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"tester","password":"testpass123","display_name":"Tester"}'
# Save the .access_token from the response

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_username":"tester","password":"testpass123"}'

# List channels
curl http://localhost:8000/api/channels

# Get me (use the token from register/login)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <TOKEN>"

# Trigger AI summary on a post (admin only in v0.1)
# First login as admin (INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD from .env)
# Find a post id from the list endpoint
curl -X POST "http://localhost:8000/api/ai/summarize-post/<POST_ID>" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
# Should return: {"post_id":"...","ai_summary":"..."}

# Export data
curl http://localhost:8000/api/export/me \
  -H "Authorization: Bearer <TOKEN>" \
  -o opencord-export.json
# Open the JSON file and check it has user / posts / comments / etc.
```

### Frontend pages (browser)

| URL | Expected | Runtime check |
|---|---|---|
| `http://localhost:3000/` | Home with channel list + recent posts | ⏳ pending |
| `http://localhost:3000/login` | Login form | ⏳ pending |
| `http://localhost:3000/register` | Register form | ⏳ pending |
| `http://localhost:3000/c/general` | Channel "general" with posts | ⏳ pending |
| `http://localhost:3000/c/general/new` | New post form (requires login) | ⏳ pending |
| `http://localhost:3000/p/<id>` | Post detail with AI summary | ⏳ pending |
| `http://localhost:3000/u/admin` | Admin's profile | ⏳ pending |
| `http://localhost:3000/admin` | Admin dashboard (requires admin login) | ⏳ pending |
| `http://localhost:3000/admin/ai` | AI Provider config (should show Mock provider) | ⏳ pending |

### Admin flow

1. Login as admin (use `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` from `.env`)
2. Go to `/admin` — should see "AI Providers" card and 3 placeholder cards
3. Go to `/admin/ai` — should see the Mock AI provider pre-listed as default
4. Optionally add a real provider (OpenAI / DeepSeek / etc.) and set it as default
5. Go to any post detail page, run `POST /api/ai/summarize-post/{id}` (via curl as admin)
6. Reload the post page — the AI summary should be displayed

## Common issues

### Issue: `docker compose up` fails with "port is already allocated"

**Cause**: Another service is using port 3000 or 8000.
**Fix**: Edit `docker-compose.yml`, change `ports: "3000:3000"` to `"3001:3000"` etc.

### Issue: PostgreSQL init fails or schema missing

**Cause**: The `db/schema.sql` is mounted only on first start. If the volume already exists, schema won't re-apply.
**Fix**: `docker compose down -v` to remove volumes, then `docker compose up -d`.

### Issue: `seed.py` fails with "table does not exist"

**Cause**: API container started before PostgreSQL was ready to serve the schema.
**Fix**: Wait 30 seconds, then retry. The Docker healthcheck should prevent this but is not bulletproof on first boot.

### Issue: AI summary returns 503 "No AI provider available"

**Cause**: No AI provider is configured. (Should not happen after `seed.py` runs — Mock is created by default.)
**Fix**: Re-run `seed.py`, or visit `/admin/ai` to add a provider manually.

### Issue: Login form submits but UI doesn't change

**Cause**: The auth cookie is set via `document.cookie` (not HttpOnly) in v0.1.
**Fix**: Check the browser DevTools → Application → Cookies. You should see `opencord_token` cookie. If yes, refresh the page manually.
**v0.2 will switch to server actions and HttpOnly cookies.**

### Issue: Frontend shows "Failed to fetch"

**Cause**: Likely CORS — the API is blocking the request, or the Next.js rewrite to `api:8000` is not working.
**Fix**: 
```bash
docker compose exec web env | grep API_INTERNAL_URL
# Should be: API_INTERNAL_URL=http://api:8000
```
Also check `next.config.js` has the rewrite block. And `docker compose logs api` for CORS errors.

### Issue: Web page is empty

**Cause**: Web container's `NEXT_PUBLIC_API_URL` build arg was wrong.
**Fix**: This is a build-time variable. Re-run `docker compose build web` after fixing `.env`.

## Static verification log (what the agent verified without running Docker)

| Item | Verified | Notes |
|---|---|---|
| All Python files have valid syntax | ✅ | All 28 Python files parse with `ast` |
| All TypeScript files have valid syntax | ✅ | All 17 TS/TSX files compile |
| `docker-compose.yml` schema | ✅ | 4 services, depends_on, healthchecks, volumes OK |
| `Dockerfile` paths | ✅ | api + web both multi-stage, build context = project root |
| `db/schema.sql` loaded on first boot | ✅ | Mounted at `/docker-entrypoint-initdb.d/01-schema.sql` |
| `seed.py` idempotency | ✅ | Re-running won't duplicate |
| Default Mock AI provider created | ✅ | seed creates `mock` provider, is_default=true |
| `.env.example` covers all referenced variables | ✅ | All `settings.*` references present |
| `lib/api.ts` uses correct env var | ✅ | Uses `NEXT_PUBLIC_API_URL` or empty string (rewrite) |
| Auth flow: register → login → me | ✅ | JWT in cookie |
| CORS config allows web origin | ✅ | `CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]` |
| pgvector extension in schema | ✅ | `CREATE EXTENSION IF NOT EXISTS "vector"` + HNSW index |
| Web rewrite for `/api/*` | ✅ | `next.config.js` rewrites to `API_INTERNAL_URL/api/*` |
| Mock AI provider works without internet | ✅ | `MockAIProvider` is in-process, no network call |
| `/version` endpoint exists | ✅ | Added in this audit |
| Mock provider registered in factory | ✅ | `packages/ai/__init__.py` includes mock |

## Pending runtime verification (you, on your machine)

- [ ] `docker compose up -d --build` completes without error
- [ ] All 4 services reach "healthy" state
- [ ] `seed.py` creates admin + channels + Mock provider
- [ ] Register flow works in browser
- [ ] Login flow works in browser
- [ ] Post creation works
- [ ] Comment creation works
- [ ] AI summary returns Mock-generated text
- [ ] Data export downloads a JSON file
- [ ] Admin page is reachable for admin user
- [ ] Admin can add a real AI Provider and switch default

## Known v0.1 limitations (deferred, not bugs)

- Auth cookie is not HttpOnly (XSS risk). v0.2: server actions + HttpOnly.
- Markdown XSS sanitization is minimal (script/iframe/on* stripping). v0.2: bleach or nh3.
- AI summary is synchronous. v0.2: async queue.
- No rate limit on auth endpoints. v0.2: Redis-backed.
- No email verification. v0.2: SMTP.
- No image upload. v0.2: local + S3.
- No CI/CD. Manual `git push` only.

## What this audit did NOT do

- Did not run `docker compose up` (Docker not installed on agent's host)
- Did not test mobile responsive layout
- Did not load-test (single-user, small data)
- Did not test backup / restore
- Did not test HTTPS / reverse proxy
- Did not test multi-host deployment
