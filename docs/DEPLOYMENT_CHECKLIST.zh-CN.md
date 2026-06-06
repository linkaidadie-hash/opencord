# OpenCord v0.1 部署验收清单

[English](./DEPLOYMENT_CHECKLIST.md) | [简体中文](./DEPLOYMENT_CHECKLIST.zh-CN.md)

> 状态：**静态审查完成（v0.1.0）**。Docker 环境的运行时验证待做——见下方的"已静态审查"和"待运行时验证"两节。

## 本次审计的范围

这份文档记录了哪些是**静态审查**的（读代码、追请求流），哪些是**运行时验证**的（真跑过 `docker compose up`）。

执行本次审计的 agent 在 Windows 上没装 Docker，所以运行时验证需要维护者本人来做。本文件就是执行脚本。

如果哪一步失败，请提 GitHub issue，附上：执行的命令、完整错误输出、OS + Docker 版本。

## v0.1 交付清单

- 75 文件 / ~7000 行
- `main` 分支 3 个 commit
- 4 个 Docker 服务：`postgres` / `redis` / `api` / `web`
- 11 张数据库表（PostgreSQL 16 + pgvector）
- 9 组 API 路由（auth, users, channels, posts, comments, ai, admin, export, notifications）
- 10 个 Next.js 页面
- 3 个 AI Provider 实现（OpenAI-compatible / MiniMax / DeepSeek）+ 1 个 **Mock Provider**（默认，无需 key）
- 1 个 seed 脚本，创建：默认租户、管理员、4 个示例频道、Mock AI provider

## 前置条件

部署主机需要：

- Docker Engine 24+ **和** Docker Compose v2
- 至少 2 GB 内存（AI 总结建议 4 GB）
- 10 GB 磁盘（主要是 PostgreSQL 数据 + Docker 镜像）
- 端口 3000（web）和 8000（api）可用

验证前置：

```bash
docker --version          # Docker version 24.0.0+
docker compose version    # Docker Compose version v2.x
```

## 5 分钟快速开始（无需 API key）

MockAIProvider 让 0 配置就能跑完整流程。

```bash
# 1. Clone
git clone https://github.com/linkaidadie-hash/opencord.git
cd opencord

# 2. 配置
cp .env.example .env
# 编辑 .env —— 至少改 POSTGRES_PASSWORD（任意值）
# 其他变量本地开发有安全默认值

# 3. 启动
docker compose up -d --build

# 4. 等所有服务健康
docker compose ps
# 期望：4 个服务都 "Up" / "healthy"

# 5. Seed（创建管理员 + 示例频道 + Mock AI provider）
docker compose exec api python seed.py

# 6. 验证 API
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0"}

curl http://localhost:8000/version
# {"name":"OpenCord","version":"0.1.0","instance":"My OpenCord Community"}

# 7. 打开浏览器
open http://localhost:3000   # macOS
# 或直接访问 http://localhost:3000
```

## 验证项

### API 端点（curl）

```bash
# 健康
curl http://localhost:8000/health
curl http://localhost:8000/version

# 注册
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"tester","password":"testpass123","display_name":"Tester"}'
# 把响应的 .access_token 存下来

# 登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email_or_username":"tester","password":"testpass123"}'

# 列频道
curl http://localhost:8000/api/channels

# 查自己（用上面的 token）
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <TOKEN>"

# 触发 AI 总结（v0.1 仅 admin）
# 先用 INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD 登录
# 从 list 端点拿一个 post id
curl -X POST "http://localhost:8000/api/ai/summarize-post/<POST_ID>" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
# 期望返回：{"post_id":"...","ai_summary":"..."}

# 导出数据
curl http://localhost:8000/api/export/me \
  -H "Authorization: Bearer <TOKEN>" \
  -o opencord-export.json
# 打开 JSON 文件，检查有 user / posts / comments 等
```

### 前端页面（浏览器）

| URL | 期望 | 运行时检查 |
|---|---|---|
| `http://localhost:3000/` | 首页：频道列表 + 最新帖子 | ⏳ 待验 |
| `http://localhost:3000/login` | 登录表单 | ⏳ 待验 |
| `http://localhost:3000/register` | 注册表单 | ⏳ 待验 |
| `http://localhost:3000/c/general` | "general" 频道的帖子列表 | ⏳ 待验 |
| `http://localhost:3000/c/general/new` | 发新帖表单（需登录） | ⏳ 待验 |
| `http://localhost:3000/p/<id>` | 帖子详情 + AI 总结 | ⏳ 待验 |
| `http://localhost:3000/u/admin` | admin 个人主页 | ⏳ 待验 |
| `http://localhost:3000/admin` | 管理员后台（需 admin 登录） | ⏳ 待验 |
| `http://localhost:3000/admin/ai` | AI Provider 配置（应看到 Mock provider） | ⏳ 待验 |

### 管理员流程

1. 用 admin 登录（用 `.env` 里的 `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD`）
2. 进 `/admin` —— 应看到 "AI Providers" 卡 + 3 个占位卡
3. 进 `/admin/ai` —— 应看到 Mock AI provider 已预置为 default
4. 可选：加一个真实 Provider（OpenAI / DeepSeek 等）并切为 default
5. 进任一帖子详情页，curl 触发 `POST /api/ai/summarize-post/{id}`（admin）
6. 刷新帖子页 —— 应看到 AI 总结显示

