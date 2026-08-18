// Теория блоками: редактор (ментор) и показ ученику.

const LEGACY_EMPTY_HTML = '<p>Новый теоретический урок</p>';
const IMAGE_ACCEPT = 'image/png,image/jpeg,image/jpg,image/gif,image/webp,image/svg+xml,.png,.jpg,.jpeg,.gif,.webp,.svg';

function newBlockId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID();
  return `b-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function hydrateTheoryBlocks(form) {
  const raw = Array.isArray(form?.blocks) ? form.blocks.filter((row) => row && row.type) : [];
  if (raw.length) {
    return raw.map((row) => ({ ...row, id: row.id || newBlockId() }));
  }
  const html = String(form?.content || '').trim();
  if (!html || html === LEGACY_EMPTY_HTML) return [];
  return [{ id: newBlockId(), type: 'text', html }];
}

function serializeTheoryBlocksForSave(blocks) {
  return (Array.isArray(blocks) ? blocks : []).map((row) => {
    if (row.type === 'heading') return { id: row.id, type: 'heading', text: row.text || '' };
    if (row.type === 'image') {
      return {
        id: row.id,
        type: 'image',
        attachment_id: row.attachment_id,
        caption: row.caption || '',
      };
    }
    return { id: row.id, type: row.type, html: row.html || '' };
  });
}

function escapeHtml(text) {
  return String(text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function imageSrc(block) {
  return window.mediaUrl?.(block?.url) || block?.url || '';
}

function BoardButton({ urls, title, navigate }) {
  const loggedIn = !!window.getAccessToken?.();
  const enabled = typeof window.whiteboardFeatureEnabled === 'function'
    ? window.whiteboardFeatureEnabled()
    : true;
  const list = (urls || []).filter(Boolean);
  if (!list.length || !enabled || typeof navigate !== 'function') return null;
  if (!loggedIn) {
    return <p className="mt-2 text-[12px] text-ink/45">Войдите, чтобы рисовать на личной доске.</p>;
  }
  return (
    <button
      type="button"
      onClick={() => window.openLessonImagesOnBoard(navigate, { urls: list, title })}
      className="mt-3 min-h-11 px-4 rounded-xl text-sm font-semibold text-violet-800 bg-violet-50 ring-1 ring-violet-200 hover:bg-violet-100"
    >
      На личную доску
    </button>
  );
}

function TheoryBlockRead({ block, navigate, lessonTitle }) {
  if (block.type === 'heading') {
    return (
      <div className="theory-content">
        <h2>{block.text || ''}</h2>
      </div>
    );
  }
  if (block.type === 'callout') {
    return (
      <div
        className="theory-callout theory-content"
        dangerouslySetInnerHTML={{ __html: window.sanitizeHtml(block.html || '') }}
      />
    );
  }
  if (block.type === 'image') {
    const href = imageSrc(block);
    if (!href) return null;
    return (
      <figure className="theory-figure">
        <img src={href} alt={block.caption || block.name || 'Картинка урока'} />
        {block.caption ? <figcaption>{block.caption}</figcaption> : null}
        <div className="px-4 pb-3">
          <BoardButton urls={[href]} title={lessonTitle} navigate={navigate} />
        </div>
      </figure>
    );
  }
  return (
    <div
      className="theory-content"
      dangerouslySetInnerHTML={{ __html: window.sanitizeHtml(block.html || '') }}
    />
  );
}

function TheoryBlocksView({ lesson, navigate }) {
  const blocks = Array.isArray(lesson?.blocks) ? lesson.blocks : [];
  const attachments = lesson?.attachments || [];
  if (blocks.length) {
    return (
      <>
        <div className="mt-6 space-y-5">
          {blocks.map((block) => (
            <TheoryBlockRead
              key={block.id || block.attachment_id || block.type}
              block={block}
              navigate={navigate}
              lessonTitle={lesson.title}
            />
          ))}
        </div>
        {window.LessonAttachments && (
          <window.LessonAttachments
            items={attachments}
            hideImages
            navigate={navigate}
            lessonTitle={lesson.title}
          />
        )}
      </>
    );
  }
  return (
    <>
      {window.LessonAttachments && (
        <window.LessonAttachments items={attachments} navigate={navigate} lessonTitle={lesson.title} />
      )}
      <div
        className="theory-content mt-6"
        dangerouslySetInnerHTML={{
          __html: window.sanitizeHtml(lesson?.content || '<p>Содержимое урока ещё добавляется.</p>'),
        }}
      />
    </>
  );
}

function RichHtmlEditor({ html, onChange, placeholder }) {
  const ref = React.useRef(null);
  const focusedRef = React.useRef(false);

  React.useEffect(() => {
    if (!ref.current || focusedRef.current) return;
    const next = html || '';
    if (ref.current.innerHTML !== next) ref.current.innerHTML = next;
  }, [html]);

  const emit = () => {
    if (ref.current) onChange(ref.current.innerHTML);
  };

  const run = (cmd, val) => {
    ref.current?.focus();
    document.execCommand(cmd, false, val || null);
    emit();
  };

  const mark = () => {
    ref.current?.focus();
    const sel = window.getSelection();
    if (!sel || sel.rangeCount === 0 || sel.isCollapsed) {
      document.execCommand('insertHTML', false, '<mark>важно</mark>');
    } else {
      document.execCommand('insertHTML', false, `<mark>${escapeHtml(sel.toString())}</mark>`);
    }
    emit();
  };

  const onPaste = (e) => {
    e.preventDefault();
    const text = e.clipboardData?.getData('text/plain') || '';
    document.execCommand('insertText', false, text);
    emit();
  };

  const btn = 'h-9 px-2.5 rounded-lg text-[12px] font-semibold ring-1 ring-black/[0.08] bg-white hover:bg-violet-50';

  return (
    <div>
      <div className="flex flex-wrap gap-1.5 mb-2">
        <button type="button" className={btn} onMouseDown={(e) => e.preventDefault()} onClick={() => run('bold')}>Жирный</button>
        <button type="button" className={btn} onMouseDown={(e) => e.preventDefault()} onClick={() => run('italic')}>Курсив</button>
        <button type="button" className={`${btn} bg-amber-50 ring-amber-200`} onMouseDown={(e) => e.preventDefault()} onClick={mark}>Маркер</button>
        <button type="button" className={btn} onMouseDown={(e) => e.preventDefault()} onClick={() => run('insertUnorderedList')}>Список</button>
        <button type="button" className={btn} onMouseDown={(e) => e.preventDefault()} onClick={() => run('insertOrderedList')}>Нумерация</button>
      </div>
      <div
        ref={ref}
        className="theory-editor-text theory-content w-full px-3 py-2.5 rounded-xl bg-white ring-1 ring-black/[0.08] text-[15px] focus:ring-violet-300"
        contentEditable
        data-placeholder={placeholder}
        suppressContentEditableWarning
        onFocus={() => { focusedRef.current = true; }}
        onBlur={() => { focusedRef.current = false; emit(); }}
        onInput={emit}
        onPaste={onPaste}
      />
    </div>
  );
}

function InsertBar({ onAdd, onPickImages, compact }) {
  const fileRef = React.useRef(null);
  const chip = compact
    ? 'h-9 px-3 rounded-lg text-[12px] font-semibold bg-white ring-1 ring-black/[0.08] hover:bg-violet-50 hover:ring-violet-200'
    : 'h-11 px-4 rounded-xl text-sm font-semibold bg-white ring-1 ring-black/[0.08] hover:bg-violet-50 hover:ring-violet-200';
  return (
    <div className={`flex flex-wrap gap-2 ${compact ? 'py-2 justify-center' : 'py-1'}`}>
      <button type="button" className={chip} onClick={() => onAdd('text')}>+ Текст</button>
      <button type="button" className={chip} onClick={() => fileRef.current?.click()}>+ Картинка</button>
      <button type="button" className={chip} onClick={() => onAdd('heading')}>+ Заголовок</button>
      <button type="button" className={chip} onClick={() => onAdd('callout')}>+ Важно</button>
      <input
        ref={fileRef}
        type="file"
        className="sr-only"
        accept={IMAGE_ACCEPT}
        multiple
        onChange={(e) => {
          const files = Array.from(e.target.files || []);
          e.target.value = '';
          if (files.length) onPickImages(files);
        }}
      />
    </div>
  );
}

function BlockChrome({ label, index, total, onMove, onRemove, children }) {
  const nav = 'h-9 w-9 rounded-lg text-sm font-semibold ring-1 ring-black/[0.08] bg-white hover:bg-black/[0.03] disabled:opacity-30';
  return (
    <div className="rounded-2xl ring-1 ring-black/[0.08] bg-white overflow-hidden">
      <div className="flex items-center gap-2 px-3 py-2 bg-black/[0.025] border-b border-black/[0.05]">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-ink/45">{label}</span>
        <div className="ml-auto flex items-center gap-1">
          <button type="button" className={nav} disabled={index === 0} onClick={() => onMove(-1)} aria-label="Выше">↑</button>
          <button type="button" className={nav} disabled={index === total - 1} onClick={() => onMove(1)} aria-label="Ниже">↓</button>
          <button type="button" className={`${nav} text-red-600 hover:bg-red-50`} onClick={onRemove} aria-label="Удалить">✕</button>
        </div>
      </div>
      <div className="p-3 sm:p-4">{children}</div>
    </div>
  );
}

function TheoryBlocksEditor({ kind, publicId, blocks, onBlocks, onAttachments }) {
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const [dragOver, setDragOver] = React.useState(null);
  const list = Array.isArray(blocks) ? blocks : [];

  const setList = (next) => {
    onBlocks((prev) => (typeof next === 'function' ? next(prev || []) : next));
  };

  const uploadFiles = async (files) => {
    const rows = [];
    for (const file of files) {
      const fd = new FormData();
      fd.append('file', file);
      const row = await window.fetchApiForm(
        `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(publicId)}/attachments/`,
        fd,
        { method: 'POST', auth: true },
      );
      rows.push(row);
    }
    onAttachments((prev) => [...(prev || []), ...rows]);
    return rows;
  };

  const insertAt = (index, items) => {
    setList((prev) => {
      const next = (prev || []).slice();
      next.splice(index, 0, ...items);
      return next;
    });
  };

  const addType = (type, index) => {
    const block = type === 'heading'
      ? { id: newBlockId(), type: 'heading', text: '' }
      : type === 'callout'
        ? { id: newBlockId(), type: 'callout', html: '' }
        : { id: newBlockId(), type: 'text', html: '' };
    insertAt(index, [block]);
  };

  const addImages = async (files, index) => {
    const images = Array.from(files || []).filter((file) => {
      const name = (file.name || '').toLowerCase();
      return (file.type || '').startsWith('image/') || /\.(png|jpe?g|gif|webp|svg)$/.test(name);
    });
    if (!images.length) {
      setErr('Нужна картинка: png, jpg, gif, webp или svg.');
      return;
    }
    setBusy(true);
    setErr('');
    try {
      const rows = await uploadFiles(images);
      insertAt(index, rows.map((row) => ({
        id: newBlockId(),
        type: 'image',
        attachment_id: row.public_id,
        caption: '',
        url: row.url,
        name: row.name,
      })));
    } catch (e) {
      setErr(e.message || 'Не удалось загрузить картинку');
    } finally {
      setBusy(false);
    }
  };

  const update = (index, patch) => {
    setList((prev) => (prev || []).map((row, i) => (i === index ? { ...row, ...patch } : row)));
  };

  const move = (index, delta) => {
    setList((prev) => {
      const next = (prev || []).slice();
      const to = index + delta;
      if (to < 0 || to >= next.length) return next;
      const [row] = next.splice(index, 1);
      next.splice(to, 0, row);
      return next;
    });
  };

  const remove = async (index) => {
    const block = list[index];
    setList((prev) => (prev || []).filter((_, i) => i !== index));
    if (block?.type === 'image' && block.attachment_id) {
      try {
        await window.fetchApiJson(
          `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(publicId)}/attachments/${encodeURIComponent(block.attachment_id)}/`,
          { method: 'DELETE', auth: true },
        );
        onAttachments((prev) => (prev || []).filter((row) => row.public_id !== block.attachment_id));
      } catch (_) { /* orphan ok */ }
    }
  };

  const replaceImage = async (index, file) => {
    if (!file) return;
    setBusy(true);
    setErr('');
    try {
      const prevBlock = list[index];
      const [row] = await uploadFiles([file]);
      update(index, { attachment_id: row.public_id, url: row.url, name: row.name });
      if (prevBlock?.attachment_id && prevBlock.attachment_id !== row.public_id) {
        try {
          await window.fetchApiJson(
            `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(publicId)}/attachments/${encodeURIComponent(prevBlock.attachment_id)}/`,
            { method: 'DELETE', auth: true },
          );
          onAttachments((prev) => (prev || []).filter((item) => item.public_id !== prevBlock.attachment_id));
        } catch (_) { /* ignore */ }
      }
    } catch (e) {
      setErr(e.message || 'Не удалось заменить картинку');
    } finally {
      setBusy(false);
    }
  };

  const onDropFiles = (event, index) => {
    event.preventDefault();
    setDragOver(null);
    const files = Array.from(event.dataTransfer?.files || []);
    if (files.length) addImages(files, index);
  };

  const dropProps = (index) => ({
    onDragOver: (e) => { e.preventDefault(); setDragOver(index); },
    onDragLeave: () => setDragOver((cur) => (cur === index ? null : cur)),
    onDrop: (e) => onDropFiles(e, index),
  });

  return (
    <div>
      <div className="mb-1.5">
        <label className="text-[12px] font-semibold uppercase tracking-wider text-ink/55">Содержание урока</label>
        <p className="text-[11px] text-ink/40 mt-0.5">Текст, картинка, снова текст — в любом количестве. Картинки можно перетащить с компьютера.</p>
      </div>
      {err && <p className="mb-2 text-sm text-red-600">{err}</p>}
      {busy && <p className="mb-2 text-[12px] text-ink/45">Загрузка картинок…</p>}

      {list.length === 0 && (
        <div
          className={`rounded-2xl ring-1 ring-dashed ring-black/[0.12] bg-black/[0.015] p-6 text-center ${dragOver === 0 ? 'theory-drop-active' : ''}`}
          {...dropProps(0)}
        >
          <p className="text-sm font-semibold text-ink mb-1">Соберите урок по шагам</p>
          <p className="text-[13px] text-ink/50 mb-4">Как на Степике: абзац, кадр, абзац. Можно сразу несколько картинок.</p>
          <InsertBar onAdd={(type) => addType(type, 0)} onPickImages={(files) => addImages(files, 0)} />
        </div>
      )}

      {list.length > 0 && (
        <div className="space-y-1">
          <div className={dragOver === 0 ? 'theory-drop-active rounded-xl' : ''} {...dropProps(0)}>
            <InsertBar compact onAdd={(type) => addType(type, 0)} onPickImages={(files) => addImages(files, 0)} />
          </div>
          {list.map((block, index) => (
            <React.Fragment key={block.id || index}>
              <BlockChrome
                label={block.type === 'heading' ? 'Заголовок' : block.type === 'image' ? 'Картинка' : block.type === 'callout' ? 'Важно' : 'Текст'}
                index={index}
                total={list.length}
                onMove={(delta) => move(index, delta)}
                onRemove={() => remove(index)}
              >
                {block.type === 'heading' && (
                  <input
                    type="text"
                    value={block.text || ''}
                    onChange={(e) => update(index, { text: e.target.value })}
                    placeholder="Название раздела"
                    className="w-full h-11 px-3 rounded-xl bg-white ring-1 ring-black/[0.08] text-[17px] font-bold focus:ring-violet-300"
                  />
                )}
                {(block.type === 'text' || block.type === 'callout') && (
                  <RichHtmlEditor
                    html={block.html || ''}
                    onChange={(html) => update(index, { html })}
                    placeholder={block.type === 'callout' ? 'Что нельзя пропустить' : 'Напишите абзац. Выделите фразу и нажмите «Маркер».'}
                  />
                )}
                {block.type === 'image' && (
                  <div>
                    {imageSrc(block) ? (
                      <img
                        src={imageSrc(block)}
                        alt={block.caption || block.name || ''}
                        className="w-full max-h-[min(56vh,560px)] object-contain rounded-xl bg-[#fafafa] ring-1 ring-black/[0.06]"
                      />
                    ) : (
                      <p className="text-sm text-red-600">Файл картинки не найден. Загрузите заново.</p>
                    )}
                    <input
                      type="text"
                      value={block.caption || ''}
                      onChange={(e) => update(index, { caption: e.target.value })}
                      placeholder="Подпись под картинкой, например: Шаг 2. Подписали степени"
                      className="mt-3 w-full h-11 px-3 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm focus:ring-violet-300"
                    />
                    <label className="mt-2 inline-flex items-center h-9 px-3 rounded-lg text-[12px] font-semibold ring-1 ring-black/[0.08] bg-white cursor-pointer">
                      Заменить файл
                      <input
                        type="file"
                        className="sr-only"
                        accept={IMAGE_ACCEPT}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          e.target.value = '';
                          if (file) replaceImage(index, file);
                        }}
                      />
                    </label>
                  </div>
                )}
              </BlockChrome>
              <div className={dragOver === index + 1 ? 'theory-drop-active rounded-xl' : ''} {...dropProps(index + 1)}>
                <InsertBar compact onAdd={(type) => addType(type, index + 1)} onPickImages={(files) => addImages(files, index + 1)} />
              </div>
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
}

window.hydrateTheoryBlocks = hydrateTheoryBlocks;
window.serializeTheoryBlocksForSave = serializeTheoryBlocksForSave;
window.TheoryBlocksView = TheoryBlocksView;
window.TheoryBlocksEditor = TheoryBlocksEditor;
