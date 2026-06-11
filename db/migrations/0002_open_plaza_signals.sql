-- =====================================================
-- OpenCord / 开弦 — Migration 0002: Open Plaza Signals
-- 阶段：C2-lite (Open Plaza 入口 + Signals)
--
-- 原则（与 0001 一致，不破旧约束）：
--   1. 新增 1 张表：signals
--   2. tenant_id NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
--   3. 不改任何旧表；不重命名旧表；不迁移旧数据
--   4. intent_type / visibility 用 VARCHAR，不建 ENUM
--   5. 合法值在 apps/api/core/open_topic.py 集中定义
--   6. topic_id NULLABLE：Signal 可以不绑议题（广场里闲逛时挂的）
--   7. tags 用 JSONB（数组），default '[]'
--   8. 不做私聊/群聊/Encounter/Agent/Project
--   9. 触发器复用 0001 已有的 trigger_set_updated_at() 函数
-- =====================================================


-- =====================================================
-- signals — 广场里的“我想找什么 / 我愿意聊什么 / 我能提供什么”
-- =====================================================
CREATE TABLE IF NOT EXISTS signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id        UUID REFERENCES topics(id) ON DELETE SET NULL,  -- 可选绑定议题
    intent_type     VARCHAR(64) NOT NULL,  -- 见 core/open_topic.py: SIGNAL_INTENT_TYPES
    title           VARCHAR(200) NOT NULL,
    body            TEXT,
    tags            JSONB NOT NULL DEFAULT '[]'::jsonb,
    visibility      VARCHAR(32) NOT NULL DEFAULT 'public',  -- public | unlisted | private
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 广场首页/列表：按 tenant + 时间倒序
CREATE INDEX IF NOT EXISTS idx_signals_tenant_recent
    ON signals(tenant_id, created_at DESC);

-- 按议题过滤（topic_id 不为 NULL 时）
CREATE INDEX IF NOT EXISTS idx_signals_topic
    ON signals(tenant_id, topic_id, created_at DESC)
    WHERE topic_id IS NOT NULL;

-- 按用户过滤（个人发布历史）
CREATE INDEX IF NOT EXISTS idx_signals_user
    ON signals(tenant_id, user_id, created_at DESC);

-- 按 intent_type 过滤（推荐 / 分类的预留，不做实际推荐逻辑）
CREATE INDEX IF NOT EXISTS idx_signals_intent
    ON signals(tenant_id, intent_type, created_at DESC);

-- 触发器：updated_at 自动维护
DROP TRIGGER IF EXISTS set_updated_at ON signals;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON signals
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
