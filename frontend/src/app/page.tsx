'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { App, listApps, deleteApp, startApp, stopApp } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  created: 'bg-zinc-600',
  generating: 'bg-blue-500 animate-pulse',
  ready: 'bg-emerald-600',
  running: 'bg-green-500',
  stopped: 'bg-zinc-500',
  error: 'bg-red-500',
};

export default function Dashboard() {
  const [apps, setApps] = useState<App[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchApps = async () => {
    try {
      const data = await listApps();
      setApps(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
    const interval = setInterval(fetchApps, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this application?')) return;
    await deleteApp(id);
    fetchApps();
  };

  const handleStart = async (id: string) => {
    await startApp(id);
    fetchApps();
  };

  const handleStop = async (id: string) => {
    await stopApp(id);
    fetchApps();
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <header className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-amber-500">Wasp Builder</h1>
            <p className="text-zinc-400 mt-1">Build full-stack apps with AI</p>
          </div>
          <Link
            href="/apps/new"
            className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-black font-semibold rounded-lg transition"
          >
            + New App
          </Link>
        </header>

        {loading ? (
          <div className="text-zinc-400">Loading...</div>
        ) : apps.length === 0 ? (
          <div className="text-center py-16 border border-zinc-800 rounded-xl bg-zinc-900/50">
            <p className="text-zinc-400 mb-4">No applications yet</p>
            <Link
              href="/apps/new"
              className="text-amber-500 hover:text-amber-400"
            >
              Create your first app →
            </Link>
          </div>
        ) : (
          <div className="grid gap-4">
            {apps.map((app) => (
              <div
                key={app.id}
                className="p-4 border border-zinc-800 rounded-xl bg-zinc-900/50 hover:border-zinc-700 transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <Link
                        href={`/apps/${app.id}`}
                        className="text-lg font-semibold hover:text-amber-500 transition"
                      >
                        {app.name}
                      </Link>
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full ${STATUS_COLORS[app.status]}`}
                      >
                        {app.status}
                      </span>
                      {app.port && app.status === 'running' && (
                        <a
                          href={`http://localhost:${app.port}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-amber-500 hover:text-amber-400"
                        >
                          :{ app.port} ↗
                        </a>
                      )}
                    </div>
                    <p className="text-sm text-zinc-400 mt-1 line-clamp-2">
                      {app.description}
                    </p>
                    {app.error_message && (
                      <p className="text-sm text-red-400 mt-1">
                        {app.error_message}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    {app.status === 'ready' || app.status === 'stopped' ? (
                      <button
                        onClick={() => handleStart(app.id)}
                        className="px-3 py-1 text-sm bg-emerald-600 hover:bg-emerald-700 rounded transition"
                      >
                        Start
                      </button>
                    ) : app.status === 'running' ? (
                      <button
                        onClick={() => handleStop(app.id)}
                        className="px-3 py-1 text-sm bg-zinc-600 hover:bg-zinc-700 rounded transition"
                      >
                        Stop
                      </button>
                    ) : null}
                    <button
                      onClick={() => handleDelete(app.id)}
                      className="px-3 py-1 text-sm bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded transition"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

