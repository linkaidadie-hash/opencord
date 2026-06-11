-- =====================================================
-- OpenCord / 开弦 — Migration 0001: Open Topic Network
-- 阶段：C (Open Topic Network 后端骨架 + 最小可见入口)
--
-- 原则（阶段 C 的硬约束）：
--   1. 新增 6 张表：communities / topics / threads / topic_summaries / relations / follows
--   2. 6 张新表全部带 tenant_id，NOT NULL，FK -> tenants(id) ON DELETE CASCADE
--   3. 不改任何旧表；不重命名旧表；不迁移旧数据
--   4. 不引入 PG ENUM，subject_type / object_type / relation_type 用 VARCHAR
--   5. 字段值由应用层 (apps/api/core/open_topic.py) 常量校验
--   6. topic_summaries.generated_by 是 string，默认 'system'；本阶段不引入 agents / agent_runs / agent_actions
--   7. follows.target_type 支持 community / topic / project / user；project 仅预留，不做 FK
--   8. 触发器复用 schema.sql 已有函数 trigger_set_updated_at()
-- =====================================================

-- 旧库可能缺此函数（如果旧 schema.sql 没被完整初始化），幂等创建
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =====================================================
-- 1) communities — 开放社群（Open Topic Network 顶层容器）
-- =====================================================
CREATE TABLE IF NOT EXISTS communities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    slug            VARCHAR(64) NOT NULL,
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    visibility      VARCHAR(32) NOT NULL DEFAULT 'public',  -- public | private
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    topic_count     INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(tenant_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_communities_tenant ON communities(tenant_id);

DROP TRIGGER IF EXISTS set_updated_at ON communities;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON communities
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- =====================================================
-- 2) topics — 开放议题（Open Topic Network 的核心实体）
-- =====================================================
CREATE TABLE IF NOT EXISTS topics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    community_id    UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    slug            VARCHAR(128) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    body_md         TEXT NOT NULL DEFAULT '',
    status          VARCHAR(32) NOT NULL DEFAULT 'open',  -- open | resolved | archived
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    thread_count    INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(community_id, slug)
);

CREATE INDEX IF NOT EXISTS idx_topics_tenant ON topics(tenant_id);
CREATE INDEX IF NOT EXISTS idx_topics_community ON topics(community_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status, updated_at DESC);

DROP TRIGGER IF EXISTS set_updated_at ON topics;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON topics
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- =====================================================
-- 3) threads — 议题下的具体讨论流
--    注：本阶段不接 posts / comments；thread 自身就是讨论流条目
-- =====================================================
CREATE TABLE IF NOT EXISTS threads (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    topic_id        UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    parent_id       UUID REFERENCES threads(id) ON DELETE CASCADE,  -- 二级嵌套保留
    created_by      UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    body_md         TEXT NOT NULL,
    body_html       TEXT NOT NULL DEFAULT '',
    status          VARCHAR(32) NOT NULL DEFAULT 'published',  -- published | hidden | deleted
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_threads_tenant ON threads(tenant_id);
CREATE INDEX IF NOT EXISTS idx_threads_topic ON threads(topic_id, created_at);
CREATE INDEX IF NOT EXISTS idx_threads_parent ON threads(parent_id);
CREATE INDEX IF NOT EXISTS idx_threads_author ON threads(created_by, created_at DESC);

DROP TRIGGER IF EXISTS set_updated_at ON threads;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON threads
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- =====================================================
-- 4) topic_summaries — 议题 AI 总结缓存
--    generated_by 留 string，本阶段默认 'system'；agent 后置
-- =====================================================
CREATE TABLE IF NOT EXISTS topic_summaries (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    topic_id        UUID NOT NULL UNIQUE REFERENCES topics(id) ON DELETE CASCADE,
    summary_md      TEXT NOT NULL,
    summary_html    TEXT NOT NULL DEFAULT '',
    generated_by    VARCHAR(64) NOT NULL DEFAULT 'system',
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_topic_summaries_tenant ON topic_summaries(tenant_id);

DROP TRIGGER IF EXISTS set_updated_at ON topic_summaries;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON topic_summaries
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- =====================================================
-- 5) relations — 通用图边（议题网络的核心）
--    subject_type / object_type / relation_type 用 VARCHAR，不建 ENUM
--    合法取值见 apps/api/core/open_topic.py：
--      subject_type/object_type: identity | user | community | topic | thread | post | project | task | agent | artifact
--      relation_type:            follows | participates_in | relates_to | hosts | generates | proposes
--                                | produces | executes | responds_to | mentions
-- =====================================================
CREATE TABLE IF NOT EXISTS relations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    subject_type    VARCHAR(32) NOT NULL,
    subject_id      UUID NOT NULL,
    relation_type   VARCHAR(32) NOT NULL,
    object_type     VARCHAR(32) NOT NULL,
    object_id       UUID NOT NULL,
    weight          NUMERIC(6, 3) NOT NULL DEFAULT 1.0,  -- 边权重，0.000-999.999
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 同一对 (sub, rel, obj) 不能重复
CREATE UNIQUE INDEX IF NOT EXISTS uq_relations_edge
    ON relations(tenant_id, subject_type, subject_id, relation_type, object_type, object_id);

-- 出边：sub -> ?
CREATE INDEX IF NOT EXISTS idx_relations_subject
    ON relations(tenant_id, subject_type, subject_id, relation_type);

-- 入边：? -> obj
CREATE INDEX IF NOT EXISTS idx_relations_object
    ON relations(tenant_id, object_type, object_id, relation_type);


-- =====================================================
-- 6) follows — 关注关系
--    target_type: community | topic | project | user
--    project 仅预留，无 FK；其余指向对应表
-- =====================================================
CREATE TABLE IF NOT EXISTS follows (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    follower_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type     VARCHAR(32) NOT NULL,  -- community | topic | project | user
    target_id       UUID NOT NULL,
    -- 不加 FK target_id：target 可能是 community / topic / user / project
    -- 用 UNIQUE 约束去重
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 同一用户对同一目标只能关注一次
CREATE UNIQUE INDEX IF NOT EXISTS uq_follows_edge
    ON follows(tenant_id, follower_id, target_type, target_id);

-- 查"用户关注了哪些 X"
CREATE INDEX IF NOT EXISTS idx_follows_follower
    ON follows(tenant_id, follower_id, target_type);

-- 查"X 被谁关注了"
CREATE INDEX IF NOT EXISTS idx_follows_target
    ON follows(tenant_id, target_type, target_id);
