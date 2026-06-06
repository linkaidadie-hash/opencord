# OpenCord API Reference

[English](./API.md) | [简体中文](./API.zh-CN.md)

> REST API reference for OpenCord v0.1.
> Base URL: `http://localhost:8000` (development) or your deployment URL.
> Interactive docs: `/docs` (Swagger UI) and `/redoc`.

---

## Authentication

Two mechanisms:

1. **JWT** — for human sessions. Obtained from `/api/auth/login` or `/api/auth/register`. Send as `Authorization: Bearer <jwt>`.
2. **API Token** — for bots / integrations. Format `oc_<random>`. Obtained from `POST /api/users/me/tokens`. Send as `Authorization: Bearer <token>`.

The auth dependency auto-detects: tokens starting with `oc_` are API tokens, everything else is treated as JWT.

---

## Endpoints

### Auth

#### `POST /api/auth/register`

Create a new user account. Disabled if `FEATURE_REGISTRATION=false`.

**Request body:**
```json
{
  "email": "user@example.com",
  "username": "alice",
  "password": "supersecret123",
  "display_name": "Alice"  // optional
}
```

**Response 201:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": { "id": "uuid", "username": "alice", ... }
}
```

#### `POST /api/auth/login`

**Request body:**
```json
{
  "email_or_username": "alice",
  "password": "supersecret123"
}
```

**Response 200:** Same as register.

#### `GET /api/auth/me`

Returns the current user.

**Headers:** `Authorization: Bearer <token>`

**Response 200:**
```json
{
  "id": "uuid",
  "username": "alice",
  "display_name": "Alice",
  "bio": null,
  "avatar_url": null,
  "role": "member",
  "created_at": "2026-06-06T..."
}
```

---

### Users

#### `GET /api/users/{username}`

Public user profile.

**Response 404** if user not found.

#### `PATCH /api/users/me`

Update your own profile.

**Request body:**
```json
{
  "display_name": "Alice W.",
  "bio": "Building OpenCord.",
  "avatar_url": "https://example.com/avatar.png"
}
```

All fields optional. Only provided fields are updated.

---

### API Tokens

#### `GET /api/users/me/tokens`

List your API tokens (metadata only; raw token never shown after creation).

#### `POST /api/users/me/tokens`

Create a new API token.

**Request body:**
```json
{
  "name": "My Bot",
  "scopes": ["post:read", "post:write"],
  "expires_in_days": 365
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "name": "My Bot",
  "token": "oc_xxxxxxxxxxxxxxxxxxxxxxxx",  // raw, shown only once
  "token_prefix": "oc_xxxxxx",
  "scopes": ["post:read", "post:write"],
  "expires_at": "2027-06-06T...",
  "created_at": "2026-06-06T..."
}
```

**Store the `token` field immediately. It cannot be retrieved later.**

#### `DELETE /api/users/me/tokens/{token_id}`

Revoke a token. Sets `revoked_at` to current time. Idempotent.

---

### Channels

#### `GET /api/channels?visibility=public&limit=50&offset=0`

List channels. Public by default; pass `visibility=private` to see private channels (requires auth).

#### `POST /api/channels`

Create a channel. Requires auth.

**Request body:**
```json
{
  "slug": "ai-tools",
  "name": "AI Tools",
  "description": "Share and discuss AI tools",
  "visibility": "public"
}
```

#### `GET /api/channels/{slug}`

Get one channel by slug.

---

### Posts

#### `GET /api/posts?channel_id=...&tag=...&limit=20&offset=0`

List posts. Filter by `channel_id` (UUID) or `tag` (slug).

#### `POST /api/posts`

Create a post. Requires auth.

**Request body:**
```json
{
  "channel_id": "uuid",
  "title": "My first post",
  "body_md": "# Hello\n\nThis is **markdown**.",
  "tag_slugs": ["intro", "show-and-tell"]
}
```

Tags are auto-created if they don't exist.

#### `GET /api/posts/{post_id}`

Get a post. Increments `view_count`.

#### `PATCH /api/posts/{post_id}`

Update your own post (or any post if admin/moderator).

**Request body:** Same as create, all fields optional.

#### `DELETE /api/posts/{post_id}`

Soft delete. Sets `status = "deleted"`. Decrements channel's `post_count`.

---

### Comments

#### `GET /api/comments/by-post/{post_id}?limit=100&offset=0`

List all comments for a post, ordered by `created_at` ascending. One-level nesting via `parent_id`.

#### `POST /api/comments`

Create a comment. Requires auth.

**Request body:**
```json
{
  "post_id": "uuid",
  "parent_id": "uuid",  // optional, for replies
  "body_md": "Great post!"
}
```

Creating a comment on someone else's post triggers a `post.commented` notification for the post author.

---

### AI

#### `GET /api/ai/providers` (admin)

List all configured AI providers. Admin only.

#### `POST /api/ai/providers` (admin)

Add a new AI provider.

**Request body:**
```json
{
  "name": "OpenAI",
  "provider_type": "openai-compatible",
  "api_key": "sk-...",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "is_default": true,
  "rpm_limit": 60
}
```

Supported `provider_type` values: `openai-compatible`, `MiniMax`, `deepseek`, `ollama`.

#### `POST /api/ai/providers/{provider_id}/set-default` (admin)

Mark a provider as the default. All other providers' `is_default` is set to false.

#### `POST /api/ai/summarize-post/{post_id}?force_refresh=false` (admin in v0.1)

Generate an AI summary for a post. v0.1 requires admin; v0.2 allows any logged-in user.

**Response 200:**
```json
{
  "post_id": "uuid",
  "ai_summary": "The post discusses..."
}
```

**Response 503** if no AI provider is available or all are rate-limited.

The summary is cached on the post row (`ai_summary`, `ai_summary_at`, `ai_provider_used`). Pass `force_refresh=true` to regenerate.

---

### Admin

#### `POST /api/admin/users/{user_id}/action` (admin)

Perform an admin action on a user.

**Request body:**
```json
{
  "action": "ban",  // ban | unban | suspend | promote | demote
  "reason": "Spamming"  // optional
}
```

You cannot ban / suspend / demote yourself.

#### `DELETE /api/admin/posts/{post_id}` (admin)

Hard delete (soft delete in v0.1: sets `status = "deleted"`). Use the regular `DELETE /api/posts/{post_id}` for non-admins.

---

### Export

#### `GET /api/export/me`

Download your full data as JSON.

**Headers:** `Authorization: Bearer <token>`

**Response 200:** `application/json` stream with this shape:
```json
{
  "export_version": "1.0",
  "exported_at": "2026-06-06T...",
  "user": { ... },
  "posts": [ ... ],
  "comments": [ ... ],
  "api_tokens": [ ... ],
  "notifications": [ ... ]
}
```

Filename pattern: `opencord-export-{username}-{YYYYMMDD}.json`.

---

### Notifications

#### `GET /api/notifications?unread_only=false&limit=50`

List your notifications, newest first.

#### `POST /api/notifications/mark-read`

Mark notifications as read.

**Request body:**
```json
{
  "notification_ids": ["uuid", "uuid"]  // null = all unread
}
```

**Response 200:**
```json
{
  "marked_read": 2
}
```

---

## Error Format

All errors follow FastAPI's default:

```json
{
  "detail": "Channel not found: <uuid>"
}
```

Standard HTTP status codes are used:
- `400` Bad request (validation, business rule violation)
- `401` Unauthenticated
- `403` Forbidden (authenticated but lacks permission)
- `404` Not found
- `422` Validation error (Pydantic)
- `503` Service unavailable (e.g. no AI provider)

---

## Rate Limits (v0.1)

Only AI provider calls are rate-limited (per-provider, configurable `rpm_limit` in admin). Everything else is unrestricted at the API level in v0.1 — deployment network boundary is assumed.

v0.2 adds:
- Per-IP rate limit on auth endpoints
- Per-user rate limit on post / comment creation
