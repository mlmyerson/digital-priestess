import { FormEvent, useEffect, useMemo, useState } from 'react';
import { BookOpen, Database, RefreshCcw, Send, Sparkles } from 'lucide-react';

import { getArchiveIndexStatus, getArchiveStatus, getHealth, getPersonaModes, indexArchive, sendChat } from './api';
import type {
  ArchiveIndexResult,
  ArchiveIndexStats,
  ArchiveStatus,
  Citation,
  HealthResponse,
  Message,
  PersonaMode,
  PersonaModeName
} from './types';

const initialMessage: Message = {
  id: 'opening',
  role: 'assistant',
  content: 'The archive channel is open. Ask for a cited reading when you are ready.'
};

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [archive, setArchive] = useState<ArchiveStatus | null>(null);
  const [indexStats, setIndexStats] = useState<ArchiveIndexStats | null>(null);
  const [lastIndexResult, setLastIndexResult] = useState<ArchiveIndexResult | null>(null);
  const [modes, setModes] = useState<PersonaMode[]>([]);
  const [mode, setMode] = useState<PersonaModeName>('archivist');
  const [messages, setMessages] = useState<Message[]>([initialMessage]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [selectedCitations, setSelectedCitations] = useState<Citation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    refreshStatus();
    getPersonaModes().then(setModes).catch((statusError: Error) => setError(statusError.message));
  }, []);

  const activeMode = useMemo(() => modes.find((personaMode) => personaMode.id === mode), [modes, mode]);

  async function refreshStatus() {
    try {
      const [nextHealth, nextArchive, nextIndexStats] = await Promise.all([
        getHealth(),
        getArchiveStatus(),
        getArchiveIndexStatus()
      ]);
      setHealth(nextHealth);
      setArchive(nextArchive);
      setIndexStats(nextIndexStats);
      setError(null);
    } catch (statusError) {
      setError(statusError instanceof Error ? statusError.message : 'Status request failed.');
    }
  }

  async function handleIndexArchive() {
    if (isIndexing) {
      return;
    }
    setIsIndexing(true);
    setError(null);
    try {
      const result = await indexArchive();
      setLastIndexResult(result);
      const nextIndexStats = await getArchiveIndexStatus();
      setIndexStats(nextIndexStats);
    } catch (indexError) {
      setError(indexError instanceof Error ? indexError.message : 'Indexing failed.');
    } finally {
      setIsIndexing(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || isSending) {
      return;
    }

    const userMessage: Message = { id: crypto.randomUUID(), role: 'user', content: trimmedInput };
    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setInput('');
    setIsSending(true);
    setError(null);

    try {
      const response = await sendChat(trimmedInput, mode);
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        usedModel: response.used_model
      };
      setMessages((currentMessages) => [...currentMessages, assistantMessage]);
      setSelectedCitations(response.citations);
      if (response.model_error) {
        setError(response.model_error);
      }
    } catch (chatError) {
      setError(chatError instanceof Error ? chatError.message : 'Chat request failed.');
    } finally {
      setIsSending(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace" aria-label="Digital Priestess workspace">
        <header className="topbar">
          <div className="brand-lockup">
            <Sparkles aria-hidden="true" size={22} />
            <div>
              <h1>Digital Priestess</h1>
              <p>{activeMode?.description ?? 'Local archive companion'}</p>
            </div>
          </div>
          <div className="status-strip">
            <StatusPill label="Model" value={health?.lm_studio_model ?? 'unknown'} active={Boolean(health?.ok)} />
            <StatusPill label="Archive" value={archive?.readable_files ? `${archive.readable_files} files` : 'pending'} active={Boolean(archive?.readable_files)} />
            <button className="icon-button" type="button" onClick={refreshStatus} title="Refresh status">
              <RefreshCcw size={18} aria-hidden="true" />
            </button>
          </div>
        </header>

        <div className="main-grid">
          <aside className="side-panel" aria-label="Archive controls">
            <div className="mode-switch" role="tablist" aria-label="Persona mode">
              {modes.map((personaMode) => (
                <button
                  key={personaMode.id}
                  className={personaMode.id === mode ? 'mode-button active' : 'mode-button'}
                  type="button"
                  onClick={() => setMode(personaMode.id)}
                  role="tab"
                  aria-selected={personaMode.id === mode}
                >
                  {personaMode.label}
                </button>
              ))}
            </div>

            <div className="panel-block">
              <div className="panel-heading">
                <Database size={18} aria-hidden="true" />
                <h2>Archive</h2>
              </div>
              <dl className="metric-list">
                <div>
                  <dt>Root</dt>
                  <dd>{archive?.root ?? 'not set'}</dd>
                </div>
                <div>
                  <dt>Readable</dt>
                  <dd>{archive?.readable_files ?? 0}</dd>
                </div>
                <div>
                  <dt>Indexed</dt>
                  <dd>{indexStats ? `${indexStats.documents} docs, ${indexStats.chunks} chunks` : '0 docs'}</dd>
                </div>
                <div>
                  <dt>Planned</dt>
                  <dd>{archive?.unsupported_files ?? 0}</dd>
                </div>
              </dl>
              <button className="panel-action" type="button" onClick={handleIndexArchive} disabled={isIndexing || !archive?.configured}>
                {isIndexing ? 'Indexing' : 'Index archive'}
              </button>
              {lastIndexResult ? (
                <div className="index-result">
                  {lastIndexResult.documents_indexed} indexed, {lastIndexResult.documents_skipped} skipped
                </div>
              ) : null}
            </div>

            <div className="panel-block">
              <div className="panel-heading">
                <BookOpen size={18} aria-hidden="true" />
                <h2>Local Model</h2>
              </div>
              <dl className="metric-list">
                <div>
                  <dt>Endpoint</dt>
                  <dd>{health?.lm_studio_base_url ?? 'offline'}</dd>
                </div>
                <div>
                  <dt>Boundary</dt>
                  <dd>{health?.local_only ? 'local' : 'check config'}</dd>
                </div>
              </dl>
            </div>
          </aside>

          <section className="chat-panel" aria-label="Chat">
            <div className="message-list">
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  <div className="message-meta">{message.role === 'user' ? 'You' : 'Digital Priestess'}</div>
                  <p>{message.content}</p>
                  {message.citations?.length ? (
                    <button className="text-button" type="button" onClick={() => setSelectedCitations(message.citations ?? [])}>
                      View {message.citations.length} citations
                    </button>
                  ) : null}
                </article>
              ))}
            </div>

            {error ? <div className="error-banner">{error}</div> : null}

            <form className="composer" onSubmit={handleSubmit}>
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask the archive"
                rows={3}
              />
              <button className="send-button" type="submit" disabled={isSending || !input.trim()} title="Send">
                <Send size={18} aria-hidden="true" />
                <span>{isSending ? 'Reading' : 'Send'}</span>
              </button>
            </form>
          </section>

          <aside className="citation-panel" aria-label="Citations">
            <h2>Citations</h2>
            {selectedCitations.length ? (
              <div className="citation-list">
                {selectedCitations.map((citation) => (
                  <article key={citation.chunk_id} className="citation-item">
                    <div className="citation-title">{citation.title}</div>
                    <div className="citation-path">{citation.path}</div>
                    <p>{citation.snippet}</p>
                    <div className="citation-meta">
                      {citation.source_type}
                      {citation.start_line && citation.end_line ? `, lines ${citation.start_line}-${citation.end_line}` : ''}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-state">No citations selected.</p>
            )}
          </aside>
        </div>
      </section>
    </main>
  );
}

type StatusPillProps = {
  label: string;
  value: string;
  active: boolean;
};

function StatusPill({ label, value, active }: StatusPillProps) {
  return (
    <div className={active ? 'status-pill active' : 'status-pill'}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default App;