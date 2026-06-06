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
