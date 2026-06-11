# Security Policy

OpenCord / 开弦 takes security seriously. This document explains how to report a vulnerability, what we consider in scope, and the security principles that guide the project.

---

## 1. Reporting a security issue

**Do not** open a public GitHub issue for security problems.

Report privately via one of:

- **GitHub Security Advisories**: the repository's "Security" tab → "Report a vulnerability". This is the preferred channel; it goes only to the maintainers.
- **Email**: see the maintainer contact in the repository's `CODEOWNERS` or `MAINTAINERS.md` (if present). If neither is present, ask in a non-sensitive channel and we'll route you.
- **Out-of-band**: for very sensitive disclosures, find the maintainer on the project's public chat and request a private channel.

When you report, please include:

- A short description of the issue and its impact.
- Reproduction steps or a minimal PoC.
- The commit hash / version you tested against.
- Whether you intend to disclose publicly (and on what timeline).

We aim to:

- Acknowledge within **3 business days**.
- Triage and assign a severity within **7 days**.
- Issue a fix or mitigation for **Critical / High** within **30 days** where possible.

We follow **coordinated disclosure**: please give us a reasonable window (default 90 days) before public disclosure. We won't threaten or sue researchers who act in good faith.

---

## 2. Secrets — what **never** goes into the repo

The following are **never** accepted in commits, issues, comments, screenshots, or any other repository content:

- API keys (OpenAI, DeepSeek, MiniMax, Ollama, etc.)
- JWT signing secrets
- Database passwords
- GitHub personal access tokens (PATs) / GitHub App private keys
- Cloud provider credentials (AWS, GCP, Cloudflare, etc.)
- Any `.env` file with real values
- Browser cookies / session tokens
- Real user data of any kind

`AGENTS.md` § 3.4 and `.gitignore` enforce the obvious cases. The rules in this section are stronger: **don't paste them into chat, screenshots, or issue comments either**, even ephemerally.

### What to do if a secret leaks

1. **Revoke it immediately** at the provider (rotate, disable, delete — whichever is fastest).
2. **Do not** try to "fix" by amending / force-pushing. The leak is in chat history anyway.
3. Open a private report (see § 1) so we can audit whether it was used.
4. Generate a new credential and store it only in the deployment-time secret manager (env, vault, k8s secret, etc.).

If you have to send a secret to a teammate (e.g. a JWT secret during onboarding), use a one-time share link from a password manager (1Password, Bitwarden Send, etc.) and rotate after.

---

## 3. AI provider keys — the project's specific policy

OpenCord v0.1 stores AI provider keys in the `ai_providers` table (DB) so the project can be self-hosted and rotated without a code deploy. **This is not the long-term answer.**

### Current state (v0.1 / C / C2-lite)

- Keys are stored **plaintext** in the `api_key` column of `ai_providers`.
- The security boundary is the **database itself**. If you can SELECT from `ai_providers`, you can read the keys.
- Encryption-at-rest for that column is a v0.2+ item. Do not add it inside a C / C2-lite PR.

### Required practices regardless

- **Do not** put AI provider keys in `.env` (the project loads from `ai_providers`, not env).
- **Do not** log the full request / response body of an LLM call without redaction. PII / keys / internal prompts can leak through logs.
- **Do not** expose the `ai_providers` table to read-only API tokens with broader scope than needed.
- **Rate limit** per-user AI usage (the `ai_usage_log` table is the basis for this; rate limiting is a v0.2+ item).
- **Audit log**: admin actions that change AI provider config (create / switch / delete) **must** be written to `audit_log`. v0.1 already does this; do not remove the writes in future PRs.

### Future direction (not in scope of current stages)

- Encryption-at-rest for the `api_key` column using a KMS-managed key.
- Per-tenant AI provider isolation (so a self-hosted instance can let each community bring its own key).
- Provider-side spend limits surfaced in `ai_usage_log`.

If a security-sensitive AI provider issue is reported (e.g. a key was leaked through the admin UI), please report it via the § 1 private channel and treat it as Critical.

---

## 4. Data portability and the privacy boundary

OpenCord's core promise is **"the community owns its data"**. This has security implications:

