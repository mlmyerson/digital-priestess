export type PersonaModeName = 'archivist' | 'priestess';

export type HealthResponse = {
  ok: boolean;
  local_only: boolean;
  lm_studio_base_url: string;
  lm_studio_model: string;
  archive_root: string | null;
  archive_ready: boolean;
};

export type ArchiveStatus = {
  configured: boolean;
  root: string | null;
  supported_files: number;
  unsupported_files: number;
  readable_files: number;
  message: string;
};

export type ArchiveIndexStats = {
  database_path: string;
  documents: number;
  chunks: number;
  last_indexed_at: string | null;
};

export type ArchiveIndexResult = {
  root: string | null;
  database_path: string;
  documents_seen: number;
  documents_indexed: number;
  documents_skipped: number;
  chunks_indexed: number;
  errors: string[];
  indexed_at: string;
};

export type PersonaMode = {
  id: PersonaModeName;
  label: string;
  description: string;
};

export type Citation = {
  chunk_id: string;
  title: string;
  path: string;
  source_type: string;
  snippet: string;
  score: number;
  start_line: number | null;
  end_line: number | null;
};

export type ChatResponse = {
  answer: string;
  mode: PersonaModeName;
  citations: Citation[];
  used_model: boolean;
  model_error: string | null;
};

export type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  usedModel?: boolean;
};