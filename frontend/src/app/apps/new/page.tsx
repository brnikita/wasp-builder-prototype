'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { createApp, generateApp } from '@/lib/api';

export default function NewApp() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !description.trim()) return;

    setLoading(true);
    setError('');

    try {
      const app = await createApp(name.trim(), description.trim());
      await generateApp(app.id);
      router.push(`/apps/${app.id}`);
    } catch (e) {
      setError('Failed to create application');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <Link
          href="/"
          className="text-zinc-400 hover:text-zinc-300 text-sm mb-6 inline-block"
        >
          ← Back to Dashboard
        </Link>

        <h1 className="text-2xl font-bold text-amber-500 mb-6">
          Create New Application
        </h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              App Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-todo-app"
              className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg focus:border-amber-500 focus:outline-none transition"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-zinc-300 mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your application in detail. What features should it have? What should users be able to do?"
              rows={6}
              className="w-full px-4 py-3 bg-zinc-900 border border-zinc-700 rounded-lg focus:border-amber-500 focus:outline-none transition resize-none"
              disabled={loading}
            />
            <p className="text-xs text-zinc-500 mt-2">
              Be specific about features, data models, and user interactions.
            </p>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !name.trim() || !description.trim()}
            className="w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-zinc-700 disabled:cursor-not-allowed text-black font-semibold rounded-lg transition"
          >
            {loading ? 'Generating with Claude...' : 'Generate Application'}
          </button>
        </form>
      </div>
    </div>
  );
}