- **JSON export** (`/api/export/me` and friends) **must** work for every user, with no hidden fields, no PII scrubbing required, no waiting period. It is a user right, not a feature.
- **NDJSON / portable format** for bulk export: planned, not yet implemented. When added, it must cover everything the JSON export covers.
- **Audit log** is read-only for the actor and admin. Users have the right to see what admins have done with their data.
- **Delete endpoints** must be **hard delete by default** for user-initiated deletions. Soft delete is acceptable for moderation flows but must be purged after a documented retention period (default 90 days).
- **Right to be forgotten**: not yet a hard requirement in v0.1, but the schema should not make it impossible. Don't add tables without a `user_id` or `tenant_id` cascade path.

Any change that **weakens** export, hides data from a user, or makes portability harder must be flagged in the PR.

---

## 5. Plugins / second-party code — what is and is not allowed

OpenCord v0.1 does **not** support hot-reloadable plugins. Future plugin systems (if any) will be designed around these principles:

- A plugin **may not** weaken the export / audit / portability story. If your plugin's data model is opaque to the host, that is a hard rejection.
- A plugin **may not** exfiltrate data. All IO must be visible to the host and to the user.
- A plugin **may not** require disabling `audit_log`.
- A plugin **may not** add private chat / DM / group chat as a "side feature". If it must, that's a fork, not a plugin.
- A plugin **must** declare its dependencies and license. AGPL / commercial / closed-source plugins are not acceptable in this repo.
- A plugin that needs new schema must follow the same migration rules in `AGENTS.md` § 3.1 (explicit, idempotent, reviewable).

Forks that add private chat or 杜工部 integration are fine, but they **fork**, they don't merge back.

---

## 6. "Private space" is allowed; "data cage" is not

OpenCord is a public plaza by default, but **private communities** (`communities.visibility = 'private'`) and **private signals** (`signals.visibility = 'unlisted'` / `'private'`) are explicitly supported. Users may form small, closed groups inside OpenCord.

What is **not** allowed:

- **Data cage**: a private space that traps user data so the user can't export it. If a private community exists, the user can still export their own data through `/api/export/me`. There is **no** "admin of a private community blocks export for its members" path.
- **Hidden AI training**: any model call made on user content is logged in `ai_usage_log`. The user can see what was sent where.
- **Background surveillance**: no model call happens without a logged event. Admin-side "AI moderation" must surface what it does.

This is a hard boundary. Any PR that introduces data-cage patterns will be reverted.

---

## 7. Authentication and session security

- **JWT** is signed with `JWT_SECRET` from env. Rotation requires redeploy. Default expiry is 7 days (`JWT_EXPIRE_MINUTES`); do not extend without a security review.
- **API tokens** (`api_tokens` table) are stored **hashed** (SHA-256, not bcrypt — they're high-entropy random tokens, not passwords). The prefix is stored in clear for UI display. Tokens are revocable; revocation is **immediate** (no grace period).
- **Passwords** are bcrypt-hashed (passlib default cost). Do not change to MD5 / SHA-1 / plain.
- **CORS** is configured via `CORS_ORIGINS` env. Default is `localhost:3000`. Do not add `*` in production; do not add wildcard origins.
- **Rate limiting**: not in v0.1. Track via issue tracker.

If you find a JWT or token bypass, report it as Critical via § 1.

---

## 8. Database security

- The PostgreSQL connection uses `psycopg2-binary` (sync) for migrations and `asyncpg` for the app. Both support TLS — set `DATABASE_URL` with `?sslmode=require` in production.
- The `ai_providers` table and `api_tokens` table contain sensitive material. **Do not** expose them via read-only public API tokens.
- Migrations must be **idempotent** (`CREATE … IF NOT EXISTS`). A non-idempotent migration that re-runs can corrupt data. See `AGENTS.md` § 3.1.
- Do not introduce `RAISE` / dynamic SQL inside application code that builds identifiers from user input. Always use parameterized queries (SQLAlchemy ORM or bound parameters).

---

## 9. Dependency management

- Python deps are pinned in `apps/api/requirements.txt`. Do not bump major versions in a feature PR — file a separate dependency-update PR.
- Node deps are pinned in `apps/web/package.json` (current lockfile-free; a `package-lock.json` is welcome as a follow-up).
- CI does not currently run `pip-audit` or `npm audit`. Adding them is a welcome contribution.
- If a CVE is found in a dependency, file an issue tagged `security` and link the CVE.

---

## 10. Acknowledgements

Thanks to everyone who reports vulnerabilities responsibly. Public credit is given on request after a fix lands.

This policy is inspired by the practices of many open-source foundations (Apache, Mozilla, Rust, etc.) and is intended to be readable, not legalistic. If something is unclear, open a PR against this file.
