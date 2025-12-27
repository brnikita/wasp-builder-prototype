'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { App, getApp, deleteApp, startApp, stopApp, getLogs } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  created: 'bg-zinc-600',
  generating: 'bg-blue-500 animate-pulse',
  ready: 'bg-emerald-600',
  running: 'bg-green-500',
  stopped: 'bg-zinc-500',
  error: 'bg-red-500',
};

export default function AppDetail() {
  const params = useParams();
  const router = useRouter();
  const [app, setApp] = useState<App | null>(null);
  const [logs, setLogs] = useState('');
  const [activeTab, setActiveTab] = useState<'wasp' | 'prisma' | 'src' | 'logs'>('wasp');
  const [loading, setLoading] = useState(true);

  const id = params.id as string;

  const fetchApp = async () => {
    try {
      const data = await getApp(id);
      setApp(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const data = await getLogs(id);
      setLogs(data.logs);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchApp();
    const interval = setInterval(fetchApp, 3000);
    return () => clearInterval(interval);
  }, [id]);

  useEffect(() => {
    if (activeTab === 'logs' && app?.container_id) {
      fetchLogs();
      const interval = setInterval(fetchLogs, 5000);
      return () => clearInterval(interval);
    }
  }, [activeTab, app?.container_id]);

  const handleDelete = async () => {
    if (!confirm('Delete this application?')) return;
    await deleteApp(id);
    router.push('/');
  };

  const handleStart = async () => {
    await startApp(id);
    fetchApp();
  };

  const handleStop = async () => {
    await stopApp(id);
    fetchApp();
  };

  if (loading) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto text-zinc-400">Loading...</div>
      </div>
    );
  }

  if (!app) {
    return (
      <div className="min-h-screen p-8">
        <div className="max-w-6xl mx-auto text-zinc-400">App not found</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <Link
          href="/"
          className="text-zinc-400 hover:text-zinc-300 text-sm mb-6 inline-block"
        >
          ← Back to Dashboard
        </Link>

        <header className="flex items-start justify-between mb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{app.name}</h1>
              <span
                className={`px-2 py-0.5 text-xs rounded-full ${STATUS_COLORS[app.status]}`}
              >
                {app.status}
              </span>
            </div>
            <p className="text-zinc-400 mt-1">{app.description}</p>
            {app.port && (
              <p className="text-sm text-zinc-500 mt-1">Port: {app.port}</p>
            )}
            {app.error_message && (
              <p className="text-sm text-red-400 mt-2">{app.error_message}</p>
            )}
          </div>
          <div className="flex gap-2">
            {app.status === 'running' && app.port && (
              <a
                href={`http://localhost:${app.port}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black font-semibold rounded-lg transition"
              >
                Open App ↗
              </a>
            )}
            {(app.status === 'ready' || app.status === 'stopped') && (
              <button
                onClick={handleStart}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg transition"
              >
                Start
              </button>
            )}
            {app.status === 'running' && (
              <button
                onClick={handleStop}
                className="px-4 py-2 bg-zinc-600 hover:bg-zinc-700 rounded-lg transition"
              >
                Stop
              </button>
            )}
            <button
              onClick={handleDelete}
              className="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded-lg transition"
            >
              Delete
            </button>
          </div>
        </header>

        {app.status === 'generating' && (
          <div className="p-6 border border-zinc-800 rounded-xl bg-zinc-900/50 text-center">
            <div className="animate-spin w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full mx-auto mb-4" />
            <p className="text-zinc-400">Generating application with Claude...</p>
          </div>
        )}

        {(app.wasp_schema || app.status === 'ready' || app.status === 'running' || app.status === 'stopped') && (
          <>
            <div className="flex gap-1 mb-4 border-b border-zinc-800">
              {['wasp', 'prisma', 'src', 'logs'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as typeof activeTab)}
                  className={`px-4 py-2 text-sm font-medium transition ${
                    activeTab === tab
                      ? 'text-amber-500 border-b-2 border-amber-500'
                      : 'text-zinc-400 hover:text-zinc-300'
                  }`}
                >
                  {tab === 'wasp' ? 'main.wasp' : tab === 'prisma' ? 'schema.prisma' : tab === 'src' ? 'Source Files' : 'Logs'}
                </button>
              ))}
            </div>

            <div className="border border-zinc-800 rounded-xl bg-zinc-900/50 overflow-hidden">
              {activeTab === 'wasp' && (
                <pre className="p-4 text-sm overflow-auto max-h-[600px]">
                  <code>{app.wasp_schema || 'No schema generated'}</code>
                </pre>
              )}
              {activeTab === 'prisma' && (
                <pre className="p-4 text-sm overflow-auto max-h-[600px]">
                  <code>{app.prisma_schema || 'No schema generated'}</code>
                </pre>
              )}
              {activeTab === 'src' && (
                <div className="divide-y divide-zinc-800">
                  {app.source_files && Object.entries(app.source_files).map(([path, content]) => (
                    <div key={path}>
                      <div className="px-4 py-2 bg-zinc-800/50 text-sm font-medium text-zinc-300">
                        src/{path}
                      </div>
                      <pre className="p-4 text-sm overflow-auto max-h-[400px]">
                        <code>{content}</code>
                      </pre>
                    </div>
                  ))}
                  {!app.source_files && (
                    <div className="p-4 text-zinc-400">No source files generated</div>
                  )}
                </div>
              )}
              {activeTab === 'logs' && (
                <pre className="p-4 text-sm overflow-auto max-h-[600px] text-zinc-400">
                  <code>{logs || 'No logs available'}</code>
                </pre>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

