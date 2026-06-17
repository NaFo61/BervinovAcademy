// EXAM page — контрольная работа (КР): старт, таймер, задания, результат

const Routes = window.Routes;
const I = window.I;
const FM = window.FM;

const CODE_POLL_INTERVAL_MS = 1200;
const CODE_POLL_MAX_ATTEMPTS = 90;
const DEFAULT_PYTHON_CODE = `def solve():
    pass

print(solve())`;

function examStepKey(kind, id) {
  return `${kind}-${id}`;
}

function parseStepParam(stepParam) {
  if (!stepParam) return { kind: null, id: null };
  const i = stepParam.indexOf('-');
  if (i <= 0) return { kind: null, id: null };
  return { kind: stepParam.slice(0, i), id: stepParam.slice(i + 1) };
}

function formatTimer(totalSeconds) {
  const sec = Math.max(0, totalSeconds || 0);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function isCodeSubmissionFinal(status) {
  return status && status !== 'pending' && status !== 'running';
}

async function pollCodeSubmission(publicId) {
  for (let i = 0; i < CODE_POLL_MAX_ATTEMPTS; i++) {
    const sub = await window.fetchApiJson(
      `/api/progress/code/${encodeURIComponent(publicId)}/`,
      { auth: true },
    );
    if (isCodeSubmissionFinal(sub.status)) return sub;
    await new Promise((r) => setTimeout(r, CODE_POLL_INTERVAL_MS));
  }
  throw new Error('Проверка занимает слишком много времени.');
}

function stepIcon(kind) {
  if (kind === 'theory') return '📖';
  if (kind === 'radio') return '?';
  if (kind === 'checkbox') return '☑';
  if (kind === 'coding') return '>_';
  return '•';
}

function isStepLockedLinear(steps, index, navigationMode) {
  if (navigationMode !== 'linear') return false;
  for (let i = 0; i < index; i++) {
    const s = steps[i];
    if (!s.answered) return true;
    if (s.kind !== 'theory' && !s.is_correct) return true;
  }
  return false;
}

function accessReasonLabel(reason) {
  if (reason.code === 'prerequisite_module') {
    return `Сначала пройдите модуль «${reason.module_title}»`;
  }
  if (reason.code === 'mentor_unlock_required') {
    return 'Нужно разрешение ментора для начала';
  }
  if (reason.code === 'already_completed') {
    return 'Контрольная уже сдана — переписывание только по разрешению ментора';
  }
  return 'Нельзя начать контрольную';
}

// ─── Timer bar ─────────────────────────────────────────────────────────────

function ExamTimerBar({ remaining, durationMinutes, warn }) {
  const total = (durationMinutes || 45) * 60;
  const pct = total ? Math.min(100, (remaining / total) * 100) : 0;
  const urgent = remaining <= 300;
  return (
    <div className={`flex items-center gap-3 px-4 py-2.5 border-b shrink-0 ${
      urgent ? 'bg-red-50 border-red-200' : 'bg-amber-50/80 border-amber-200/80'
    }`}>
      <I.Clock className={`w-4 h-4 shrink-0 ${urgent ? 'text-red-600' : 'text-amber-700'}`}/>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between text-[11px] font-semibold mb-1">
          <span className={urgent ? 'text-red-700' : 'text-amber-800'}>Осталось времени</span>
          <span className={`font-mono text-sm ${urgent ? 'text-red-700 animate-pulse' : 'text-amber-900'}`}>
            {formatTimer(remaining)}
          </span>
        </div>
        <div className="h-1.5 bg-black/[0.08] rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-1000 ${urgent ? 'bg-red-500' : 'bg-amber-500'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      {warn > 0 && (
        <span className="text-[10px] font-bold px-2 py-1 rounded-md bg-amber-500/15 text-amber-900 shrink-0">
          ⚠ {warn}
        </span>
      )}
    </div>
  );
}

// ─── Landing ─────────────────────────────────────────────────────────────────

