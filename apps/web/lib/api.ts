/**
 * OpenCord API client (server-side)
 *
 * URL 解析规则（按优先级）：
 * 1. NEXT_PUBLIC_API_URL（绝对 URL，浏览器直接访问，覆盖一切）
 * 2. 空字符串（让 Next.js rewrite 把 /api/* 转发到后端）
 *
 * 故意不读 API_INTERNAL_URL —— 那是 docker 内部地址（http://api:8000），
 * 浏览器在用户机器上访问不到，只供 next.config.js 的 rewrite 用。
 */
import 'server-only';

const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || '';

export class APIError extends Error {
  constructor(public status: number, public detail: any) {
    super(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers, ...rest } = options;
  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers || {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    let detail: any;
    try { detail = await res.json(); } catch { detail = await res.text(); }
    throw new APIError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// ---- Types ----
export interface UserPublic {
  id: string;
  username: string;
  display_name: string | null;
  bio: string | null;
  avatar_url: string | null;
  role: string;
  created_at: string;
}

export interface ChannelPublic {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  visibility: string;
  post_count: number;
  created_at: string;
  created_by: string;
}

export interface PostListItem {
  id: string;
  channel_id: string;
  author: UserPublic;
  title: string;
  status: string;
  pinned: boolean;
  comment_count: number;
  ai_summary: string | null;
  created_at: string;
  tag_slugs: string[];
}

export interface PostPublic extends PostListItem {
  body_md: string;
  body_html: string;
  view_count: number;
  ai_summary_at: string | null;
  updated_at: string;
}

export interface CommentPublic {
  id: string;
  post_id: string;
  parent_id: string | null;
  author: UserPublic;
  body_md: string;
  body_html: string;
  created_at: string;
}

export interface NotificationPublic {
  id: string;
  type: string;
  actor: UserPublic | null;
  target_type: string;
  target_id: string;
  payload: Record<string, any>;
  read_at: string | null;
  created_at: string;
}

// ---- Functions ----
export async function listChannels(): Promise<ChannelPublic[]> {
  return request('/api/channels');
}

export async function getChannel(slug: string): Promise<ChannelPublic> {
  return request(`/api/channels/${slug}`);
}

export async function listPosts(opts: { channelId?: string; tag?: string; limit?: number; offset?: number } = {}): Promise<PostListItem[]> {
  const params = new URLSearchParams();
  if (opts.channelId) params.set('channel_id', opts.channelId);
  if (opts.tag) params.set('tag', opts.tag);
  if (opts.limit) params.set('limit', String(opts.limit));
  if (opts.offset) params.set('offset', String(opts.offset));
  const qs = params.toString();
  return request(`/api/posts${qs ? `?${qs}` : ''}`);
}

export async function getPost(id: string): Promise<PostPublic> {
  return request(`/api/posts/${id}`);
}

export async function createPost(token: string, body: { channel_id: string; title: string; body_md: string; tag_slugs?: string[] }): Promise<PostPublic> {
  return request('/api/posts', { method: 'POST', body: JSON.stringify(body), token });
}

export async function listComments(postId: string): Promise<CommentPublic[]> {
  return request(`/api/comments/by-post/${postId}`);
}

export async function createComment(token: string, body: { post_id: string; parent_id?: string; body_md: string }): Promise<CommentPublic> {
  return request('/api/comments', { method: 'POST', body: JSON.stringify(body), token });
}

export async function listNotifications(token: string, unreadOnly = false): Promise<NotificationPublic[]> {
  return request(`/api/notifications${unreadOnly ? '?unread_only=true' : ''}`, { token });
}

export async function me(token: string): Promise<UserPublic> {
  return request('/api/auth/me', { token });
}

export async function getUser(username: string): Promise<UserPublic> {
  return request(`/api/users/${username}`);
}

export async function listUserPosts(username: string): Promise<PostListItem[]> {
  const user = await getUser(username);
  return listPosts({ limit: 50, offset: 0 }).then((all) => all.filter((p) => p.author.id === user.id));
}

// =====================================================
// Open Topic Network（C 阶段最小客户端）
// =====================================================
export interface CommunityPublicV2 {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  visibility: string;
  topic_count: number;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface TopicListItemV2 {
  id: string;
  community_id: string;
  slug: string;
  title: string;
  status: string;
  thread_count: number;
  created_at: string;
  updated_at: string;
}

export interface TopicPublicV2 extends TopicListItemV2 {
  body_md: string;
}

export interface ThreadPublicV2 {
  id: string;
  topic_id: string;
  parent_id: string | null;
  created_by: string;
  body_md: string;
  body_html: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface RelationPublicV2 {
  id: string;
  subject_type: string;
  subject_id: string;
  relation_type: string;
  object_type: string;
  object_id: string;
  weight: number;
  created_at: string;
}

export interface FollowPublicV2 {
  id: string;
  follower_id: string;
  target_type: string;
  target_id: string;
  created_at: string;
}

export async function listOpenTopicCommunities(): Promise<CommunityPublicV2[]> {
  return request('/api/open-topic/communities');
}

export async function getOpenTopicCommunity(id: string): Promise<CommunityPublicV2> {
  return request(`/api/open-topic/communities/${id}`);
}

export async function listOpenTopicTopics(opts: { communityId?: string; status?: string; limit?: number } = {}): Promise<TopicListItemV2[]> {
  const params = new URLSearchParams();
  if (opts.communityId) params.set('community_id', opts.communityId);
  if (opts.status) params.set('status', opts.status);
  if (opts.limit) params.set('limit', String(opts.limit));
  const qs = params.toString();
  return request(`/api/open-topic/topics${qs ? `?${qs}` : ''}`);
}

export async function getOpenTopicTopic(id: string): Promise<TopicPublicV2> {
  return request(`/api/open-topic/topics/${id}`);
}

export async function listOpenTopicThreads(topicId: string): Promise<ThreadPublicV2[]> {
  return request(`/api/open-topic/threads?topic_id=${encodeURIComponent(topicId)}`);
}

export async function listOpenTopicRelations(opts: {
  subjectType?: string;
  subjectId?: string;
  objectType?: string;
  objectId?: string;
  relationType?: string;
}): Promise<RelationPublicV2[]> {
  const params = new URLSearchParams();
  if (opts.subjectType) params.set('subject_type', opts.subjectType);
  if (opts.subjectId) params.set('subject_id', opts.subjectId);
  if (opts.objectType) params.set('object_type', opts.objectType);
  if (opts.objectId) params.set('object_id', opts.objectId);
  if (opts.relationType) params.set('relation_type', opts.relationType);
  const qs = params.toString();
  return request(`/api/open-topic/relations${qs ? `?${qs}` : ''}`);
}

// =====================================================
// Open Plaza + Signals（C2-lite 最小客户端）
// =====================================================
export interface SignalListItemV2 {
  id: string;
  user_id: string;
  topic_id: string | null;
  intent_type: string;
  title: string;
  tags: string[];
  created_at: string;
}

export interface SignalPublicV2 extends SignalListItemV2 {
  body: string | null;
  visibility: string;
  expires_at: string | null;
  updated_at: string;
}

export interface PlazaResponse {
  description: string;
  recent_topics: TopicListItemV2[];
  recent_signals: SignalListItemV2[];
  hot: any[];
}

export async function getPlaza(): Promise<PlazaResponse> {
  return request('/api/plaza');
}

export async function listOpenTopicSignals(opts: { intentType?: string; topicId?: string; limit?: number } = {}): Promise<SignalListItemV2[]> {
  const params = new URLSearchParams();
  if (opts.intentType) params.set('intent_type', opts.intentType);
  if (opts.topicId) params.set('topic_id', opts.topicId);
  if (opts.limit) params.set('limit', String(opts.limit));
  const qs = params.toString();
  return request(`/api/open-topic/signals${qs ? `?${qs}` : ''}`);
}

export async function getOpenTopicSignal(id: string): Promise<SignalPublicV2> {
  return request(`/api/open-topic/signals/${id}`);
}

export async function createOpenTopicSignal(token: string, body: {
  topic_id?: string | null;
  intent_type: string;
  title: string;
  body?: string | null;
  tags?: string[];
  visibility?: string;
}): Promise<SignalPublicV2> {
  return request('/api/open-topic/signals', {
    method: 'POST',
    body: JSON.stringify(body),
    token,
  });
}
