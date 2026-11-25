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

function imageIdentity(url) {
  const raw = String(url || '').split('#')[0].split('?')[0];
  try {
    const parsed = new URL(raw, 'https://academy.local');
    return decodeURIComponent(parsed.pathname).toLowerCase();
  } catch (_) {
    return raw.toLowerCase();
  }
}

function resolveImageUrl(src) {
  return String(window.mediaUrl?.(src) || src || '');
}

function htmlHasVisibleContent(html) {
  const raw = String(html || '');
  if (!raw.trim()) return false;
  if (typeof document === 'undefined') return true;
  const node = document.createElement('div');
  node.innerHTML = raw;
  if (node.querySelector('pre, table, iframe, video, ul, ol, blockquote')) return true;
  return (node.textContent || '').replace(/\u00a0/g, ' ').trim().length > 0;
}

function takeImagesFromHtml(html) {
  const clean = window.sanitizeHtml ? window.sanitizeHtml(html || '') : String(html || '');
  if (typeof document === 'undefined') return { html: clean, images: [] };
  const template = document.createElement('template');
  template.innerHTML = clean;
  const images = [];
  Array.from(template.content.querySelectorAll('img')).forEach((img) => {
    const src = img.getAttribute('src') || '';
    if (!src) return;
    const figure = img.closest('figure');
    const caption = figure?.querySelector('figcaption')?.textContent?.replace(/\s+/g, ' ').trim();
    images.push({
      src,
      alt: caption || img.getAttribute('alt') || 'Схема',
    });
    img.remove();
    if (figure && !figure.querySelector('img')) figure.remove();
  });
  template.content.querySelectorAll('p, figure').forEach((node) => {
    if (!(node.textContent || '').replace(/\u00a0/g, ' ').trim() && !node.querySelector('img, iframe, video')) {
      node.remove();
    }
  });
  const holder = document.createElement('div');
  holder.append(...template.content.childNodes);
  return { html: holder.innerHTML, images };
}

function prepareTheoryView(lesson) {
  const images = [];
  const seen = new Set();
  const push = (src, alt) => {
    const href = resolveImageUrl(src);
    if (!href) return;
    const key = imageIdentity(href);
    if (!key || seen.has(key)) return;
    seen.add(key);
    images.push({ src: href, alt: alt || 'Схема' });
  };

  const rawBlocks = Array.isArray(lesson?.blocks) ? lesson.blocks : [];
  let blocks = null;
  let legacyHtml = '';
  if (rawBlocks.length) {
    blocks = rawBlocks.map((block) => {
      if (!block) return null;
      if (block.type === 'image') {
        push(imageSrc(block), block.caption || block.name || 'Картинка урока');
        return null;
      }
      if (block.type === 'text' || block.type === 'callout') {
        const split = takeImagesFromHtml(block.html || '');
        split.images.forEach((image) => push(image.src, image.alt));
        if (!htmlHasVisibleContent(split.html)) return null;
        return { ...block, html: split.html };
      }
      return block;
    }).filter(Boolean);
  } else {
    const split = takeImagesFromHtml(lesson?.content || '');
    split.images.forEach((image) => push(image.src, image.alt));
    if (split.html.trim()) legacyHtml = split.html;
    else if (!images.length) legacyHtml = '<p>Содержимое урока ещё добавляется.</p>';
  }

  const attachments = Array.isArray(lesson?.attachments) ? lesson.attachments : [];
  const isImage = typeof window.isLessonImageAttachment === 'function'
    ? window.isLessonImageAttachment
    : (row) => /\.(png|jpe?g|gif|webp|svg)$/i.test(String(row?.name || row?.url || ''));
  attachments.forEach((row) => {
    if (!isImage(row)) return;
    push(row.url, row.name || 'Схема');
  });

  return { blocks, legacyHtml, images };
}

function theoryExerciseText(view) {
  const chunks = [];
  if (view?.blocks) {
    view.blocks.forEach((block) => {
      if (!block) return;
      if (block.type === 'heading' && block.text) chunks.push(block.text);
      else if ((block.type === 'text' || block.type === 'callout') && block.html) chunks.push(block.html);
    });
  } else if (view?.legacyHtml) {
    chunks.push(view.legacyHtml);
  }
  return chunks.join('\n\n');
}

function BoardButton({ urls, title, navigate, statement, files }) {
  const loggedIn = !!window.getAccessToken?.();
  const enabled = typeof window.whiteboardFeatureEnabled === 'function'
    ? window.whiteboardFeatureEnabled()
    : true;
  const list = (urls || []).filter(Boolean);
  const [busy, setBusy] = React.useState(false);
  if (!list.length || !enabled || typeof navigate !== 'function') return null;
  if (!loggedIn) {
    return <p className="mt-2 text-[12px] text-ink/45">Войдите, чтобы рисовать на личной доске.</p>;
  }
  const text = window.buildExerciseBoardText
    ? window.buildExerciseBoardText({ statement, files })
    : '';
  const send = async () => {
    if (text && window.openTaskSheetOnBoard) {
      setBusy(true);
      try {
        await window.openTaskSheetOnBoard(navigate, { urls: list, title, statement: text });
      } finally {
        setBusy(false);
      }
      return;
    }
    window.openLessonImagesOnBoard(navigate, { urls: list, title });
  };
  return (
    <div>
      <button
        type="button"
        disabled={busy}
        onClick={send}
        title="Переместить на доску схему, текст урока и связанные части"
        className="mt-3 min-h-11 px-4 rounded-xl text-sm font-semibold text-violet-800 bg-violet-50 ring-1 ring-violet-200 hover:bg-violet-100 disabled:opacity-60"
      >
        {busy ? 'Собираем…' : 'На личную доску'}
      </button>
      <p className="mt-2 text-[12px] text-ink/45 leading-relaxed">
        {text
          ? 'На доску попадут текст урока и схемы вместе. Можно рисовать сверху. Это черновик, на оценку не влияет.'
          : 'Картинка откроется на вашей доске. Можно рисовать сверху. Это черновик, на оценку не влияет.'}
      </p>
    </div>
  );
}

