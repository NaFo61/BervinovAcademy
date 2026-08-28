// Content editor — редактирование уроков курса (ментор / admin)

const I = window.I;
const Routes = window.Routes;

const KIND_META = {
  theory: { emoji: '📖', label: 'Теория', color: 'text-blue-600 bg-blue-50' },
  radio: { emoji: '🔘', label: 'Radio', color: 'text-violet-600 bg-violet-50' },
  checkbox: { emoji: '☑️', label: 'Checkbox', color: 'text-cyan-600 bg-cyan-50' },
  short_answer: { emoji: '✎', label: 'Краткий ответ', color: 'text-amber-700 bg-amber-50' },
  coding: { emoji: '💻', label: 'Код', color: 'text-purple-600 bg-purple-50' },
};

const DIFFICULTY_OPTS = [
  ['beginner', 'Начинающий'],
  ['easy', 'Легкий'],
  ['medium', 'Средний'],
  ['hard', 'Сложный'],
  ['expert', 'Эксперт'],
];

function FieldLabel({ children, hint }) {
  return (
    <div className="mb-1.5">
      <label className="text-[12px] font-semibold uppercase tracking-wider text-ink/55">{children}</label>
      {hint && <p className="text-[11px] text-ink/40 mt-0.5 normal-case tracking-normal">{hint}</p>}
    </div>
  );
}

function TextInput({ value, onChange, placeholder, className }) {
  return (
    <input type="text" value={value || ''} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      className={`w-full h-11 px-3 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm focus:ring-violet-300 ${className || ''}`}/>
  );
}

function TextArea({ value, onChange, rows, placeholder, mono, className }) {
  return (
    <textarea value={value || ''} onChange={(e) => onChange(e.target.value)} rows={rows || 4} placeholder={placeholder}
      spellCheck={!mono}
      className={`w-full px-3 py-2.5 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm resize-y focus:ring-violet-300
        ${mono ? 'font-mono text-[13px]' : ''} ${className || ''}`}/>
  );
}

