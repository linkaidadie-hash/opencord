import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  getOpenTopicTopic,
  listOpenTopicThreads,
  listOpenTopicRelations,
  TopicPublicV2,
  ThreadPublicV2,
  RelationPublicV2,
} from '@/lib/api';

export const dynamic = 'force-dynamic';

export default async function OpenTopicDetail({ params }: { params: { topicId: string } }) {
  let topic: TopicPublicV2;
  let threads: ThreadPublicV2[] = [];
  let outRelations: RelationPublicV2[] = [];
  let loadError: string | null = null;

  try {
    topic = await getOpenTopicTopic(params.topicId);
    [threads, outRelations] = await Promise.all([
      listOpenTopicThreads(topic.id).catch(() => []),
      listOpenTopicRelations({
        subjectType: 'topic',
        subjectId: topic.id,
      }).catch(() => []),
    ]);
  } catch (e: any) {
    if (e?.status === 404) notFound();
    loadError = e?.message ?? String(e);
    return (
      <div>
        <Link href="/open-topic" className="text-sm text-primary-600">← 返回</Link>
        <div className="card mt-4 border-l-4 border-yellow-500 bg-yellow-50">
          <p className="text-sm text-yellow-800">加载失败：<code>{loadError}</code></p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Link href="/open-topic" className="text-sm text-primary-600">← 返回 Open Topic</Link>

      {/* 议题头 */}
      <div className="card mt-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold">{topic.title}</h1>
            <div className="text-xs text-gray-500 mt-1">
              /{topic.slug} · status: {topic.status} · {topic.thread_count} 个讨论流
            </div>
          </div>
        </div>
        {topic.body_md && (
          <pre className="mt-3 text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-3 rounded">
            {topic.body_md}
          </pre>
        )}
      </div>

      {/* 关系（出边） */}
      {outRelations.length > 0 && (
        <div className="card mt-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-2">关系（出边）</h2>
          <ul className="text-xs text-gray-600 space-y-1">
            {outRelations.map((r) => (
              <li key={r.id}>
                <code className="bg-gray-100 px-1 rounded">{r.relation_type}</code>
                {' '}-{'> '}
                <span>{r.object_type}:{r.object_id.slice(0, 8)}</span>
                {r.weight !== 1.0 && <span className="text-gray-400"> (w={r.weight})</span>}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 讨论流 */}
      <div className="mt-6">
        <h2 className="text-lg font-semibold mb-3">讨论流（Threads）</h2>
        {threads.length === 0 ? (
          <p className="text-sm text-gray-500">这个议题还没有讨论流</p>
        ) : (
          <div className="space-y-2">
            {threads.map((th) => (
              <div key={th.id} className="card">
                <div className="text-xs text-gray-500 mb-1">
                  {new Date(th.created_at).toLocaleString('zh-CN')} · {th.status}
                </div>
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">
                  {th.body_md}
                </pre>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
