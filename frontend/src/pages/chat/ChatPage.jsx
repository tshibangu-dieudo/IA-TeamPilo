/**
 * ChatPage — AI chat assistant at /chat
 * See docs/12_Frontend_Architecture.md §3 (ChatPanel → ChatPage).
 * See docs/13_AI_Architecture.md §3.3 (Chain 3).
 *
 * Layout:
 *   Left sidebar  — conversation list + new conversation button
 *   Right panel   — active conversation messages + composer
 *
 * Rules:
 * - Tailwind utility classes only — no custom CSS (.ai/coding-rules.md).
 * - AI explanation text always visible, never hidden (.ai/coding-rules.md §FE-3).
 * - No TypeScript (.ai/coding-rules.md §FE-1).
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { chatAPI } from '../../api/chat';

// ------------------------------------------------------------------ helpers
const GENERATED_BY_LABELS = {
  granite: 'IBM Granite',
  fallback_template: 'Fallback (AI unavailable)',
};

function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });
}

// ------------------------------------------------------------------ sub-components

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={[
          'max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
          isUser
            ? 'bg-indigo-600 text-white rounded-br-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm shadow-sm',
        ].join(' ')}
      >
        {/* Message content — always fully visible per coding rules §FE-3 */}
        <p className="whitespace-pre-wrap">{message.content}</p>

        <div className={`mt-1 flex items-center gap-2 text-xs ${isUser ? 'text-indigo-200' : 'text-gray-400'}`}>
          <span>{formatTime(message.created_at)}</span>
          {!isUser && message.generated_by && (
            <span className="italic">
              · {GENERATED_BY_LABELS[message.generated_by] ?? message.generated_by}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function ConversationItem({ conv, active, onClick, onDelete }) {
  return (
    <li className="group flex items-center justify-between">
      <button
        onClick={onClick}
        className={[
          'flex-1 text-left px-3 py-2 rounded-lg text-sm truncate transition-colors',
          active
            ? 'bg-indigo-100 text-indigo-900 font-medium'
            : 'text-gray-700 hover:bg-gray-100',
        ].join(' ')}
        title={conv.title || 'Untitled conversation'}
      >
        {conv.title || 'Untitled conversation'}
      </button>
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
        aria-label="Delete conversation"
        className="ml-1 p-1 rounded opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-opacity"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </li>
  );
}

// ------------------------------------------------------------------ main component

export default function ChatPage() {
  const [conversations, setConversations] = useState([]);
  const [activeConvId, setActiveConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // ---- load conversation list
  const fetchConversations = useCallback(async () => {
    try {
      const res = await chatAPI.listConversations();
      const data = res.data;
      setConversations(Array.isArray(data) ? data : (data.results ?? []));
    } catch (err) {
      setError('Failed to load conversations.');
    } finally {
      setLoadingConvs(false);
    }
  }, []);

  useEffect(() => { fetchConversations(); }, [fetchConversations]);

  // ---- load messages for active conversation
  const loadConversation = useCallback(async (convId) => {
    if (!convId) { setMessages([]); return; }
    setLoadingMessages(true);
    try {
      const res = await chatAPI.getConversation(convId);
      setMessages(res.data.messages ?? []);
    } catch {
      setError('Failed to load conversation.');
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  useEffect(() => { loadConversation(activeConvId); }, [activeConvId, loadConversation]);

  // ---- auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ---- send question
  async function handleSend(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q || sending) return;

    setSending(true);
    setError(null);

    // Optimistic user message
    const optimisticUser = { id: 'temp-user', role: 'user', content: q, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, optimisticUser]);
    setQuestion('');

    try {
      const res = await chatAPI.query({
        question: q,
        conversation_id: activeConvId ?? undefined,
      });

      const { answer, generated_by, conversation_id, conversation_title } = res.data;

      // Update active conversation
      setActiveConvId(conversation_id);

      // Replace optimistic + add assistant reply
      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== 'temp-user');
        return [
          ...withoutTemp,
          { id: `u-${Date.now()}`, role: 'user', content: q, created_at: new Date().toISOString() },
          { id: `a-${Date.now()}`, role: 'assistant', content: answer, generated_by, created_at: new Date().toISOString() },
        ];
      });

      // Refresh conversation list (new conv may have been created / title set)
      await fetchConversations();

    } catch (err) {
      setMessages((prev) => prev.filter((m) => m.id !== 'temp-user'));
      setError('Failed to send message. Please try again.');
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(e) {
    // Submit on Enter (not Shift+Enter)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  }

  async function handleDeleteConversation(convId) {
    try {
      await chatAPI.deleteConversation(convId);
      if (activeConvId === convId) {
        setActiveConvId(null);
        setMessages([]);
      }
      setConversations((prev) => prev.filter((c) => c.id !== convId));
    } catch {
      setError('Failed to delete conversation.');
    }
  }

  function handleNewConversation() {
    setActiveConvId(null);
    setMessages([]);
    textareaRef.current?.focus();
  }

  // ---------------------------------------------------------------- render

  return (
    <div className="flex h-screen bg-gray-50">
      {/* ---- Sidebar ---- */}
      <aside className="w-64 flex-shrink-0 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">AI Assistant</h2>
          <p className="text-xs text-gray-500 mt-0.5">Powered by IBM Granite</p>
        </div>

        <div className="p-3">
          <button
            onClick={handleNewConversation}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            New conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 pb-4">
          {loadingConvs ? (
            <p className="text-xs text-gray-400 px-2 py-4">Loading…</p>
          ) : conversations.length === 0 ? (
            <p className="text-xs text-gray-400 px-2 py-4">No conversations yet.</p>
          ) : (
            <ul className="space-y-1">
              {conversations.map((conv) => (
                <ConversationItem
                  key={conv.id}
                  conv={conv}
                  active={conv.id === activeConvId}
                  onClick={() => setActiveConvId(conv.id)}
                  onDelete={handleDeleteConversation}
                />
              ))}
            </ul>
          )}
        </div>
      </aside>

      {/* ---- Chat panel ---- */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="px-6 py-4 bg-white border-b border-gray-200 flex items-center justify-between">
          <div>
            <h1 className="text-base font-semibold text-gray-900">
              {activeConvId
                ? (conversations.find((c) => c.id === activeConvId)?.title || 'Conversation')
                : 'New conversation'}
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Ask about workload, risks, tasks, or recommendations for your projects.
            </p>
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mx-6 mt-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-4 text-red-400 hover:text-red-600">✕</button>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loadingMessages ? (
            <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
              Loading conversation…
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-50 flex items-center justify-center mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <p className="text-gray-700 font-medium">Ask me anything about your projects</p>
              <p className="mt-1 text-sm text-gray-500">
                Try: "Who is overloaded?" · "What tasks are blocked?" · "What's the risk status?"
              </p>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <MessageBubble key={msg.id ?? i} message={msg} />
              ))}
              {sending && (
                <div className="flex justify-start mb-3">
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                    <div className="flex gap-1 items-center h-5">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Composer */}
        <div className="px-6 py-4 bg-white border-t border-gray-200">
          <form onSubmit={handleSend} className="flex items-end gap-3">
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question… (Enter to send, Shift+Enter for new line)"
              rows={2}
              disabled={sending}
              className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-50"
              aria-label="Chat message"
            />
            <button
              type="submit"
              disabled={!question.trim() || sending}
              className="flex-shrink-0 p-3 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
              aria-label="Send message"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </form>
          <p className="mt-2 text-xs text-gray-400 text-center">
            Responses are grounded in your project data. AI cannot modify any records.
          </p>
        </div>
      </main>
    </div>
  );
}
