# OpenCord API 参考

[English](./API.md) | [简体中文](./API.zh-CN.md)

> OpenCord v0.1 REST API 参考。
> Base URL：`http://localhost:8000`（开发）或你的部署地址。
> 交互式文档：`/docs`（Swagger UI）和 `/redoc`。

---

## 鉴权

两种方式：

1. **JWT** —— 人类会话。从 `/api/auth/login` 或 `/api/auth/register` 拿到。以 `Authorization: Bearer <jwt>` 发送
2. **API Token** —— 机器人/集成。格式 `oc_<random>`。从 `POST /api/users/me/tokens` 创建。以 `Authorization: Bearer <token>` 发送

鉴权依赖自动识别：以 `oc_` 开头是 API Token，否则按 JWT 处理。

---

## 端点

### 鉴权

#### `POST /api/auth/register`

创建新用户。`FEATURE_REGISTRATION=false` 时关闭。

**请求体：**
```json
{
  "email": "user@example.com",
  "username": "alice",
  "password": "supersecret123",
  "display_name": "Alice"
}
```

**响应 201：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": { "id": "uuid", "username": "alice" }
}
```

#### `POST /api/auth/login`

**请求体：**
```json
{
  "email_or_username": "alice",
  "password": "supersecret123"
}
```

**响应 200：** 同 register。

#### `GET /api/auth/me`

返回当前用户。

**Headers：** `Authorization: Bearer <token>`

**响应 200：**
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

### 用户

#### `GET /api/users/{username}`

公开用户主页。

**响应 404** 用户不存在。

#### `PATCH /api/users/me`

更新自己的资料。

**请求体：**
```json
{
  "display_name": "Alice W.",
  "bio": "Building OpenCord.",
  "avatar_url": "https://example.com/avatar.png"
}
```

所有字段可选。只更新提供的字段。

---

### API Token

#### `GET /api/users/me/tokens`

列出自己的 API Token（只元数据；明文 token 创建后不再显示）。

#### `POST /api/users/me/tokens`

创建新 API Token。

**请求体：**
```json
{
  "name": "My Bot",
  "scopes": ["post:read", "post:write"],
  "expires_in_days": 365
}
```

**响应 201：**
```json
{
  "id": "uuid",
  "name": "My Bot",
  "token": "oc_xxxxxxxxxxxxxxxxxxxxxxxx",
  "token_prefix": "oc_xxxxxx",
  "scopes": ["post:read", "post:write"],
  "expires_at": "2027-06-06T...",
  "created_at": "2026-06-06T..."
}
```

**立即保存 `token` 字段。之后无法再查。**

#### `DELETE /api/users/me/tokens/{token_id}`

吊销 Token。把 `revoked_at` 设为当前时间。幂等。

---

### 频道

#### `GET /api/channels?visibility=public&limit=50&offset=0`

列出频道。默认公开；传 `visibility=private` 看私有频道（需鉴权）。

#### `POST /api/channels`

创建频道。需鉴权。

**请求体：**
```json
{
  "slug": "ai-tools",
  "name": "AI Tools",
  "description": "分享讨论 AI 工具",
  "visibility": "public"
}
```

#### `GET /api/channels/{slug}`

按 slug 查单个频道。

---

### 帖子

#### `GET /api/posts?channel_id=...&tag=...&limit=20&offset=0`

列出帖子。按 `channel_id`（UUID）或 `tag`（slug）过滤。

#### `POST /api/posts`

发新帖。需鉴权。

**请求体：**
```json
{
  "channel_id": "uuid",
  "title": "我的第一帖",
  "body_md": "# 你好\n\n这是 **Markdown**。",
  "tag_slugs": ["intro", "show-and-tell"]
}
```

标签不存在会自动创建。

#### `GET /api/posts/{post_id}`

查单个帖子。`view_count` 自增。

#### `PATCH /api/posts/{post_id}`

更新自己的帖子（admin/moderator 可更新任何帖子）。

**请求体：** 同 create，所有字段可选。

#### `DELETE /api/posts/{post_id}`

软删。`status` 置 `"deleted"`，频道 `post_count` 减一。

---

### 评论

#### `GET /api/comments/by-post/{post_id}?limit=100&offset=0`

列出帖子所有评论，按 `created_at` 升序。一级嵌套用 `parent_id`。

#### `POST /api/comments`

发评论。需鉴权。

**请求体：**
```json
{
  "post_id": "uuid",
  "parent_id": "uuid",
  "body_md": "好帖！"
}
```

给别人帖子发评论会触发 `post.commented` 通知给帖子作者。

---

### AI

#### `GET /api/ai/providers`（admin）

列出所有 AI Provider 配置。仅管理员。

#### `POST /api/ai/providers`（admin）

添加 AI Provider。

**请求体：**
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

支持的 `provider_type`：`openai-compatible`、`MiniMax`、`deepseek`、`ollama`。

#### `POST /api/ai/providers/{provider_id}/set-default`（admin）

把某 Provider 设为默认。其他 Provider 的 `is_default` 自动设 false。

#### `POST /api/ai/summarize-post/{post_id}?force_refresh=false`（v0.1 仅 admin）

为帖子生成 AI 总结。v0.1 仅 admin 可调；v0.2 任何登录用户可调。

**响应 200：**
```json
{
  "post_id": "uuid",
  "ai_summary": "这篇帖子讨论了..."
}
```

**响应 503** 没有可用 AI Provider 或全部被限流。

总结缓存到帖子行（`ai_summary`、`ai_summary_at`、`ai_provider_used`）。传 `force_refresh=true` 强制重生成。

---

### 后台

#### `POST /api/admin/users/{user_id}/action`（admin）

对用户执行管理员操作。

**请求体：**
```json
{
  "action": "ban",
  "reason": "发垃圾"
}
```

`action` 可选：`ban` | `unban` | `suspend` | `promote` | `demote`

不能对自己 ban / suspend / demote。

#### `DELETE /api/admin/posts/{post_id}`（admin）

硬删（v0.1 实际是软删：`status = "deleted"`）。非管理员用普通 `DELETE /api/posts/{post_id}`。

---

### 数据导出

#### `GET /api/export/me`

下载自己完整数据为 JSON。

**Headers：** `Authorization: Bearer <token>`

**响应 200：** `application/json` 流，结构如下：
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

文件名格式：`opencord-export-{username}-{YYYYMMDD}.json`。

---

### 通知

#### `GET /api/notifications?unread_only=false&limit=50`

列出自己的通知，最新在前。

#### `POST /api/notifications/mark-read`

标记通知已读。

**请求体：**
```json
{
  "notification_ids": ["uuid", "uuid"]
}
```

`notification_ids = null` 表示全部未读都标记。

**响应 200：**
```json
{
  "marked_read": 2
}
```

---

## 错误格式

所有错误遵循 FastAPI 默认：

```json
{
  "detail": "Channel not found: <uuid>"
}
```

标准 HTTP 状态码：
- `400` 错误请求（校验、业务规则违反）
- `401` 未鉴权
- `403` 禁止（已鉴权但无权限）
- `404` 未找到
- `422` 校验错误（Pydantic）
- `503` 服务不可用（如没 AI Provider）

---

## 限流（v0.1）

只有 AI Provider 调用限流（每 Provider，可配 `rpm_limit`）。其他 API v0.1 不限流，假设部署网络边界可控。

v0.2 加：
- 鉴权端点按 IP 限流
- 发帖 / 发评论按用户限流
