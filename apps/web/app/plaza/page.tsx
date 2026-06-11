import Link from 'next/link';
import {
  getPlaza,
  PlazaResponse,
  TopicListItemV2,
  SignalListItemV2,
} from '@/lib/api';

export const dynamic = 'force-dynamic';

export default async function PlazaPage() {
  let data: PlazaResponse | null = null;
  let loadError: string | null = null;
  try {
    data = await getPlaza();
  } catch (e: any) {
    loadError = e?.message ?? String(e);
  }

  return (
    <div>
      {/* Plaza header */}
      <div className="card mb-6 border-l-4 border-primary-600 bg-primary-50">
        <h1 className="text-2xl font-bold text-primary-800">Open Plaza · 开放广场</h1>
        <p className="text-sm text-primary-700 mt-2">
          {data?.description ??
            'A public square for topics, signals, and open encounters.'}
        </p>
        <p className="text-xs text-primary-600 mt-1">
          本页面 <code className="bg-white px-1 rounded">/api/plaza</code> · 广场不是私聊
        </p>
      </div>

      {loadError && (
        <div className="card mb-6 border-l-4 border-yellow-500 bg-yellow-50">
          <p className="text-sm text-yellow-800">
            后端未启动或数据库未迁移：<code>{loadError}</code>
          </p>
          <p className="text-xs text-yellow-700 mt-1">
            参考 <code>db/migrations/0002_open_plaza_signals.sql</code>
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 最近议题 */}
        <section>
          <h2 className="text-lg font-semibold mb-3">最近议题（Topics）</h2>
          {data && data.recent_topics.length === 0 ? (
            <p className="text-sm text-gray-500">广场里还没有议题</p>
          ) : (
            <ul className="space-y-2">
              {(data?.recent_topics ?? []).map((t: TopicListItemV2) => (
                <li key={t.id} className="card">
                  <Link href={`/open-topic/${t.id}`} className="font-medium hover:text-primary-700">
                    {t.title}
                  </Link>
                  <div className="text-xs text-gray-500 mt-1">
                    {t.status} · {t.thread_count} 个讨论流
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* 最近 Signals */}
        <section>
          <h2 className="text-lg font-semibold mb-3">最近 Signal</h2>
          {data && data.recent_signals.length === 0 ? (
            <p className="text-sm text-gray-500">还没有人挂 signal</p>
          ) : (
            <ul className="space-y-2">
              {(data?.recent_signals ?? []).map((s: SignalListItemV2) => (
                <li key={s.id} className="card">
                  <div className="text-xs text-primary-600 font-mono mb-1">
                    {s.intent_type}
                  </div>
                  <div className="font-medium">{s.title}</div>
                  {s.tags && s.tags.length > 0 && (
                    <div className="text-xs text-gray-500 mt-1">
                      {s.tags.map((t) => `#${t}`).join(' ')}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {/* 最小 Signal 发布表单（C2-lite 占位，不接后端） */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold mb-2">挂一个 Signal（占位 UI）</h2>
        <p className="text-xs text-gray-500 mb-3">
          C2-lite 阶段只展示表单结构。实际 POST 由后续阶段接（POST /api/open-topic/signals）。
        </p>
        <form className="space-y-2 text-sm">
          <div>
            <label className="block text-gray-700">intent_type</label>
            <select className="input" disabled>
              <option>looking_for_person</option>
              <option>looking_for_help</option>
              <option>looking_for_project</option>
              <option>offering_help</option>
              <option>open_to_chat</option>
              <option>seeking_feedback</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700">title</label>
            <input className="input" placeholder="我在找 / 我能提供" disabled />
          </div>
          <div>
            <label className="block text-gray-700">body</label>
            <textarea className="input" rows={3} disabled />
          </div>
          <div>
            <label className="block text-gray-700">tags (逗号分隔)</label>
            <input className="input" placeholder="rust, agent, 创作" disabled />
          </div>
          <button type="button" className="btn-secondary" disabled>
            发布（C2-lite 占位）
          </button>
        </form>
      </div>
    </div>
  );
}