function TheoryShotRow({ images, onOpen }) {
  if (!images.length) return null;
  const many = images.length > 1;
  return (
    <div className="theory-shots" aria-label={many ? 'Схемы урока' : 'Схема урока'}>
      <div className="theory-shots-label">{many ? 'Схемы' : 'Схема'}</div>
      <div className="theory-shots-row">
        {images.map((image, index) => (
          <button
            key={`${image.src}-${index}`}
            type="button"
            className="theory-shot"
            title={image.alt}
            aria-label={`Открыть схему: ${image.alt}`}
            onClick={(event) => {
              event.stopPropagation();
              onOpen(image);
            }}
          >
            <img src={image.src} alt={image.alt} />
          </button>
        ))}
      </div>
      <p className="theory-shots-hint">Нажмите на квадрат, чтобы открыть схему.</p>
    </div>
  );
}

function TheoryBlockRead({ block }) {
  if (block.type === 'image') return null;
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
  return (
    <div
      className="theory-content"
      dangerouslySetInnerHTML={{ __html: window.sanitizeHtml(block.html || '') }}
    />
  );
}

function TheoryBlocksView({ lesson, navigate }) {
  const hostRef = React.useRef(null);
  const [zoom, setZoom] = React.useState(null);
  const view = prepareTheoryView(lesson);
  const blocks = view.blocks;
  const attachments = lesson?.attachments || [];
  const imageUrls = view.images.map((image) => image.src);
  React.useEffect(() => {
    if (hostRef.current && window.enhancePythonBlocks) {
      window.enhancePythonBlocks(hostRef.current, navigate);
    }
  }, [lesson?.content, lesson?.public_id, blocks?.length, navigate]);
  React.useEffect(() => {
    const root = hostRef.current;
    if (!root) return undefined;
    const onClick = (event) => {
      const img = event.target.closest && event.target.closest('img');
      if (!img || !root.contains(img) || img.closest('.theory-shot')) return;
      setZoom({ src: img.currentSrc || img.src, alt: img.alt || 'Схема' });
    };
    root.addEventListener('click', onClick);
    return () => root.removeEventListener('click', onClick);
  }, [lesson?.content, lesson?.public_id, blocks?.length, view.images.length]);
  const zoomNode = zoom && window.LessonImageZoom
    ? <window.LessonImageZoom src={zoom.src} alt={zoom.alt} onClose={() => setZoom(null)} />
    : null;
  const relatedFiles = attachments.filter((row) => {
    const isImage = typeof window.isLessonImageAttachment === 'function'
      ? window.isLessonImageAttachment
      : () => false;
    return !isImage(row);
  });
  const gallery = (
    <>
      <TheoryShotRow
        images={view.images}
        onOpen={(image) => setZoom({ src: image.src, alt: image.alt || 'Схема' })}
      />
      <BoardButton
        urls={imageUrls}
        title={lesson?.title}
        navigate={navigate}
        statement={theoryExerciseText(view)}
        files={relatedFiles}
      />
    </>
  );
  if (blocks) {
    return (
      <div ref={hostRef}>
        <div className="mt-6">
          {gallery}
          {blocks.length > 0 && (
            <div className={`space-y-5 ${view.images.length ? 'mt-6' : ''}`}>
              {blocks.map((block) => (
                <TheoryBlockRead
                  key={block.id || block.attachment_id || block.type}
                  block={block}
                />
              ))}
            </div>
          )}
        </div>
        {window.LessonAttachments && (
          <window.LessonAttachments
            items={attachments}
            hideImages
            navigate={navigate}
            lessonTitle={lesson.title}
          />
        )}
        {zoomNode}
      </div>
    );
  }
  return (
    <div ref={hostRef}>
      {view.images.length > 0 && (
        <div className="mt-6">
          {gallery}
        </div>
      )}
      {window.LessonAttachments && (
        <window.LessonAttachments
          items={attachments}
          hideImages
          navigate={navigate}
          lessonTitle={lesson.title}
        />
      )}
      {view.legacyHtml ? (
        <div
          className="theory-content mt-6"
          dangerouslySetInnerHTML={{ __html: window.sanitizeHtml(view.legacyHtml) }}
        />
      ) : null}
      {zoomNode}
    </div>
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
                        className="max-w-full w-auto h-auto max-h-[min(40vh,360px)] object-contain rounded-xl bg-white ring-1 ring-black/[0.06]"
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
