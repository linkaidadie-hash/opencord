'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

function getToken(): string {
  const m = document.cookie.match(/(?:^|;\s*)opencord_token=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : '';
}

export default function NewPostPage() {
  const router = useRouter();
  const params = useParams<{ slug: string }>();
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [tags, setTags] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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
      // 先取 channel id
      const chRes = await fetch(`${API_URL}/api/channels/${params.slug}`);
      if (!chRes.ok) throw new Error('频道不存在');
      const ch = await chRes.json();
      const res = await fetch(`${API_URL}/api/posts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          channel_id: ch.id,
          title,
          body_md: body,
          tag_slugs: tags
            .split(/[\s,]+/)
            .map((t) => t.trim())
            .filter(Boolean),
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '发新帖失败' }));
        throw new Error(err.detail || '发新帖失败');
      }
      const post = await res.json();
      router.push(`/p/${post.id}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">在 #{params.slug} 发新帖</h1>
      <form onSubmit={onSubmit} className="space-y-4 card">
        <div>
          <label className="block text-sm font-medium mb-1">标题</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
            required
            maxLength={255}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">正文（Markdown）</label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            className="input font-mono text-sm"
            rows={15}
            required
            minLength={1}
            maxLength={50000}
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">标签（空格或逗号分隔）</label>
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="input"
            placeholder="例如：ai 工具 教程"
          />
        </div>
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <div className="flex gap-2">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? '发布中…' : '发布'}
          </button>
          <button type="button" onClick={() => router.back()} className="btn-secondary">
            取消
          </button>
        </div>
      </form>
    </div>
  );
}
