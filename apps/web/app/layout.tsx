import type { Metadata } from 'next';
import './globals.css';
import 'highlight.js/styles/github.css';
import { Nav } from '@/components/Nav';

export const metadata: Metadata = {
  title: 'OpenCord / 开弦',
  description: 'An open, AI-native community system.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 min-h-screen text-gray-900">
        <Nav />
        <main className="max-w-4xl mx-auto px-4 py-6">
          {children}
        </main>
        <footer className="text-center text-sm text-gray-500 py-8">
          OpenCord / 开弦 · v0.1 · MIT License
        </footer>
      </body>
    </html>
  );
}
