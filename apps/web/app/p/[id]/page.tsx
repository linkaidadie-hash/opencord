import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getPost, listComments } from '@/lib/api';
import { MarkdownView } from '@/components/MarkdownView';
import { CommentForm, CommentList } from './_components';

export default async function PostPage({ params }: { params: { id: string } }) {
  let post, comments;
  try {
    [post, comments] = await Promise.all([
      getPost(params.id),
      listComments(params.id).catch(() => []),
    ]);
  } catch {
    notFound();
  }

  return (
    <article className="max-w-3xl mx-auto">
      <header className="mb-6 pb-4 border-b">
        <h1 className="text-3xl font-bold mb-2">{post.title}</h1>
        <div className="text-sm text-gray-500">
          <Link href={`/u/${post.author.username}`} className="font-medium text-gray-700 hover:text-primary-600">
            @{post.author.username}
          </Link>
          {' · '}
          <time>{new Date(post.created_at).toLocaleString('zh-CN')}</time>
          {' · 👁 '}{post.view_count}
          {' · 💬 '}{post.comment_count}
        </div>
        {post.tag_slugs.length > 0 && (
          <div className="flex gap-2 mt-2">
            {post.tag_slugs.map((t) => (
              <Link key={t} href={`/?tag=${t}`} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded hover:bg-gray-200">
                #{t}
              </Link>
            ))}
          </div>
        )}
      </header>

      {post.ai_summary && (
        <div className="card bg-primary-50 border-primary-200 mb-6">
          <div className="text-xs text-primary-700 font-medium mb-1">✨ AI 总结</div>
          <div className="text-sm text-gray-700">{post.ai_summary}</div>
        </div>
      )}

      <div className="card mb-6">
        <MarkdownView source={post.body_md} />
      </div>

      <section className="mt-8">
        <h2 className="text-xl font-semibold mb-4">评论 ({comments.length})</h2>
        <CommentForm postId={post.id} />
        <div className="mt-6 space-y-4">
          <CommentList comments={comments} />
        </div>
      </section>
    </article>
  );
}
