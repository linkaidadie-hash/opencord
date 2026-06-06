import Link from 'next/link';
import type { PostListItem } from '@/lib/api';

export function PostCard({ post }: { post: PostListItem }) {
  return (
    <Link href={`/p/${post.id}`} className="block card hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between text-sm text-gray-500 mb-2">
        <span>
          {post.pinned && <span className="text-yellow-600 mr-1">📌</span>}
          <span className="font-medium text-gray-700">@{post.author.username}</span>
          {' · '}
          <time>{new Date(post.created_at).toLocaleString('zh-CN')}</time>
        </span>
        <span>💬 {post.comment_count}</span>
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-1">{post.title}</h3>
      {post.ai_summary && (
        <div className="text-sm text-primary-700 bg-primary-50 rounded px-2 py-1 mt-2">
          ✨ {post.ai_summary}
        </div>
      )}
      {post.tag_slugs.length > 0 && (
        <div className="flex gap-2 mt-2">
          {post.tag_slugs.map((t) => (
            <span key={t} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
              #{t}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
