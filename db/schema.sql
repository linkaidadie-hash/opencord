-- =====================================================
-- OpenCord / 开弦 — PostgreSQL Schema v0.1
-- 原则：
--   1. 所有核心表带 tenant_id（v0.1 单租户，字段 nullable 预留）
--   2. 使用 uuid 作为主键（避免自增 ID 在多租户场景下的冲突）
--   3. 时间统一 timestamptz
--   4. 向量字段用 pgvector
-- =====================================================

-- 需要扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =====================================================
-- Tenants (v0.1 单租户，v0.4 多租户)
-- =====================================================
CREATE TABLE IF NOT EXISTS tenants (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug        VARCHAR(64) UNIQUE NOT NULL,
    name        VARCHAR(128) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE
);

-- 默认租户（v0.1 用）
INSERT INTO tenants (id, slug, name)
VALUES ('00000000-0000-0000-0000-000000000001', 'default', 'Default Community')
ON CONFLICT (id) DO NOTHING;


-- =====================================================
-- Users
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(64) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    display_name    VARCHAR(128),
    bio             TEXT,
    avatar_url      VARCHAR(512),
    role            VARCHAR(32) NOT NULL DEFAULT 'member',  -- member | moderator | admin
    status          VARCHAR(32) NOT NULL DEFAULT 'active',  -- active | suspended | banned
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ
);

CREATE INDEX idx_users_tenant ON users(tenant_id);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);


-- =====================================================
-- API Tokens (v0.1 用户级；v0.2 加 Bot 级别)
-- =====================================================
CREATE TABLE IF NOT EXISTS api_tokens (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(128) NOT NULL,
    token_hash      VARCHAR(255) NOT NULL UNIQUE,  -- 存 hash，不存明文
    token_prefix    VARCHAR(16) NOT NULL,  -- 明文前 8 位用于识别
    scopes          TEXT[] NOT NULL DEFAULT '{}',  -- post:read post:write comment:write ...
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ
);

CREATE INDEX idx_api_tokens_user ON api_tokens(user_id);
CREATE INDEX idx_api_tokens_hash ON api_tokens(token_hash);


-- =====================================================
-- Channels
-- =====================================================
CREATE TABLE IF NOT EXISTS channels (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    slug            VARCHAR(64) NOT NULL,
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    visibility      VARCHAR(32) NOT NULL DEFAULT 'public',  -- public | private
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    post_count      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, slug)
);

CREATE INDEX idx_channels_tenant ON channels(tenant_id);


-- =====================================================
-- Posts
-- =====================================================
CREATE TABLE IF NOT EXISTS posts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    channel_id      UUID NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    author_id       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title           VARCHAR(255) NOT NULL,
    body_md         TEXT NOT NULL,
    body_html       TEXT NOT NULL,  -- 渲染后的 HTML，节省前端开销
    status          VARCHAR(32) NOT NULL DEFAULT 'published',  -- draft | published | hidden | deleted
    pinned          BOOLEAN NOT NULL DEFAULT FALSE,
    view_count      INTEGER NOT NULL DEFAULT 0,
    comment_count   INTEGER NOT NULL DEFAULT 0,
    -- AI 总结缓存
    ai_summary      TEXT,
    ai_summary_at   TIMESTAMPTZ,
    ai_provider_used VARCHAR(64),
    -- 向量（v0.2+ 用于匹配 / 搜索，v0.1 先存）
    embedding       VECTOR(1536),  -- 跟 OpenAI text-embedding-3-small 对齐
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_posts_tenant ON posts(tenant_id);
CREATE INDEX idx_posts_channel ON posts(channel_id, created_at DESC);
CREATE INDEX idx_posts_author ON posts(author_id, created_at DESC);
CREATE INDEX idx_posts_status ON posts(status, created_at DESC);
-- 向量索引（先用 HNSW，后期数据量大了再调）
CREATE INDEX IF NOT EXISTS idx_posts_embedding ON posts USING hnsw (embedding vector_cosine_ops);


