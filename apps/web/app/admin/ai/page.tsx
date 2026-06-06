'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

function getToken(): string {
  const m = document.cookie.match(/(?:^|;\s*)opencord_token=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : '';
}

const PRESETS: Record<string, { base_url: string; model: string; type: string }> = {
  'openai': { base_url: 'https://api.openai.com/v1', model: 'gpt-4o-mini', type: 'openai-compatible' },
  'deepseek': { base_url: 'https://api.deepseek.com/v1', model: 'deepseek-chat', type: 'deepseek' },
  'MiniMax': { base_url: 'https://api.MiniMax.chat/v1', model: 'MiniMax-abab6.5s-chat', type: 'MiniMax' },
  'ollama': { base_url: 'http://host.docker.internal:11434/v1', model: 'llama3.1', type: 'openai-compatible' },
  'siliconflow': { base_url: 'https://api.siliconflow.cn/v1', model: 'Qwen/Qwen2.5-7B-Instruct', type: 'openai-compatible' },
  'openrouter': { base_url: 'https://openrouter.ai/api/v1', model: 'openai/gpt-4o-mini', type: 'openai-compatible' },
};

export default function AIProviderAdminPage() {
  const router = useRouter();
  const [preset, setPreset] = useState<keyof typeof PRESETS>('openai');
  const [name, setName] = useState('OpenAI');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState(PRESETS.openai.base_url);
  const [model, setModel] = useState(PRESETS.openai.model);
  const [isDefault, setIsDefault] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function onPresetChange(p: keyof typeof PRESETS) {
    setPreset(p);
    const cfg = PRESETS[p];
    setBaseUrl(cfg.base_url);
    setModel(cfg.model);
    if (p === 'MiniMax') setName('MiniMax');
    else setName(p.charAt(0).toUpperCase() + p.slice(1));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    const token = getToken();
    if (!token) {
      setMessage('请先登录');
      setLoading(false);
      return;
    }
    try {
      const res = await fetch(`${API_URL}/api/ai/providers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name,
          provider_type: PRESETS[preset].type,
          api_key: apiKey,
          base_url: baseUrl,
          model,
          is_default: isDefault,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: '添加失败' }));
        throw new Error(err.detail || '添加失败');
      }
      setMessage('✅ Provider 添加成功');
      setApiKey('');
      router.refresh();
    } catch (e: any) {
      setMessage('❌ ' + e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">AI Provider 配置</h1>
      <p className="text-sm text-gray-600 mb-6">
        OpenCord 不绑定任何 LLM 平台。先添加一个 Provider 并设为默认，AI 总结功能就能用了。
      </p>

      <form onSubmit={onSubmit} className="space-y-4 card">
        <div>
          <label className="block text-sm font-medium mb-1">快速预设</label>
          <select
            value={preset}
            onChange={(e) => onPresetChange(e.target.value as keyof typeof PRESETS)}
            className="input"
          >
            <option value="openai">OpenAI</option>
            <option value="deepseek">DeepSeek</option>
            <option value="MiniMax">MiniMax</option>
            <option value="siliconflow">硅基流动（SiliconFlow）</option>
            <option value="openrouter">OpenRouter</option>
            <option value="ollama">Ollama（本地）</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">选完预设会自动填好 base_url 和 model</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">名称</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input" required />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">API Key</label>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            className="input"
            placeholder="sk-..."
            required
          />
          <p className="text-xs text-gray-500 mt-1">v0.1 暂存明文，v0.2 加密</p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Base URL</label>
          <input
            type="text"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            className="input font-mono text-sm"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Model</label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="input font-mono text-sm"
            required
          />
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="isDefault"
            checked={isDefault}
            onChange={(e) => setIsDefault(e.target.checked)}
            className="mr-2"
          />
          <label htmlFor="isDefault" className="text-sm">设为默认 Provider</label>
        </div>

        {message && <div className="text-sm">{message}</div>}

        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? '添加中…' : '添加 Provider'}
        </button>
      </form>

      <div className="mt-6 text-sm text-gray-500">
        💡 提示：填好之后，回到任何帖子详情页，调 <code>POST /api/ai/summarize-post/{`{post_id}`}</code> 就能生成 AI 总结。
        （v0.1 用 API 触发；v0.2 在帖子页加一个"生成总结"按钮）
      </div>
    </div>
  );
}