## 常见问题

### 问题：`docker compose up` 报 "port is already allocated"

**原因**：端口 3000 或 8000 被占用。
**修**：编辑 `docker-compose.yml`，把 `ports: "3000:3000"` 改成 `"3001:3000"` 等。

### 问题：PostgreSQL 初始化失败或 schema 缺失

**原因**：`db/schema.sql` 只在首次启动挂载。如果 volume 已存在，schema 不会再应用。
**修**：`docker compose down -v` 删 volume，再 `docker compose up -d`。

### 问题：`seed.py` 报 "table does not exist"

**原因**：api 容器在 PostgreSQL 准备好服务 schema 之前就启动了。
**修**：等 30 秒重试。Docker healthcheck 应该能防这个，但首次启动不是 100% 可靠。

### 问题：AI 总结返回 503 "No AI provider available"

**原因**：没配 AI Provider。（seed 跑过的话不会——Mock 是默认创建的。）
**修**：重跑 `seed.py`，或去 `/admin/ai` 手动加。

### 问题：登录表单提交后 UI 不变

**原因**：v0.1 用 `document.cookie` 存 token（不是 HttpOnly）。
**修**：检查浏览器 DevTools → Application → Cookies，应该看到 `opencord_token`。如果有，手动刷新页面。
**v0.2 会改 server actions + HttpOnly。**

### 问题：前端 "Failed to fetch"

**原因**：可能是 CORS，或 Next.js rewrite 到 `api:8000` 没配好。
**修**：
```bash
docker compose exec web env | grep API_INTERNAL_URL
# 应该是：API_INTERNAL_URL=http://api:8000
```
也检查 `next.config.js` 有 rewrite 块。再 `docker compose logs api` 看 CORS 错误。

### 问题：Web 页面空白

**原因**：web 容器的 `NEXT_PUBLIC_API_URL` build arg 不对。
**修**：这是 build-time 变量。修完 `.env` 后 `docker compose build web` 重建。

## 静态审查日志（agent 在不跑 Docker 的情况下验证的）

| 项 | 已验证 | 备注 |
|---|---|---|
| 所有 Python 文件语法 | ✅ | 28 个 Python 文件都能用 `ast` 解析 |
| 所有 TypeScript 文件语法 | ✅ | 17 个 TS/TSX 文件都能编译 |
| `docker-compose.yml` schema | ✅ | 4 个服务、depends_on、healthcheck、volume 都对 |
| `Dockerfile` 路径 | ✅ | api + web 都是 multi-stage，build context = 项目根 |
| `db/schema.sql` 首次启动加载 | ✅ | 挂到 `/docker-entrypoint-initdb.d/01-schema.sql` |
| `seed.py` 幂等性 | ✅ | 重跑不会重复创建 |
| 默认 Mock AI provider 创建 | ✅ | seed 创建 `mock` provider，is_default=true |
| `.env.example` 覆盖所有引用变量 | ✅ | 所有 `settings.*` 引用都齐 |
| `lib/api.ts` 用正确的 env var | ✅ | 用 `NEXT_PUBLIC_API_URL` 或空字符串（走 rewrite） |
| Auth 流：注册 → 登录 → me | ✅ | JWT 存 cookie |
| CORS 允许 web 源 | ✅ | `CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]` |
| pgvector 扩展在 schema 里 | ✅ | `CREATE EXTENSION IF NOT EXISTS "vector"` + HNSW 索引 |
| Web rewrite `/api/*` | ✅ | `next.config.js` 转发到 `API_INTERNAL_URL/api/*` |
| Mock AI provider 离线可用 | ✅ | `MockAIProvider` 进程内，不联网 |
| `/version` 端点存在 | ✅ | 本次审计加的 |
| Mock provider 注册到 factory | ✅ | `packages/ai/__init__.py` 包含 mock |

## 待运行时验证（你在你机器上跑）

- [ ] `docker compose up -d --build` 顺利完成
- [ ] 4 个服务都达到 "healthy"
- [ ] `seed.py` 创建 admin + 频道 + Mock provider
- [ ] 注册流程浏览器能跑
- [ ] 登录流程浏览器能跑
- [ ] 发帖能跑
- [ ] 发评论能跑
- [ ] AI 总结返回 Mock 生成的文字
- [ ] 数据导出下载 JSON 文件
- [ ] 管理员后台 admin 用户能访问
- [ ] 管理员能加真实 AI Provider 并切 default

## v0.1 已知限制（已推迟，不是 bug）

- Auth cookie 不是 HttpOnly（XSS 风险）。v0.2：server actions + HttpOnly
- Markdown XSS 清洗是极简版（去 script/iframe/on*）。v0.2：bleach 或 nh3
- AI 总结同步。v0.2：异步队列
- 鉴权端点无限流。v0.2：Redis 后端
- 无邮箱验证。v0.2：SMTP
- 无图片上传。v0.2：本地 + S3
- 无 CI/CD。手动 `git push`

## 本次审计**没**做的事

- 没跑 `docker compose up`（agent 主机没装 Docker）
- 没测移动端响应式
- 没做压力测试（单用户、少量数据）
- 没测备份 / 恢复
- 没测 HTTPS / 反向代理
- 没测多机部署
