import type {
  ArchiveIndexResult,
  ArchiveIndexStats,
  ArchiveStatus,
  ChatResponse,
  HealthResponse,
  PersonaMode,
  PersonaModeName
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

export function getPersonaModes(): Promise<PersonaMode[]> {
  return request<PersonaMode[]>('/api/persona/modes');
}

export function sendChat(message: string, mode: PersonaModeName): Promise<ChatResponse> {
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, mode, max_citations: 5 })
  });
}