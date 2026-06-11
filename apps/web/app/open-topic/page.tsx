import Link from 'next/link';
import {
  listOpenTopicCommunities,
  listOpenTopicTopics,
  CommunityPublicV2,
  TopicListItemV2,
} from '@/lib/api';

export const dynamic = 'force-dynamic';

export default async function OpenTopicIndex() {
  let communities: CommunityPublicV2[] = [];
  let topics: TopicListItemV2[] = [];
  let loadError: string | null = null;
  try {
    [communities, topics] = await Promise.all([
      listOpenTopicCommunities().catch(() => []),
      listOpenTopicTopics({ limit: 20 }).catch(() => []),
    ]);
  } catch (e: any) {
    loadError = e?.message ?? String(e);
  }

  return (
    <div>
      {/* 阶段定位横幅 */}
      <div className="card mb-6 border-l-4 border-primary-600 bg-primary-50">
        <h1 className="text-2xl font-bold text-primary-800">Open Topic Network · 开放议题网络</h1>
        <p className="text-sm text-primary-700 mt-2">
          开弦 C 阶段第一段主干：议题（topic）成为核心实体，社群（community）作为议题容器，
          讨论流（thread）挂在议题下。关系（relation）构成一张图。
        </p>
        <p className="text-xs text-primary-600 mt-1">
          本页面 <code className="bg-white px-1 rounded">/api/open-topic/*</code> · 不替代旧 API
        </p>
      </div>

      {loadError && (
        <div className="card mb-6 border-l-4 border-yellow-500 bg-yellow-50">
          <p className="text-sm text-yellow-800">
            后端未启动或数据库未迁移：<code>{loadError}</code>
          </p>
          <p className="text-xs text-yellow-700 mt-1">
            参考 <code>db/migrations/0001_open_topic_network.sql</code> 和
            <code>scripts/apply_migration_0001.py</code>
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 社群列表 */}
        <section>
          <h2 className="text-lg font-semibold mb-3">社群（Community）</h2>
          {communities.length === 0 ? (
            <p className="text-sm text-gray-500">还没有社群</p>
          ) : (
            <div className="space-y-2">
              {communities.map((c) => (
                <div key={c.id} className="card">
                  <div className="font-medium">{c.name}</div>
                  <div className="text-xs text-gray-500">/{c.slug} · {c.visibility}</div>
                  {c.description && (
                    <div className="text-sm text-gray-600 mt-1">{c.description}</div>
                  )}
                  <div className="text-xs text-gray-400 mt-1">{c.topic_count} 个议题</div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 议题列表 */}
        <section>
          <h2 className="text-lg font-semibold mb-3">最新议题（Topic）</h2>
          {topics.length === 0 ? (
            <p className="text-sm text-gray-500">还没有议题</p>
          ) : (
            <div className="space-y-2">
              {topics.map((t) => (
                <Link
                  key={t.id}
                  href={`/open-topic/${t.id}`}
                  className="block card hover:shadow-md"
                >
                  <div className="font-medium">{t.title}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {t.status} · {t.thread_count} 个讨论流
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
