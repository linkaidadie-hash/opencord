"""apps/api/core/open_topic.py

Open Topic Network 的核心类型常量 + 校验函数。

设计原则：
- 不使用 PG ENUM。所有 "类型" 字段在数据库都是 VARCHAR
- 合法值集合在此处集中定义，service / router 共用
- 新增合法值只动这一个文件

C 阶段硬约束（与 db/migrations/0001_open_topic_network.sql 一致）：
- 不引入 agents / agent_runs / agent_actions 表
- 不接杜工部；project / task / agent / artifact 等类型仅预留
"""
from __future__ import annotations
import uuid
from typing import Final
from sqlalchemy.ext.asyncio import AsyncSession


# =====================================================
# subject_type / object_type 合法取值
# =====================================================
SUBJECT_TYPES: Final[tuple[str, ...]] = (
    "identity",
    "user",
    "community",
    "topic",
    "thread",
    "post",
    "project",
    "task",
    "agent",
    "artifact",
)

OBJECT_TYPES: Final[tuple[str, ...]] = SUBJECT_TYPES  # 同集合


# =====================================================
# relation_type 合法取值
# =====================================================
RELATION_TYPES: Final[tuple[str, ...]] = (
    "follows",
    "participates_in",
    "relates_to",
    "hosts",
    "generates",
    "proposes",
    "produces",
    "executes",
    "responds_to",
    "mentions",
)


# =====================================================
# follows.target_type 合法取值
# =====================================================
FOLLOW_TARGET_TYPES: Final[tuple[str, ...]] = (
    "community",
    "topic",
    "project",  # 仅预留，无 FK
    "user",
)


# =====================================================
# topic / community / thread 状态
# =====================================================
TOPIC_STATUSES: Final[tuple[str, ...]] = (
    "open",
    "resolved",
    "archived",
)

THREAD_STATUSES: Final[tuple[str, ...]] = (
    "published",
    "hidden",
    "deleted",
)

COMMUNITY_VISIBILITIES: Final[tuple[str, ...]] = (
    "public",
    "private",
)


# =====================================================
# topic_summaries.generated_by 默认值
# =====================================================
SUMMARY_GENERATED_BY_DEFAULT: Final[str] = "system"


# =====================================================
# 默认 tenant_id（与 channel_service / seed.py 保持一致）
# =====================================================
DEFAULT_TENANT_ID: Final[str] = "00000000-0000-0000-0000-000000000001"


# =====================================================
# 校验函数
# =====================================================
def ensure_in(value: str, allowed: tuple[str, ...], field: str) -> None:
    """校验 value 在 allowed 中；否则抛 ValueError，带字段名便于上层返回 400。"""
    if value not in allowed:
        raise ValueError(
            f"Invalid value for {field!r}: {value!r}. "
            f"Allowed: {', '.join(allowed)}"
        )


def ensure_subject_type(value: str) -> None:
    ensure_in(value, SUBJECT_TYPES, "subject_type")


def ensure_object_type(value: str) -> None:
    ensure_in(value, OBJECT_TYPES, "object_type")


def ensure_relation_type(value: str) -> None:
    ensure_in(value, RELATION_TYPES, "relation_type")


def ensure_follow_target_type(value: str) -> None:
    ensure_in(value, FOLLOW_TARGET_TYPES, "target_type")


def ensure_topic_status(value: str) -> None:
    ensure_in(value, TOPIC_STATUSES, "status")


def ensure_thread_status(value: str) -> None:
    ensure_in(value, THREAD_STATUSES, "status")


def ensure_community_visibility(value: str) -> None:
    ensure_in(value, COMMUNITY_VISIBILITIES, "visibility")


# =====================================================
# tenant 解析 + 存在性校验
# =====================================================
# 失败时由 router 统一转 HTTPException(code=500, detail=...)
class TenantResolutionError(Exception):
    """tenant_id 无法解析时抛出（由 router 转 4xx/5xx）。"""


class TenantMissingError(Exception):
    """tenant_id 在数据库中不存在时抛出（由 router 转 500/503）。"""


def resolve_tenant_id(user) -> uuid.UUID:
    """从 current_user 解析 tenant_id；缺则 fallback DEFAULT_TENANT_ID。

    C 阶段约定：v0.1 是单租户，user.tenant_id 为 None 时回退默认租户。
    这避免了上一版"硬编码 DEFAULT_TENANT_ID"丢掉 user 信息的隐患。
    """
    raw = getattr(user, "tenant_id", None)
    if raw is None:
        return uuid.UUID(DEFAULT_TENANT_ID)
    if isinstance(raw, uuid.UUID):
        return raw
    return uuid.UUID(str(raw))


async def ensure_tenant_exists(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    """写库前确保 tenant_id 真的存在于 tenants 表。

    替换原版"INSERT 裸跑让 PG FK 抛 500"的隐患：先 SELECT 一次，
    不存在就抛 TenantMissingError，由 router 转 500/503 + 明确错误信息。
    """
    from sqlalchemy import select
    from models import Tenant
    stmt = select(Tenant.id).where(Tenant.id == tenant_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise TenantMissingError(
            f"Tenant {tenant_id} does not exist. "
            f"Open Topic Network C 阶段要求 tenants 表必须包含此 id。 "
            f"请确认 db/schema.sql 已执行（默认租户 {DEFAULT_TENANT_ID} 会被自动 seed）。"
        )
