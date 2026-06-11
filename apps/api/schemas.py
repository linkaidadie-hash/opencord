"""Pydantic schemas for request/response."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# =====================================================
# Auth
# =====================================================
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=128)


class LoginRequest(BaseModel):
    email_or_username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserPublic"


# =====================================================
# User
# =====================================================
class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    display_name: str | None
    bio: str | None
    avatar_url: str | None
    role: str
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=128)
    bio: str | None = Field(default=None, max_length=1000)
    avatar_url: str | None = Field(default=None, max_length=512)


# =====================================================
# API Token
# =====================================================
class APITokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    scopes: list[str] = Field(default_factory=list)
    expires_in_days: int | None = None  # None = 不过期


class APITokenCreated(BaseModel):
    id: uuid.UUID
    name: str
    token: str  # 明文，只在创建时返回一次
    token_prefix: str
    scopes: list[str]
    expires_at: datetime | None
    created_at: datetime


class APITokenPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    token_prefix: str
    scopes: list[str]
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    revoked_at: datetime | None


# =====================================================
# Channel
# =====================================================
class ChannelCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    visibility: Literal["public", "private"] = "public"


class ChannelPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    visibility: str
    post_count: int
    created_at: datetime
    created_by: uuid.UUID


# =====================================================
# Post
# =====================================================
class PostCreate(BaseModel):
    channel_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    body_md: str = Field(min_length=1, max_length=50000)
    tag_slugs: list[str] = Field(default_factory=list)


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body_md: str | None = Field(default=None, min_length=1, max_length=50000)


class PostPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    channel_id: uuid.UUID
    author: UserPublic
    title: str
    body_md: str
    body_html: str
    status: str
    pinned: bool
    view_count: int
    comment_count: int
    ai_summary: str | None
    ai_summary_at: datetime | None
    created_at: datetime
    updated_at: datetime
    tag_slugs: list[str] = Field(default_factory=list)


class PostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    channel_id: uuid.UUID
    author: UserPublic
    title: str
    status: str
    pinned: bool
    comment_count: int
    ai_summary: str | None
    created_at: datetime
    tag_slugs: list[str] = Field(default_factory=list)


# =====================================================
# Comment
# =====================================================
class CommentCreate(BaseModel):
    post_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    body_md: str = Field(min_length=1, max_length=10000)


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    post_id: uuid.UUID
    parent_id: uuid.UUID | None
    author: UserPublic
    body_md: str
    body_html: str
    created_at: datetime


# =====================================================
# Notification
# =====================================================
class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: str
    actor: UserPublic | None
    target_type: str
    target_id: uuid.UUID
    payload: dict
    read_at: datetime | None
    created_at: datetime


# =====================================================
# AI Provider
# =====================================================
class AIProviderCreate(BaseModel):
    name: str
    provider_type: Literal["openai-compatible", "MiniMax", "deepseek", "ollama"]
    api_key: str
    base_url: str
    model: str
    is_default: bool = False
    rpm_limit: int | None = None


class AIProviderPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    provider_type: str
    base_url: str
    model: str
    is_active: bool
    is_default: bool
    supports_chat: bool
    supports_summarize: bool
    supports_embed: bool
    rpm_limit: int | None
    created_at: datetime


# =====================================================
# Admin
# =====================================================
class AdminUserAction(BaseModel):
    action: Literal["ban", "unban", "suspend", "promote", "demote"]
    reason: str | None = None


# Update forward refs
TokenResponse.model_rebuild()


# =====================================================
# Open Topic Network（C 阶段）
#   所有 type 字段在应用层用 core/open_topic.py 校验
# =====================================================
class CommunityCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    visibility: str = "public"


class CommunityPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    visibility: str
    topic_count: int
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TopicCreate(BaseModel):
    community_id: uuid.UUID
    slug: str = Field(min_length=2, max_length=128, pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=1, max_length=255)
    body_md: str = Field(default="", max_length=50000)


class TopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body_md: str | None = Field(default=None, max_length=50000)
    status: str | None = None


class TopicPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    community_id: uuid.UUID
    slug: str
    title: str
    body_md: str
    status: str
    created_by: uuid.UUID
    thread_count: int
    created_at: datetime
    updated_at: datetime


class TopicListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    community_id: uuid.UUID
    slug: str
    title: str
    status: str
    thread_count: int
    created_at: datetime
    updated_at: datetime


class ThreadCreate(BaseModel):
    topic_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    body_md: str = Field(min_length=1, max_length=50000)


class ThreadPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    topic_id: uuid.UUID
    parent_id: uuid.UUID | None
    created_by: uuid.UUID
    body_md: str
    body_html: str
    status: str
    created_at: datetime
    updated_at: datetime


class TopicSummaryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    topic_id: uuid.UUID
    summary_md: str
    summary_html: str
    generated_by: str
    generated_at: datetime
    updated_at: datetime


class RelationCreate(BaseModel):
    subject_type: str
    subject_id: uuid.UUID
    relation_type: str
    object_type: str
    object_id: uuid.UUID
    weight: float = Field(default=1.0, ge=0.0, le=999.999)


class RelationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    subject_type: str
    subject_id: uuid.UUID
    relation_type: str
    object_type: str
    object_id: uuid.UUID
    weight: float
    created_at: datetime


class FollowCreate(BaseModel):
    target_type: str
    target_id: uuid.UUID


class FollowPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    follower_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    created_at: datetime


# =====================================================
# C2-lite: Open Plaza Signals
# =====================================================
class SignalCreate(BaseModel):
    topic_id: uuid.UUID | None = None
    intent_type: str
    title: str = Field(min_length=1, max_length=200)
    body: str | None = Field(default=None, max_length=10000)
    tags: list[str] = Field(default_factory=list, max_length=20)
    visibility: str = "public"
    expires_at: datetime | None = None


class SignalPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    topic_id: uuid.UUID | None
    intent_type: str
    title: str
    body: str | None
    tags: list[str] = Field(default_factory=list)
    visibility: str
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SignalListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    topic_id: uuid.UUID | None
    intent_type: str
    title: str
    tags: list[str] = Field(default_factory=list)
    created_at: datetime


# =====================================================
# Plaza 聚合响应（首页用）
# =====================================================
class PlazaResponse(BaseModel):
    description: str
    recent_topics: list[TopicListItem]
    recent_signals: list[SignalListItem]
    hot: list = Field(default_factory=list)  # 预留（C2-lite 不做推荐）
