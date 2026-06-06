import Link from 'next/link';

export function Nav() {
  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-xl font-bold text-primary-700">
            OpenCord
          </Link>
          <Link href="/" className="text-gray-700 hover:text-primary-600">
            频道
          </Link>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm text-gray-700 hover:text-primary-600">
            登录
          </Link>
          <Link href="/register" className="btn-primary text-sm">
            注册
          </Link>
        </div>
      </div>
    </nav>
  );
}