function ExamLanding({ exam, access, starting, onStart, onBack, embedded }) {
  const latest = access?.latest_attempt;
  const wrapClass = embedded
    ? 'py-10 px-5'
    : 'min-h-[calc(100vh-64px)] mesh-bg-dim flex items-center justify-center px-5 py-12';
  return (
    <div className={wrapClass}>
      <div className={`max-w-lg w-full bg-white rounded-3xl shadow-glow ring-1 ring-black/[0.06] p-8 sm:p-10 ${embedded ? 'mx-auto' : ''}`}>
        <div className="text-[11px] font-bold uppercase tracking-widest text-violet-600 mb-2">
          Контрольная работа
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">{exam.title}</h1>
        {exam.description && (
          <p className="mt-3 text-sm text-ink/65 leading-relaxed">{exam.description}</p>
        )}

        <div className="mt-6 grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-violet-500/[0.06] p-4">
            <div className="text-[10px] font-semibold uppercase tracking-widest text-ink/45">Время</div>
            <div className="text-lg font-bold mt-1">{exam.duration_minutes} мин</div>
          </div>
          <div className="rounded-xl bg-cyan-500/[0.06] p-4">
            <div className="text-[10px] font-semibold uppercase tracking-widest text-ink/45">Заданий</div>
            <div className="text-lg font-bold mt-1">{(exam.lessons || []).length}</div>
          </div>
        </div>

        <ul className="mt-6 space-y-2 text-sm text-ink/70">
          <li className="flex gap-2">
            <span className="text-violet-500">•</span>
            {exam.navigation_mode === 'linear'
              ? 'Задания строго по порядку'
              : 'Можно переключаться между заданиями'}
          </li>
          <li className="flex gap-2">
            <span className="text-violet-500">•</span>
            {exam.tab_policy === 'warn'
              ? `При уходе с вкладки — предупреждение (лимит ${exam.tab_warn_limit})`
              : 'Уход с вкладки логируется для ментора'}
          </li>
          <li className="flex gap-2">
            <span className="text-violet-500">•</span>
            Зачёт от {exam.pass_score_percent}% баллов
          </li>
        </ul>

        {(access?.reasons || []).length > 0 && (
          <div className="mt-6 p-4 rounded-xl bg-rose-50 ring-1 ring-rose-200 text-sm text-rose-900 space-y-2">
            {(access.reasons || []).map((r, i) => (
              <div key={i}>{accessReasonLabel(r)}</div>
            ))}
          </div>
        )}

        {latest && latest.status !== 'in_progress' && (
          <div className="mt-6 p-4 rounded-xl bg-black/[0.03] ring-1 ring-black/[0.06] text-sm">
            <div className="font-semibold text-ink/80">Последняя попытка</div>
            <div className="mt-1 text-ink/60">
              {latest.score}/{latest.max_score} баллов · {latest.passed ? 'зачёт' : 'незачёт'}
            </div>
          </div>
        )}

        <div className="mt-8 flex flex-col sm:flex-row gap-3">
          <button type="button" onClick={onStart} disabled={!access?.can_start || starting}
            className="flex-1 h-12 rounded-xl btn-grad btn-shimmer text-white font-semibold shadow-soft
              disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2">
            {starting ? (
              <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"/>
            ) : (
              <I.Play className="w-4 h-4"/>
            )}
            {starting ? 'Запуск…' : 'Начать контрольную'}
          </button>
          <button type="button" onClick={onBack}
            className="h-12 px-5 rounded-xl border border-black/[0.08] text-sm font-semibold text-ink/60 hover:border-violet-300">
            К курсу
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Result ──────────────────────────────────────────────────────────────────

function ExamResultScreen({ attempt, exam, courseId, navigate, embedded }) {
  const pct = attempt.max_score
    ? Math.round((attempt.score / attempt.max_score) * 100)
    : 0;
  const wrapClass = embedded
    ? 'py-4'
    : 'min-h-[calc(100vh-64px)] bg-paper flex items-center justify-center px-5 py-12';
  return (
    <div className={wrapClass}>
      <div className="max-w-2xl w-full">
        <div className={`rounded-3xl p-8 sm:p-10 ring-1 shadow-glow text-center ${
          attempt.passed
            ? 'bg-emerald-50/50 ring-emerald-200'
            : 'bg-white ring-black/[0.06]'
        }`}>
          <div className="text-5xl mb-4">{attempt.passed ? '🎉' : '📝'}</div>
          <h1 className="text-2xl font-extrabold">
            {attempt.passed ? 'Контрольная сдана!' : 'Контрольная завершена'}
          </h1>
          <p className="mt-2 text-ink/60">{exam.title}</p>
          <div className="mt-6 text-4xl font-extrabold grad-text">
            {attempt.score} <span className="text-2xl text-ink/40">/ {attempt.max_score}</span>
          </div>
          <div className="text-sm text-ink/55 mt-2">{pct}% · порог {exam.pass_score_percent}%</div>
          {attempt.submit_reason === 'timeout' && (
            <p className="mt-3 text-sm text-amber-700">Время вышло — сохранены ответы на момент окончания</p>
          )}
          {attempt.submit_reason === 'warn_limit' && (
            <p className="mt-3 text-sm text-amber-700">Автосдача после предупреждений о переключении вкладки</p>
          )}
        </div>

        <div className="mt-6 bg-white rounded-2xl ring-1 ring-black/[0.06] p-6">
          <div className="text-sm font-bold mb-4">Разбор по заданиям</div>
          <div className="space-y-2">
            {(attempt.steps || []).map((s, i) => (
              <div key={s.public_id || i}
                className="flex items-center gap-3 p-3 rounded-xl bg-black/[0.02] ring-1 ring-black/[0.04]">
                <span className="text-lg">{stepIcon(s.kind)}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{s.title}</div>
                  <div className="text-[11px] text-ink/45">
                    {s.kind === 'theory' ? 'теория' : `${s.points_earned || 0} / ${s.max_points || 0} б.`}
                  </div>
                </div>
                {s.kind === 'theory' ? (
                  s.answered ? <span className="check-dot"/> : <span className="w-4 h-4 rounded-full bg-ink/10"/>
                ) : s.is_correct ? (
                  <span className="check-dot"/>
                ) : s.answered ? (
                  <span className="cross-dot"/>
                ) : (
                  <span className="text-[11px] text-ink/40">—</span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 flex gap-3 justify-center">
          <button type="button"
            onClick={() => navigate(window.Routes.COURSE, { id: courseId })}
            className="h-11 px-6 rounded-xl btn-grad text-white font-semibold">
            К курсу
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Step panels ─────────────────────────────────────────────────────────────

function ExamTheoryPanel({ lesson, marked, onMark }) {
  React.useEffect(() => {
    if (marked || !lesson?.public_id) return;
    onMark();
  }, [lesson?.public_id, marked, onMark]);

  return (
    <div>
      <ExamLessonHeader kind="theory" title={lesson.title} label="Справочная теория"/>
      <window.VideoExplanation video={lesson.video} title="Видео"/>
      <div
        className="theory-content mt-6"
        dangerouslySetInnerHTML={{ __html: lesson.content || '<p>Текст теории.</p>' }}
      />
      <div className="mt-8 flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
        <span className="check-dot"/>
        <span className="text-sm font-semibold text-emerald-700">
          {marked ? 'Просмотрено' : 'Отмечаем просмотр…'}
        </span>
      </div>
    </div>
  );
}

function ExamLessonHeader({ kind, title, label }) {
  const icons = { theory: '📖', radio: '🔘', checkbox: '☑️', coding: '💻' };
  return (
    <div className="flex items-start gap-4">
      <div className="w-11 h-11 rounded-xl bg-violet-500/10 flex items-center justify-center text-2xl shrink-0">
        {icons[kind] || '📄'}
      </div>
      <div>
        <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/40">{label}</div>
        <h1 className="text-[22px] font-extrabold text-ink leading-tight mt-1">{title}</h1>
      </div>
    </div>
  );
}

function ExamRadioPanel({ lesson, step, attemptId, onUpdated }) {
  const [selected, setSelected] = React.useState(step?.payload?.selected_answer_public_id || null);
  const [loading, setLoading] = React.useState(false);
  const answered = step?.answered;

  React.useEffect(() => {
    setSelected(step?.payload?.selected_answer_public_id || null);
  }, [lesson.public_id, step?.answered]);

  const submit = async () => {
    if (!selected || answered || loading) return;
    setLoading(true);
    try {
      const data = await window.fetchApiJson(
        `/api/exams/attempts/${encodeURIComponent(attemptId)}/radio/`,
        { method: 'POST', body: { question: lesson.public_id, selected_answer: selected }, auth: true },
      );
      onUpdated(data);
    } catch (e) {
      alert(e.message || 'Не удалось отправить ответ');
    }
    setLoading(false);
  };

  return (
    <div>
      <ExamLessonHeader kind="radio" title={lesson.title} label="Один правильный ответ"/>
      <div className="mt-6 p-6 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft">
        <p className="text-[15px] text-ink/80 leading-relaxed">{lesson.question_text}</p>
      </div>
      <div className="mt-5 space-y-3">
        {(lesson.answer_options || []).map((opt) => {
          const isSel = selected === opt.public_id;
          const showOk = answered && isSel && step.is_correct;
          const showBad = answered && isSel && !step.is_correct;
          return (
            <label key={opt.public_id}
              className={`flex items-center gap-4 p-4 rounded-xl ring-1 transition-all
                ${answered ? 'cursor-default' : 'cursor-pointer hover:ring-violet-300 hover:bg-violet-50/60'}
                ${showOk ? 'ring-emerald-400 bg-emerald-50' : showBad ? 'ring-red-400 bg-red-50' : isSel ? 'ring-violet-500 bg-violet-50' : 'ring-black/[0.06] bg-white'}
              `}>
              <input type="radio" className="sr-only" checked={isSel} disabled={answered}
                onChange={() => !answered && setSelected(opt.public_id)}/>
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0
                ${showOk ? 'border-emerald-500 bg-emerald-500' : showBad ? 'border-red-500 bg-red-500' : isSel ? 'border-violet-600 bg-violet-600' : 'border-ink/20'}
              `}>
                {isSel && <div className="w-2 h-2 rounded-full bg-white"/>}
              </div>
              <span className="text-[14px] font-medium flex-1">{opt.text}</span>
              {showOk && <I.Check className="w-5 h-5 text-emerald-500"/>}
              {showBad && <I.X className="w-5 h-5 text-red-500"/>}
            </label>
          );
        })}
      </div>
      {!answered && (
        <button type="button" onClick={submit} disabled={!selected || loading}
          className="mt-7 btn-grad h-12 px-7 rounded-xl text-white font-semibold disabled:opacity-40 inline-flex items-center gap-2">
          {loading ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"/> : <I.Send className="w-4 h-4"/>}
          Ответить
        </button>
      )}
      {answered && (
        <div className={`mt-7 p-4 rounded-xl border ${step.is_correct ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'}`}>
          <span className="font-bold text-sm">{step.is_correct ? 'Верно' : 'Неверно'}</span>
          {step.points_earned > 0 && (
            <span className="ml-2 text-xs text-emerald-700">+{step.points_earned} б.</span>
          )}
        </div>
      )}
    </div>
  );
}

function ExamCheckboxPanel({ lesson, step, attemptId, onUpdated }) {
  const initial = new Set(step?.payload?.selected_answer_public_ids || []);
  const [selected, setSelected] = React.useState(initial);
  const [loading, setLoading] = React.useState(false);
  const answered = step?.answered;

  React.useEffect(() => {
    setSelected(new Set(step?.payload?.selected_answer_public_ids || []));
  }, [lesson.public_id, step?.answered]);

  const toggle = (id) => {
    if (answered) return;
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const submit = async () => {
    if (answered || loading) return;
    setLoading(true);
    try {
      const data = await window.fetchApiJson(
        `/api/exams/attempts/${encodeURIComponent(attemptId)}/checkbox/`,
        {
          method: 'POST',
          body: { question: lesson.public_id, selected_answers: [...selected] },
          auth: true,
        },
      );
      onUpdated(data);
    } catch (e) {
      alert(e.message || 'Не удалось отправить ответ');
    }
    setLoading(false);
  };

  return (
    <div>
      <ExamLessonHeader kind="checkbox" title={lesson.title} label="Несколько правильных ответов"/>
      <div className="mt-6 p-6 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft">
        <p className="text-[15px] text-ink/80 leading-relaxed">{lesson.question_text}</p>
      </div>
      <div className="mt-5 space-y-3">
        {(lesson.answer_options || []).map((opt) => {
          const isSel = selected.has(opt.public_id);
          return (
            <label key={opt.public_id}
              className={`flex items-center gap-4 p-4 rounded-xl ring-1 cursor-pointer
                ${answered ? 'cursor-default' : 'hover:ring-cyan-300'}
                ${isSel ? 'ring-cyan-500 bg-cyan-50' : 'ring-black/[0.06] bg-white'}
              `}>
              <input type="checkbox" className="sr-only" checked={isSel} disabled={answered}
                onChange={() => toggle(opt.public_id)}/>
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${isSel ? 'border-cyan-600 bg-cyan-600' : 'border-ink/20'}`}>
                {isSel && <I.Check className="w-3 h-3 text-white"/>}
              </div>
              <span className="text-[14px] font-medium flex-1">{opt.text}</span>
            </label>
          );
        })}
      </div>
      {!answered && (
        <button type="button" onClick={submit} disabled={loading}
          className="mt-7 btn-grad h-12 px-7 rounded-xl text-white font-semibold disabled:opacity-40 inline-flex items-center gap-2">
          {loading ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"/> : <I.Send className="w-4 h-4"/>}
          Ответить
        </button>
      )}
      {answered && (
        <div className={`mt-7 p-4 rounded-xl border ${step.is_correct ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'}`}>
          <span className="font-bold text-sm">{step.is_correct ? 'Верно' : 'Неверно'}</span>
        </div>
      )}
    </div>
  );
}

function ExamCodingPanel({ lesson, step, attemptId, onUpdated }) {
  const [code, setCode] = React.useState(lesson.initial_code || DEFAULT_PYTHON_CODE);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [result, setResult] = React.useState(null);
  const answered = step?.answered;
  const passed = step?.is_correct;

  React.useEffect(() => {
    setCode(lesson.initial_code || DEFAULT_PYTHON_CODE);
    setResult(null);
    setError('');
  }, [lesson.public_id]);

  const submit = async () => {
    if (loading) return;
    const trimmed = (code || '').trim();
    if (!trimmed) { setError('Введите код'); return; }
    setLoading(true);
    setError('');
    try {
      const resp = await window.fetchApiJson(
        `/api/exams/attempts/${encodeURIComponent(attemptId)}/code/`,
        { method: 'POST', body: { challenge: lesson.public_id, code: trimmed }, auth: true },
      );
      onUpdated(resp.attempt);
      let sub = resp.submission;
      setResult(sub);
      if (!isCodeSubmissionFinal(sub.status)) {
        sub = await pollCodeSubmission(sub.public_id);
        setResult(sub);
        const fresh = await window.fetchApiJson(
          `/api/exams/attempts/${encodeURIComponent(attemptId)}/`,
          { auth: true },
        );
        onUpdated(fresh);
      }
    } catch (e) {
      setError(e.message || 'Ошибка отправки');
    }
    setLoading(false);
  };

  return (
    <div>
      <ExamLessonHeader kind="coding" title={lesson.title} label="Задача с кодом"/>
      <div className="mt-6 prose prose-sm max-w-none text-ink/75">
        <p>{lesson.description}</p>
        {lesson.instructions && <p className="whitespace-pre-wrap">{lesson.instructions}</p>}
      </div>
      <window.VideoExplanation video={lesson.video} title="Разбор"/>
      <div className="mt-6 rounded-2xl overflow-hidden ring-1 ring-black/[0.06] bg-[#0f172a]">
        <div className="px-4 py-2 border-b border-white/10 text-xs text-slate-400 font-mono">solution.py</div>
        <textarea value={code} onChange={(e) => setCode(e.target.value)} disabled={answered && passed}
          className="w-full min-h-[260px] bg-transparent text-slate-100 font-mono text-xs p-4 resize-y focus:outline-none"/>
      </div>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {(!answered || !passed) && (
        <button type="button" onClick={submit} disabled={loading}
          className="mt-6 btn-grad h-12 px-7 rounded-xl text-white font-semibold disabled:opacity-40 inline-flex items-center gap-2">
          {loading ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"/> : <I.Send className="w-4 h-4"/>}
          Отправить на проверку
        </button>
      )}
      {result && (
        <div className={`mt-6 p-4 rounded-xl border text-sm ${
          result.status === 'completed' ? 'bg-emerald-50 border-emerald-200' : 'bg-rose-50 border-rose-200'
        }`}>
          {result.status === 'completed' ? 'Все тесты пройдены' : 'Решение не принято'}
          {result.total_tests > 0 && (
            <span className="ml-2 text-ink/60">{result.tests_passed}/{result.total_tests} тестов</span>
          )}
        </div>
      )}
      {answered && passed && (
        <div className="mt-4 flex items-center gap-2 text-sm text-emerald-700 font-semibold">
          <span className="check-dot"/> Задача зачтена · +{step.points_earned || 0} б.
        </div>
      )}
    </div>
  );
}

// ─── Active session ────────────────────────────────────────────────────────────

function ExamActiveSession({
  exam,
  attempt,
  courseId,
  stepParam,
  navigate,
  onAttemptChange,
  onFinish,
  embedded,
}) {
  const [remaining, setRemaining] = React.useState(attempt.remaining_seconds || 0);
  const [focusToast, setFocusToast] = React.useState('');
  const [submitting, setSubmitting] = React.useState(false);
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [lessonData, setLessonData] = React.useState(null);
  const [lessonLoading, setLessonLoading] = React.useState(false);

  const steps = attempt.steps || [];
  const parsed = parseStepParam(stepParam);
  let currentIdx = steps.findIndex((s) => s.kind === parsed.kind && s.public_id === parsed.id);
  if (currentIdx < 0) {
    const firstOpen = steps.findIndex((s, i) => !isStepLockedLinear(steps, i, attempt.navigation_mode));
    currentIdx = firstOpen >= 0 ? firstOpen : 0;
  }
  const currentStep = steps[currentIdx] || null;

  React.useEffect(() => {
    if (!currentStep || !courseId || !exam.public_id) return;
    const key = examStepKey(currentStep.kind, currentStep.public_id);
    if (stepParam !== key) {
      navigate(Routes.LEARN, window.buildExamQuery(courseId, exam.public_id, currentStep.kind, currentStep.public_id));
    }
  }, [currentStep?.kind, currentStep?.public_id, courseId, exam.public_id, stepParam, navigate]);

  React.useEffect(() => {
    setRemaining(attempt.remaining_seconds || 0);
  }, [attempt.public_id, attempt.remaining_seconds]);

  React.useEffect(() => {
    if (attempt.status !== 'in_progress') return undefined;
    const tick = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(tick);
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(tick);
  }, [attempt.public_id, attempt.status]);

  React.useEffect(() => {
    if (attempt.status !== 'in_progress') return undefined;
    const sync = setInterval(async () => {
      try {
        const data = await window.fetchApiJson(
          `/api/exams/attempts/${encodeURIComponent(attempt.public_id)}/`,
          { auth: true },
        );
        setRemaining(data.remaining_seconds || 0);
        onAttemptChange(data);
        if (data.status !== 'in_progress') onFinish(data);
      } catch (_) {}
    }, 30000);
    return () => clearInterval(sync);
  }, [attempt.public_id, attempt.status]);

  React.useEffect(() => {
    if (remaining === 0 && attempt.status === 'in_progress') {
      window.fetchApiJson(
        `/api/exams/attempts/${encodeURIComponent(attempt.public_id)}/submit/`,
        { method: 'POST', auth: true },
      ).then(onFinish).catch(() => {});
    }
  }, [remaining, attempt.status, attempt.public_id]);

  React.useEffect(() => {
    if (attempt.status !== 'in_progress') return undefined;
    const reportFocus = (eventType) => {
      window.fetchApiJson(
        `/api/exams/attempts/${encodeURIComponent(attempt.public_id)}/focus/`,
        { method: 'POST', body: { event_type: eventType }, auth: true },
      ).then((data) => {
        if (attempt.tab_policy === 'warn' && data.logged) {
          setFocusToast(`Предупреждение ${data.focus_warn_count}/${attempt.tab_warn_limit}: не переключайте вкладку`);
          setTimeout(() => setFocusToast(''), 5000);
        }
        if (data.attempt) {
          onAttemptChange(data.attempt);
          if (data.attempt.status !== 'in_progress') onFinish(data.attempt);
        }
      }).catch(() => {});
    };
    const onVis = () => { if (document.hidden) reportFocus('visibility_hidden'); };
    document.addEventListener('visibilitychange', onVis);
    return () => document.removeEventListener('visibilitychange', onVis);
  }, [attempt.public_id, attempt.status, attempt.tab_policy, attempt.tab_warn_limit]);

  React.useEffect(() => {
    if (!currentStep) return;
    setLessonData(null);
    setLessonLoading(true);
    const paths = {
      theory: `/api/content/lessons-theory/${encodeURIComponent(currentStep.public_id)}/`,
      radio: `/api/content/lessons-radio/${encodeURIComponent(currentStep.public_id)}/`,
      checkbox: `/api/content/lessons-checkbox/${encodeURIComponent(currentStep.public_id)}/`,
      coding: `/api/content/challenges/${encodeURIComponent(currentStep.public_id)}/`,
    };
    window.fetchApiJson(paths[currentStep.kind])
      .then((d) => { setLessonData(d); setLessonLoading(false); })
      .catch(() => setLessonLoading(false));
  }, [currentStep?.kind, currentStep?.public_id]);

  const goStep = (idx) => {
    const s = steps[idx];
    if (!s) return;
    if (isStepLockedLinear(steps, idx, attempt.navigation_mode)) return;
    navigate(Routes.LEARN, window.buildExamQuery(courseId, exam.public_id, s.kind, s.public_id));
    setSidebarOpen(false);
  };

  const handleSubmitExam = async () => {
    if (!window.confirm('Завершить контрольную? После этого изменить ответы нельзя.')) return;
    setSubmitting(true);
    try {
      const data = await window.fetchApiJson(
        `/api/exams/attempts/${encodeURIComponent(attempt.public_id)}/submit/`,
        { method: 'POST', auth: true },
      );
      onFinish(data);
    } catch (e) {
      alert(e.message || 'Не удалось завершить');
    }
    setSubmitting(false);
  };

  const stepState = steps.find(
    (s) => s.kind === currentStep?.kind && s.public_id === currentStep?.public_id,
  ) || {};

  const lessonPanels = lessonLoading ? (
    <div className="flex justify-center py-20 gap-3 text-ink/50">
      <span className="w-6 h-6 border-2 border-violet-500 border-t-transparent rounded-full animate-spin"/>
      Загружаем задание…
    </div>
  ) : !lessonData ? (
    <div className="text-center py-20 text-ink/45">Не удалось загрузить задание</div>
  ) : currentStep?.kind === 'theory' ? (
    <ExamTheoryPanel
      lesson={lessonData}
      marked={stepState.answered}
      onMark={async () => {
        const data = await window.fetchApiJson(
          `/api/exams/attempts/${encodeURIComponent(attempt.public_id)}/theory/`,
          { method: 'POST', body: { lesson: lessonData.public_id }, auth: true },
        );
        onAttemptChange(data);
      }}
    />
  ) : currentStep?.kind === 'radio' ? (
    <ExamRadioPanel
      lesson={lessonData}
      step={stepState}
      attemptId={attempt.public_id}
      onUpdated={onAttemptChange}
    />
  ) : currentStep?.kind === 'checkbox' ? (
    <ExamCheckboxPanel
      lesson={lessonData}
      step={stepState}
      attemptId={attempt.public_id}
      onUpdated={onAttemptChange}
    />
  ) : currentStep?.kind === 'coding' ? (
    <ExamCodingPanel
      lesson={lessonData}
      step={stepState}
      attemptId={attempt.public_id}
      onUpdated={onAttemptChange}
    />
  ) : null;

  if (embedded) {
    return (
      <div className="flex flex-col min-h-0">
        <ExamTimerBar
          remaining={remaining}
          durationMinutes={exam.duration_minutes}
          warn={attempt.focus_warn_count}
        />
        {focusToast && (
          <div className="px-4 py-2 bg-amber-100 border-b border-amber-300 text-sm text-amber-900 text-center">
            {focusToast}
          </div>
        )}
        <div className="px-5 sm:px-10 py-6 border-b border-black/[0.06] bg-white shrink-0">
          <div className="flex items-center justify-between gap-3 mb-4">
            <div className="min-w-0">
              <div className="text-[11px] font-semibold uppercase tracking-widest text-violet-600">Контрольная</div>
              <div className="text-[16px] font-extrabold text-ink truncate">{exam.title}</div>
            </div>
            <div className="text-[11px] text-ink/45 shrink-0 font-mono">
              {attempt.score || 0}/{attempt.max_score} б.
            </div>
          </div>
          <div className="grid grid-cols-8 sm:grid-cols-12 md:grid-cols-16 gap-1.5">
            {steps.map((s, i) => {
              const locked = isStepLockedLinear(steps, i, attempt.navigation_mode);
              const active = i === currentIdx;
              return (
                <button key={s.public_id} type="button" disabled={locked} onClick={() => goStep(i)}
                  title={s.title}
                  className={`aspect-square rounded-lg text-[11px] font-bold transition-all
                    ${active ? 'grad-bg text-white shadow-soft ring-2 ring-violet-300' : 'bg-black/[0.04] text-ink/55 hover:bg-violet-500/10'}
                    ${locked ? 'opacity-30 cursor-not-allowed' : ''}`}>
                  {s.answered && s.kind !== 'theory' && s.is_correct ? '✓'
                    : s.answered && s.kind !== 'theory' && !s.is_correct ? '✗'
                    : i + 1}
                </button>
              );
            })}
          </div>
          <button type="button" onClick={handleSubmitExam} disabled={submitting}
            className="mt-4 h-10 px-4 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-sm font-semibold disabled:opacity-50">
            {submitting ? 'Сдаём…' : 'Завершить КР'}
          </button>
        </div>
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="max-w-3xl mx-auto px-5 sm:px-10 py-10">
            {lessonPanels}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex overflow-hidden" style={{ height: 'calc(100vh - 64px)' }}>
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setSidebarOpen(false)}/>
      )}

      <aside className={`fixed lg:static z-40 inset-y-0 left-0 w-72 flex flex-col bg-white border-r border-black/[0.06]
        transition-transform duration-300 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
        style={{ height: '100%' }}>
        <div className="px-4 py-4 border-b shrink-0">
          <div className="text-[10px] font-bold uppercase tracking-widest text-violet-600">Контрольная</div>
          <div className="font-bold text-sm mt-1 line-clamp-2">{exam.title}</div>
          <div className="mt-2 text-[11px] text-ink/50">
            {attempt.score || 0} / {attempt.max_score} баллов
          </div>
        </div>
        <div className="flex-1 overflow-y-auto py-2 scrollbar-thin">
          {steps.map((s, i) => {
            const locked = isStepLockedLinear(steps, i, attempt.navigation_mode);
            const active = i === currentIdx;
            return (
              <button key={s.public_id} type="button" disabled={locked} onClick={() => goStep(i)}
                className={`w-full text-left px-4 py-3 flex items-center gap-3 transition-colors
                  ${active ? 'bg-violet-500/[0.08]' : 'hover:bg-black/[0.02]'}
                  ${locked ? 'opacity-40 cursor-not-allowed' : ''}`}>
                <span className="w-8 h-8 rounded-lg bg-black/[0.04] flex items-center justify-center text-sm shrink-0">
                  {s.answered && s.kind !== 'theory' && s.is_correct ? '✓'
                    : s.answered && s.kind !== 'theory' && !s.is_correct ? '✗'
                    : s.answered ? '✓' : stepIcon(s.kind)}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] font-semibold truncate">{s.title}</div>
                  <div className="text-[10px] text-ink/40">{i + 1}. {s.kind}</div>
                </div>
              </button>
            );
          })}
        </div>
        <div className="p-4 border-t shrink-0">
          <button type="button" onClick={handleSubmitExam} disabled={submitting}
            className="w-full h-11 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-sm font-semibold disabled:opacity-50">
            {submitting ? 'Сдаём…' : 'Завершить КР'}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <ExamTimerBar
          remaining={remaining}
          durationMinutes={exam.duration_minutes}
          warn={attempt.focus_warn_count}
        />
        {focusToast && (
          <div className="px-4 py-2 bg-amber-100 border-b border-amber-300 text-sm text-amber-900 text-center">
            {focusToast}
          </div>
        )}
        <div className="bg-white border-b px-4 py-3 flex items-center gap-3 shrink-0">
          <button type="button" onClick={() => setSidebarOpen(true)} className="lg:hidden p-2 rounded-lg hover:bg-black/[0.04]">
            <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
          </button>
          <div className="flex-1 text-sm font-medium truncate">{currentStep?.title || 'Задание'}</div>
          <div className="text-[11px] text-ink/40 font-mono">{currentIdx + 1}/{steps.length}</div>
        </div>

        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="max-w-3xl mx-auto px-5 sm:px-10 py-10">
            {lessonPanels}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Exam content (learn embed + standalone) ───────────────────────────────

function ExamContent({ courseId, examId, stepParam, navigate, embedded }) {

  const [phase, setPhase] = React.useState('loading');
  const [exam, setExam] = React.useState(null);
  const [attempt, setAttempt] = React.useState(null);
  const [error, setError] = React.useState('');
  const [starting, setStarting] = React.useState(false);

  const loadExam = React.useCallback(async () => {
    if (!examId) throw new Error('Контрольная не указана');
    return window.fetchApiJson(`/api/exams/${encodeURIComponent(examId)}/`, { auth: true });
  }, [examId]);

  const loadAttempt = React.useCallback(async (attemptId) => {
    return window.fetchApiJson(`/api/exams/attempts/${encodeURIComponent(attemptId)}/`, { auth: true });
  }, []);

  React.useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      navigate(Routes.AUTH);
      return;
    }
    if (!examId || !courseId) {
      setPhase('error');
      setError('Укажите course и exam в адресе');
      return;
    }
    let cancelled = false;
    (async () => {
      setPhase('loading');
      try {
        const ex = await loadExam();
        if (cancelled) return;
        setExam(ex);
        const access = ex.access || {};
        if (access.active_attempt_public_id) {
          const att = await loadAttempt(access.active_attempt_public_id);
          if (cancelled) return;
          setAttempt(att);
          setPhase(att.status === 'in_progress' ? 'active' : 'result');
        } else if (access.latest_attempt && !access.can_start) {
          const att = await loadAttempt(access.latest_attempt.public_id);
          if (cancelled) return;
          setAttempt(att);
          setPhase('result');
        } else {
          setPhase('landing');
        }
      } catch (e) {
        if (!cancelled) {
          setError(e.message || 'Ошибка загрузки');
          setPhase('error');
        }
      }
    })();
    return () => { cancelled = true; };
  }, [examId, courseId, loadExam, loadAttempt, navigate]);

  const handleStart = async () => {
    if (!examId || starting) return;
    setStarting(true);
    try {
      const att = await window.fetchApiJson(
        `/api/exams/${encodeURIComponent(examId)}/start/`,
        { method: 'POST', auth: true },
      );
      setAttempt(att);
      setPhase('active');
      const first = (att.steps || [])[0];
      if (first) {
        navigate(Routes.LEARN, window.buildExamQuery(courseId, examId, first.kind, first.public_id));
      }
    } catch (e) {
      alert(e.message || 'Не удалось начать');
    }
    setStarting(false);
  };

  if (phase === 'loading') {
    return (
      <div className={`flex items-center justify-center gap-3 text-ink/60 ${embedded ? 'py-20' : 'min-h-[50vh]'}`}>
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <span className="text-sm">Загружаем контрольную…</span>
      </div>
    );
  }

  if (phase === 'error') {
    return (
      <div className={`flex flex-col items-center justify-center gap-4 px-6 text-center ${embedded ? 'py-20' : 'min-h-[50vh]'}`}>
        <div className="text-4xl">⚠️</div>
        <div className="font-bold text-lg">{error || 'Ошибка'}</div>
        <button type="button" onClick={() => navigate(Routes.CATALOG)}
          className="btn-grad h-11 px-6 rounded-xl text-white font-semibold">Каталог</button>
      </div>
    );
  }

  if (phase === 'landing' && exam) {
    return (
      <ExamLanding
        exam={exam}
        access={exam.access}
        starting={starting}
        onStart={handleStart}
        onBack={() => navigate(Routes.COURSE, { id: courseId })}
        embedded={embedded}
      />
    );
  }

  if (phase === 'result' && attempt && exam) {
    return (
      <ExamResultScreen
        attempt={attempt}
        exam={exam}
        courseId={courseId}
        navigate={navigate}
        embedded={embedded}
      />
    );
  }

  if (phase === 'active' && attempt && exam) {
    return (
      <ExamActiveSession
        exam={exam}
        attempt={attempt}
        courseId={courseId}
        stepParam={stepParam}
        navigate={navigate}
        embedded={embedded}
        onAttemptChange={(att) => {
          setAttempt(att);
          if (att.status !== 'in_progress') setPhase('result');
        }}
        onFinish={(att) => {
          setAttempt(att);
          setPhase('result');
        }}
      />
    );
  }

  return null;
}

function ExamPage({ navigate, hashParams }) {
  React.useEffect(() => {
    const courseId = hashParams?.get('course');
    const examId = hashParams?.get('exam');
    const step = hashParams?.get('step');
    if (courseId && examId) {
      const q = { course: courseId, exam: examId };
      if (step) q.step = step;
      navigate(Routes.LEARN, q);
    } else {
      navigate(Routes.CATALOG);
    }
  }, [navigate, hashParams]);

  return (
    <div className="min-h-[50vh] flex items-center justify-center gap-3 text-ink/60">
      <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
      <span className="text-sm">Переход к контрольной…</span>
    </div>
  );
}

window.ExamPage = ExamPage;
window.ExamContent = ExamContent;
