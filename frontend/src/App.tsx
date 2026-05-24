import { FormEvent, useEffect, useState } from 'react';
import { BookOpen, Database, RefreshCcw, Send, Sparkles } from 'lucide-react';

import { getArchiveIndexStatus, getArchiveStatus, getHealth, indexArchive, sendChat } from './api';
import type {
  ArchiveIndexResult,
  ArchiveIndexStats,
  ArchiveStatus,
  ChatHistoryMessage,
  Citation,
  HealthResponse,
  Message
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
  const [messages, setMessages] = useState<Message[]>([initialMessage]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isIndexing, setIsIndexing] = useState(false);
  const [selectedCitations, setSelectedCitations] = useState<Citation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    refreshStatus();
  }, []);

  const noticeLabel = error && (error.includes('LM Studio') || error.includes('chat/completions')) ? 'Model fallback' : 'Notice';

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
    const history: ChatHistoryMessage[] = messages
      .filter((message) => message.id !== initialMessage.id)
      .slice(-12)
      .map((message) => ({ role: message.role, content: message.content }));
    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setInput('');
    setIsSending(true);
    setError(null);

    try {
      const response = await sendChat(trimmedInput, history);
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
      <section className="workspace" aria-label="Aelira workspace">
        <header className="topbar">
          <div className="brand-lockup">
            <Sparkles aria-hidden="true" size={22} />
            <div>
              <h1>Aelira</h1>
              <p>Digital priestess and archivist reading the local archive with cited memory.</p>
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
            <div className="panel-block">
              <div className="panel-heading">
                <Database size={18} aria-hidden="true" />
                <h2>Archive</h2>
              </div>
              <div className="archive-summary" aria-label="Archive summary">
                <div>
                  <strong>{archive?.readable_files ?? 0}</strong>
                  <span>files</span>
                </div>
                <div>
                  <strong>{indexStats?.documents ?? 0}</strong>
                  <span>docs</span>
                </div>
                <div>
                  <strong>{indexStats?.chunks ?? 0}</strong>
                  <span>chunks</span>
                </div>
              </div>
              <dl className="metric-list">
                <div>
                  <dt>Root</dt>
                  <dd title={archive?.root ?? undefined}>{archive?.root ?? 'not set'}</dd>
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
                  <dd title={health?.lm_studio_base_url ?? undefined}>{health?.lm_studio_base_url ?? 'offline'}</dd>
                </div>
                <div>
                  <dt>Boundary</dt>
                  <dd>{health?.local_only ? 'local' : 'check config'}</dd>
                </div>
              </dl>
            </div>
          </aside>

          <section className="chat-panel" aria-label="Chat">
            <div className="message-list" aria-live="polite">
              {messages.map((message) => (
                <article key={message.id} className={`message ${message.role}`}>
                  <div className="message-meta">{message.role === 'user' ? 'You' : 'Aelira'}</div>
                  <p>{message.content}</p>
                  {message.role === 'assistant' && message.usedModel === false ? (
                    <div className="message-note">Answered from archive retrieval</div>
                  ) : null}
                  {message.citations?.length ? (
                    <button className="citation-chip" type="button" onClick={() => setSelectedCitations(message.citations ?? [])}>
                      <span>{message.citations.length}</span>
                      {message.citations.length === 1 ? 'citation' : 'citations'}
                    </button>
                  ) : null}
                </article>
              ))}
            </div>

            {error ? (
              <div className="error-banner" role="status">
                <strong>{noticeLabel}</strong>
                <span>{error}</span>
              </div>
            ) : null}

            <form className="composer" onSubmit={handleSubmit}>
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask for a cited reading"
                rows={3}
              />
              <button className="send-button" type="submit" disabled={isSending || !input.trim()} title="Send">
                <Send size={18} aria-hidden="true" />
                <span>{isSending ? 'Reading' : 'Send'}</span>
              </button>
            </form>
          </section>

          <aside className="citation-panel" aria-label="Citations">
            <h2>{selectedCitations.length ? `Citations (${selectedCitations.length})` : 'Citations'}</h2>
            {selectedCitations.length ? (
              <div className="citation-list">
                {selectedCitations.map((citation, citationIndex) => (
                  <article key={citation.chunk_id} className="citation-item">
                    <div className="citation-kicker">Source {citationIndex + 1}</div>
                    <div className="citation-title">{citation.title}</div>
                    <div className="citation-path" title={citation.path}>{citation.path}</div>
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