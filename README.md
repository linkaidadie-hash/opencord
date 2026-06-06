# OpenCord / 开弦

**An open, AI-native community system.**

A self-hostable social layer for communities that want to own their rules, data, and AI workflows.

OpenCord is not trying to become another walled garden.

---

## 核心理念

- 用户自己拥有身份
- 社区自己拥有规则
- 数据不被平台封锁
- AI 帮助理解、匹配、整理、连接
- 自部署、可二开、可迁移

---

## v0.1 范围（当前里程碑）

- [x] 项目骨架 + 文档
- [ ] 用户注册 / 登录（邮箱 + 密码）
- [ ] 个人主页
- [ ] API Token（用户级，Bot 接入预留）
- [ ] 频道（公开 / 私有）
- [ ] 帖子（含 Markdown）
- [ ] 评论（一级 + 二级）
- [ ] 标签
- [ ] 站内通知（轮询，不上 WebSocket）
- [ ] 基础后台：封号、删帖、AI Provider 配置
- [ ] AI Provider 抽象层（OpenAI-compatible + 至少一家国产）
- [ ] AI 总结帖子（基础能力 demo）
- [ ] PostgreSQL schema（所有核心表预留 `tenant_id`）
- [ ] JSON 数据导出
- [ ] Docker Compose 一键部署
- [ ] README / ROADMAP / LICENSE

## 不在 v0.1（已砍）

私信 / 群聊 / WebSocket / Webhook / Bot 框架 / AI 画像 / AI 匹配 / AI 反垃圾 / 插件热加载 / ActivityPub / AT Protocol → 全部进 v0.2 / v0.3。

## v0.1 原则

- **单租户运行，多租户预留**：每张核心表带 `tenant_id uuid nullable` 字段
- **不上 WebSocket**：通知走 `GET /api/notifications` 轮询
- **AI Provider 不写死**：抽象层接 OpenAI-compatible + 国产兜底
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

- Web 前端：<http://localhost:3000>
- API 文档：<http://localhost:8000/docs>
- PostgreSQL：localhost:5432

---

## 技术栈

| 层 | 选型 | 原因 |
|---|---|---|
| 前端 | Next.js 14 (App Router) + TypeScript + Tailwind | SSR、生态成熟、自部署简单 |
| 后端 | FastAPI (Python 3.12) | AI 生态最顺，类型友好，文档自动出 |
| 数据库 | PostgreSQL 16 + pgvector | 主存储 + 向量检索（同库） |
| 缓存 | Redis 7 | 会话 / 限流 / AI 结果缓存 |
| 实时通信 | **v0.1 不上** | SSE / WebSocket 留 v0.2 |
| 对象存储 | 本地存储（v0.1）→ S3 兼容（v0.2+） | 减少部署摩擦 |
| AI | OpenAI-compatible 抽象 | 不绑定单一平台 |
| 部署 | Docker Compose | 一键起，零配置 |

---

## 项目结构

```
opencord/
├── apps/
│   ├── web/          # Next.js 前端
│   └── api/          # FastAPI 后端
├── packages/
│   ├── core/         # 领域模型 + 业务规则（核心逻辑）
│   ├── ai/           # AI Provider 抽象层
│   ├── export/       # 数据导出工具
│   └── database/     # SQLAlchemy 模型 + Alembic 迁移
├── services/
│   ├── user_service.py
│   ├── post_service.py
│   ├── comment_service.py
│   ├── notification_service.py
│   └── ai_summary_service.py
├── db/
│   └── schema.sql    # 初始 schema（带 tenant_id 预留）
├── docs/
│   ├── ROADMAP.md
│   └── ARCHITECTURE.md
├── scripts/
│   └── seed.py       # 初始化种子数据
├── docker-compose.yml
├── .env.example
└── README.md
```

`core` 和 `service` 的边界：
- `core`：纯领域逻辑，无 I/O 依赖（纯函数 + dataclass）
- `service`：编排 core + 数据库 + AI，**是未来插件替换的边界**

---

## 商业层（不挣钱也可以做，但不堵死）

- 开源社区系统：**免费**
- 托管版：v0.4 再设计
- 企业私有部署：v0.4 起开放
- 插件市场：v0.3 之后再说
- AI 额度托管：v0.4
- 定制开发：现在就能接

v0.1 阶段不预设商业化。

---

## 协议

- 代码：[MIT](LICENSE)
- 文档：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- 数据：用户自有（导出 JSON 即可搬家）

---

## 路线图

详见 [ROADMAP.md](docs/ROADMAP.md)。

简版：

- **v0.1** — Skeleton（当前）
- **v0.2** — Messaging & Bots（私信 / 群聊 / WebSocket / Bot API）
- **v0.3** — Federation & Migration（ActivityPub 探索 / 迁移工具 / 插件系统 alpha）
- **v0.4** — Hosted / Multi-tenant（租户管理 / 托管版 / 插件市场）

---

## 贡献

v0.1 阶段不接受大改 PR（骨架还在动）。欢迎：

- 提 Issue 讨论设计
- 修 bug / 补测试
- 完善文档

---

## 维护者

- @linkaidadie-hash

"造船出海，不是池塘里捞虾。"
