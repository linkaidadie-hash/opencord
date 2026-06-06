import { notFound } from 'next/navigation';
import { getUser, listPosts } from '@/lib/api';
import { PostCard } from '@/components/PostCard';

export default async function UserPage({ params }: { params: { username: string } }) {
  let user, posts;
  try {
    user = await getUser(params.username);
    const all = await listPosts({ limit: 50 });
    posts = all.filter((p) => p.author.id === user.id);
  } catch {
    notFound();
  }

  return (
    <div>
      <header className="card mb-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-full bg-primary-500 text-white flex items-center justify-center text-2xl font-bold">
            {user.display_name?.[0] || user.username[0]}
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold">{user.display_name || user.username}</h1>
            <p className="text-sm text-gray-500">@{user.username} · {user.role}</p>
            {user.bio && <p className="text-gray-700 mt-2">{user.bio}</p>}
            <p className="text-xs text-gray-400 mt-2">
              加入于 {new Date(user.created_at).toLocaleDateString('zh-CN')}
            </p>
          </div>
        </div>
      </header>

      <h2 className="text-lg font-semibold mb-3">TA 的帖子 ({posts.length})</h2>
      <div className="space-y-3">
        {posts.length === 0 && <p className="text-gray-500 text-sm">还没有发过帖</p>}
        {posts.map((p) => <PostCard key={p.id} post={p} />)}
      </div>
    </div>
  );
}
