import type {
  ArchiveIndexResult,
  ArchiveIndexStats,
  ArchiveStatus,
  ChatHistoryMessage,
  ChatResponse,
  HealthResponse
} from './types';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers ?? {}) },
    ...options
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health');
}

export function getArchiveStatus(): Promise<ArchiveStatus> {
  return request<ArchiveStatus>('/api/archive/status');
}

export function getArchiveIndexStatus(): Promise<ArchiveIndexStats> {
  return request<ArchiveIndexStats>('/api/archive/index');
}

export function indexArchive(): Promise<ArchiveIndexResult> {
  return request<ArchiveIndexResult>('/api/archive/index', { method: 'POST' });
}

export function sendChat(message: string, history: ChatHistoryMessage[]): Promise<ChatResponse> {
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history, max_citations: 5 })
  });
}