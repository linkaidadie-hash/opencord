# OpenCord / 开弦

[English](./README.md) | 简体中文

OpenCord 是一个开源的 AI 原生社区系统。

它不是微信群替代品，也不是另一个封闭平台。它是一套可以自部署、可二开、可迁移的社交底座。个人、团队、社群和组织可以用它搭建自己的社区，拥有自己的规则、数据和 AI 工作流。

## 为什么做 OpenCord

今天很多社区被困在封闭平台里：

- 关系链不属于自己
- 数据不能自由导出
- API 能力被限制
- 自动化和 AI 接入处处受限
- 平台规则随时变化

OpenCord 想提供另一条路：让社区自己拥有地基。

## 核心理念

- **用户拥有自己的数据** —— JSON 一键导出，无锁定
- **社区拥有自己的规则** —— 审核、频道、可见性，全部自己说了算
- **可自部署** —— `git clone` 然后 `docker compose up` 就跑起来
- **数据可搬家** —— 导入导出工具，未来支持 ActivityPub
- **AI 不绑定单一模型** —— OpenAI / DeepSeek / MiniMax / Ollama / 任何 OpenAI 兼容接口都能接
- **默认开放** —— REST API / 未来 WebSocket / 未来 Webhook / 未来插件系统

---

## v0.1 范围

这是骨架版本。我们主动砍掉功能，只为交付一个能跑的地基。

**包含：**
- 用户注册 / 登录（邮箱 + 密码）
- 个人主页
- API Token（给 Bot 和第三方集成用）
- 频道（公开 / 私有）
- 帖子（Markdown）
- 评论（一级 + 二级嵌套）
- 标签
- 站内通知（轮询，不上 WebSocket）
- 基础后台：封号 / 解封 / 暂停 / 升降级 / 删帖
- AI Provider 抽象层（OpenAI 兼容 + 国产模型）
- AI 总结帖子
- PostgreSQL schema（带 tenant_id 预留）
- JSON 数据导出
- Docker Compose 一键部署
- README / ROADMAP / VISION / ARCHITECTURE / API 文档（中英双语）

**不在 v0.1（推迟到 v0.2+）：**
- 私信 / 群聊
- WebSocket / 实时通信
- Webhook / Bot API
- AI 画像 / AI 匹配 / AI 反垃圾
- 插件热加载
- ActivityPub / 联邦协议

## v0.1 原则

- **单租户运行，多租户预留**：每张核心表带 `tenant_id uuid nullable` 字段
- **不上 WebSocket**：通知走 `GET /api/notifications` 轮询
- **AI Provider 不写死**：任何 LLM 都通过 `AIProvider` 抽象层接入
- **代码按插件思路分层**：domain / service / api 三层解耦，service 是未来插件替换的边界

---

## 快速开始

```bash
git clone https://github.com/linkaidadie-hash/opencord.git
cd opencord
cp .env.example .env
# 编辑 .env，至少填上 POSTGRES_PASSWORD 和至少一个 AI Provider 的 Key
docker compose up -d
```

启动后：

- Web 前端：http://localhost:3000
- API 文档：http://localhost:8000/docs
- PostgreSQL：localhost:5432

首次启动后跑 seed 脚本创建默认租户、管理员账号和示例频道：

```bash
docker compose exec api python seed.py
```

默认管理员（在 `.env` 里改）：

- 邮箱：`INITIAL_ADMIN_EMAIL`（默认 `admin@opencord.local`）
- 密码：`INITIAL_ADMIN_PASSWORD`（默认 `change-me`）

然后访问 `/admin/ai` 加一个 AI Provider，回到任意帖子详情页，通过 `POST /api/ai/summarize-post/{post_id}` 触发 AI 总结。

---

## 技术栈

| 层 | 选型 | 原因 |
|---|---|---|
| 前端 | Next.js 14 (App Router) + TypeScript + Tailwind | SSR、生态成熟、自部署简单 |
| 后端 | FastAPI (Python 3.12) | AI 生态最顺，类型友好，文档自动出 |
| 数据库 | PostgreSQL 16 + pgvector | 主存储 + 向量检索（同库） |
| 缓存 | Redis 7 | 会话 / 限流 / AI 结果缓存 |
| 实时通信 | **v0.1 不上** | SSE / WebSocket 留 v0.2 |
| 对象存储 | 本地（v0.1）→ S3（v0.2+） | 减少部署摩擦 |
| AI | OpenAI-compatible 抽象 | 不绑定单一平台 |
| 部署 | Docker Compose | 一键起，零配置 |

---

## 项目结构

```
opencord/
├── apps/
│   ├── web/                  # Next.js 前端
│   └── api/                  # FastAPI 后端
├── packages/
│   ├── ai/                   # AI Provider 抽象层（独立 Python 包）
│   ├── core/                 # （v0.2 预留）领域模型
│   ├── export/               # （v0.2 预留）数据导出工具
│   └── database/             # （v0.2 预留）SQLAlchemy 模型 / Alembic
├── services/                 # （顶层）跨应用的服务契约（未来）
├── db/
│   └── schema.sql            # 初始 schema（带 tenant_id 预留 + pgvector）
├── docs/
│   ├── ROADMAP.md / ROADMAP.zh-CN.md
│   ├── ARCHITECTURE.md / ARCHITECTURE.zh-CN.md
│   ├── API.md / API.zh-CN.md
│   └── VISION.md / VISION.zh-CN.md
├── scripts/
│   └── seed.py
├── docker-compose.yml
├── .env.example
└── README.md / README.zh-CN.md
```

`apps/api` 内部和顶层 `services` 的边界是有意设计：

- 领域逻辑靠近类型定义，无 I/O 依赖
- service 编排领域 + 数据库 + AI，是未来插件替换的边界

---

## 商业层（v0.1 不预设）

开源不等于"不挣钱"：

- 开源社区系统：**免费**
- 托管版：v0.4
- 企业私有部署：v0.4+
- 插件市场：v0.3+
- AI 额度托管：v0.4
- 定制开发：现在就能接

v0.1 阶段不商业化。第一目标是交付一个能跑、能传播的骨架。

---

## 文档

- [ROADMAP.md](docs/ROADMAP.md) / [ROADMAP.zh-CN.md](docs/ROADMAP.zh-CN.md) — 版本规划
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) / [ARCHITECTURE.zh-CN.md](docs/ARCHITECTURE.zh-CN.md) — 技术架构
- [API.md](docs/API.md) / [API.zh-CN.md](docs/API.zh-CN.md) — REST API 参考
- [VISION.md](docs/VISION.md) / [VISION.zh-CN.md](docs/VISION.zh-CN.md) — 为什么做 OpenCord

---

## 协议

- 代码：[MIT](LICENSE)
- 文档：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- 数据：用户自有（导出 JSON 即可搬家）

---

## 维护者

- @linkaidadie-hash

> 造船出海，不是池塘里捞虾。
