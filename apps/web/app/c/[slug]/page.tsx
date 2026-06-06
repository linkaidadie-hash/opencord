import Link from 'next/link';
import { notFound } from 'next/navigation';
import { getChannel, listPosts } from '@/lib/api';
import { PostCard } from '@/components/PostCard';

export default async function ChannelPage({ params }: { params: { slug: string } }) {
  let channel;
  let posts = [];
  try {
    channel = await getChannel(params.slug);
    posts = await listPosts({ channelId: channel.id, limit: 50 });
  } catch {
    notFound();
  }

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">#{channel.slug}</h1>
            <p className="text-gray-600 mt-1">{channel.name}</p>
            {channel.description && (
              <p className="text-sm text-gray-500 mt-1">{channel.description}</p>
            )}
          </div>
          <Link href={`/c/${channel.slug}/new`} className="btn-primary text-sm">
            发新帖
          </Link>
        </div>
      </div>

      <div className="space-y-3">
        {posts.length === 0 && (
          <p className="text-gray-500 text-sm">这个频道还没有帖子</p>
        )}
        {posts.map((p) => (
          <PostCard key={p.id} post={p} />
        ))}
      </div>
    </div>
  );
}
