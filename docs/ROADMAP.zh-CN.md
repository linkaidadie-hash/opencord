# OpenCord 路线图

[English](./ROADMAP.md) | [简体中文](./ROADMAP.zh-CN.md)

> 这是方向文档，不是时间表。每个版本的范围是设计目标，不是承诺。实际顺序可能根据社区反馈调整。

---

## v0.1 — Skeleton（当前）

**目标**：让 `git clone + docker compose up` 跑出一个能注册、能发帖、能跑 AI 总结、能导出 JSON 的社区。

**包含：**

- [x] 项目骨架（monorepo：apps + packages + services + db）
- [x] README / ROADMAP / VISION / ARCHITECTURE / API 文档（中英双语）
- [x] PostgreSQL schema（11 张表 + tenant_id 预留 + pgvector）
- [x] FastAPI 后端
  - [x] 用户：注册、登录、JWT、API Token
  - [x] 个人主页：查看、编辑
  - [x] 频道：创建、列表、详情
  - [x] 帖子：创建、列表、详情、Markdown 渲染
  - [x] 评论：创建、列表、嵌套
  - [x] 标签：绑定、查询
  - [x] 通知：拉取、标记已读
  - [x] 后台：封号 / 解封 / 暂停 / 升降级 / 删帖 / AI Provider 配置
- [x] AI Provider 抽象层
  - [x] `AIProvider` 接口：`chat` / `summarize` / `embed`
  - [x] `OpenAICompatibleProvider`（覆盖 OpenAI / DeepSeek / Ollama / 硅基流动 / OpenRouter）
  - [x] `MiniMaxProvider`（OpenAI 兼容）
  - [x] `DeepSeekProvider`（OpenAI 兼容，v0.2 加 thinking mode）
  - [x] Provider 配置存 DB，后台可切换
- [x] AI 总结帖子
  - [x] 总结结果缓存到 post 行
  - [x] v0.1 同步调用（v0.2 异步队列）
  - [x] 用量日志 + 每 Provider 限流
- [x] Next.js 前端
  - [x] 注册 / 登录页
  - [x] 首页：频道列表 + 最新帖子
  - [x] 频道页：帖子列表
  - [x] 帖子详情（含 AI 总结展示）
  - [x] 个人主页
  - [x] 后台：AI Provider 配置
- [x] 数据导出
  - [x] `/api/export/me` — 当前用户完整数据 JSON
- [x] Docker Compose
  - [x] postgres + redis + api + web
  - [x] 一键 `docker compose up -d`

**不在 v0.1：**

- 私信 / 群聊
- WebSocket / 实时通信
- Webhook / Bot 框架
- AI 画像 / AI 匹配 / AI 反垃圾
- 插件热加载
- 联邦协议（ActivityPub / AT Protocol）
- 多租户管理界面

---

## v0.2 — Messaging & Bots

**目标**：让社区"能私聊 + 机器人能接入"。

- [ ] 私信（点对点，含加密选项）
- [ ] 群聊（多对多，频道化）
- [ ] WebSocket / SSE 实时通信
- [ ] 消息已读、未读、撤回
- [ ] Bot API（基于 API Token）
- [ ] Webhook 事件（post.created / comment.added / user.joined ...）
- [ ] AI 画像（基于用户发帖 + 行为）
- [ ] AI 匹配（基于画像 + 向量检索）
- [ ] AI 反垃圾（基于分类 + 行为）

---

## v0.3 — Federation & Migration

**目标**：让社区"能搬家、能联邦"。

- [ ] ActivityPub 探索（最小可读 / 可写）
- [ ] 数据导入工具（兼容 v0.1 / v0.2 导出格式）
- [ ] 数据迁移工具（从 Discourse / Mastodon 导入）
- [ ] 插件系统 alpha
  - [ ] Service hot-reload
  - [ ] 插件 manifest 规范
  - [ ] 至少 2 个示例插件
- [ ] 主题 / 皮肤系统
- [ ] 社区规则引擎（可配置）

---

## v0.4 — Hosted / Multi-tenant

**目标**：让"不会部署的人也能用"。

- [ ] 多租户管理界面
- [ ] 租户隔离（DB schema 升级）
- [ ] 托管版注册流程
- [ ] 计费模块（可选接入）
- [ ] 插件市场 alpha
- [ ] 行业模板（外贸圈 / 开发者圈 / 工厂内部 / 兴趣社群）
- [ ] 企业 SSO（OIDC / SAML）

---

## v0.5+ — 待规划

- 移动端 PWA
- 端到端加密私信
- 联邦宇宙全面兼容
- 联邦 AI（多个社区的 AI 协作）
- 去中心化身份（DID）

---

## 设计原则（所有版本通用）

1. **不写死平台**：任何"必须用 X"的限制都是反模式
2. **数据可搬家**：用户随时能导出完整数据走人
3. **AI 可换**：任何 LLM 都能通过 Provider 抽象层接入
4. **代码可分叉**：核心代码 MIT 协议，文档 CC BY 4.0
5. **后向兼容**：schema 升级不破坏旧数据（保留 1 个版本的字段）

---

## 现状

- v0.1 状态：🚧 进行中（代码完成，部署验证中）
- 预计完成：2026 Q2
- 维护者：单人 + AI 协作

进度慢没关系，方向不能偏。
