import Link from 'next/link';
import { redirect } from 'next/navigation';
import { getAuthToken } from '@/lib/auth';
import { me } from '@/lib/api';

export default async function AdminPage() {
  const token = getAuthToken();
  if (!token) redirect('/login');

  let user;
  try {
    user = await me(token);
  } catch {
    redirect('/login');
  }

  if (user.role !== 'admin' && user.role !== 'moderator') {
    return (
      <div className="card">
        <h1 className="text-2xl font-bold mb-2">无权访问</h1>
        <p className="text-gray-600">此页面仅限管理员</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">管理后台</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link href="/admin/ai" className="card hover:shadow-md">
          <h2 className="text-lg font-semibold">🤖 AI Providers</h2>
          <p className="text-sm text-gray-600 mt-1">配置 OpenAI / MiniMax / DeepSeek / Ollama 等 AI 服务</p>
        </Link>
        <div className="card opacity-60">
          <h2 className="text-lg font-semibold">👥 用户管理</h2>
          <p className="text-sm text-gray-600 mt-1">v0.2 上线（封号 / 解封 / 升降级）</p>
        </div>
        <div className="card opacity-60">
          <h2 className="text-lg font-semibold">📋 审计日志</h2>
          <p className="text-sm text-gray-600 mt-1">v0.2 上线</p>
        </div>
        <div className="card opacity-60">
          <h2 className="text-lg font-semibold">📊 统计</h2>
          <p className="text-sm text-gray-600 mt-1">v0.2 上线</p>
        </div>
      </div>
    </div>
  );
}
