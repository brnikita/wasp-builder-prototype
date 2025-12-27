const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface App {
  id: string;
  name: string;
  description: string;
  status: 'created' | 'generating' | 'ready' | 'running' | 'stopped' | 'error';
  port: number | null;
  wasp_schema: string | null;
  prisma_schema: string | null;
  source_files: Record<string, string> | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export async function listApps(): Promise<App[]> {
  const res = await fetch(`${API_URL}/api/apps`);
  if (!res.ok) throw new Error('Failed to fetch apps');
  return res.json();
}

export async function getApp(id: string): Promise<App> {
  const res = await fetch(`${API_URL}/api/apps/${id}`);
  if (!res.ok) throw new Error('Failed to fetch app');
  return res.json();
}

export async function createApp(name: string, description: string): Promise<App> {
  const res = await fetch(`${API_URL}/api/apps`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error('Failed to create app');
  return res.json();
}

export async function deleteApp(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/apps/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete app');
}

export async function generateApp(id: string): Promise<App> {
  const res = await fetch(`${API_URL}/api/apps/${id}/generate`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to generate app');
  return res.json();
}

export async function startApp(id: string): Promise<App> {
  const res = await fetch(`${API_URL}/api/apps/${id}/start`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to start app');
  return res.json();
}

export async function stopApp(id: string): Promise<App> {
  const res = await fetch(`${API_URL}/api/apps/${id}/stop`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to stop app');
  return res.json();
}

export async function getLogs(id: string): Promise<{ logs: string }> {
  const res = await fetch(`${API_URL}/api/apps/${id}/logs`);
  if (!res.ok) throw new Error('Failed to fetch logs');
  return res.json();
}

