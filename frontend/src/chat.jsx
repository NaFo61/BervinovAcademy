// MESSAGES page — единый чат ментор ↔ студент
const Routes = window.Routes;
const I = window.I;
const CHAT_MAX_ALBUM = 10;

function chatParticipantName(user) {
  if (!user) return 'Участник';
  return [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || user.email || 'Участник';
}
function avatarUrl(user) { return user?.avatar ? (window.mediaUrl?.(user.avatar) || user.avatar) : ''; }
function initials(user) {
  return chatParticipantName(user).split(/\s+/).filter(Boolean).slice(0, 2).map((v) => v[0]).join('').toUpperCase() || '?';
}
function formatChatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso); const now = new Date();
  return d.toDateString() === now.toDateString()
    ? d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}
function formatRelativeListTime(iso) {
  if (!iso) return '';
  const d = new Date(iso); const now = new Date(); const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  if (d.toDateString() === yesterday.toDateString()) return 'вчера';
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: d.getFullYear() !== now.getFullYear() ? '2-digit' : undefined });
}
function formatChatDateLabel(iso) {
  if (!iso) return '';
  const d = new Date(iso); const now = new Date(); const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (d.toDateString() === now.toDateString()) return 'Сегодня';
  if (d.toDateString() === yesterday.toDateString()) return 'Вчера';
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: d.getFullYear() !== now.getFullYear() ? 'numeric' : undefined });
}
function chatDateKey(iso) { return iso ? new Date(iso).toDateString() : ''; }
function messagePreview(message) {
  if (!message) return '';
  if (message.is_deleted) return 'Сообщение удалено';
  if (message.kind === 'system') return message.body || '';
  if (message.kind === 'code') return 'Код (Python)';
  const media = messageAttachments(message);
  if (message.kind === 'album') return `${media.length > 1 ? `Альбом (${media.length})` : 'Альбом'}${message.body ? `: ${message.body.slice(0, 100)}` : ''}`;
  if (message.kind === 'image') return message.body ? `Фото: ${message.body.slice(0, 100)}` : 'Фото';
  if (message.kind === 'video') return message.body ? `Видео: ${message.body.slice(0, 100)}` : 'Видео';
  return (message.body || '').slice(0, 120);
}
function messageAttachments(message) {
  if (!message || message.is_deleted) return [];
  if (Array.isArray(message.attachments) && message.attachments.length) {
    return message.attachments.map((a) => ({ kind: a.kind || 'image', url: window.mediaUrl?.(a.url) || a.url || '', sort_order: a.sort_order ?? 0 }))
      .filter((a) => a.url).sort((a, b) => a.sort_order - b.sort_order);
  }
  const url = window.mediaUrl?.(message.attachment_url) || message.attachment_url || '';
  return url ? [{ kind: message.kind === 'video' ? 'video' : 'image', url, sort_order: 0 }] : [];
}
function isChatMessageMine(message, myId) {
  if (typeof message?.is_mine === 'boolean') return message.is_mine;
  return Boolean(myId && message?.sender?.public_id && String(message.sender.public_id) === String(myId));
}
function upsertChatMessage(prev, payload) {
  if (!payload?.public_id) return prev;
  const index = prev.findIndex((m) => m.public_id === payload.public_id);
  if (index < 0) return [...prev, payload];
  const next = [...prev]; next[index] = { ...next[index], ...payload }; return next;
}
function ChatAvatar({ user, size = 'md', className = '' }) {
  const pixels = size === 'sm' ? 'h-8 w-8 text-[10px]' : size === 'lg' ? 'h-11 w-11 text-sm' : 'h-9 w-9 text-xs';
  const src = avatarUrl(user);
  return src
    ? <img src={src} alt="" className={`${pixels} shrink-0 rounded-full object-cover bg-violet-100 ${className}`} />
    : <span aria-hidden="true" className={`${pixels} shrink-0 rounded-full bg-gradient-to-br from-violet-500 to-blue-500 text-white font-bold grid place-items-center ${className}`}>{initials(user)}</span>;
}
function EmptyState({ icon: Icon = I.Send, title, children, action }) {
  return <div className="mx-auto flex max-w-sm flex-col items-center px-6 py-14 text-center">
    <span className="mb-3 grid h-12 w-12 place-items-center rounded-2xl bg-violet-500/10 text-violet-600"><Icon className="h-5 w-5" /></span>
    <div className="font-bold text-ink">{title}</div>
    {children && <div className="mt-1 text-sm leading-relaxed text-ink/50">{children}</div>}
    {action}
  </div>;
}
function PythonCodeBlock({ code, navigate }) {
  const [copied, setCopied] = React.useState(false);
  const html = React.useMemo(() => {
    try { return window.Prism?.languages?.python ? window.Prism.highlight(code || '', window.Prism.languages.python, 'python') : null; } catch (_) { return null; }
  }, [code]);
  const copy = async () => {
    try { await navigator.clipboard.writeText(code || ''); setCopied(true); setTimeout(() => setCopied(false), 1400); } catch (_) { /* clipboard unavailable */ }
  };
  const openInterpreter = () => {
    if (window.openPlaygroundWithCode) window.openPlaygroundWithCode(navigate, code || '');
    else navigate?.(window.Routes.PLAYGROUND);
  };
  return <div className="space-y-1">
    <div className="flex items-center justify-between gap-2 text-[10px] font-bold uppercase tracking-widest text-violet-200">
      <span>Python</span>
      <span className="flex items-center gap-0.5">
        <button type="button" onClick={openInterpreter} aria-label="Открыть в интерпретаторе" className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 hover:bg-white/10 text-cyan-200">
          <I.Play className="h-3 w-3" />Интерпретатор
        </button>
        <button type="button" onClick={copy} aria-label="Скопировать код" className="inline-flex items-center gap-1 rounded-md px-1.5 py-1 hover:bg-white/10">
          <I.Copy className="h-3 w-3" />{copied ? 'Готово' : 'Копировать'}
        </button>
      </span>
    </div>
    <pre className="chat-code-block overflow-x-auto rounded-xl border border-violet-300/30 bg-slate-950/90 px-3 py-2.5 whitespace-pre language-python"><code className="language-python" {...(html ? { dangerouslySetInnerHTML: { __html: html } } : {})}>{html ? undefined : code}</code></pre>
  </div>;
}
function MediaLightbox({ item, onClose }) {
  React.useEffect(() => {
    const key = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', key); return () => document.removeEventListener('keydown', key);
  }, [onClose]);
  if (!item) return null;
  return <div role="dialog" aria-modal="true" aria-label={item.kind === 'video' ? 'Просмотр видео' : 'Просмотр изображения'} className="fixed inset-0 z-[90] grid place-items-center bg-slate-950/90 p-4" onMouseDown={onClose}>
    <button type="button" aria-label="Закрыть просмотр" onClick={onClose} className="absolute right-4 top-4 grid h-10 w-10 place-items-center rounded-xl bg-white/10 text-white hover:bg-white/20"><I.X className="h-5 w-5" /></button>
    <div className="max-h-full max-w-full" onMouseDown={(e) => e.stopPropagation()}>
      {item.kind === 'video' ? <video controls autoPlay src={item.url} className="max-h-[85dvh] max-w-[94vw] rounded-xl bg-black" /> : <img src={item.url} alt="Вложение сообщения" className="max-h-[85dvh] max-w-[94vw] rounded-xl object-contain" />}
    </div>
  </div>;
}
function AlbumGrid({ items, onOpen }) {
  if (!items.length) return null;
  const cols = items.length === 1 ? 'grid-cols-1' : items.length <= 4 ? 'grid-cols-2' : 'grid-cols-3';
  return <div className={`mb-2 -mx-1 grid overflow-hidden rounded-xl bg-black/10 ${cols} gap-1`}>
    {items.map((item, index) => <button type="button" key={`${item.url}-${index}`} onClick={() => onOpen(item)} aria-label={item.kind === 'video' ? 'Открыть видео' : 'Открыть изображение'} className={`group/media relative min-h-[104px] overflow-hidden bg-black focus:outline-none focus:ring-2 focus:ring-violet-300 ${items.length === 1 ? 'max-h-80' : 'aspect-square'}`}>
      {item.kind === 'video' ? <video preload="metadata" src={item.url} className="h-full w-full object-cover" /> : <img src={item.url} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-200 group-hover/media:scale-[1.03]" />}
      {item.kind === 'video' && <span className="absolute inset-0 grid place-items-center bg-black/20"><span className="grid h-10 w-10 place-items-center rounded-full bg-white/90 text-violet-700 shadow"><I.Play className="h-4 w-4" /></span></span>}
    </button>)}
  </div>;
}
function ReplyQuote({ reply, mine, onJumpTo }) {
  if (!reply) return null;
  return <button type="button" onClick={() => onJumpTo?.(reply.public_id)} className={`mb-2 w-full rounded-xl border-l-2 px-3 py-2 text-left text-xs transition hover:brightness-95 ${mine ? 'border-white/70 bg-white/15 text-white/90' : 'border-violet-500 bg-violet-50 text-ink/80'}`}>
    <div className="mb-0.5 font-semibold">{reply.sender ? chatParticipantName(reply.sender) : 'Сообщение'}</div>
    <div className="line-clamp-2 opacity-75">{reply.is_deleted ? 'Сообщение удалено' : (reply.body_preview || 'Вложение')}</div>
  </button>;
}
function ConferenceSystemBubble({ message, navigate, inCall, onOpenWhiteboard }) {
  const conf = message.conference; const canJoin = conf && ['waiting', 'active'].includes(conf.status) && !inCall;
  const dark = inCall;
  return <div className="my-4 flex justify-center px-2"><div className={`w-full max-w-md rounded-2xl px-4 py-3 text-center ring-1 ${dark ? 'bg-white/[.06] text-white/85 ring-white/10' : 'bg-violet-500/[.06] text-ink/75 ring-violet-500/15'}`}>
    <div className="mb-1 text-[11px] font-bold uppercase tracking-widest opacity-60">Созвон</div><div className="text-sm font-medium">{message.body}</div>
    {conf?.status === 'completed' && conf?.has_whiteboard && onOpenWhiteboard && <button type="button" onClick={() => onOpenWhiteboard(conf.public_id)} className={`mt-3 h-9 rounded-lg px-4 text-xs font-semibold ${dark ? 'bg-white/10' : 'bg-white ring-1 ring-black/[.08]'}`}>Конспект доски</button>}
    {canJoin && <button type="button" onClick={() => window.openConferenceCall(navigate, conf.public_id)} className="btn-grad mt-3 h-9 rounded-lg px-4 text-xs font-semibold text-white">Войти в созвон</button>}
    <div className={`mt-2 text-[10px] ${dark ? 'text-white/45' : 'text-ink/40'}`}>{formatChatTime(message.created_at)}</div>
  </div></div>;
}
function MessageMenu({ mine, message, onReply, onForward, onEdit, onDelete }) {
  const [open, setOpen] = React.useState(false); const ref = React.useRef(null);
  React.useEffect(() => {
    if (!open) return undefined;
    const close = (e) => { if (e.key === 'Escape' || (e.type === 'mousedown' && !ref.current?.contains(e.target))) setOpen(false); };
    document.addEventListener('keydown', close); document.addEventListener('mousedown', close);
    return () => { document.removeEventListener('keydown', close); document.removeEventListener('mousedown', close); };
  }, [open]);
  const action = (callback) => () => { setOpen(false); callback?.(message); };
  return <div ref={ref} className={`absolute top-1 z-10 opacity-100 transition-opacity md:opacity-0 md:group-hover:opacity-100 ${mine ? '-left-9' : '-right-9'}`}>
    <button type="button" aria-label="Открыть меню сообщения" aria-expanded={open} onClick={() => setOpen((v) => !v)} className="grid h-8 w-8 place-items-center rounded-lg bg-white text-ink/65 shadow-sm ring-1 ring-black/[.08]"><I.More className="h-4 w-4" /></button>
    {open && <div role="menu" className={`absolute mt-1 min-w-[140px] overflow-hidden rounded-xl bg-white py-1 text-left shadow-soft ring-1 ring-black/[.08] ${mine ? 'right-0' : 'left-0'}`}>
      <button type="button" role="menuitem" onClick={action(onReply)} className="w-full px-3 py-2 text-left text-xs font-semibold text-ink hover:bg-black/[.03]">Ответить</button>
      <button type="button" role="menuitem" onClick={action(onForward)} className="w-full px-3 py-2 text-left text-xs font-semibold text-ink hover:bg-black/[.03]">Переслать</button>
      {mine && ['text', 'code'].includes(message.kind) && <button type="button" role="menuitem" onClick={action(onEdit)} className="w-full px-3 py-2 text-left text-xs font-semibold text-ink hover:bg-black/[.03]">Изменить</button>}
      {mine && <button type="button" role="menuitem" onClick={action(onDelete)} className="w-full px-3 py-2 text-left text-xs font-semibold text-red-600 hover:bg-red-50">Удалить</button>}
    </div>}
  </div>;
}
function ChatBubble({ message, mine, editing, editBusy, onEdit, onDelete, onReply, onForward, onSaveEdit, onCancelEdit, onJumpTo, navigate, inCall, onOpenWhiteboard }) {
  const [editText, setEditText] = React.useState(message.body || ''); const [lightbox, setLightbox] = React.useState(null);
  React.useEffect(() => { if (editing) setEditText(message.body || ''); }, [editing, message.body]);
  if (message.kind === 'system') return <ConferenceSystemBubble message={message} navigate={navigate} inCall={inCall} onOpenWhiteboard={onOpenWhiteboard} />;
  if (message.is_deleted) return <div data-msg-id={message.public_id} className={`my-1.5 flex ${mine ? 'justify-end' : 'justify-start'}`}><div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm italic text-ink/40 ${mine ? 'bg-violet-500/8' : 'bg-black/[.04]'}`}>{mine ? 'Вы удалили сообщение' : 'Сообщение удалено'}</div></div>;
  if (editing) return <div className={`my-1.5 flex ${mine ? 'justify-end' : 'justify-start'}`}><div className="w-full max-w-[85%] space-y-2 sm:max-w-[70%]"><textarea value={editText} disabled={editBusy} onChange={(e) => setEditText(e.target.value)} rows={message.kind === 'code' ? 8 : 3} className={`w-full resize-y rounded-xl px-4 py-3 text-sm outline-none ring-1 ring-violet-300 ${message.kind === 'code' ? 'font-mono text-xs' : ''}`} /><div className="flex justify-end gap-2"><button type="button" onClick={onCancelEdit} className="h-9 rounded-lg bg-white px-3 text-xs font-semibold ring-1 ring-black/[.08]">Отмена</button><button type="button" disabled={editBusy || !editText.trim()} onClick={() => onSaveEdit(editText.trim())} className="btn-grad h-9 rounded-lg px-3 text-xs font-semibold text-white disabled:opacity-50">{editBusy ? '…' : 'Сохранить'}</button></div></div></div>;
  const media = messageAttachments(message); const source = message.forwarded_from;
  const sourceName = source?.sender ? chatParticipantName(source.sender) : source?.first_name || source?.name || source?.email || '';
  return <><div data-msg-id={message.public_id} className={`group my-1.5 flex scroll-mt-6 transition duration-300 ${mine ? 'justify-end' : 'justify-start'} ${message.pending ? 'opacity-60' : ''}`}><div className={`relative max-w-[85%] break-words rounded-2xl px-4 py-2.5 text-sm sm:max-w-[70%] ${mine ? 'rounded-br-md bg-violet-600/95 text-white shadow-sm' : 'rounded-bl-md bg-white text-ink ring-1 ring-black/[.06]'}`}>
    <MessageMenu mine={mine} message={message} onReply={onReply} onForward={onForward} onEdit={onEdit} onDelete={onDelete} />
    {source && <div className={`mb-1 text-[10px] font-bold uppercase tracking-wide ${mine ? 'text-white/70' : 'text-ink/45'}`}>Переслано{sourceName ? ` от ${sourceName}` : ''}</div>}
    <ReplyQuote reply={message.reply_to} mine={mine} onJumpTo={onJumpTo} />
    {media.length > 0 && <AlbumGrid items={media} onOpen={setLightbox} />}
    {message.kind === 'code' ? <PythonCodeBlock code={message.body} navigate={navigate} /> : message.body && <div className="whitespace-pre-wrap">{message.body}</div>}
    <div className={`mt-1 text-[10px] ${mine ? 'text-white/65' : 'text-ink/40'}`}>{message.pending ? 'Отправка…' : formatChatTime(message.created_at)}{message.show_edited && message.edited_at ? ' · изменено' : ''}</div>
  </div></div>{lightbox && <MediaLightbox item={lightbox} onClose={() => setLightbox(null)} />}</>;
}
function ChatComposer({ disabled, onSend, sending, embedded = false, replyTo, onCancelReply }) {
  const [text, setText] = React.useState(''); const [mode, setMode] = React.useState('text'); const [files, setFiles] = React.useState([]);
  const fileRef = React.useRef(null); const inputRef = React.useRef(null);
  const previews = React.useMemo(() => files.map((f) => ({ file: f, url: URL.createObjectURL(f) })), [files]);
  React.useEffect(() => () => previews.forEach((p) => URL.revokeObjectURL(p.url)), [previews]);
  const addFiles = (list) => { const valid = Array.from(list || []).filter((f) => /^(image|video)\//.test(f.type)); if (valid.length) { setFiles((old) => [...old, ...valid].slice(0, CHAT_MAX_ALBUM)); setMode('text'); } };
  const submit = async () => {
    const body = text.trim(); if (disabled || sending || (!body && !files.length)) return;
    try { await onSend({ kind: mode === 'code' ? 'code' : 'text', body, files, reply_to: replyTo?.public_id || null }); setText(''); setFiles([]); onCancelReply?.(); inputRef.current?.focus(); } catch (_) { /* error shown by thread */ }
  };
  const control = embedded ? 'bg-white/10 text-white ring-1 ring-white/15 hover:bg-white/15' : 'bg-white text-ink/70 ring-1 ring-black/[.08] hover:bg-black/[.03]';
  return <div className={`border-t px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 sm:px-4 sm:pb-4 ${embedded ? 'border-white/10 bg-[#0a1020]' : 'border-black/[.06] bg-white'}`}>
    {replyTo && <div className={`mb-2 flex items-start gap-2 rounded-xl px-3 py-2 text-xs ${embedded ? 'bg-white/8 text-white/85' : 'bg-violet-500/[.08] text-ink/80'}`}><div className="min-w-0 flex-1"><b>Ответ · {chatParticipantName(replyTo.sender)}</b><div className="truncate opacity-70">{replyTo.body_preview || messagePreview(replyTo)}</div></div><button type="button" aria-label="Отменить ответ" onClick={onCancelReply} className="grid h-7 w-7 place-items-center rounded-lg bg-black/5"><I.X className="h-4 w-4" /></button></div>}
    {files.length > 0 && <div className={`mb-2 rounded-xl p-2 ${embedded ? 'bg-white/8' : 'bg-black/[.03]'}`}><div className="mb-2 flex justify-between text-xs font-semibold"><span>{files.length === 1 ? 'Вложение' : `Альбом · ${files.length}`}</span><button type="button" onClick={() => setFiles([])} className="text-violet-600">Очистить</button></div><div className="flex gap-2 overflow-x-auto">{previews.map(({ file, url }, index) => <div key={`${file.name}-${index}`} className="relative shrink-0">{file.type.startsWith('image/') ? <img src={url} alt="" className="h-16 w-16 rounded-lg object-cover" /> : <div className="grid h-16 w-16 place-items-center rounded-lg bg-slate-900 text-white"><I.Play className="h-4 w-4" /></div>}<button type="button" aria-label={`Удалить файл ${file.name}`} onClick={() => setFiles((all) => all.filter((_, i) => i !== index))} className="absolute -right-1 -top-1 grid h-5 w-5 place-items-center rounded-full bg-black/75 text-white"><I.X className="h-3 w-3" /></button></div>)}</div></div>}
    <div className="flex items-end gap-2"><input ref={fileRef} type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/webm,video/quicktime" className="hidden" onChange={(e) => { addFiles(e.target.files); e.target.value = ''; }} />
      <button type="button" aria-label="Прикрепить фото или видео" title="Прикрепить фото или видео" disabled={disabled || sending || files.length >= CHAT_MAX_ALBUM} onClick={() => fileRef.current?.click()} className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl disabled:opacity-50 ${control}`}><I.Paperclip className="h-4 w-4" /></button>
      <button type="button" aria-label="Включить режим Python-кода" title="Python-код" disabled={disabled || sending || files.length > 0} onClick={() => setMode((v) => v === 'code' ? 'text' : 'code')} className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl disabled:opacity-50 ${mode === 'code' ? 'btn-grad text-white' : control}`}><I.Code className="h-4 w-4" /></button>
      <textarea ref={inputRef} rows={mode === 'code' ? 5 : 1} value={text} disabled={disabled || sending} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && mode !== 'code') { e.preventDefault(); submit(); } }} onPaste={(e) => { const pasted = Array.from(e.clipboardData?.items || []).filter((v) => v.type.startsWith('image/')).map((v) => v.getAsFile()).filter(Boolean); if (pasted.length) { e.preventDefault(); addFiles(pasted); } }} placeholder={files.length ? 'Подпись к альбому (необязательно)…' : mode === 'code' ? 'Вставьте Python-код…' : 'Напишите сообщение…'} className={`min-h-[44px] max-h-48 min-w-0 flex-1 resize-y rounded-xl px-3 py-3 text-sm outline-none disabled:opacity-50 ${mode === 'code' ? 'font-mono text-xs' : ''} ${embedded ? 'bg-white/10 text-white placeholder:text-white/40 ring-1 ring-white/15 focus:ring-violet-400' : 'ring-1 ring-black/[.08] focus:ring-violet-400'}`} />
      <button type="button" aria-label="Отправить сообщение" title="Отправить" disabled={disabled || sending || (!text.trim() && !files.length)} onClick={submit} className="btn-grad grid h-11 w-11 shrink-0 place-items-center rounded-xl text-white disabled:opacity-50">{sending ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : <I.Send className="h-4 w-4" />}</button>
    </div>{mode === 'code' && <div className={`mt-1.5 text-[11px] ${embedded ? 'text-violet-200/70' : 'text-ink/45'}`}>Python · Enter добавляет новую строку</div>}
  </div>;
}
function ForwardModal({ open, threads, currentThreadId, onClose, onPick, busy }) {
  const dialogRef = React.useRef(null);
  React.useEffect(() => {
    if (!open) return undefined; const previous = document.activeElement; const timer = setTimeout(() => dialogRef.current?.focus(), 0);
    const keys = (e) => { if (e.key === 'Escape') onClose(); if (e.key === 'Tab') { const nodes = dialogRef.current?.querySelectorAll('button:not([disabled])'); if (!nodes?.length) return; const first = nodes[0]; const last = nodes[nodes.length - 1]; if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); } } };
    document.addEventListener('keydown', keys); return () => { clearTimeout(timer); document.removeEventListener('keydown', keys); previous?.focus?.(); };
  }, [open, onClose]);
  if (!open) return null; const options = threads.filter((t) => t.public_id !== currentThreadId);
  return <div className="fixed inset-0 z-[80] flex items-end justify-center bg-black/40 sm:items-center sm:p-4" onMouseDown={onClose}><div ref={dialogRef} tabIndex="-1" role="dialog" aria-modal="true" aria-label="Переслать в диалог" onMouseDown={(e) => e.stopPropagation()} className="max-h-[85dvh] w-full max-w-md rounded-t-2xl bg-white shadow-soft outline-none sm:rounded-2xl"><div className="flex items-center justify-between border-b border-black/[.06] px-4 py-3"><b>Переслать в диалог</b><button type="button" aria-label="Закрыть" onClick={onClose} className="grid h-8 w-8 place-items-center rounded-lg ring-1 ring-black/[.08]"><I.X className="h-4 w-4" /></button></div><div className="max-h-[65dvh] overflow-y-auto p-2">{options.length ? options.map((t) => <button key={t.public_id} type="button" disabled={busy} onClick={() => onPick(t)} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left hover:bg-black/[.03] disabled:opacity-50"><ChatAvatar user={t.other_participant} size="sm" /><span className="min-w-0"><b className="block truncate text-sm">{chatParticipantName(t.other_participant)}</b><span className="block truncate text-xs text-ink/45">{t.last_message_preview || 'Нет сообщений'}</span></span></button>) : <EmptyState title="Нет других диалогов">Сначала откройте ещё один чат.</EmptyState>}</div></div></div>;
}
function ChatThreadView({ thread, onBack, compact = false, embedded = false, inCall = false, navigate, onThreadActivity, onOpenWhiteboard, markReadOnView = true, onUnreadMessage, onMarkedRead, threads = [] }) {
  const [messages, setMessages] = React.useState([]); const [loading, setLoading] = React.useState(true); const [loadingMore, setLoadingMore] = React.useState(false); const [hasMore, setHasMore] = React.useState(false); const [error, setError] = React.useState(''); const [sending, setSending] = React.useState(false); const [editBusy, setEditBusy] = React.useState(false); const [editingId, setEditingId] = React.useState(null); const [replyTo, setReplyTo] = React.useState(null); const [forwardMsg, setForwardMsg] = React.useState(null); const [forwardBusy, setForwardBusy] = React.useState(false); const [wsState, setWsState] = React.useState('connecting');
  const listRef = React.useRef(null); const stickRef = React.useRef(true); const markedRef = React.useRef(onMarkedRead); const activityRef = React.useRef(onThreadActivity); const unreadRef = React.useRef(onUnreadMessage); const previousMarkRef = React.useRef(markReadOnView);
  const token = localStorage.getItem('access_token'); const myId = window.currentUserPublicId ? window.currentUserPublicId(token) : String((token ? window.parseJwtPayload(token) : {})?.public_id || (token ? window.parseJwtPayload(token) : {})?.user_id || ''); const other = thread?.other_participant;
  React.useEffect(() => { markedRef.current = onMarkedRead; activityRef.current = onThreadActivity; unreadRef.current = onUnreadMessage; }, [onMarkedRead, onThreadActivity, onUnreadMessage]);
  const notifyActivity = React.useCallback((message) => activityRef.current?.({ threadId: thread?.public_id, preview: messagePreview(message), lastMessageAt: message?.created_at || new Date().toISOString() }), [thread?.public_id]);
  const scrollToBottom = React.useCallback((force = false) => { const node = listRef.current; if (node && (force || stickRef.current)) node.scrollTop = node.scrollHeight; }, []);
  const jumpTo = React.useCallback((id) => { const node = listRef.current?.querySelector(`[data-msg-id="${id}"]`); if (!node) return; node.scrollIntoView({ behavior: 'smooth', block: 'center' }); node.classList.add('ring-2', 'ring-violet-400', 'ring-offset-2'); setTimeout(() => node.classList.remove('ring-2', 'ring-violet-400', 'ring-offset-2'), 1250); }, []);
  const loadMessages = React.useCallback(async (before) => {
    if (!thread?.public_id) return; before ? setLoadingMore(true) : setLoading(true); setError('');
    try { const path = `/api/communication/chat/threads/${encodeURIComponent(thread.public_id)}/messages/`; const data = await window.fetchApiJson(before ? `${path}?before=${encodeURIComponent(before)}&limit=50` : `${path}?limit=50${markReadOnView ? '' : '&mark_read=0'}`, { auth: true }); const rows = data.results || [];
      if (before) setMessages((old) => [...rows.filter((m) => !old.some((p) => p.public_id === m.public_id)), ...old]); else { setMessages(rows); if (markReadOnView) { markedRef.current?.(); window.refreshChatUnread?.(); } } setHasMore(Boolean(data.has_more));
    } catch (e) { setError(e.message || 'Не удалось загрузить сообщения'); } finally { setLoading(false); setLoadingMore(false); }
  }, [thread?.public_id, markReadOnView]);
  React.useEffect(() => { if (thread?.public_id) { setEditingId(null); setReplyTo(null); stickRef.current = true; loadMessages(); } }, [thread?.public_id, loadMessages]);
  React.useEffect(() => {
    if (!thread?.public_id) return undefined; setWsState('connecting');
    const close = window.openChatThreadWs(thread.public_id, (data) => { if (data.event === 'connected') { setWsState('online'); return; } const payload = data.payload; if (!payload?.public_id) return;
      if (data.event === 'message.new') {
        setMessages((old) => {
          let next = old;
          if (isChatMessageMine(payload, myId)) {
            next = old.filter((m) => !String(m.public_id).startsWith('temp-'));
          }
          return upsertChatMessage(next, payload);
        });
        notifyActivity(payload);
        if (!isChatMessageMine(payload, myId) && !markReadOnView) unreadRef.current?.(payload);
        else scrollToBottom();
      }
      if (data.event === 'message.updated' || data.event === 'message.deleted') { setMessages((old) => upsertChatMessage(old, payload)); notifyActivity(payload); }
    });
    return () => { close?.(); setWsState('offline'); };
  }, [thread?.public_id, myId, markReadOnView, notifyActivity, scrollToBottom]);
  React.useEffect(() => { const opened = !previousMarkRef.current && markReadOnView; previousMarkRef.current = markReadOnView; if (!thread?.public_id || !opened) return undefined; let cancelled = false; (async () => { try { await window.fetchApiJson(`/api/communication/chat/threads/${encodeURIComponent(thread.public_id)}/read/`, { method: 'POST', auth: true }); if (!cancelled) { markedRef.current?.(); window.refreshChatUnread?.(); } } catch (_) { /* ignore */ } })(); return () => { cancelled = true; }; }, [thread?.public_id, markReadOnView]);
  React.useEffect(() => { if (!loading) scrollToBottom(true); }, [loading, thread?.public_id, scrollToBottom]);
  const sendMessage = async (payload) => {
    if (!thread?.public_id) return; setSending(true); setError(''); const files = payload.files || []; const tempId = `temp-${Date.now()}-${Math.random()}`; const isOptimistic = !files.length;
    const temp = { public_id: tempId, kind: payload.kind || 'text', body: payload.body, reply_to: replyTo, sender: { public_id: myId }, is_mine: true, created_at: new Date().toISOString(), pending: true };
    if (isOptimistic) { setMessages((old) => [...old, temp]); scrollToBottom(true); }
    try { let message; if (files.length) { const form = new FormData(); files.forEach((file) => form.append('files', file)); if (payload.body) form.append('body', payload.body); if (payload.reply_to) form.append('reply_to', payload.reply_to); message = await window.fetchApiForm(`/api/communication/chat/threads/${encodeURIComponent(thread.public_id)}/messages/`, form, { method: 'POST', auth: true }); } else { const body = { kind: payload.kind || 'text', body: payload.body }; if (payload.reply_to) body.reply_to = payload.reply_to; message = await window.fetchApiJson(`/api/communication/chat/threads/${encodeURIComponent(thread.public_id)}/messages/`, { method: 'POST', body, auth: true }); }
      setMessages((old) => { const withoutTemp = old.filter((m) => m.public_id !== tempId); return upsertChatMessage(withoutTemp, message); }); notifyActivity(message); scrollToBottom(true);
    } catch (e) { if (isOptimistic) setMessages((old) => old.filter((m) => m.public_id !== tempId)); setError(e.message || 'Не удалось отправить'); throw e; } finally { setSending(false); }
  };
  const saveEdit = async (id, body) => { setEditBusy(true); setError(''); try { const msg = await window.fetchApiJson(`/api/communication/chat/messages/${encodeURIComponent(id)}/`, { method: 'PATCH', body: { body }, auth: true }); setMessages((old) => upsertChatMessage(old, msg)); setEditingId(null); notifyActivity(msg); } catch (e) { setError(e.message || 'Не удалось сохранить'); } finally { setEditBusy(false); } };
  const deleteMessage = async (id) => { if (!window.confirm('Удалить сообщение? Это действие нельзя отменить.')) return; setError(''); try { const msg = await window.fetchApiJson(`/api/communication/chat/messages/${encodeURIComponent(id)}/`, { method: 'DELETE', auth: true }); setMessages((old) => upsertChatMessage(old, msg)); notifyActivity(msg); } catch (e) { setError(e.message || 'Не удалось удалить'); } };
  const forwardTo = async (target) => { if (!forwardMsg?.public_id || !target?.public_id) return; setForwardBusy(true); try { await window.fetchApiJson(`/api/communication/chat/messages/${encodeURIComponent(forwardMsg.public_id)}/forward/`, { method: 'POST', body: { thread: target.public_id }, auth: true }); setForwardMsg(null); notifyActivity({ created_at: new Date().toISOString() }); } catch (e) { setError(e.message || 'Не удалось переслать'); } finally { setForwardBusy(false); } };
  const status = wsState === 'online' ? 'подключено' : wsState === 'connecting' ? 'подключение…' : 'нет связи';
  return <div className={`flex min-h-0 flex-col ${compact || embedded ? 'h-full' : 'h-[min(72vh,760px)]'} ${embedded ? 'bg-[#0a1020]' : 'bg-paper'}`}>
    <div className={`flex shrink-0 items-center gap-3 border-b px-4 py-3 ${embedded ? 'border-white/10 text-white' : 'border-black/[.06] bg-white'}`}>{onBack && <button type="button" aria-label={embedded ? 'Закрыть чат' : 'К списку диалогов'} onClick={onBack} className={`grid h-9 w-9 place-items-center rounded-xl ${embedded ? 'bg-white/10' : 'md:hidden ring-1 ring-black/[.08]'}`}>{embedded ? <I.X className="h-4 w-4" /> : <I.ChevronRight className="h-5 w-5 rotate-180" />}</button>}<ChatAvatar user={other} size="sm" /><div className="min-w-0 flex-1"><button type="button" onClick={() => other?.public_id && window.openStudentProfile?.(navigate, other.public_id)} className="block max-w-full truncate text-left text-sm font-bold hover:text-violet-600">{chatParticipantName(other)}</button><div className={`text-[11px] ${embedded ? 'text-white/45' : 'text-ink/45'}`}>{status}</div></div></div>
    <div ref={listRef} onScroll={() => { const node = listRef.current; if (node) stickRef.current = node.scrollHeight - node.scrollTop - node.clientHeight < 80; }} className={`min-h-0 flex-1 overflow-y-auto px-3 py-4 scrollbar-thin sm:px-4 ${embedded ? 'bg-[#070b18]' : ''}`}>{hasMore && <div className="mb-3 text-center"><button type="button" disabled={loadingMore} onClick={() => messages.length && loadMessages(messages[0].created_at)} className="text-xs font-semibold text-violet-600 hover:underline">{loadingMore ? 'Загрузка…' : 'Показать раньше'}</button></div>}
      {loading ? <div className={`py-16 text-center text-sm ${embedded ? 'text-white/45' : 'text-ink/45'}`}>Загрузка сообщений…</div> : !messages.length ? <EmptyState icon={I.Send} title="Пока нет сообщений">Начните разговор — собеседник увидит его сразу.</EmptyState> : messages.map((msg, index) => <React.Fragment key={msg.public_id}>{(!index || chatDateKey(messages[index - 1].created_at) !== chatDateKey(msg.created_at)) && <div className={`my-4 flex justify-center ${embedded ? 'text-white/45' : 'text-ink/40'}`}><span className={`rounded-full px-3 py-1 text-[11px] font-semibold ${embedded ? 'bg-white/8' : 'bg-black/[.04]'}`}>{formatChatDateLabel(msg.created_at)}</span></div>}<ChatBubble message={msg} mine={isChatMessageMine(msg, myId)} editing={editingId === msg.public_id} editBusy={editBusy} onEdit={() => setEditingId(msg.public_id)} onDelete={() => deleteMessage(msg.public_id)} onReply={(m) => setReplyTo({ public_id: m.public_id, sender: m.sender, body_preview: messagePreview(m), kind: m.kind })} onForward={setForwardMsg} onSaveEdit={(body) => saveEdit(msg.public_id, body)} onCancelEdit={() => setEditingId(null)} onJumpTo={jumpTo} navigate={navigate} inCall={inCall} onOpenWhiteboard={onOpenWhiteboard} /></React.Fragment>)}</div>
    {error && <div className={`mx-4 mb-2 rounded-xl px-3 py-2 text-xs ring-1 ${embedded ? 'bg-red-500/15 text-red-200 ring-red-400/30' : 'bg-red-50 text-red-700 ring-red-200'}`}>{error}</div>}
    <ChatComposer disabled={!thread} onSend={sendMessage} sending={sending} embedded={embedded} replyTo={replyTo} onCancelReply={() => setReplyTo(null)} />
    <ForwardModal open={!!forwardMsg} threads={threads} currentThreadId={thread?.public_id} busy={forwardBusy} onClose={() => setForwardMsg(null)} onPick={forwardTo} />
  </div>;
}
function MessagesPage({ navigate, hashParams }) {
  const WhiteboardPreviewModal = window.WhiteboardPreviewModal; const [previewConfId, setPreviewConfId] = React.useState(null); const [threads, setThreads] = React.useState([]); const [activeThread, setActiveThread] = React.useState(null); const [loading, setLoading] = React.useState(true); const [error, setError] = React.useState(''); const [threadSearch, setThreadSearch] = React.useState('');
  const targetUser = hashParams?.get('user') || null; const targetCourse = hashParams?.get('course') || null; const token = localStorage.getItem('access_token');
  const loadThreads = React.useCallback(async () => { setLoading(true); setError(''); try { const data = await window.fetchApiJson('/api/communication/chat/threads/', { auth: true }); setThreads(Array.isArray(data) ? data : data.results || []); } catch (e) { setError(e.message || 'Не удалось загрузить диалоги'); } finally { setLoading(false); } }, []);
  const openTarget = React.useCallback(async () => { if (!targetUser && !targetCourse) return; setError(''); try { const qs = targetUser ? `user=${encodeURIComponent(targetUser)}` : `course=${encodeURIComponent(targetCourse)}`; const thread = await window.fetchApiJson(`/api/communication/chat/threads/open/?${qs}`, { auth: true }); setActiveThread(thread); setThreads((old) => [thread, ...old.filter((t) => t.public_id !== thread.public_id)]); } catch (e) { setError(e.message || 'Не удалось открыть диалог'); } }, [targetUser, targetCourse]);
  React.useEffect(() => { if (token) loadThreads(); }, [token, loadThreads]); React.useEffect(() => { if (token && (targetUser || targetCourse)) openTarget(); }, [token, targetUser, targetCourse, openTarget]);
  const activity = React.useCallback(({ threadId, preview, lastMessageAt }) => { setThreads((old) => { const next = old.map((t) => t.public_id === threadId ? { ...t, last_message_preview: preview, last_message_at: lastMessageAt } : t); return next.sort((a, b) => new Date(b.last_message_at || 0) - new Date(a.last_message_at || 0)); }); setActiveThread((old) => old?.public_id === threadId ? { ...old, last_message_preview: preview, last_message_at: lastMessageAt } : old); window.refreshChatUnread?.(); }, []);
  const markRead = React.useCallback((id) => { setThreads((old) => old.map((t) => t.public_id === id ? { ...t, unread_count: 0 } : t)); setActiveThread((old) => old?.public_id === id ? { ...old, unread_count: 0 } : old); }, []);
  const filtered = React.useMemo(() => { const q = threadSearch.trim().toLowerCase(); return q ? threads.filter((t) => chatParticipantName(t.other_participant).toLowerCase().includes(q) || (t.last_message_preview || '').toLowerCase().includes(q)) : threads; }, [threads, threadSearch]);
  if (!token) return <div className="mx-auto max-w-md px-5 py-20 text-center"><div className="text-2xl font-bold">Нужен вход</div><button type="button" onClick={() => navigate(Routes.AUTH)} className="btn-grad mt-6 h-11 rounded-xl px-6 text-sm font-semibold text-white">Войти</button></div>;
  const onMobileThread = Boolean(activeThread);
  return <div data-screen-label="Messages" className="min-h-[calc(100dvh-4rem)] bg-paper">{previewConfId && WhiteboardPreviewModal && <WhiteboardPreviewModal conferenceId={previewConfId} onClose={() => setPreviewConfId(null)} />}
    <header className="border-b border-black/[.04] bg-white py-3 sm:py-5"><div className="mx-auto flex max-w-6xl items-baseline justify-between px-4 sm:px-8"><div><h1 className="text-xl font-extrabold tracking-tight sm:text-2xl">Сообщения</h1><p className="hidden text-sm text-ink/55 sm:block">Диалоги с ментором и учениками</p></div></div></header>
    <main className="mx-auto max-w-6xl px-0 py-0 sm:px-5 sm:py-5">{error && <div className="mx-4 mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200 sm:mx-0">{error}</div>}<div className="grid min-h-[calc(100dvh-4rem)] overflow-hidden bg-white sm:min-h-[min(76vh,780px)] sm:rounded-2xl sm:shadow-soft sm:ring-1 sm:ring-black/[.04] md:grid-cols-[300px_minmax(0,1fr)]">
      <aside className={`border-r border-black/[.06] ${onMobileThread ? 'hidden md:block' : 'block'}`}><div className="border-b border-black/[.06] px-4 py-3"><div className="mb-2 text-sm font-bold">Диалоги</div>{threads.length > 0 && <label className="flex h-9 items-center gap-2 rounded-lg bg-black/[.02] px-2 ring-1 ring-black/[.08]"><I.Search className="h-3.5 w-3.5 shrink-0 text-ink/40" /><input type="search" value={threadSearch} onChange={(e) => setThreadSearch(e.target.value)} placeholder="Поиск…" className="min-w-0 flex-1 bg-transparent text-xs outline-none placeholder:text-ink/40" /></label>}</div>
        {loading ? <div className="p-8 text-center text-sm text-ink/45">Загрузка…</div> : !threads.length ? <EmptyState title="Пока нет диалогов">Написать можно из курса или профиля ментора</EmptyState> : !filtered.length ? <EmptyState icon={I.Search} title="Ничего не найдено">Попробуйте другое имя.</EmptyState> : <ul className="max-h-[calc(100dvh-10rem)] divide-y divide-black/[.05] overflow-y-auto scrollbar-thin md:max-h-[min(72vh,700px)]">{filtered.map((thread) => { const unread = Number(thread.unread_count || 0); const active = activeThread?.public_id === thread.public_id; return <li key={thread.public_id}><button type="button" onClick={() => setActiveThread(thread)} className={`flex w-full gap-3 px-4 py-3 text-left transition hover:bg-black/[.02] ${active ? 'bg-violet-500/8' : ''}`}><ChatAvatar user={thread.other_participant} /><span className="min-w-0 flex-1"><span className="flex items-center gap-2"><b className="min-w-0 flex-1 truncate text-sm">{chatParticipantName(thread.other_participant)}</b><time className="shrink-0 text-[10px] text-ink/40">{formatRelativeListTime(thread.last_message_at)}</time></span><span className={`mt-0.5 block truncate text-xs ${unread ? 'font-semibold text-ink/80' : 'text-ink/45'}`}>{thread.last_message_preview || 'Нет сообщений'}</span></span>{unread > 0 && <span className="mt-1 grid h-5 min-w-5 shrink-0 place-items-center rounded-full bg-violet-600 px-1 text-[10px] font-bold text-white">{unread > 99 ? '99+' : unread}</span>}</button></li>; })}</ul>}
      </aside>
      <section className={`min-h-0 ${onMobileThread ? 'block' : 'hidden md:block'}`}>{activeThread ? <ChatThreadView thread={activeThread} threads={threads} onBack={() => setActiveThread(null)} onThreadActivity={activity} onMarkedRead={() => activeThread?.public_id && markRead(activeThread.public_id)} navigate={navigate} onOpenWhiteboard={setPreviewConfId} /> : <div className="flex h-full min-h-[360px] items-center justify-center"><EmptyState title="Выберите диалог">Написать можно из курса или профиля ментора</EmptyState></div>}</section>
    </div></main>
  </div>;
}

window.MessagesPage = MessagesPage;
window.ChatThreadView = ChatThreadView;
