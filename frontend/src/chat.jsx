// MESSAGES page — единый чат ментор ↔ студент

const Routes = window.Routes;
const I = window.I;

function chatParticipantName(user) {
  if (!user) return 'Участник';
  return [user.first_name, user.last_name].filter(Boolean).join(' ').trim()
    || user.email
    || 'Участник';
}

function formatChatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  if (sameDay) {
    return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  }
  return d.toLocaleString('ru-RU', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  });
}

function formatChatDateLabel(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === now.toDateString()) return 'Сегодня';
  if (d.toDateString() === yesterday.toDateString()) return 'Вчера';
  return d.toLocaleDateString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: d.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  });
}

function chatDateKey(iso) {
  if (!iso) return '';
  return new Date(iso).toDateString();
}

function messagePreview(message) {
  if (!message) return '';
  if (message.is_deleted) return 'Сообщение удалено';
  if (message.kind === 'system') return message.body || '';
  return (message.body || '').slice(0, 120);
}

function upsertChatMessage(prev, payload) {
  if (!payload?.public_id) return prev;
  const idx = prev.findIndex((m) => m.public_id === payload.public_id);
  if (idx >= 0) {
    const next = [...prev];
    next[idx] = payload;
    return next;
  }
  return [...prev, payload];
}

function ConferenceSystemBubble({ message, navigate, inCall, onOpenWhiteboard }) {
  const conf = message.conference;
  const canJoin = conf && (conf.status === 'waiting' || conf.status === 'active') && !inCall;
  const ended = conf?.status === 'completed';
  const dark = inCall;

  return (
    <div className="flex justify-center my-4 px-2">
      <div className={`max-w-md w-full rounded-2xl px-4 py-3 text-center ring-1 ${
        dark
          ? 'bg-white/[0.06] ring-white/10 text-white/85'
          : 'bg-violet-500/[0.06] ring-violet-500/15 text-ink/75'
      }`}>
        <div className="text-[11px] font-semibold uppercase tracking-widest opacity-60 mb-1">
          Созвон
        </div>
        <div className="text-sm font-medium">{message.body}</div>
        {ended && conf?.has_whiteboard && onOpenWhiteboard && (
          <button type="button" onClick={() => onOpenWhiteboard(conf.public_id)}
            className={`mt-3 h-9 px-4 rounded-lg text-xs font-semibold ${
              dark ? 'bg-white/10 hover:bg-white/15' : 'bg-white ring-1 ring-black/[0.08]'
            }`}>
            Конспект доски
          </button>
        )}
        {canJoin && navigate && (
          <button type="button"
            onClick={() => window.openConferenceCall(navigate, conf.public_id)}
            className="mt-3 h-9 px-4 rounded-lg btn-grad text-white text-xs font-semibold">
            Войти в созвон
          </button>
        )}
        <div className={`mt-2 text-[10px] ${dark ? 'text-white/45' : 'text-ink/40'}`}>
          {formatChatTime(message.created_at)}
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ message, mine, onEdit, onDelete, editing, onSaveEdit, onCancelEdit, editBusy, navigate, inCall, onOpenWhiteboard }) {
  const [editText, setEditText] = React.useState(message.body || '');
  const [menuOpen, setMenuOpen] = React.useState(false);
  const menuRef = React.useRef(null);

  React.useEffect(() => {
    if (editing) setEditText(message.body || '');
  }, [editing, message.body]);

  React.useEffect(() => {
    if (!menuOpen) return undefined;
    const onDoc = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [menuOpen]);

  if (message.kind === 'system') {
    return (
      <ConferenceSystemBubble
        message={message}
        navigate={navigate}
        inCall={inCall}
        onOpenWhiteboard={onOpenWhiteboard}
      />
    );
  }

  if (message.is_deleted) {
    return (
      <div className={`flex ${mine ? 'justify-end' : 'justify-start'} my-1.5`}>
        <div className={`max-w-[85%] sm:max-w-[70%] px-4 py-2.5 rounded-2xl text-sm italic text-ink/40 ${
          mine ? 'bg-violet-500/8' : 'bg-black/[0.04]'
        }`}>
          {mine ? 'Вы удалили сообщение' : 'Сообщение удалено'}
        </div>
      </div>
    );
  }

  if (editing) {
    return (
      <div className={`flex ${mine ? 'justify-end' : 'justify-start'} my-1.5`}>
        <div className="max-w-[85%] sm:max-w-[70%] w-full sm:w-auto space-y-2">
          <textarea
            value={editText}
            disabled={editBusy}
            onChange={(e) => setEditText(e.target.value)}
            rows={3}
            className="w-full px-4 py-3 rounded-xl ring-1 ring-violet-300 text-sm resize-y outline-none"
          />
          <div className="flex gap-2 justify-end">
            <button type="button" disabled={editBusy} onClick={onCancelEdit}
              className="h-9 px-3 rounded-lg bg-white ring-1 ring-black/[0.08] text-xs font-semibold">
              Отмена
            </button>
            <button type="button" disabled={editBusy || !editText.trim()} onClick={() => onSaveEdit(editText.trim())}
              className="h-9 px-3 rounded-lg btn-grad text-white text-xs font-semibold disabled:opacity-50">
              {editBusy ? '…' : 'Сохранить'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`group flex ${mine ? 'justify-end' : 'justify-start'} my-1.5`}>
      <div className={`relative max-w-[85%] sm:max-w-[70%] px-4 py-2.5 rounded-2xl text-sm whitespace-pre-wrap break-words ${
        mine
          ? 'bg-violet-600 text-white rounded-br-md'
          : 'bg-white ring-1 ring-black/[0.06] text-ink rounded-bl-md'
      }`}>
        {mine && (
          <div className="absolute -left-9 top-1 opacity-0 group-hover:opacity-100 transition-opacity" ref={menuRef}>
            <button type="button" onClick={() => setMenuOpen((v) => !v)}
              className="w-7 h-7 rounded-lg bg-white ring-1 ring-black/[0.08] text-ink/60 text-xs font-bold">
              ⋮
            </button>
            {menuOpen && (
              <div className="absolute right-0 mt-1 z-10 min-w-[120px] bg-white rounded-xl ring-1 ring-black/[0.08] shadow-soft py-1 text-left">
                <button type="button" onClick={() => { setMenuOpen(false); onEdit?.(); }}
                  className="w-full px-3 py-2 text-xs font-semibold text-left hover:bg-black/[0.03]">
                  Изменить
                </button>
                <button type="button" onClick={() => { setMenuOpen(false); onDelete?.(); }}
                  className="w-full px-3 py-2 text-xs font-semibold text-left text-red-600 hover:bg-red-50">
                  Удалить
                </button>
              </div>
            )}
          </div>
        )}
        <div>{message.body}</div>
        <div className={`mt-1 text-[10px] ${mine ? 'text-white/65' : 'text-ink/40'}`}>
          {formatChatTime(message.created_at)}
          {message.show_edited && message.edited_at ? ' · изменено' : ''}
        </div>
      </div>
    </div>
  );
}

function ChatComposer({ disabled, onSend, sending, embedded = false }) {
  const [text, setText] = React.useState('');
  const inputRef = React.useRef(null);

  const submit = async () => {
    const body = text.trim();
    if (!body || disabled || sending) return;
    setText('');
    await onSend(body);
    inputRef.current?.focus();
  };

  return (
    <div className={`border-t p-3 sm:p-4 ${embedded ? 'border-white/10 bg-[#0a1020]' : 'border-black/[0.06] bg-white'}`}>
      <div className="flex gap-2 items-end">
        <textarea
          ref={inputRef}
          rows={1}
          value={text}
          disabled={disabled || sending}
          placeholder="Напишите сообщение…"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          className={`flex-1 min-h-[44px] max-h-32 px-4 py-3 rounded-xl text-sm resize-y outline-none disabled:opacity-50 ${
            embedded
              ? 'bg-white/10 ring-1 ring-white/15 text-white placeholder:text-white/40 focus:ring-violet-400'
              : 'ring-1 ring-black/[0.08] focus:ring-violet-400'
          }`}
        />
        <button type="button" disabled={disabled || sending || !text.trim()} onClick={submit}
          className="h-11 px-5 rounded-xl btn-grad text-white text-sm font-semibold disabled:opacity-50 shrink-0">
          {sending ? '…' : 'Отправить'}
        </button>
      </div>
      {!embedded && (
      <div className="text-[11px] text-ink/40 mt-2">Enter — отправить, Shift+Enter — новая строка</div>
      )}
    </div>
  );
}

function ChatThreadView({
  thread,
  onBack,
  compact = false,
  embedded = false,
  inCall = false,
  navigate,
  onThreadActivity,
  onOpenWhiteboard,
  markReadOnView = true,
  onUnreadMessage,
  onMarkedRead,
}) {
  const [messages, setMessages] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [loadingMore, setLoadingMore] = React.useState(false);
  const [hasMore, setHasMore] = React.useState(false);
  const [error, setError] = React.useState('');
  const [sending, setSending] = React.useState(false);
  const [editBusy, setEditBusy] = React.useState(false);
  const [editingId, setEditingId] = React.useState(null);
  const [wsState, setWsState] = React.useState('connecting');
  const listRef = React.useRef(null);
  const stickToBottomRef = React.useRef(true);
  const onMarkedReadRef = React.useRef(onMarkedRead);
  const onThreadActivityRef = React.useRef(onThreadActivity);
  const onUnreadMessageRef = React.useRef(onUnreadMessage);
  const prevMarkReadRef = React.useRef(markReadOnView);
  const token = localStorage.getItem('access_token');
  const me = token ? window.parseJwtPayload(token) : null;
  const other = thread?.other_participant;

  React.useEffect(() => { onMarkedReadRef.current = onMarkedRead; }, [onMarkedRead]);
  React.useEffect(() => { onThreadActivityRef.current = onThreadActivity; }, [onThreadActivity]);
  React.useEffect(() => { onUnreadMessageRef.current = onUnreadMessage; }, [onUnreadMessage]);

  const notifyActivity = React.useCallback((message) => {
    onThreadActivityRef.current?.({
      threadId: thread?.public_id,
      preview: messagePreview(message),
      lastMessageAt: message?.created_at || new Date().toISOString(),
    });
  }, [thread?.public_id]);

  const scrollToBottom = React.useCallback((force = false) => {
    const el = listRef.current;
    if (!el) return;
    if (force || stickToBottomRef.current) {
      el.scrollTop = el.scrollHeight;
    }
  }, []);

  const handleListScroll = () => {
    const el = listRef.current;
    if (!el) return;
    stickToBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  const loadMessages = React.useCallback(async (before) => {
    if (!thread?.public_id) return;
    if (before) setLoadingMore(true);
    else setLoading(true);
    setError('');
    try {
      const path = `/api/communication/chat/threads/${encodeURIComponent(thread.public_id)}/messages/`;
      const readQs = markReadOnView ? '' : '&mark_read=0';
      const url = before
        ? `${path}?before=${encodeURIComponent(before)}&limit=50`
        : `${path}?limit=50${readQs}`;
      const data = await window.fetchApiJson(url, { auth: true });
      const rows = data.results || [];
      if (before) {
        setMessages((prev) => {
          const ids = new Set(prev.map((m) => m.public_id));
          return [...rows.filter((m) => !ids.has(m.public_id)), ...prev];
        });
      } else {
        setMessages(rows);
        if (markReadOnView) {
          onMarkedReadRef.current?.();
          window.refreshChatUnread?.();
        }
      }
      setHasMore(Boolean(data.has_more));
    } catch (e) {
      setError(e.message || 'Не удалось загрузить сообщения');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [thread?.public_id, markReadOnView]);

  React.useEffect(() => {
    if (!thread?.public_id) return undefined;
    setEditingId(null);
    stickToBottomRef.current = true;
    loadMessages();
  }, [thread?.public_id, markReadOnView, loadMessages]);

  React.useEffect(() => {
    if (!thread?.public_id) return undefined;
    const close = window.openChatThreadWs(thread.public_id, (data) => {
      if (data.event === 'connected') {
        setWsState('online');
        return;
      }
      const payload = data.payload;
      if (!payload?.public_id) return;
      if (data.event === 'message.new') {
        setMessages((prev) => upsertChatMessage(prev, payload));
        notifyActivity(payload);
        const fromOther = payload.sender?.public_id && payload.sender.public_id !== me?.public_id;
        if (fromOther && !markReadOnView) {
          onUnreadMessageRef.current?.(payload);
        } else {
          scrollToBottom();
        }
        return;
      }
      if (data.event === 'message.updated' || data.event === 'message.deleted') {
        setMessages((prev) => upsertChatMessage(prev, payload));
        notifyActivity(payload);
      }
    });
    setWsState('connecting');
    return () => {
      close?.();
      setWsState('offline');
    };
  }, [thread?.public_id, notifyActivity, scrollToBottom, markReadOnView, me?.public_id]);

  React.useEffect(() => {
    const openedHiddenChat = !prevMarkReadRef.current && markReadOnView;
    prevMarkReadRef.current = markReadOnView;
    if (!thread?.public_id || !openedHiddenChat) return undefined;
    let cancelled = false;
    (async () => {
      try {
        await window.fetchApiJson(
          `/api/communication/chat/threads/${encodeURIComponent(thread.public_id)}/read/`,
          { method: 'POST', auth: true },
        );
        if (!cancelled) {
          onMarkedReadRef.current?.();
          window.refreshChatUnread?.();
        }
      } catch (_) { /* ignore */ }
    })();
    return () => { cancelled = true; };
  }, [thread?.public_id, markReadOnView]);

  React.useEffect(() => {
    if (!loading) scrollToBottom(true);
  }, [thread?.public_id, loading, scrollToBottom]);

  const sendMessage = async (body) => {
    if (!thread?.public_id) return;
    setSending(true);
    setError('');
    try {
      const msg = await window.fetchApiJson(
        `/api/communication/chat/threads/${encodeURIComponent(thread.public_id)}/messages/`,
        { method: 'POST', body: { body }, auth: true },
      );
      setMessages((prev) => upsertChatMessage(prev, msg));
      notifyActivity(msg);
      scrollToBottom(true);
    } catch (e) {
      setError(e.message || 'Не удалось отправить');
    } finally {
      setSending(false);
    }
  };

  const saveEdit = async (messageId, body) => {
    setEditBusy(true);
    setError('');
    try {
      const msg = await window.fetchApiJson(
        `/api/communication/chat/messages/${encodeURIComponent(messageId)}/`,
        { method: 'PATCH', body: { body }, auth: true },
      );
      setMessages((prev) => upsertChatMessage(prev, msg));
      setEditingId(null);
      notifyActivity(msg);
    } catch (e) {
      setError(e.message || 'Не удалось сохранить');
    } finally {
      setEditBusy(false);
    }
  };

  const deleteMessage = async (messageId) => {
    if (!window.confirm('Удалить сообщение?')) return;
    setError('');
    try {
      const msg = await window.fetchApiJson(
        `/api/communication/chat/messages/${encodeURIComponent(messageId)}/`,
        { method: 'DELETE', auth: true },
      );
      setMessages((prev) => upsertChatMessage(prev, msg));
      notifyActivity(msg);
    } catch (e) {
      setError(e.message || 'Не удалось удалить');
    }
  };

  const loadOlder = () => {
    if (!hasMore || loadingMore || !messages.length) return;
    loadMessages(messages[0].created_at);
  };

  return (
    <div className={`flex flex-col min-h-0 ${
      compact || embedded ? 'h-full' : 'h-[min(72vh,720px)]'
    } ${embedded ? 'bg-[#0a1020]' : 'bg-paper'}`}>
      {!embedded && (
      <div className="px-4 sm:px-5 py-3 border-b border-black/[0.06] bg-white flex items-center gap-3 shrink-0">
        {onBack && (
          <button type="button" onClick={onBack}
            className="md:hidden w-10 h-10 rounded-xl ring-1 ring-black/[0.08] flex items-center justify-center">
            <I.ChevronRight className="w-5 h-5 rotate-180"/>
          </button>
        )}
        <div className="flex-1 min-w-0">
          <button type="button"
            onClick={() => other?.public_id && window.openStudentProfile?.(navigate, other.public_id)}
            className="font-bold truncate text-left hover:text-violet-600 transition-colors">
            {chatParticipantName(other)}
          </button>
          <div className="text-xs text-ink/45">
            {wsState === 'online' ? 'в сети' : wsState === 'connecting' ? 'подключение…' : 'офлайн'}
          </div>
        </div>
      </div>
      )}

      {embedded && (
        <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between shrink-0">
          <div>
            <div className="font-semibold text-white text-sm">{chatParticipantName(other)}</div>
            <div className="text-[11px] text-white/45">
              {wsState === 'online' ? 'чат · online' : 'чат'}
            </div>
          </div>
          {onBack && (
            <button type="button" onClick={onBack}
              className="w-9 h-9 rounded-lg bg-white/10 hover:bg-white/15 flex items-center justify-center text-white/80">
              <I.X className="w-4 h-4"/>
            </button>
          )}
        </div>
      )}

      <div ref={listRef} onScroll={handleListScroll}
        className={`flex-1 min-h-0 overflow-y-auto px-3 sm:px-4 py-4 scrollbar-thin ${embedded ? 'bg-[#070b18]' : ''}`}>
        {hasMore && (
          <div className="text-center mb-3">
            <button type="button" disabled={loadingMore} onClick={loadOlder}
              className="text-xs font-semibold text-violet-600 hover:underline disabled:opacity-50">
              {loadingMore ? 'Загрузка…' : 'Показать раньше'}
            </button>
          </div>
        )}
        {loading ? (
          <div className="py-16 text-center text-sm text-ink/50">Загрузка сообщений…</div>
        ) : messages.length === 0 ? (
          <div className="py-16 text-center text-sm text-ink/45">
            Пока нет сообщений. Напишите первым!
          </div>
        ) : (
          messages.map((msg, idx) => {
            const prev = messages[idx - 1];
            const showDate = !prev || chatDateKey(prev.created_at) !== chatDateKey(msg.created_at);
            return (
              <React.Fragment key={msg.public_id}>
                {showDate && (
                  <div className={`flex justify-center my-4 ${embedded ? 'text-white/45' : 'text-ink/40'}`}>
                    <span className={`text-[11px] font-semibold px-3 py-1 rounded-full ${
                      embedded ? 'bg-white/8' : 'bg-black/[0.04]'
                    }`}>
                      {formatChatDateLabel(msg.created_at)}
                    </span>
                  </div>
                )}
                <ChatBubble
                  message={msg}
                  mine={msg.sender?.public_id === me?.public_id}
                  editing={editingId === msg.public_id}
                  editBusy={editBusy}
                  onEdit={() => setEditingId(msg.public_id)}
                  onCancelEdit={() => setEditingId(null)}
                  onSaveEdit={(body) => saveEdit(msg.public_id, body)}
                  onDelete={() => deleteMessage(msg.public_id)}
                  navigate={navigate}
                  inCall={inCall}
                  onOpenWhiteboard={onOpenWhiteboard}
                />
              </React.Fragment>
            );
          })
        )}
      </div>

      {error && (
        <div className={`mx-4 mb-2 px-3 py-2 rounded-xl text-xs ring-1 ${
          embedded
            ? 'bg-red-500/15 text-red-200 ring-red-400/30'
            : 'bg-red-50 text-red-700 ring-red-200'
        }`}>
          {error}
        </div>
      )}

      <div className={embedded ? 'border-t border-white/10 bg-[#0a1020]' : ''}>
        <ChatComposer
          disabled={!thread}
          onSend={sendMessage}
          sending={sending}
          embedded={embedded}
        />
      </div>
    </div>
  );
}

function MessagesPage({ navigate, hashParams }) {
  const WhiteboardPreviewModal = window.WhiteboardPreviewModal;
  const [previewConfId, setPreviewConfId] = React.useState(null);
  const targetUser = hashParams?.get('user') || null;
  const targetCourse = hashParams?.get('course') || null;
  const [threads, setThreads] = React.useState([]);
  const [activeThread, setActiveThread] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [threadSearch, setThreadSearch] = React.useState('');
  const token = localStorage.getItem('access_token');

  const loadThreads = React.useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await window.fetchApiJson('/api/communication/chat/threads/', { auth: true });
      setThreads(Array.isArray(data) ? data : (data.results || []));
    } catch (e) {
      setError(e.message || 'Не удалось загрузить диалоги');
    } finally {
      setLoading(false);
    }
  }, []);

  const openTarget = React.useCallback(async () => {
    if (!targetUser && !targetCourse) return;
    setError('');
    try {
      const qs = targetUser
        ? `user=${encodeURIComponent(targetUser)}`
        : `course=${encodeURIComponent(targetCourse)}`;
      const thread = await window.fetchApiJson(
        `/api/communication/chat/threads/open/?${qs}`,
        { auth: true },
      );
      setActiveThread(thread);
      setThreads((prev) => {
        const rest = prev.filter((t) => t.public_id !== thread.public_id);
        return [thread, ...rest];
      });
    } catch (e) {
      setError(e.message || 'Не удалось открыть диалог');
    }
  }, [targetUser, targetCourse]);

  React.useEffect(() => {
    if (!token) return;
    loadThreads();
  }, [token, loadThreads]);

  React.useEffect(() => {
    if (!token) return;
    if (targetUser || targetCourse) {
      openTarget();
    }
  }, [token, targetUser, targetCourse, openTarget]);

  if (!token) {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Нужен вход</div>
        <button type="button" onClick={() => navigate(Routes.AUTH)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
          Войти
        </button>
      </div>
    );
  }

  const showThreadOnMobile = Boolean(activeThread);

  const handleThreadActivity = React.useCallback(({ threadId, preview, lastMessageAt }) => {
    setThreads((prev) => {
      const next = prev.map((t) => (
        t.public_id === threadId
          ? { ...t, last_message_preview: preview, last_message_at: lastMessageAt }
          : t
      ));
      next.sort((a, b) => {
        const ta = a.last_message_at ? new Date(a.last_message_at).getTime() : 0;
        const tb = b.last_message_at ? new Date(b.last_message_at).getTime() : 0;
        return tb - ta;
      });
      return next;
    });
    setActiveThread((prev) => (
      prev?.public_id === threadId
        ? { ...prev, last_message_preview: preview, last_message_at: lastMessageAt }
        : prev
    ));
    window.refreshChatUnread?.();
  }, []);

  const handleMarkedRead = React.useCallback((threadId) => {
    setThreads((prev) => prev.map((t) => (
      t.public_id === threadId ? { ...t, unread_count: 0 } : t
    )));
    setActiveThread((prev) => (
      prev?.public_id === threadId ? { ...prev, unread_count: 0 } : prev
    ));
  }, []);

  const onActiveThreadMarkedRead = React.useCallback(() => {
    if (activeThread?.public_id) handleMarkedRead(activeThread.public_id);
  }, [activeThread?.public_id, handleMarkedRead]);

  const filteredThreads = React.useMemo(() => {
    const q = threadSearch.trim().toLowerCase();
    if (!q) return threads;
    return threads.filter((thread) => (
      chatParticipantName(thread.other_participant).toLowerCase().includes(q)
      || (thread.last_message_preview || '').toLowerCase().includes(q)
    ));
  }, [threads, threadSearch]);

  return (
    <div data-screen-label="Messages" className="min-h-[calc(100dvh-4rem)] bg-paper">
      {previewConfId && WhiteboardPreviewModal && (
        <WhiteboardPreviewModal
          conferenceId={previewConfId}
          onClose={() => setPreviewConfId(null)}
        />
      )}
      <section className="mesh-bg border-b border-black/[0.04] py-8">
        <div className="max-w-5xl mx-auto px-5 sm:px-8">
          <h1 className="text-3xl font-extrabold tracking-tight">Сообщения</h1>
          <p className="text-sm text-ink/60 mt-2">Единый диалог с ментором или учеником</p>
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-5 sm:px-8 py-6">
        {error && (
          <div className="mb-4 p-4 rounded-xl bg-red-50 text-red-700 text-sm ring-1 ring-red-200">{error}</div>
        )}

        <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft overflow-hidden min-h-[min(72vh,720px)] grid md:grid-cols-[280px_minmax(0,1fr)]">
          <aside className={`border-r border-black/[0.06] ${showThreadOnMobile ? 'hidden md:block' : 'block'}`}>
            <div className="px-4 py-3 border-b border-black/[0.06]">
              <div className="font-bold text-sm mb-2">Диалоги</div>
              {threads.length > 0 && (
                <div className="flex items-center gap-2 px-2 h-9 rounded-lg ring-1 ring-black/[0.08] bg-black/[0.02]">
                  <I.Search className="w-3.5 h-3.5 text-ink/40 shrink-0" />
                  <input
                    type="search"
                    value={threadSearch}
                    onChange={(e) => setThreadSearch(e.target.value)}
                    placeholder="Поиск…"
                    className="flex-1 min-w-0 bg-transparent text-xs outline-none placeholder:text-ink/40"
                  />
                </div>
              )}
            </div>
            {loading ? (
              <div className="p-8 text-center text-sm text-ink/45">Загрузка…</div>
            ) : threads.length === 0 ? (
              <div className="p-8 text-center text-sm text-ink/45">Пока нет диалогов</div>
            ) : filteredThreads.length === 0 ? (
              <div className="p-8 text-center text-sm text-ink/45">Ничего не найдено</div>
            ) : (
              <ul className="divide-y divide-black/[0.05] max-h-[min(68vh,680px)] overflow-y-auto scrollbar-thin">
                {filteredThreads.map((thread) => {
                  const other = thread.other_participant;
                  const active = activeThread?.public_id === thread.public_id;
                  return (
                    <li key={thread.public_id}>
                      <button type="button" onClick={() => setActiveThread(thread)}
                        className={`w-full text-left px-4 py-3 hover:bg-black/[0.02] transition-colors ${
                          active ? 'bg-violet-500/8' : ''
                        }`}>
                        <div className="flex items-start justify-between gap-2">
                          <div className="font-semibold text-sm truncate">{chatParticipantName(other)}</div>
                          {(thread.unread_count || 0) > 0 && (
                            <span className="shrink-0 min-w-[1.25rem] h-5 px-1.5 rounded-full bg-violet-600 text-white text-[10px] font-bold flex items-center justify-center">
                              {thread.unread_count > 99 ? '99+' : thread.unread_count}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-ink/45 truncate mt-0.5">
                          {thread.last_message_preview || 'Нет сообщений'}
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </aside>

          <div className={`min-h-0 ${showThreadOnMobile ? 'block' : 'hidden md:block'}`}>
            {activeThread ? (
              <ChatThreadView
                thread={activeThread}
                onBack={() => setActiveThread(null)}
                onThreadActivity={handleThreadActivity}
                onMarkedRead={onActiveThreadMarkedRead}
                navigate={navigate}
                onOpenWhiteboard={(confId) => setPreviewConfId(confId)}
              />
            ) : (
              <div className="h-full min-h-[320px] flex items-center justify-center text-sm text-ink/45 p-8 text-center">
                Выберите диалог слева или откройте чат из профиля / панели ментора
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

window.MessagesPage = MessagesPage;
window.ChatThreadView = ChatThreadView;
