import Link from 'next/link';
import { listChannels, listPosts } from '@/lib/api';
import { PostCard } from '@/components/PostCard';

export default async function Home() {
  const [channels, recentPosts] = await Promise.all([
    listChannels().catch(() => []),
    listPosts({ limit: 20 }).catch(() => []),
  ]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* 频道列表 */}
      <aside className="md:col-span-1">
        <h2 className="text-lg font-semibold mb-3">频道</h2>
        <div className="space-y-2">
          {channels.length === 0 && (
            <p className="text-sm text-gray-500">还没有频道</p>
          )}
          {channels.map((c) => (
            <Link
              key={c.id}
              href={`/c/${c.slug}`}
              className="block card hover:shadow-md"
            >
              <div className="font-medium">#{c.slug}</div>
              <div className="text-sm text-gray-600">{c.name}</div>
              <div className="text-xs text-gray-400 mt-1">{c.post_count} 帖子</div>
            </Link>
          ))}
        </div>
      </aside>

      {/* 最新帖子 */}
      <section className="md:col-span-2">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">最新帖子</h2>
          {channels[0] && (
            <Link href={`/c/${channels[0].slug}/new`} className="btn-primary text-sm">
              发新帖
            </Link>
          )}
        </div>
        <div className="space-y-3">
          {recentPosts.length === 0 && (
            <p className="text-gray-500 text-sm">还没有帖子，发第一个吧 👋</p>
          )}
          {recentPosts.map((p) => (
            <PostCard key={p.id} post={p} />
          ))}
        </div>
      </section>
    </div>
  );
}
