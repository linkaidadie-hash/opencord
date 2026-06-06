'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import type { CommentPublic } from '@/lib/api';
import { MarkdownView } from '@/components/MarkdownView';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

function getToken(): string {
  const m = document.cookie.match(/(?:^|;\s*)opencord_token=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : '';
}

export function CommentForm({ postId, parentId }: { postId: string; parentId?: string }) {
  const router = useRouter();
  const [body, setBody] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const token = getToken();
    if (!token) {
      setError('请先登录');
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ post_id: postId, parent_id: parentId, body_md: body }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '发送失败' }));
        throw new Error(err.detail || '发送失败');
      }
      setBody('');
      router.refresh();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-2">
      <textarea
        value={body}
        onChange={(e) => setBody(e.target.value)}
        className="input"
        rows={3}
        placeholder={parentId ? '回复…' : '写评论…（支持 Markdown）'}
        required
        minLength={1}
        maxLength={10000}
      />
      {error && <div className="text-red-600 text-sm">{error}</div>}
      <button type="submit" disabled={loading} className="btn-primary text-sm">
        {loading ? '发送中…' : parentId ? '回复' : '发送'}
      </button>
    </form>
  );
}

export function CommentList({ comments }: { comments: CommentPublic[] }) {
  if (comments.length === 0) {
    return <p className="text-gray-500 text-sm">还没有评论</p>;
  }

  // 一级评论
  const top = comments.filter((c) => !c.parent_id);
  // 二级评论，按 parent_id 分组
  const replies = new Map<string, CommentPublic[]>();
  for (const c of comments.filter((c) => c.parent_id)) {
    if (!replies.has(c.parent_id!)) replies.set(c.parent_id!, []);
    replies.get(c.parent_id!)!.push(c);
  }

  return (
    <>
      {top.map((c) => (
        <div key={c.id} className="card">
          <div className="text-sm text-gray-500 mb-1">
            <span className="font-medium text-gray-700">@{c.author.username}</span>
            {' · '}
            <time>{new Date(c.created_at).toLocaleString('zh-CN')}</time>
          </div>
          <MarkdownView source={c.body_md} />
          {replies.has(c.id) && (
            <div className="mt-3 ml-4 pl-3 border-l-2 border-gray-200 space-y-3">
              {replies.get(c.id)!.map((r) => (
                <div key={r.id}>
                  <div className="text-sm text-gray-500 mb-1">
                    <span className="font-medium text-gray-700">@{r.author.username}</span>
                    {' · '}
                    <time>{new Date(r.created_at).toLocaleString('zh-CN')}</time>
                  </div>
                  <MarkdownView source={r.body_md} />
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </>
  );
}
