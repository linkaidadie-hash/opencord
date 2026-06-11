import Link from 'next/link';
import {
  getPlaza,
  PlazaResponse,
  TopicListItemV2,
  SignalListItemV2,
} from '@/lib/api';

export const dynamic = 'force-dynamic';

// intent_type (machine) → human-readable label + emoji + short hint
// Single source of truth for the Plaza UI. Keep in sync with
// apps/api/core/open_topic.py: SIGNAL_INTENT_TYPES.
const INTENT_LABELS: Record<string, { label: string; emoji: string; hint: string }> = {
  looking_for_person: {
    label: 'Looking for people',
    emoji: '👥',
    hint: 'I want to find someone to work / think with',
  },
  looking_for_help: {
    label: 'Looking for help',
    emoji: '🆘',
    hint: 'I need a hand on a specific problem',
  },
  looking_for_project: {
    label: 'Looking for projects',
    emoji: '🧭',
    hint: 'I want to join or start something',
  },
  offering_help: {
    label: 'Offering help',
    emoji: '🙋',
    hint: 'I can lend a hand; here is what I can do',
  },
  open_to_chat: {
    label: 'Open to talk',
    emoji: '💬',
    hint: 'Around a topic, no specific ask',
  },
  seeking_feedback: {
    label: 'Seeking feedback',
    emoji: '👀',
    hint: 'I made something; I want honest reactions',
  },
};

function renderIntent(intent: string) {
  const meta = INTENT_LABELS[intent];
  if (!meta) {
    return <span className="text-xs text-gray-400 font-mono">{intent}</span>;
  }
  return (
    <span
      className="inline-flex items-center gap-1 text-xs text-primary-700 bg-primary-50 px-2 py-0.5 rounded"
      title={meta.hint}
    >
      <span aria-hidden>{meta.emoji}</span>
      <span>{meta.label}</span>
    </span>
  );
}

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
        <p className="text-xs text-primary-600 mt-2">
          这里是开弦的开放广场入口。你可以闲逛、围观议题、也可以挂一个 Signal：
          <span className="italic">「我在找什么 / 我愿意聊什么 / 我能提供什么」</span>。
          这里 <strong>不</strong> 做私聊，不做群聊，不做消息推送。
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
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-lg font-semibold">最近议题（Topics）</h2>
            <span className="text-xs text-gray-500">
              来自 Open Topic Network
            </span>
          </div>
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
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-lg font-semibold">最近 Signal</h2>
            <span className="text-xs text-gray-500">
              来自 Open Plaza
            </span>
          </div>
          {data && data.recent_signals.length === 0 ? (
            <p className="text-sm text-gray-500">还没有人挂 signal</p>
          ) : (
            <ul className="space-y-2">
              {(data?.recent_signals ?? []).map((s: SignalListItemV2) => (
                <li key={s.id} className="card">
                  <div className="mb-1">{renderIntent(s.intent_type)}</div>
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

      {/* 最小 Signal 发布表单（C2-polish 占位，POST 由后续阶段接） */}
      <div className="card mt-6">
        <h2 className="text-lg font-semibold mb-2">挂一个 Signal</h2>
        <p className="text-xs text-gray-500 mb-3">
          表达 <span className="italic">「我想找什么 / 我愿意聊什么 / 我能提供什么」</span>。
          C2-polish 阶段只展示表单结构；实际 POST 由后续阶段接 <code>POST /api/open-topic/signals</code>。
        </p>
        <form className="space-y-2 text-sm">
          <div>
            <label className="block text-gray-700">intent_type</label>
            <select className="input" disabled>
              {Object.entries(INTENT_LABELS).map(([key, meta]) => (
                <option key={key} value={key}>
                  {meta.emoji} {meta.label} — {meta.hint}
                </option>
              ))}
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
            <input className="input" placeholder="rust, ai, 创作" disabled />
          </div>
          <button type="button" className="btn-secondary" disabled>
            发布（C2-polish 占位）
          </button>
        </form>
      </div>
    </div>
  );
}
