// Content editor — редактирование уроков курса (ментор / admin)

const I = window.I;
const Routes = window.Routes;

const KIND_META = {
  theory: { emoji: '📖', label: 'Теория', color: 'text-blue-600 bg-blue-50' },
  radio: { emoji: '🔘', label: 'Radio', color: 'text-violet-600 bg-violet-50' },
  checkbox: { emoji: '☑️', label: 'Checkbox', color: 'text-cyan-600 bg-cyan-50' },
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

  React.useEffect(() => {
    setLoading(true);
    setError('');
    setSuccess('');
    setVideoFile(null);
    setTab('main');
    window.fetchApiJson(
      `/api/mentoring/editor/lessons/${encodeURIComponent(kind)}/${encodeURIComponent(lesson.public_id)}/`,
      { auth: true },
    )
      .then((d) => { setForm(d); setLoading(false); })
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
      const saved = await saveLesson(kind, form.public_id, payload, videoFile);
      setForm(saved);
      setVideoFile(null);
      setSuccess('Сохранено');
      onSaved?.(saved);
    } catch (e) {
      setError(e.message || 'Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!form || !window.confirm('Скрыть урок? Ученики перестанут его видеть.')) return;
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
                  <FieldLabel hint="HTML поддерживается">Содержание</FieldLabel>
                  <TextArea value={form.content} onChange={(v) => setForm({ ...form, content: v })} rows={12}/>
                </div>
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
              </>
            )}

            {(kind === 'radio' || kind === 'checkbox') && (
              <div>
                <FieldLabel>Текст вопроса</FieldLabel>
                <TextArea value={form.question_text} onChange={(v) => setForm({ ...form, question_text: v })} rows={4}/>
              </div>
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
              <FieldLabel hint="Показывается ученику на вкладке задания">Заметка преподавателя</FieldLabel>
              <TextArea value={form.comment} onChange={(v) => setForm({ ...form, comment: v })} rows={3}/>
            </div>

            {(kind === 'radio' || kind === 'checkbox') && (
              <div>
                <FieldLabel hint="Короткий текст после ответа">Пояснение после ответа</FieldLabel>
                <TextArea value={form.explanation} onChange={(v) => setForm({ ...form, explanation: v })} rows={3}/>
              </div>
            )}

            <div className="grid sm:grid-cols-3 gap-4">
              {(kind === 'radio' || kind === 'checkbox' || kind === 'coding') && (
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

function ContentEditorPanel({ courseId, courses, onCourseChange }) {
  const [, navigate] = window.useHashRoute();
  const [outline, setOutline] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [selected, setSelected] = React.useState(null);
  const [expandedModules, setExpandedModules] = React.useState({});
  const [creating, setCreating] = React.useState(null);

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
          <p className="text-[11px] text-ink/40 leading-relaxed">
            Выберите урок слева или создайте новый. Видео и текст решения — вкладка «Эталонное решение».
          </p>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin p-3">
          {loading && !outline ? (
            <p className="text-sm text-ink/45 p-4">Загрузка структуры…</p>
          ) : (outline?.modules || []).length === 0 ? (
            <p className="text-sm text-ink/45 p-4">В курсе пока нет модулей. Добавьте их в Django Admin.</p>
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
              Выберите урок в дереве слева или создайте новый: теорию, тест или задачу с кодом.
            </p>
            <a href="/admin/content/" target="_blank" rel="noreferrer"
              className="mt-6 text-xs text-violet-600 font-semibold hover:underline">
              Django Admin (модули курса) ↗
            </a>
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
  );
}

window.ContentEditorPanel = ContentEditorPanel;