-- =====================================================
-- Comments
-- =====================================================
CREATE TABLE IF NOT EXISTS comments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    post_id         UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id       UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    parent_id       UUID REFERENCES comments(id) ON DELETE CASCADE,  -- 二级嵌套
    body_md         TEXT NOT NULL,
    body_html       TEXT NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'published',  -- published | hidden | deleted
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_comments_post ON comments(post_id, created_at);
CREATE INDEX idx_comments_author ON comments(author_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);


-- =====================================================
-- Tags
-- =====================================================
CREATE TABLE IF NOT EXISTS tags (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name            VARCHAR(64) NOT NULL,
    slug            VARCHAR(64) NOT NULL,
    description     TEXT,
    post_count      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, slug)
);

CREATE INDEX idx_tags_tenant ON tags(tenant_id);


-- =====================================================
-- Post-Tag relation
-- =====================================================
CREATE TABLE IF NOT EXISTS post_tags (
    post_id         UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    tag_id          UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (post_id, tag_id)
);

CREATE INDEX idx_post_tags_tag ON post_tags(tag_id);


-- =====================================================
-- Notifications
-- =====================================================
CREATE TABLE IF NOT EXISTS notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(64) NOT NULL,  -- comment.created | post.replied | mention ...
    actor_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    target_type     VARCHAR(32) NOT NULL,  -- post | comment | channel
    target_id       UUID NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}',
    read_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id) WHERE read_at IS NULL;


-- =====================================================
-- AI Providers (运行时配置，存 DB 而非 env)
-- 后台可切换；v0.1 至少 1 个 active
-- =====================================================
CREATE TABLE IF NOT EXISTS ai_providers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name            VARCHAR(64) NOT NULL,           -- 显示名
    provider_type   VARCHAR(64) NOT NULL,           -- openai-compatible | MiniMax | deepseek | ollama
    api_key         VARCHAR(512) NOT NULL,          -- 加密存储（v0.2+ 加密，v0.1 暂明文）
    base_url        VARCHAR(512) NOT NULL,
    model           VARCHAR(128) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT FALSE,
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    -- 能力开关
    supports_chat        BOOLEAN NOT NULL DEFAULT TRUE,
    supports_summarize   BOOLEAN NOT NULL DEFAULT TRUE,
    supports_embed       BOOLEAN NOT NULL DEFAULT TRUE,
    -- 限流
    rpm_limit       INTEGER,  -- 每分钟请求数
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_ai_providers_default ON ai_providers(tenant_id) WHERE is_default = TRUE;


-- =====================================================
-- AI Usage Log (用于限流 / 统计)
-- =====================================================
CREATE TABLE IF NOT EXISTS ai_usage_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    provider_id     UUID NOT NULL REFERENCES ai_providers(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    task_type       VARCHAR(32) NOT NULL,  -- chat | summarize | embed
    tokens_in       INTEGER,
    tokens_out      INTEGER,
    cost_estimate   NUMERIC(10, 6),  -- 美元
    latency_ms      INTEGER,
    error_code      VARCHAR(64),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_usage_log_provider ON ai_usage_log(provider_id, created_at DESC);


-- =====================================================
-- Audit Log (管理员操作记录)
-- =====================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    actor_id        UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(64) NOT NULL,  -- user.ban | post.delete | ai_provider.switch ...
    target_type     VARCHAR(32),
    target_id       UUID,
    details         JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_tenant ON audit_log(tenant_id, created_at DESC);


-- =====================================================
-- 触发器：自动更新 updated_at
-- =====================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT unnest(ARRAY['users', 'channels', 'posts', 'comments', 'ai_providers'])
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS set_updated_at ON %I; '
            'CREATE TRIGGER set_updated_at BEFORE UPDATE ON %I '
            'FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();',
            t, t
        );
    END LOOP;
END $$;