function EditorTabs({ tabs, active, onChange }) {
  return (
    <div className="flex gap-1 p-1 rounded-xl bg-black/[0.04] ring-1 ring-black/[0.05] overflow-x-auto">
      {tabs.map((t) => (
        <button key={t.id} type="button" onClick={() => onChange(t.id)}
          className={`px-4 py-2 rounded-lg text-[13px] font-semibold whitespace-nowrap transition-all
            ${active === t.id ? 'bg-white text-ink shadow-sm ring-1 ring-black/[0.06]' : 'text-ink/50 hover:text-ink/75'}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

function SolutionFields({ form, set, videoFile, setVideoFile }) {
  return (
    <div className="space-y-5">
      <div className="p-4 rounded-xl bg-amber-50/80 border border-amber-100 text-[13px] text-amber-900/80">
        Видео и текст показываются ученику на вкладке «Эталонное решение» после правильного ответа или 3 ошибок.
      </div>
      <div>
        <FieldLabel hint="YouTube, Rutube или VK">Ссылка на видео</FieldLabel>
        <TextInput value={form.video_url} onChange={(v) => set({ ...form, video_url: v })} placeholder="https://www.youtube.com/watch?v=…"/>
      </div>
      <div>
        <FieldLabel hint="MP4 или WebM, если нет ссылки">Файл видео</FieldLabel>
        <input type="file" accept="video/mp4,video/webm,video/*"
          onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-ink/60 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-violet-50 file:text-violet-700 file:font-semibold"/>
        {form.video?.embed_url && !videoFile && (
          <div className="mt-3">
            <window.VideoExplanation video={form.video} title="Текущее видео"/>
          </div>
        )}
      </div>
      <div>
        <FieldLabel hint="HTML: текст, код в &lt;pre&gt;&lt;code&gt;, картинки, списки">Текст эталонного решения</FieldLabel>
        <TextArea value={form.solution_text} onChange={(v) => set({ ...form, solution_text: v })} rows={10}
          placeholder={'Подробный разбор…\n\n<pre><code>def solve():\n    return 42</code></pre>'}/>
      </div>
    </div>
  );
}

function OptionsEditor({ options, setOptions, multi }) {
  const update = (i, patch) => {
    const next = options.map((o, j) => (j === i ? { ...o, ...patch } : o));
    setOptions(next);
  };
  const add = () => setOptions([...options, { text: 'Новый вариант', is_correct: false }]);
  const remove = (i) => setOptions(options.filter((_, j) => j !== i));

  return (
    <div className="space-y-3">
      {options.map((opt, i) => (
        <div key={opt.public_id || i} className="flex gap-2 items-start p-3 rounded-xl ring-1 ring-black/[0.06] bg-white">
          <button type="button" title={multi ? 'Правильный' : 'Единственный правильный'}
            onClick={() => {
              if (multi) update(i, { is_correct: !opt.is_correct });
              else setOptions(options.map((o, j) => ({ ...o, is_correct: j === i })));
            }}
            className={`mt-1 w-6 h-6 rounded-md shrink-0 flex items-center justify-center text-xs font-bold ring-1
              ${opt.is_correct ? 'bg-emerald-500 text-white ring-emerald-500' : 'bg-white text-ink/30 ring-black/10'}`}>
            {opt.is_correct ? '✓' : ''}
          </button>
          <TextInput value={opt.text} onChange={(v) => update(i, { text: v })} className="flex-1"/>
          <button type="button" onClick={() => remove(i)} className="mt-2 text-ink/30 hover:text-red-500 px-1">×</button>
        </div>
      ))}
      <button type="button" onClick={add}
        className="h-10 px-4 rounded-xl text-sm font-semibold ring-1 ring-black/[0.08] hover:bg-violet-50 hover:text-violet-700">
        + Вариант
      </button>
    </div>
  );
}

function TestsEditor({ tests, setTests }) {
  const update = (i, patch) => setTests(tests.map((t, j) => (j === i ? { ...t, ...patch } : t)));
  const add = () => setTests([...tests, { input_data: '', expected_output: '', is_hidden: false }]);
  const remove = (i) => setTests(tests.filter((_, j) => j !== i));

  return (
    <div className="space-y-4">
      {tests.map((tc, i) => (
        <div key={tc.public_id || i} className="p-4 rounded-xl ring-1 ring-black/[0.06] bg-black/[0.02] space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-ink/45">Тест {i + 1}</span>
            <label className="flex items-center gap-2 text-xs text-ink/55">
              <input type="checkbox" checked={!!tc.is_hidden} onChange={(e) => update(i, { is_hidden: e.target.checked })}/>
              Скрытый
            </label>
          </div>
          <div>
            <FieldLabel>Вход</FieldLabel>
            <TextArea mono value={tc.input_data} onChange={(v) => update(i, { input_data: v })} rows={2}/>
          </div>
          <div>
            <FieldLabel>Ожидаемый вывод</FieldLabel>
            <TextArea mono value={tc.expected_output} onChange={(v) => update(i, { expected_output: v })} rows={2}/>
          </div>
          <button type="button" onClick={() => remove(i)} className="text-xs text-red-500 font-semibold">Удалить тест</button>
        </div>
      ))}
      <button type="button" onClick={add}
        className="h-10 px-4 rounded-xl text-sm font-semibold ring-1 ring-black/[0.08] hover:bg-violet-50 hover:text-violet-700">
        + Тест
      </button>
    </div>
  );
}

function AttachmentsEditor({ kind, publicId, items, onChange, hideImages }) {
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState('');
  const list = (Array.isArray(items) ? items : []).filter((row) => (
    hideImages ? !window.isLessonImageAttachment?.(row) : true
  ));

  const upload = async (file) => {
    if (!file || busy) return;
    setBusy(true);
    setErr('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      const row = await window.fetchApiForm(
        `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(publicId)}/attachments/`,
        fd,
        { method: 'POST', auth: true },
      );
      onChange([...(list || []), row]);
    } catch (e) {
      setErr(e.message || 'Не удалось загрузить файл');
    } finally {
      setBusy(false);
    }
  };

  const remove = async (row) => {
    if (busy) return;
    setBusy(true);
    setErr('');
    try {
      await window.fetchApiJson(
        `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(publicId)}/attachments/${encodeURIComponent(row.public_id)}/`,
        { method: 'DELETE', auth: true },
      );
      onChange(list.filter((x) => x.public_id !== row.public_id));
    } catch (e) {
      setErr(e.message || 'Не удалось удалить');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <FieldLabel hint={hideImages
        ? 'PDF, Word, Excel, презентации, zip, txt. Картинки добавляйте кнопкой «+ Картинка» в тексте урока. До 20 МБ на файл, без ограничения по числу.'
        : 'PDF, Word, Excel, презентации, картинки (png, jpg, svg), zip, txt, md. До 20 МБ на файл, без ограничения по числу. Ученик увидит файлы в задании.'}>
        {hideImages ? 'Документы к уроку' : 'Файлы к заданию'}
      </FieldLabel>
      {err && <p className="mb-2 text-sm text-red-600">{err}</p>}
      <ul className="space-y-2 mb-3">
        {list.map((row) => (
          <li key={row.public_id} className="flex items-center gap-2 min-h-11 px-3 py-2 rounded-xl ring-1 ring-black/[0.06] bg-white">
            <span className="flex-1 min-w-0 text-sm font-medium truncate">{row.name}</span>
            <span className="text-[11px] text-ink/40 shrink-0">{window.formatFileSize?.(row.size)}</span>
            <button type="button" onClick={() => remove(row)} disabled={busy}
              className="h-9 px-3 rounded-lg text-xs font-semibold text-red-600 hover:bg-red-50">
              Удалить
            </button>
          </li>
        ))}
      </ul>
      <label className="inline-flex items-center justify-center h-11 px-4 rounded-xl text-sm font-semibold ring-1 ring-black/[0.08] bg-white cursor-pointer">
        {busy ? 'Загрузка…' : '+ Файл'}
        <input
          type="file"
          className="sr-only"
          disabled={busy}
          accept={hideImages
            ? '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.zip,.txt,.md'
            : '.pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg,.gif,.webp,.svg,.zip,.txt,.md'}
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = '';
            if (file) upload(file);
          }}
        />
      </label>
    </div>
  );
}

async function saveLesson(kind, publicId, payload, videoFile) {
  const path = `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(publicId)}/`;
  if (videoFile) {
    const fd = new FormData();
    Object.entries(payload).forEach(([k, v]) => {
      if (v === undefined || v === null) return;
      if (typeof v === 'object') fd.append(k, JSON.stringify(v));
      else fd.append(k, String(v));
    });
    fd.append('video_file', videoFile);
    return window.fetchApiForm(path, fd, { method: 'PATCH', auth: true });
  }
  return window.fetchApiJson(path, { method: 'PATCH', body: payload, auth: true });
}

function LessonEditorForm({ lesson, courseId, moduleId, onSaved, onDeleted, navigate }) {
  const kind = lesson.kind;
  const [form, setForm] = React.useState(null);
  const [tab, setTab] = React.useState('main');
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState('');
  const [success, setSuccess] = React.useState('');
  const [videoFile, setVideoFile] = React.useState(null);
  const [confirmHide, setConfirmHide] = React.useState(false);

  React.useEffect(() => {
    setLoading(true);
    setError('');
    setSuccess('');
    setVideoFile(null);
    setTab('main');
    setConfirmHide(false);
    window.fetchApiJson(
      `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(lesson.public_id)}/`,
      { auth: true },
    )
      .then((d) => {
        const next = { ...d };
        if (kind === 'theory' && window.hydrateTheoryBlocks) {
          next.blocks = window.hydrateTheoryBlocks(d);
        }
        setForm(next);
        setLoading(false);
      })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [kind, lesson.public_id]);

  const tabs = [
    { id: 'main', label: 'Основное' },
    ...(kind !== 'theory' ? [{ id: 'solution', label: 'Эталонное решение' }] : []),
    ...(kind === 'coding' ? [{ id: 'code', label: 'Код и тесты' }] : []),
    ...(kind === 'radio' || kind === 'checkbox' ? [{ id: 'options', label: 'Варианты' }] : []),
  ];

  const handleSave = async () => {
    if (!form || saving) return;
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const payload = { ...form };
      delete payload.video;
      delete payload.module_public_id;
      delete payload.course_public_id;
      delete payload.public_id;
      delete payload.attachments;
      if (kind === 'theory' && window.serializeTheoryBlocksForSave) {
        payload.blocks = window.serializeTheoryBlocksForSave(form.blocks);
        delete payload.content;
      }
      const saved = await saveLesson(kind, form.public_id, payload, videoFile);
      const next = { ...saved };
      if (kind === 'theory' && window.hydrateTheoryBlocks) {
        next.blocks = window.hydrateTheoryBlocks(saved);
      }
      setForm(next);
      setVideoFile(null);
      setSuccess('Сохранено');
      onSaved?.(saved);
    } catch (e) {
      setError(e.message || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = () => {
    if (!form) return;
    setConfirmHide(true);
  };

  const confirmHideLesson = async () => {
    if (!form) return;
    setConfirmHide(false);
    try {
      await window.fetchApiJson(
        `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(form.public_id)}/`,
        { method: 'DELETE', auth: true },
      );
      onDeleted?.();
    } catch (e) {
      setError(e.message);
    }
  };

  const preview = () => {
    const q = window.buildLearnQuery(courseId, moduleId, kind, form?.public_id);
    if (q) navigate(Routes.LEARN, q);
  };

  if (loading) {
    return <div className="py-20 text-center text-sm text-ink/45">Загружаем урок…</div>;
  }
  if (!form) {
    return <div className="py-20 text-center text-sm text-red-600">{error || 'Не удалось загрузить'}</div>;
  }

  const meta = KIND_META[kind] || KIND_META.theory;

  return (
    <div className="flex flex-col h-full min-h-0">
      {window.ConfirmDialog && (
        <window.ConfirmDialog
          open={confirmHide}
          title="Скрыть урок?"
          body="Ученики перестанут его видеть. Сам урок останется в редакторе."
          confirmLabel="Скрыть"
          cancelLabel="Отмена"
          danger
          onConfirm={confirmHideLesson}
          onCancel={() => setConfirmHide(false)}
        />
      )}
      <div className="flex flex-wrap items-start gap-3 mb-5 shrink-0">
        <span className={`text-xs font-bold px-2.5 py-1 rounded-lg ${meta.color}`}>{meta.emoji} {meta.label}</span>
        <h2 className="text-xl font-extrabold text-ink flex-1 min-w-0">{form.title || 'Без названия'}</h2>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={preview}
            className="h-9 px-3 rounded-lg text-xs font-semibold ring-1 ring-black/[0.08] hover:bg-black/[0.03]">
            Предпросмотр ↗
          </button>
          <button type="button" onClick={handleDelete}
            className="h-9 px-3 rounded-lg text-xs font-semibold text-red-600 ring-1 ring-red-100 hover:bg-red-50">
            Скрыть
          </button>
          <button type="button" onClick={handleSave} disabled={saving}
            className="h-9 px-5 rounded-lg btn-grad text-white text-xs font-semibold disabled:opacity-50">
            {saving ? 'Сохранение…' : 'Сохранить'}
          </button>
        </div>
      </div>

      {error && <div className="mb-3 p-3 rounded-xl bg-red-50 text-red-700 text-sm ring-1 ring-red-100">{error}</div>}
      {success && <div className="mb-3 p-3 rounded-xl bg-emerald-50 text-emerald-700 text-sm ring-1 ring-emerald-100">{success}</div>}

      <EditorTabs tabs={tabs} active={tab} onChange={setTab}/>

      <div className="flex-1 overflow-y-auto scrollbar-thin mt-5 pr-1 space-y-5 pb-8">
        {tab === 'main' && (
          <>
            <div>
              <FieldLabel>Название</FieldLabel>
              <TextInput value={form.title} onChange={(v) => setForm({ ...form, title: v })}/>
            </div>

            {kind === 'theory' && (
              <>
                <div>
                  <FieldLabel hint="YouTube, Rutube или VK — показывается в уроке">Видео к уроку</FieldLabel>
                  <TextInput value={form.video_url} onChange={(v) => setForm({ ...form, video_url: v })} placeholder="https://www.youtube.com/watch?v=…"/>
                </div>
                <div>
                  <FieldLabel hint="MP4 или WebM">Файл видео</FieldLabel>
                  <input type="file" accept="video/mp4,video/webm,video/*"
                    onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                    className="block w-full text-sm text-ink/60 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-violet-50 file:text-violet-700 file:font-semibold"/>
                  {form.video?.embed_url && !videoFile && (
                    <div className="mt-3">
                      <window.VideoExplanation video={form.video} title="Текущее видео"/>
                    </div>
                  )}
                </div>
                {window.TheoryBlocksEditor ? (
                  <window.TheoryBlocksEditor
                    kind={kind}
                    publicId={form.public_id}
                    blocks={form.blocks || []}
                    attachments={form.attachments || []}
                    onBlocks={(next) => setForm((f) => ({
                      ...f,
                      blocks: typeof next === 'function' ? next(f.blocks || []) : next,
                    }))}
                    onAttachments={(next) => setForm((f) => ({
                      ...f,
                      attachments: typeof next === 'function' ? next(f.attachments || []) : next,
                    }))}
                  />
                ) : (
                  <div>
                    <FieldLabel hint="HTML поддерживается">Содержание</FieldLabel>
                    <TextArea value={form.content} onChange={(v) => setForm({ ...form, content: v })} rows={12}/>
                  </div>
                )}
              </>
            )}

            {(kind === 'radio' || kind === 'checkbox' || kind === 'short_answer') && (
              <div>
                <FieldLabel>Текст вопроса</FieldLabel>
                <TextArea value={form.question_text} onChange={(v) => setForm({ ...form, question_text: v })} rows={4}/>
              </div>
            )}

            {kind === 'short_answer' && (
              <>
                <div>
                  <FieldLabel hint="Не показывается ученику до разбора">Эталонный ответ</FieldLabel>
                  <TextInput value={form.correct_answer} onChange={(v) => setForm({ ...form, correct_answer: v })}/>
                </div>
                <div>
                  <FieldLabel>Нормализация</FieldLabel>
                  <select
                    value={form.answer_normalize || 'strip_casefold'}
                    onChange={(e) => setForm({ ...form, answer_normalize: e.target.value })}
                    className="w-full h-11 px-3 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm"
                  >
                    <option value="strip_casefold">Trim + пробелы + без регистра</option>
                    <option value="exact">Точное совпадение</option>
                    <option value="numeric">Числовое (зарезервировано)</option>
                  </select>
                </div>
              </>
            )}

            {kind === 'coding' && (
              <>
                <div>
                  <FieldLabel>Описание задачи</FieldLabel>
                  <TextArea value={form.description} onChange={(v) => setForm({ ...form, description: v })} rows={4}/>
                </div>
                <div>
                  <FieldLabel>Инструкции</FieldLabel>
                  <TextArea mono value={form.instructions} onChange={(v) => setForm({ ...form, instructions: v })} rows={4}/>
                </div>
              </>
            )}

            <div>
              <FieldLabel hint="Добавляется к общему + курсу + модулю. Можно опираться на {{condition}} и {{instructions}}. Также: {{tests}}, {{title}}, {{course}}, {{module}}, {{kind}}, {{code}}">
                Промпт ИИ для этого урока
              </FieldLabel>
              <TextArea
                mono
                value={form.assistant_prompt || ''}
                onChange={(v) => setForm({ ...form, assistant_prompt: v })}
                rows={6}
                placeholder="Пусто = общий + курс + модуль. Сюда — нюансы именно этого урока (теория, тест или код)."
              />
            </div>

            <div>
              <FieldLabel hint="Показывается ученику на вкладке задания">Заметка преподавателя</FieldLabel>
              <TextArea value={form.comment} onChange={(v) => setForm({ ...form, comment: v })} rows={3}/>
            </div>

            <AttachmentsEditor
              kind={kind}
              publicId={form.public_id}
              items={form.attachments}
              hideImages={kind === 'theory'}
              onChange={(next) => setForm({ ...form, attachments: next })}
            />

            {(kind === 'radio' || kind === 'checkbox' || kind === 'short_answer') && (
              <div>
                <FieldLabel hint="Короткий текст после ответа">Пояснение после ответа</FieldLabel>
                <TextArea value={form.explanation} onChange={(v) => setForm({ ...form, explanation: v })} rows={3}/>
              </div>
            )}

            <div className="grid sm:grid-cols-3 gap-4">
              {(kind === 'radio' || kind === 'checkbox' || kind === 'short_answer' || kind === 'coding') && (
                <div>
                  <FieldLabel>Баллы</FieldLabel>
                  <TextInput value={String(form.points ?? '')} onChange={(v) => setForm({ ...form, points: Number(v) || 0 })}/>
                </div>
              )}
              {kind === 'coding' && (
                <>
                  <div>
                    <FieldLabel>Сложность</FieldLabel>
                    <select value={form.difficulty || 'medium'} onChange={(e) => setForm({ ...form, difficulty: e.target.value })}
                      className="w-full h-11 px-3 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm">
                      {DIFFICULTY_OPTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                    </select>
                  </div>
                  <div>
                    <FieldLabel>Лимит времени (мс)</FieldLabel>
                    <TextInput value={String(form.time_limit_ms ?? '')} onChange={(v) => setForm({ ...form, time_limit_ms: Number(v) || 0 })}/>
                  </div>
                </>
              )}
              <div>
                <FieldLabel>Порядок</FieldLabel>
                <TextInput value={String(form.order_index ?? '')} onChange={(v) => setForm({ ...form, order_index: Number(v) || 1 })}/>
              </div>
              <div className="flex items-end pb-1">
                <label className="flex items-center gap-2 text-sm text-ink/70">
                  <input type="checkbox" checked={form.is_active !== false} onChange={(e) => setForm({ ...form, is_active: e.target.checked })}/>
                  Опубликован
                </label>
              </div>
            </div>
          </>
        )}

        {tab === 'solution' && (
          <SolutionFields form={form} set={setForm} videoFile={videoFile} setVideoFile={setVideoFile}/>
        )}

        {tab === 'options' && (
          <OptionsEditor
            options={form.answer_options || []}
            setOptions={(opts) => setForm({ ...form, answer_options: opts })}
            multi={kind === 'checkbox'}
          />
        )}

        {tab === 'code' && (
          <>
            <div>
              <FieldLabel>Стартовый код для ученика</FieldLabel>
              <TextArea mono value={form.initial_code} onChange={(v) => setForm({ ...form, initial_code: v })} rows={10}/>
            </div>
            <div>
              <FieldLabel hint="Используется системой проверки">Шаблон решения (solution_template)</FieldLabel>
              <TextArea mono value={form.solution_template} onChange={(v) => setForm({ ...form, solution_template: v })} rows={10}/>
            </div>
            <div>
              <FieldLabel>Тестовые случаи</FieldLabel>
              <TestsEditor
                tests={form.test_cases || []}
                setTests={(t) => setForm({ ...form, test_cases: t })}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function GlobalAssistantPromptPanel() {
  const [open, setOpen] = React.useState(false);
  const [prompt, setPrompt] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [msg, setMsg] = React.useState('');
  const [err, setErr] = React.useState('');

  const load = React.useCallback(() => {
    setLoading(true);
    setErr('');
    window.fetchApiJson('/api/mentoring/assistant/settings/', { auth: true })
      .then((d) => setPrompt(d.base_prompt || ''))
      .catch((e) => setErr(e.message || 'Не удалось загрузить общий промпт'))
      .finally(() => setLoading(false));
  }, []);

  React.useEffect(() => {
    if (open) load();
  }, [open, load]);

  const save = async () => {
    setSaving(true);
    setMsg('');
    setErr('');
    try {
      await window.fetchApiJson('/api/mentoring/assistant/settings/', {
        method: 'PATCH',
        auth: true,
        body: { base_prompt: prompt },
      });
      setMsg('Общий промпт сохранён');
    } catch (e) {
      setErr(e.message || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mb-4 rounded-2xl ring-1 ring-violet-200/80 bg-violet-50/40 overflow-hidden">
      <button type="button" onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-4 py-3 text-left hover:bg-violet-50/80">
        <span className="text-sm font-semibold text-violet-900">Общий промпт ИИ (вся школа)</span>
        <span className="text-[11px] text-violet-700/70 ml-auto">{open ? 'Скрыть' : 'Настроить'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-violet-100">
          <p className="text-[11px] text-ink/50 pt-3">
            Правила для всей школы. Дальше добавляются: курс → модуль → урок.
            Плейсхолдеры: {'{{course}}'}, {'{{module}}'}, {'{{title}}'}, {'{{kind}}'}, {'{{condition}}'}, {'{{instructions}}'}, {'{{tests}}'}, {'{{code}}'}.
          </p>
          {loading ? (
            <p className="text-sm text-ink/45">Загрузка…</p>
          ) : (
            <TextArea mono value={prompt} onChange={setPrompt} rows={8}
              placeholder="Общие правила помощника…"/>
          )}
          {err && <p className="text-sm text-red-600">{err}</p>}
          {msg && <p className="text-sm text-emerald-700">{msg}</p>}
          <button type="button" disabled={saving || loading} onClick={save}
            className="h-10 px-4 rounded-xl text-sm font-semibold bg-violet-600 text-white disabled:opacity-40">
            {saving ? 'Сохраняю…' : 'Сохранить общий промпт'}
          </button>
        </div>
      )}
    </div>
  );
}

function CoursePromptEditor({ courseId, outline, onSaved }) {
  const [open, setOpen] = React.useState(false);
  const [prompt, setPrompt] = React.useState(outline?.assistant_prompt || '');
  const [saving, setSaving] = React.useState(false);
  const [err, setErr] = React.useState('');

  React.useEffect(() => {
    setPrompt(outline?.assistant_prompt || '');
  }, [courseId, outline?.assistant_prompt]);

  if (!courseId) return null;

  const save = async () => {
    setSaving(true);
    setErr('');
    try {
      await window.fetchApiJson(
        `/api/mentoring/editor/courses/${encodeURIComponent(courseId)}/`,
        { method: 'PATCH', auth: true, body: { assistant_prompt: prompt } },
      );
      onSaved && onSaved();
      setOpen(false);
    } catch (ex) {
      setErr(ex.message || 'Ошибка');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mb-4 rounded-2xl ring-1 ring-sky-200/80 bg-sky-50/40 overflow-hidden">
      <button type="button" onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-4 py-3 text-left hover:bg-sky-50/80">
        <span className="text-sm font-semibold text-sky-900">Промпт ИИ курса</span>
        <span className="text-[11px] text-sky-700/70 ml-auto">
          {open ? 'Скрыть' : (outline?.assistant_prompt ? 'Задан ✓' : 'Настроить')}
        </span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-3 border-t border-sky-100">
          <p className="text-[11px] text-ink/50 pt-3">
            Добавляется ко всем урокам этого курса. Можно вставить {'{{condition}}'} / {'{{instructions}}'},
            чтобы модель видела текст текущего задания и могла его решать.
          </p>
          <TextArea mono value={prompt} onChange={setPrompt} rows={6}
            placeholder={'Например:\nУсловие задания:\n{{condition}}\n\nРеши задачу и объясни кратко.'}/>
          {err && <p className="text-sm text-red-600">{err}</p>}
          <button type="button" disabled={saving} onClick={save}
            className="h-10 px-4 rounded-xl text-sm font-semibold bg-sky-600 text-white disabled:opacity-40">
            {saving ? 'Сохраняю…' : 'Сохранить промпт курса'}
          </button>
        </div>
      )}
    </div>
  );
}

function ContentPackImportPanel({ courseId, onImported }) {
  const [open, setOpen] = React.useState(false);
  const [file, setFile] = React.useState(null);
  const [dragOver, setDragOver] = React.useState(false);
  const [preview, setPreview] = React.useState(null);
  const [busy, setBusy] = React.useState('');
  const [error, setError] = React.useState('');
  const inputRef = React.useRef(null);

  const reset = () => {
    setPreview(null);
    setError('');
  };

  const pickFile = (next) => {
    if (!next || !next.name.toLowerCase().endsWith('.zip')) {
      setError('Нужен ZIP-архив с manifest.json и questions.json.');
      return;
    }
    setFile(next);
    reset();
  };

  const upload = async (dryRun) => {
    if (!courseId || !file) return;
    setBusy(dryRun ? 'preview' : 'import');
    setError('');
    try {
      const form = new FormData();
      form.append('archive', file);
      if (dryRun) form.append('dry_run', '1');
      const data = await window.fetchApiForm(
        `/api/mentoring/editor/courses/${encodeURIComponent(courseId)}/import-pack/`,
        form,
        { method: 'POST', auth: true },
      );
      setPreview(data);
      if (!dryRun && typeof onImported === 'function') onImported();
    } catch (ex) {
      setError(ex.message || 'Не удалось обработать архив');
      setPreview(null);
    } finally {
      setBusy('');
    }
  };

  return (
    <div className="rounded-2xl ring-1 ring-emerald-200 bg-emerald-50/50 overflow-hidden">
      <button type="button" onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-emerald-50 transition-colors">
        <span className="text-xl">📦</span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-bold text-emerald-900">Импорт пакета заданий</div>
          <div className="text-[11px] text-emerald-800/70">ZIP с manifest.json и questions.json</div>
        </div>
        <span className="text-[11px] text-emerald-700/70">{open ? 'Скрыть' : 'Открыть'}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-4 border-t border-emerald-100">
          <div className="pt-3 text-[12px] text-ink/60 space-y-2">
            <p><strong>Что положить в ZIP:</strong></p>
            <ul className="list-disc pl-5 space-y-1">
              <li><code className="text-[11px]">manifest.json</code> — куда вешать пакет (курс, модуль, pack_id)</li>
              <li><code className="text-[11px]">questions.json</code> — теория и вопросы</li>
              <li><code className="text-[11px]">images/</code> — картинки (если есть в вопросах)</li>
            </ul>
            <p>Повторный импорт с тем же pack_id обновляет вопросы по названию, не дублирует.</p>
          </div>

          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              pickFile(e.dataTransfer.files?.[0] || null);
            }}
            onClick={() => inputRef.current?.click()}
            className={`rounded-xl border-2 border-dashed p-6 text-center cursor-pointer transition-colors
              ${dragOver ? 'border-emerald-400 bg-emerald-50' : 'border-emerald-200/80 bg-white/70 hover:border-emerald-300'}`}>
            <input ref={inputRef} type="file" accept=".zip,application/zip" className="hidden"
              onChange={(e) => pickFile(e.target.files?.[0] || null)} />
            <div className="text-2xl mb-2">⬆️</div>
            <p className="text-sm font-semibold text-ink/75">
              {file ? file.name : 'Перетащите ZIP сюда или нажмите для выбора'}
            </p>
            <p className="text-[11px] text-ink/45 mt-1">Только .zip</p>
          </div>

          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={!file || !!busy} onClick={() => upload(true)}
              className="h-10 px-4 rounded-xl text-sm font-semibold bg-white ring-1 ring-emerald-200 text-emerald-800 disabled:opacity-40">
              {busy === 'preview' ? 'Проверяю…' : 'Проверить (без записи)'}
            </button>
            <button type="button" disabled={!file || !!busy} onClick={() => upload(false)}
              className="h-10 px-4 rounded-xl text-sm font-semibold bg-emerald-600 text-white disabled:opacity-40">
              {busy === 'import' ? 'Импортирую…' : 'Импортировать в курс'}
            </button>
          </div>

          {error && (
            <div className="p-3 rounded-xl bg-red-50 text-red-700 text-sm ring-1 ring-red-100">{error}</div>
          )}

          {preview && (
            <div className="p-4 rounded-xl bg-white ring-1 ring-emerald-100 space-y-3 text-sm">
              <p className="font-semibold text-emerald-900">{preview.message}</p>
              <div className="grid sm:grid-cols-2 gap-2 text-[12px] text-ink/65">
                <div><span className="text-ink/40">pack_id:</span> {preview.pack_id}</div>
                <div><span className="text-ink/40">модуль:</span> {preview.module_title}</div>
                <div><span className="text-ink/40">создать:</span> {preview.created}</div>
                <div><span className="text-ink/40">обновить:</span> {preview.updated}</div>
              </div>
              {preview.lessons?.length > 0 && (
                <div>
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-ink/40 mb-2">
                    Уроки в архиве ({preview.lesson_count || preview.lessons.length})
                  </div>
                  <ul className="max-h-40 overflow-y-auto space-y-1 text-[12px] text-ink/70">
                    {preview.lessons.map((ls) => (
                      <li key={`${ls.index}-${ls.title}`} className="flex gap-2">
                        <span className="text-ink/35 shrink-0">{ls.index}.</span>
                        <span className="shrink-0">{KIND_META[ls.type]?.emoji || '•'}</span>
                        <span className="truncate">{ls.title}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ModulePromptEditor({ mod, onSaved }) {
  const [open, setOpen] = React.useState(false);
  const [prompt, setPrompt] = React.useState(mod.assistant_prompt || '');
  const [saving, setSaving] = React.useState(false);
  const [err, setErr] = React.useState('');

  React.useEffect(() => {
    setPrompt(mod.assistant_prompt || '');
  }, [mod.public_id, mod.assistant_prompt]);

  const save = async (e) => {
    e.stopPropagation();
    setSaving(true);
    setErr('');
    try {
      await window.fetchApiJson(
        `/api/mentoring/editor/modules/${encodeURIComponent(mod.public_id)}/`,
        { method: 'PATCH', auth: true, body: { assistant_prompt: prompt } },
      );
      onSaved && onSaved();
      setOpen(false);
    } catch (ex) {
      setErr(ex.message || 'Ошибка');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mt-1 mb-2">
      <button type="button"
        onClick={(e) => { e.stopPropagation(); setOpen((v) => !v); }}
        className="text-[10px] font-semibold px-2 py-1 rounded-md bg-violet-50 text-violet-700 hover:bg-violet-100">
        {open ? 'Скрыть промпт модуля' : (mod.assistant_prompt ? 'Промпт модуля ✓' : 'Промпт модуля')}
      </button>
      {open && (
        <div className="mt-2 p-3 rounded-xl bg-paper ring-1 ring-black/[0.06] space-y-2" onClick={(e) => e.stopPropagation()}>
          <p className="text-[10px] text-ink/45">
            Добавляется ко всем урокам модуля (после общего и курса). Вставьте {'{{condition}}'} / {'{{instructions}}'},
            если модель должна видеть текст задания и уметь его выполнять.
          </p>
          <TextArea mono value={prompt} onChange={setPrompt} rows={5}
            placeholder={'Условие:\n{{condition}}\n\nИнструкции:\n{{instructions}}\n\nРеши и проверь по {{tests}}.'}/>
          {err && <p className="text-xs text-red-600">{err}</p>}
          <button type="button" disabled={saving} onClick={save}
            className="h-8 px-3 rounded-lg text-xs font-semibold bg-violet-600 text-white disabled:opacity-40">
            {saving ? '…' : 'Сохранить'}
          </button>
        </div>
      )}
    </div>
  );
}

function ContentEditorPanel({ courseId, courses, onCourseChange, onCoursesRefresh }) {
  const [, navigate] = window.useHashRoute();
  const [outline, setOutline] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [selected, setSelected] = React.useState(null);
  const [expandedModules, setExpandedModules] = React.useState({});
  const [creating, setCreating] = React.useState(null);
  const [newCourseTitle, setNewCourseTitle] = React.useState('');
  const [creatingCourse, setCreatingCourse] = React.useState(false);

  const loadOutline = React.useCallback(() => {
    if (!courseId) return;
    setLoading(true);
    setError('');
    window.fetchApiJson(`/api/mentoring/editor/courses/${encodeURIComponent(courseId)}/`, { auth: true })
      .then((d) => {
        setOutline(d);
        setExpandedModules((prev) => {
          const next = { ...prev };
          (d.modules || []).forEach((m) => { if (next[m.public_id] === undefined) next[m.public_id] = true; });
          return next;
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [courseId]);

  React.useEffect(() => { loadOutline(); }, [loadOutline]);

  const refreshCourses = async (selectId) => {
    if (typeof onCoursesRefresh === 'function') {
      await onCoursesRefresh(selectId);
    } else if (selectId) {
      onCourseChange(selectId);
    }
  };

  const createCourse = async () => {
    const title = newCourseTitle.trim();
    if (!title) return;
    setCreatingCourse(true);
    setError('');
    try {
      const created = await window.fetchApiJson('/api/mentoring/editor/courses/', {
        method: 'POST',
        body: { title, description: title },
        auth: true,
      });
      setNewCourseTitle('');
      await refreshCourses(created.public_id);
    } catch (e) {
      setError(e.message);
    } finally {
      setCreatingCourse(false);
    }
  };

  const createModule = async () => {
    if (!courseId) return;
    setCreating('module');
    try {
      const mod = await window.fetchApiJson(
        `/api/mentoring/editor/courses/${encodeURIComponent(courseId)}/modules/`,
        { method: 'POST', body: { title: 'Новый модуль' }, auth: true },
      );
      loadOutline();
      setExpandedModules((p) => ({ ...p, [mod.public_id]: true }));
    } catch (e) {
      setError(e.message);
    } finally {
      setCreating(null);
    }
  };

  const createExam = async () => {
    if (!courseId) return;
    setCreating('exam');
    try {
      await window.fetchApiJson(
        `/api/mentoring/editor/courses/${encodeURIComponent(courseId)}/exams/`,
        { method: 'POST', body: { title: 'Контрольная работа', duration_minutes: 45 }, auth: true },
      );
      loadOutline();
    } catch (e) {
      setError(e.message);
    } finally {
      setCreating(null);
    }
  };

  const createLesson = async (moduleId, kind) => {
    setCreating(`${moduleId}-${kind}`);
    try {
      const created = await window.fetchApiJson(
        `/api/mentoring/editor/modules/${encodeURIComponent(moduleId)}/lessons/`,
        { method: 'POST', body: { kind, title: `Новый ${KIND_META[kind]?.label || kind}` }, auth: true },
      );
      loadOutline();
      setSelected({ kind, public_id: created.public_id, module_public_id: moduleId, title: created.title });
      setExpandedModules((p) => ({ ...p, [moduleId]: true }));
    } catch (e) {
      setError(e.message);
    } finally {
      setCreating(null);
    }
  };

  return (
    <div className="space-y-4">
      <GlobalAssistantPromptPanel />
      <CoursePromptEditor courseId={courseId} outline={outline} onSaved={loadOutline} />
      <ContentPackImportPanel courseId={courseId} onImported={loadOutline} />
      <div className="grid lg:grid-cols-[minmax(260px,320px)_1fr] gap-6 min-h-[560px]">
      <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft flex flex-col min-h-[480px] overflow-hidden">
        <div className="p-4 border-b border-black/[0.06] space-y-3">
          <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/40">Курс</div>
          <select value={courseId || ''} onChange={(e) => onCourseChange(e.target.value)}
            className="w-full h-10 px-3 rounded-xl bg-paper ring-1 ring-black/[0.08] text-sm">
            {(courses || []).map((c) => (
              <option key={c.course_public_id} value={c.course_public_id}>{c.course_title}</option>
            ))}
          </select>
          <div className="flex gap-2">
            <input type="text" value={newCourseTitle} onChange={(e) => setNewCourseTitle(e.target.value)}
              placeholder="Новый курс…"
              className="flex-1 h-9 px-3 rounded-lg bg-paper ring-1 ring-black/[0.08] text-xs"/>
            <button type="button" disabled={creatingCourse || !newCourseTitle.trim()} onClick={createCourse}
              className="h-9 px-3 rounded-lg text-xs font-semibold bg-violet-600 text-white disabled:opacity-40">
              +
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" disabled={!courseId || creating === 'module'} onClick={createModule}
              className="text-[11px] font-semibold px-2.5 py-1.5 rounded-lg bg-black/[0.04] hover:bg-violet-100 hover:text-violet-700 disabled:opacity-40">
              + Модуль
            </button>
            <button type="button" disabled={!courseId || creating === 'exam'} onClick={createExam}
              className="text-[11px] font-semibold px-2.5 py-1.5 rounded-lg bg-black/[0.04] hover:bg-amber-100 hover:text-amber-800 disabled:opacity-40">
              + КР
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin p-3">
          {loading && !outline ? (
            <p className="text-sm text-ink/45 p-4">Загрузка структуры…</p>
          ) : (
            <>
              {(outline?.modules || []).length === 0 ? (
                <p className="text-sm text-ink/45 p-4">Нет модулей — нажмите «+ Модуль».</p>
              ) : (
                outline.modules.map((mod) => (
                  <div key={mod.public_id} className="mb-3">
                    <button type="button" onClick={() => setExpandedModules((p) => ({ ...p, [mod.public_id]: !p[mod.public_id] }))}
                      className="w-full flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-black/[0.03] text-left">
                      <span className="text-ink/35 text-xs">{expandedModules[mod.public_id] ? '▼' : '▶'}</span>
                      <span className="font-semibold text-sm text-ink truncate">{mod.title}</span>
                      <span className="text-[10px] text-ink/35 ml-auto">{mod.lessons?.length || 0}</span>
                    </button>
                    {expandedModules[mod.public_id] && (
                      <div className="ml-2 pl-2 border-l border-black/[0.06] space-y-1">
                        <ModulePromptEditor mod={mod} onSaved={loadOutline} />
                        {(mod.lessons || []).map((ls) => {
                          const m = KIND_META[ls.kind] || KIND_META.theory;
                          const active = selected?.public_id === ls.public_id;
                          return (
                            <button key={`${ls.kind}-${ls.public_id}`} type="button"
                              onClick={() => setSelected({ ...ls, module_public_id: mod.public_id })}
                              className={`w-full flex items-center gap-2 px-3 py-2 rounded-xl text-left text-sm transition-colors
                                ${active ? 'bg-violet-50 ring-1 ring-violet-200 text-violet-900' : 'hover:bg-black/[0.025] text-ink/75'}
                                ${!ls.is_active ? 'opacity-45' : ''}`}>
                              <span>{m.emoji}</span>
                              <span className="truncate flex-1">{ls.title}</span>
                            </button>
                          );
                        })}
                        <div className="pt-2 flex flex-wrap gap-1">
                          {Object.entries(KIND_META).map(([k, m]) => (
                            <button key={k} type="button" disabled={creating === `${mod.public_id}-${k}`}
                              onClick={() => createLesson(mod.public_id, k)}
                              className="text-[10px] font-semibold px-2 py-1 rounded-md bg-black/[0.04] hover:bg-violet-100 hover:text-violet-700 disabled:opacity-40">
                              + {m.emoji}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
              {(outline?.exams || []).length > 0 && (
                <div className="mt-4 pt-3 border-t border-black/[0.06]">
                  <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/40 px-2 mb-2">Контрольные</div>
                  {outline.exams.map((ex) => (
                    <div key={ex.public_id}
                      className="px-3 py-2 rounded-xl text-sm text-ink/70 bg-amber-50/60 ring-1 ring-amber-100 mb-1">
                      📝 {ex.title}
                    </div>
                  ))}
                  <p className="text-[10px] text-ink/40 px-2 mt-2">
                    Задания КР пока добавляются через структуру курса в панели владельца при необходимости. Unlock/retake — вкладка «КР».
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft p-5 sm:p-6 min-h-[480px] flex flex-col">
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 text-red-700 text-sm ring-1 ring-red-100">{error}</div>
        )}
        {!selected ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center py-16 px-6">
            <div className="text-5xl mb-4 opacity-30">✏️</div>
            <h3 className="text-lg font-bold text-ink/70">Редактор контента</h3>
            <p className="text-sm text-ink/45 mt-2 max-w-sm">
              Создайте модуль, добавьте уроки слева. Всё для менторов — здесь, без Django Admin.
            </p>
          </div>
        ) : (
          <LessonEditorForm
            lesson={selected}
            courseId={courseId}
            moduleId={selected.module_public_id}
            navigate={navigate}
            onSaved={() => loadOutline()}
            onDeleted={() => { setSelected(null); loadOutline(); }}
          />
        )}
      </div>
    </div>
    </div>
  );
}

window.ContentEditorPanel = ContentEditorPanel;
