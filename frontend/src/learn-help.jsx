// Learn help drawer — mentor chat + lesson-context AI assistant

const I = window.I;

function mentorDisplayName(mentor) {
  if (!mentor) return 'Ментор';
  const name = [mentor.first_name, mentor.last_name].filter(Boolean).join(' ').trim();
  return name || mentor.email || 'Ментор';
}

function lessonStatementFromData(lessonType, lessonData) {
  if (!lessonData) return '';
  const chunks = [];
  if (lessonData.description) chunks.push(String(lessonData.description));
  if (lessonData.content) chunks.push(String(lessonData.content));
  if (lessonData.question_text) chunks.push(String(lessonData.question_text));
  if (lessonData.instructions) chunks.push(String(lessonData.instructions));
  return chunks.join('\n\n').trim().slice(0, 2500);
}

function LearnAssistantPane({ context }) {
  const [messages, setMessages] = React.useState([]);
  const [draft, setDraft] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState('');
  const [mode, setMode] = React.useState('');
  const listRef = React.useRef(null);

  React.useEffect(() => {
    const node = listRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [messages, busy]);

  const send = async () => {
    const text = draft.trim();
    if (!text || busy) return;
    setDraft('');
    setError('');
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((old) => [...old, { role: 'user', content: text }]);
    setBusy(true);
    try {
      const liveContext = {
        ...(context || {}),
        user_code:
          (typeof window !== 'undefined' && window.__learnAssistantCode) ||
          context?.user_code ||
          '',
      };
      const data = await window.fetchApiJson('/api/mentoring/assistant/chat/', {
        method: 'POST',
        auth: true,
        body: { message: text, history, context: liveContext },
      });
      setMode(data.mode || '');
      setMessages((old) => [...old, { role: 'assistant', content: data.reply || 'Пустой ответ' }]);
    } catch (e) {
      setError(e.message || 'Не удалось получить ответ');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="shrink-0 border-b border-black/[.06] bg-sky-50/80 px-4 py-3 text-xs text-ink/70">
        <div className="font-semibold text-ink/80">Контекст задания</div>
        <div className="mt-1 line-clamp-3">
          {context?.lesson_title
            ? `${context.lesson_kind || 'урок'}: ${context.lesson_title}`
            : 'Откройте урок — помощник увидит условие.'}
        </div>
        {mode === 'mock' || mode === 'mock_fallback' ? (
          <div className="mt-2 text-[11px] text-amber-700">Демо-режим (без ключа LLM)</div>
        ) : null}
      </div>
      <div ref={listRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto px-4 py-4 scrollbar-thin">
        {!messages.length && (
          <div className="rounded-xl bg-black/[.03] px-3 py-3 text-sm text-ink/55">
            Спросите про текущую задачу: «с чего начать?», «почему тест падает?»
          </div>
        )}
        {messages.map((m, idx) => (
          <div
            key={`${m.role}-${idx}`}
            className={`max-w-[92%] rounded-2xl px-3 py-2 text-sm whitespace-pre-wrap ${
              m.role === 'user'
                ? 'ml-auto bg-violet-600 text-white'
                : 'mr-auto bg-white ring-1 ring-black/[.06] text-ink/85'
            }`}
          >
            {m.content}
          </div>
        ))}
        {busy && <div className="text-xs text-ink/45">Думаю…</div>}
      </div>
      {error && (
        <div className="mx-4 mb-2 rounded-xl bg-red-50 px-3 py-2 text-xs text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}
      <div className="shrink-0 border-t border-black/[.06] p-3">
        <div className="flex gap-2">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            rows={2}
            placeholder="Вопрос по заданию…"
            className="min-h-[44px] flex-1 resize-none rounded-xl border border-black/[.08] bg-white px-3 py-2 text-sm outline-none focus:border-violet-400"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button
            type="button"
            disabled={busy || !draft.trim()}
            onClick={send}
            className="h-11 shrink-0 rounded-xl btn-grad px-4 text-sm font-semibold text-white disabled:opacity-40"
          >
            Спросить
          </button>
        </div>
      </div>
    </div>
  );
}

function LearnHelpDrawer({ open, onClose, navigate, courseTitle, moduleTitle, lessonType, lessonData }) {
  const [tab, setTab] = React.useState('mentor');
  const [mentorInfo, setMentorInfo] = React.useState(null);
  const [thread, setThread] = React.useState(null);
  const [loadError, setLoadError] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const ChatThreadView = window.ChatThreadView;
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null;

  const context = React.useMemo(() => ({
    course_title: courseTitle || '',
    module_title: moduleTitle || '',
    lesson_kind: lessonType || '',
    lesson_title: lessonData?.title || '',
    lesson_statement: lessonStatementFromData(lessonType, lessonData),
    lesson_public_id: lessonData?.public_id || '',
    user_code: typeof window !== 'undefined' ? (window.__learnAssistantCode || '') : '',
  }), [courseTitle, moduleTitle, lessonType, lessonData, open]);

  React.useEffect(() => {
    if (!open || !token) return undefined;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setLoadError('');
      try {
        const [mine, opened] = await Promise.all([
          window.fetchApiJson('/api/mentoring/my-mentor/', { auth: true }),
          window.fetchApiJson('/api/communication/chat/threads/open/?assigned=1', { auth: true }),
        ]);
        if (cancelled) return;
        setMentorInfo(mine);
        setThread(opened);
      } catch (e) {
        if (!cancelled) setLoadError(e.message || 'Не удалось открыть чат с ментором');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [open, token]);

  React.useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[70] flex justify-end">
      <button type="button" aria-label="Закрыть" className="absolute inset-0 bg-black/35" onClick={onClose} />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Помощь на уроке"
        className="relative z-10 flex h-full w-full max-w-md flex-col bg-paper shadow-glow ring-1 ring-black/[.06]"
      >
        <div className="flex items-center gap-2 border-b border-black/[.06] bg-white px-3 py-3">
          <div className="min-w-0 flex-1">
            <div className="text-sm font-bold">Помощь</div>
            <div className="truncate text-[11px] text-ink/45">
              {tab === 'mentor'
                ? mentorDisplayName(mentorInfo?.mentor)
                : 'ИИ по текущему заданию'}
            </div>
          </div>
          <button
            type="button"
            aria-label="Закрыть панель"
            onClick={onClose}
            className="grid h-9 w-9 place-items-center rounded-xl ring-1 ring-black/[.08]"
          >
            <I.X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex shrink-0 gap-1 border-b border-black/[.06] bg-white px-3 py-2">
          {[
            { id: 'mentor', label: 'Ментор' },
            { id: 'ai', label: 'ИИ-помощник' },
          ].map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setTab(item.id)}
              className={`h-9 flex-1 rounded-xl text-xs font-semibold transition-colors ${
                tab === item.id
                  ? 'bg-violet-600 text-white'
                  : 'bg-black/[.03] text-ink/65 hover:bg-black/[.06]'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div className="min-h-0 flex-1">
          {!token ? (
            <div className="p-6 text-center text-sm text-ink/60">
              Войдите, чтобы писать ментору или ИИ.
              <button
                type="button"
                className="mt-4 block w-full rounded-xl btn-grad py-2.5 text-sm font-semibold text-white"
                onClick={() => navigate?.(window.Routes.AUTH)}
              >
                Войти
              </button>
            </div>
          ) : tab === 'mentor' ? (
            loading ? (
              <div className="flex h-full items-center justify-center text-sm text-ink/45">Открываем чат…</div>
            ) : loadError ? (
              <div className="p-4 text-sm text-red-600">{loadError}</div>
            ) : thread && ChatThreadView ? (
              <ChatThreadView
                thread={thread}
                compact
                onBack={onClose}
                navigate={navigate}
                markReadOnView
              />
            ) : (
              <div className="p-4 text-sm text-ink/55">Диалог недоступен</div>
            )
          ) : (
            <LearnAssistantPane context={context} />
          )}
        </div>
      </aside>
    </div>
  );
}

function LearnHelpFab({ onOpen }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="fixed bottom-5 right-5 z-40 flex h-12 items-center gap-2 rounded-full btn-grad px-4 text-sm font-semibold text-white shadow-glow"
      aria-label="Открыть помощь: ментор и ИИ"
    >
      <I.Chat className="h-4 w-4" />
      Помощь
    </button>
  );
}

window.LearnHelpDrawer = LearnHelpDrawer;
window.LearnHelpFab = LearnHelpFab;
