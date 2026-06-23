// LEARN page — sidebar + lesson viewer (theory / radio / checkbox / coding)

const Routes = window.Routes;
const FM = window.FM;
const I = window.I;

// ─── helpers ────────────────────────────────────────────────────────────────

function buildFlatLessons(modules) {
  const list = [];
  for (const mod of (modules || [])) {
    const items = [];
    const push = (type, row) => {
      items.push({
        type,
        id: row.public_id,
        title: row.title,
        order: row.order_index || 0,
        modId: mod.public_id,
        modTitle: mod.title,
      });
    };
    for (const t of (mod.lessons_theories || [])) push('theory', t);
    for (const r of (mod.lessons_radio || [])) push('radio', r);
    for (const c of (mod.lessons_checkbox || [])) push('checkbox', c);
    for (const ch of (mod.lessons_coding || [])) push('coding', ch);
    items.sort((a, b) => (a.order - b.order) || String(a.type).localeCompare(b.type));
    list.push(...items);
  }
  return list;
}

function buildModuleLessonItems(mod) {
  const items = [];
  const push = (type, row) => {
    items.push({
      type,
      lesson: row,
      order: row.order_index || 0,
    });
  };
  for (const t of (mod.lessons_theories || [])) push('theory', t);
  for (const r of (mod.lessons_radio || [])) push('radio', r);
  for (const c of (mod.lessons_checkbox || [])) push('checkbox', c);
  for (const ch of (mod.lessons_coding || [])) push('coding', ch);
  items.sort((a, b) => (a.order - b.order) || String(a.type).localeCompare(b.type));
  return items;
}

function buildExamLessonItems(exam) {
  const items = [];
  const push = (type, row) => {
    items.push({
      type,
      lesson: row,
      order: row.order_index || 0,
    });
  };
  for (const t of (exam.lessons_theories || [])) push('theory', t);
  for (const r of (exam.lessons_radio || [])) push('radio', r);
  for (const c of (exam.lessons_checkbox || [])) push('checkbox', c);
  for (const ch of (exam.lessons_coding || [])) push('coding', ch);
  items.sort((a, b) => (a.order - b.order) || String(a.type).localeCompare(b.type));
  return items;
}

function buildContentOutline(modules, exams) {
  const items = [];
  for (const m of (modules || [])) {
    items.push({ kind: 'module', order: m.order_index || 0, data: m });
  }
  for (const e of (exams || [])) {
    items.push({ kind: 'exam', order: e.order_index || 0, data: e });
  }
  items.sort((a, b) => (a.order - b.order) || (a.kind === 'module' ? -1 : 1));
  return items;
}

function lessonKey(type, id) { return type + '-' + id; }

// ─── Main page ───────────────────────────────────────────────────────────────

function LearnPage({ navigate, hashParams }) {
  const courseId   = hashParams?.get('course') || null;
  const moduleParam = hashParams?.get('module') || null;
  const lessonParam = hashParams?.get('lesson') || null;
  const examParam   = hashParams?.get('exam') || null;
  const stepParam   = hashParams?.get('step') || null;
  const ExamContent = window.ExamContent;

  const dashIdx    = lessonParam ? lessonParam.indexOf('-') : -1;
  const lessonType = dashIdx > 0 ? lessonParam.slice(0, dashIdx) : null;
  const lessonId   = dashIdx > 0 ? lessonParam.slice(dashIdx + 1) : null;

  // ── course state ──
  const [courseData, setCourseData] = React.useState(null);
  const [courseState, setCourseState] = React.useState('loading'); // loading | ok | err
  const [courseErr, setCourseErr]     = React.useState('');

  // ── lesson state ──
  const [lessonData, setLessonData]   = React.useState(null);
  const [lessonLoading, setLessonLoading] = React.useState(false);

  // ── quiz state ──
  const [selectedRadio, setSelectedRadio]         = React.useState(null);
  const [selectedBoxes, setSelectedBoxes]         = React.useState(new Set());
  const [submitted, setSubmitted]                 = React.useState(false);
  const [submitResult, setSubmitResult]           = React.useState(null); // API response or null
  const [submitLoading, setSubmitLoading]         = React.useState(false);

  // ── progress (backend only) ──
  const [completed, setCompleted] = React.useState(new Set());

  const markDone = React.useCallback((type, id) => {
    setCompleted(prev => {
      const next = new Set(prev);
      next.add(lessonKey(type, id));
      return next;
    });
  }, []);

  const refreshCourseProgress = React.useCallback(() => {
    if (!courseId) return Promise.resolve();
    const token = localStorage.getItem('access_token');
    if (!token) return Promise.resolve();
    return window.fetchCourseProgress(courseId)
      .then((data) => {
        setCompleted(new Set(data?.completed || []));
      })
      .catch(() => {});
  }, [courseId]);

  // ── enroll + load progress from backend ──
  React.useEffect(() => {
    if (courseState !== 'ok' || !courseId) return;
    const token = localStorage.getItem('access_token');
    if (!token) return;
    window.enrollInCourse(courseId).catch(() => {});
    refreshCourseProgress();
  }, [courseState, courseId, refreshCourseProgress]);

  // ── sidebar toggle (mobile) ──
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  // ── load course ──
  React.useEffect(() => {
    if (!courseId) { setCourseState('err'); setCourseErr('Курс не указан.'); return; }
    setCourseState('loading');
    setCourseData(null);
    window.fetchApiJson(`/api/content/courses/${encodeURIComponent(courseId)}/`)
      .then(d => { setCourseData(d); setCourseState('ok'); })
      .catch(e => { setCourseErr(e.message || 'Ошибка загрузки'); setCourseState('err'); });
  }, [courseId]);

  // ── flat lesson list ──
  const allLessons = React.useMemo(
    () => courseData ? buildFlatLessons(courseData.modules) : [],
    [courseData]
  );

  const contentOutline = React.useMemo(
    () => courseData ? buildContentOutline(courseData.modules, courseData.exams) : [],
    [courseData],
  );

  const currentExam = React.useMemo(() => {
    if (!courseData || !examParam) return null;
    return (courseData.exams || []).find((e) => e.public_id === examParam) || null;
  }, [courseData, examParam]);

  const inExamMode = !!examParam;

  const moduleLessons = React.useMemo(() => {
    if (!courseData || !moduleParam) return [];
    const mod = (courseData.modules || []).find(m => m.public_id === moduleParam) || null;
    if (!mod) return [];
    return buildModuleLessonItems(mod).map(({ type, lesson }) => ({
      type,
      id: lesson.public_id,
      title: lesson.title,
      order: lesson.order_index || 0,
      modId: mod.public_id,
      modTitle: mod.title,
    }));
  }, [courseData, moduleParam]);

  // ── redirect to first tile ──
  React.useEffect(() => {
    if (courseState !== 'ok') return;
    if (examParam) return;

    // If module is set but lesson isn't: open first tile in module (or stay on module stub)
    if (moduleParam && !lessonId) {
      const mod = (courseData?.modules || []).find(m => m.public_id === moduleParam) || null;
      if (!mod) return;
      const items = buildModuleLessonItems(mod);
      const first = items[0] || null;
      if (!first) return;
      navigate(Routes.LEARN, { course: courseId, module: moduleParam, lesson: lessonKey(first.type, first.lesson.public_id) });
      return;
    }

    // First visit: open 1st item in course outline
    if (!moduleParam && !lessonId) {
      const firstItem = contentOutline[0] || null;
      if (!firstItem) return;
      if (firstItem.kind === 'module') {
        const items = buildModuleLessonItems(firstItem.data);
        const first = items[0] || null;
        if (!first) {
          navigate(Routes.LEARN, { course: courseId, module: firstItem.data.public_id });
          return;
        }
        navigate(Routes.LEARN, {
          course: courseId,
          module: firstItem.data.public_id,
          lesson: lessonKey(first.type, first.lesson.public_id),
        });
      } else {
        navigate(Routes.LEARN, { course: courseId, exam: firstItem.data.public_id });
      }
    }
  }, [courseState, allLessons, lessonId, moduleParam, examParam, courseId, courseData, contentOutline, navigate]);

  // ── current index in flat list ──
  const currentIdx = React.useMemo(() => {
    if (!lessonType || !lessonId || allLessons.length === 0) return 0;
    const i = allLessons.findIndex(l => l.type === lessonType && l.id === lessonId);
    return i >= 0 ? i : 0;
  }, [allLessons, lessonType, lessonId]);

  const currentLesson = allLessons[currentIdx] || null;
  const currentModule = React.useMemo(() => {
    if (!courseData) return null;
    const id = moduleParam || currentLesson?.modId || null;
    if (!id) return null;
    return (courseData.modules || []).find(m => m.public_id === id) || null;
  }, [courseData, moduleParam, currentLesson]);
  const hasModuleStub = !!currentModule && moduleLessons.length === 0;

  // ── keep module param consistent with current lesson ──
  React.useEffect(() => {
    if (courseState !== 'ok' || examParam) return;
    if (!lessonType || !lessonId) return;
    const cur = allLessons[currentIdx] || null;
    if (!cur) return;
    if (moduleParam !== cur.modId) {
      navigate(Routes.LEARN, { course: courseId, module: cur.modId, lesson: lessonKey(cur.type, cur.id) });
    }
  }, [courseState, lessonType, lessonId, allLessons, currentIdx, moduleParam, courseId]);

  // ── load lesson detail ──
  React.useEffect(() => {
    if (examParam || !lessonType || !lessonId) return;
    setLessonData(null);
    setLessonLoading(true);
    setSubmitted(false);
    setSubmitResult(null);
    setSelectedRadio(null);
    setSelectedBoxes(new Set());

    const paths = {
      theory:   `/api/content/lessons-theory/${encodeURIComponent(lessonId)}/`,
      radio:    `/api/content/lessons-radio/${encodeURIComponent(lessonId)}/`,
      checkbox: `/api/content/lessons-checkbox/${encodeURIComponent(lessonId)}/`,
      coding:   `/api/content/challenges/${encodeURIComponent(lessonId)}/`,
    };
    const path = paths[lessonType];
    if (!path) { setLessonLoading(false); return; }

    window.fetchApiJson(path, { auth: true })
      .then(d => { setLessonData(d); setLessonLoading(false); })
      .catch(() => setLessonLoading(false));
  }, [lessonType, lessonId, examParam]);

  const refreshLesson = React.useCallback(() => {
    if (!lessonType || !lessonId) return Promise.resolve();
    const paths = {
      theory:   `/api/content/lessons-theory/${encodeURIComponent(lessonId)}/`,
      radio:    `/api/content/lessons-radio/${encodeURIComponent(lessonId)}/`,
      checkbox: `/api/content/lessons-checkbox/${encodeURIComponent(lessonId)}/`,
      coding:   `/api/content/challenges/${encodeURIComponent(lessonId)}/`,
    };
    const path = paths[lessonType];
    if (!path) return Promise.resolve();
    return window.fetchApiJson(path, { auth: true })
      .then((d) => { setLessonData(d); return d; })
      .catch(() => {});
  }, [lessonType, lessonId]);

  // ── auto-mark theory as read on view ──
  React.useEffect(() => {
    if (lessonType !== 'theory') return;
    if (!lessonData || lessonLoading) return;
    const id = lessonData.public_id || lessonId;
    if (!id) return;
    const token = localStorage.getItem('access_token');
    if (token) {
      window.fetchApiJson('/api/progress/theory/', {
        method: 'POST',
        body: { lesson: id },
        auth: true,
      })
        .then(() => {
          markDone('theory', id);
          refreshCourseProgress();
        })
        .catch(() => {});
    }
  }, [lessonType, lessonData, lessonLoading, lessonId, markDone, refreshCourseProgress]);

  // ── navigation helpers ──
  const goTo = (lesson) => {
    navigate(Routes.LEARN, { course: courseId, module: lesson.modId, lesson: lessonKey(lesson.type, lesson.id) });
    setSidebarOpen(false);
  };
  const goNext = () => {
    if (currentIdx < allLessons.length - 1) goTo(allLessons[currentIdx + 1]);
    else navigate(Routes.COURSE, { id: courseId });
  };
  const goPrev = () => { if (currentIdx > 0) goTo(allLessons[currentIdx - 1]); };

  // ── submit radio ──
  const handleRadioSubmit = async () => {
    if (!selectedRadio || submitted) return;
    setSubmitLoading(true);
    let res = null;
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        res = await window.fetchApiJson('/api/progress/radio/', {
          method: 'POST',
          body: { question: lessonId, selected_answer: selectedRadio },
          auth: true,
        });
        setSubmitResult(res);
      } catch (_) {}
    }
    setSubmitted(true);
    setSubmitLoading(false);
    if (res?.is_correct || res?.solved_ever) {
      markDone('radio', lessonId);
      refreshCourseProgress();
    }
  };

  const handleRadioRetry = () => {
    setSubmitted(false);
    setSubmitResult(null);
    setSelectedRadio(null);
  };

  const handleBoxRetry = () => {
    setSubmitted(false);
    setSubmitResult(null);
    setSelectedBoxes(new Set());
  };

  // ── submit checkbox ──
  const handleBoxSubmit = async () => {
    if (submitted) return;
    setSubmitLoading(true);
    let res = null;
    const token = localStorage.getItem('access_token');
    if (token) {
      try {
        res = await window.fetchApiJson('/api/progress/checkbox/', {
          method: 'POST',
          body: { question: lessonId, selected_answers: [...selectedBoxes] },
          auth: true,
        });
        setSubmitResult(res);
      } catch (_) {}
    }
    setSubmitted(true);
    setSubmitLoading(false);
    if (res?.is_correct) {
      markDone('checkbox', lessonId);
      refreshCourseProgress();
    }
  };

  // ── loading / error states ──
  if (!courseId || courseState === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center gap-3 text-ink/60 bg-paper">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <span className="text-sm">Загружаем курс…</span>
      </div>
    );
  }

  if (courseState === 'err' || !courseData) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-paper text-center px-6">
        <div className="text-5xl">🔍</div>
        <div className="text-xl font-bold text-ink/80">Курс не найден</div>
        <p className="text-sm text-ink/55 max-w-sm">{courseErr || 'Попробуйте открыть через каталог.'}</p>
        <button onClick={() => navigate(Routes.CATALOG)}
          className="btn-grad btn-shimmer h-11 px-6 rounded-xl text-white font-semibold mt-2">
          Каталог курсов
        </button>
      </div>
    );
  }

  const totalLessons  = allLessons.length;
  const doneCount     = allLessons.filter(l => completed.has(lessonKey(l.type, l.id))).length;
  const progressPct   = totalLessons ? Math.round((doneCount / totalLessons) * 100) : 0;

  return (
    <div className="flex overflow-hidden" style={{ height: 'calc(100vh - 64px)' }}>

      {/* ── Mobile sidebar backdrop ── */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden"
          onClick={() => setSidebarOpen(false)} aria-hidden/>
      )}

      {/* ══ LEFT SIDEBAR ══ */}
      <aside className={`
        fixed lg:static z-40 inset-y-0 left-0
        w-72 flex-shrink-0 flex flex-col
        bg-white border-r border-black/[0.06]
        transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}
        style={{ height: '100%' }}>

        {/* sidebar header */}
        <div className="px-5 pt-4 pb-3 border-b border-black/[0.06] shrink-0">
          <button
            onClick={() => navigate(Routes.COURSE, { id: courseId })}
            className="flex items-center gap-1.5 text-[11px] text-ink/50 hover:text-violet-600 transition-colors mb-3">
            <I.ChevronRight className="w-3 h-3 rotate-180"/> Назад к курсу
          </button>
          <div className="font-bold text-[13px] leading-snug text-ink line-clamp-2">
            {courseData.title}
          </div>
          {/* progress bar */}
          <div className="mt-3">
            <div className="flex justify-between text-[10px] text-ink/45 mb-1.5">
              <span>Прогресс</span>
              <span>{doneCount}/{totalLessons} уроков</span>
            </div>
            <div className="h-1.5 bg-black/[0.06] rounded-full overflow-hidden">
              <div
                className="h-full grad-bg rounded-full transition-all duration-500"
                style={{ width: `${progressPct}%` }}/>
            </div>
          </div>
        </div>

        {/* modules + exams */}
        <div className="flex-1 overflow-y-auto scrollbar-thin py-2">
          {contentOutline.map((item, oi) => {
            if (item.kind === 'module') {
              const mod = item.data;
              const items = buildModuleLessonItems(mod);
              const total = items.length;
              const doneInModule = items.filter(
                ({ type, lesson }) => completed.has(lessonKey(type, lesson.public_id)),
              ).length;
              const active = !inExamMode && (moduleParam ? mod.public_id === moduleParam : currentLesson?.modId === mod.public_id);

              return (
                <button
                  key={`mod-${mod.public_id}`}
                  type="button"
                  onClick={() => {
                    const first = items[0] || null;
                    if (first) {
                      goTo({
                        type: first.type,
                        id: first.lesson.public_id,
                        title: first.lesson.title,
                        modId: mod.public_id,
                        modTitle: mod.title,
                      });
                    } else {
                      navigate(Routes.LEARN, { course: courseId, module: mod.public_id });
                      setSidebarOpen(false);
                    }
                  }}
                  className={`w-full px-4 py-3 flex items-center gap-3 text-left transition-colors
                    ${active ? 'bg-violet-500/[0.07]' : 'hover:bg-black/[0.025]'}`}
                >
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-[11px] font-bold shrink-0
                    ${active ? 'grad-bg text-white' : 'bg-black/[0.04] text-ink/55'}`}>
                    {oi + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-[13px] leading-snug truncate ${active ? 'font-semibold text-violet-700' : 'font-semibold text-ink'}`}>
                      {mod.title}
                    </div>
                    {total > 0 ? (
                      <div className="text-[10px] text-ink/40 mt-0.5">{doneInModule}/{total} завершено</div>
                    ) : (
                      <div className="text-[10px] text-ink/30 mt-0.5 italic">Пока нет материалов</div>
                    )}
                  </div>
                  {active && <div className="w-1.5 h-1.5 rounded-full bg-violet-500 shrink-0"/>}
                </button>
              );
            }

            const ex = item.data;
            const examItems = buildExamLessonItems(ex);
            const active = inExamMode && examParam === ex.public_id;
            return (
              <button
                key={`exam-${ex.public_id}`}
                type="button"
                onClick={() => {
                  navigate(Routes.LEARN, { course: courseId, exam: ex.public_id });
                  setSidebarOpen(false);
                }}
                className={`w-full px-4 py-3 flex items-center gap-3 text-left transition-colors
                  ${active ? 'bg-amber-500/[0.08]' : 'hover:bg-black/[0.025]'}`}
              >
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0
                  ${active ? 'bg-amber-500 text-white' : 'bg-amber-500/10 text-amber-700'}`}>
                  <I.Clock className="w-3.5 h-3.5"/>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded shrink-0
                      ${active ? 'bg-amber-500/20 text-amber-800' : 'bg-amber-500/10 text-amber-700'}`}>
                      КР
                    </span>
                    <span className={`text-[13px] leading-snug truncate ${active ? 'font-semibold text-amber-900' : 'font-semibold text-ink'}`}>
                      {ex.title}
                    </span>
                  </div>
                  <div className="text-[10px] text-ink/40 mt-0.5">
                    {ex.duration_minutes} мин · {examItems.length} заданий
                  </div>
                </div>
                {active && <div className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"/>}
              </button>
            );
          })}
          {contentOutline.length === 0 && (
            <div className="px-5 py-10 text-sm text-ink/35 text-center">
              В этом курсе пока нет материалов
            </div>
          )}
        </div>
      </aside>

      {/* ══ MAIN CONTENT ══ */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* top bar */}
        <div className="bg-white border-b border-black/[0.06] px-4 py-3 flex items-center gap-3 shrink-0">
          {/* hamburger (mobile) */}
          <button onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg hover:bg-black/[0.04] text-ink/60 shrink-0"
            aria-label="Открыть меню">
            <svg viewBox="0 0 24 24" className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M3 12h18M3 18h18" strokeLinecap="round"/>
            </svg>
          </button>

          {/* breadcrumb */}
          <div className="flex-1 min-w-0">
            {inExamMode && currentExam ? (
              <div className="flex items-center gap-1.5 text-[13px] min-w-0">
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 shrink-0">КР</span>
                <I.ChevronRight className="w-3 h-3 text-ink/30 shrink-0"/>
                <span className="font-medium text-ink/80 truncate">{currentExam.title}</span>
              </div>
            ) : currentLesson && (
              <div className="flex items-center gap-1.5 text-[13px] min-w-0">
                <span className="text-ink/40 shrink-0 truncate max-w-[120px]">{currentLesson.modTitle}</span>
                <I.ChevronRight className="w-3 h-3 text-ink/30 shrink-0"/>
                <span className="font-medium text-ink/80 truncate">{currentLesson.title}</span>
              </div>
            )}
          </div>

          {/* counter */}
          {!inExamMode && totalLessons > 0 && (
            <div className="text-[11px] text-ink/40 shrink-0 font-mono">
              {currentIdx + 1} / {totalLessons}
            </div>
          )}
        </div>

        {/* lesson / exam area */}
        <div className={`flex-1 min-h-0 ${inExamMode ? 'overflow-hidden flex flex-col' : 'overflow-y-auto scrollbar-thin'}`}>
          {inExamMode && ExamContent ? (
            <ExamContent
              courseId={courseId}
              examId={examParam}
              stepParam={stepParam}
              navigate={navigate}
              embedded
            />
          ) : (
          <div className="max-w-3xl mx-auto px-5 sm:px-10 py-10">

            {/* module tiles */}
            {currentModule && (
              <div className="mb-8">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <div className="min-w-0">
                    <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/40">Модуль</div>
                    <div className="text-[18px] font-extrabold text-ink truncate">{currentModule.title}</div>
                  </div>
                  {moduleLessons.length > 0 && (
                    <div className="text-[11px] text-ink/45 shrink-0">
                      {moduleLessons.filter(l => completed.has(lessonKey(l.type, l.id))).length}/{moduleLessons.length} в модуле
                    </div>
                  )}
                </div>

                {hasModuleStub ? (
                  <div className="rounded-2xl bg-black/[0.02] ring-1 ring-black/[0.06] p-6 text-center text-ink/45">
                    <div className="text-3xl mb-2">📦</div>
                    <div className="text-sm font-semibold text-ink/60">В этом модуле пока нет материалов</div>
                    <div className="text-xs mt-1">Выберите другой модуль слева</div>
                  </div>
                ) : (
                  <div className="grid grid-cols-8 sm:grid-cols-12 md:grid-cols-16 gap-1.5">
                    {moduleLessons.map((l, idx) => {
                      const active = currentLesson?.type === l.type && currentLesson?.id === l.id;
                      const done = completed.has(lessonKey(l.type, l.id));
                      const icon = (
                        l.type === 'theory' ? '📖'
                        : l.type === 'radio' ? '?'
                        : l.type === 'checkbox' ? '☑'
                        : l.type === 'coding' ? '>_'
                        : '•'
                      );
                      return (
                        <button
                          key={lessonKey(l.type, l.id)}
                          type="button"
                          onClick={() => goTo(l)}
                          title={`${idx + 1}. ${l.title}`}
                          className={`relative w-9 h-9 sm:w-10 sm:h-10 rounded-lg ring-1 transition-all select-none
                            ${active ? 'ring-violet-500 bg-violet-50' : 'ring-black/[0.06] bg-white hover:ring-violet-200 hover:bg-violet-50/30'}
                          `}
                        >
                          <div className={`absolute inset-0 rounded-lg ${done ? 'bg-emerald-500/[0.10]' : ''}`}/>
                          <div className="absolute top-0.5 left-1 text-[9px] font-mono text-ink/35">
                            {idx + 1}
                          </div>
                          <div className="absolute inset-0 flex items-center justify-center">
                            {done ? (
                              <span className="check-dot" style={{ width: 18, height: 18 }}/>
                            ) : (
                              <span className="font-mono text-[13px] text-ink/70">{icon}</span>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {lessonLoading ? (
              <div className="flex items-center justify-center gap-3 py-24 text-ink/50">
                <span className="w-6 h-6 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
                <span className="text-sm">Загружаем урок…</span>
              </div>

            ) : !lessonData && lessonType ? (
              <div className="text-center py-24 text-ink/40">
                <div className="text-4xl mb-3">📭</div>
                <div className="text-sm">Не удалось загрузить содержимое урока</div>
              </div>

            ) : lessonType === 'theory' && lessonData ? (
              <TheoryLesson
                lesson={lessonData}
                isDone={completed.has(lessonKey('theory', lessonData.public_id))}
                onComplete={() => {
                  markDone('theory', lessonData.public_id);
                  refreshCourseProgress();
                }}
                onLogin={() => navigate(Routes.AUTH)}
              />

            ) : lessonType === 'radio' && lessonData ? (
              <RadioLesson
                lesson={lessonData}
                selected={selectedRadio}
                setSelected={setSelectedRadio}
                submitted={submitted}
                result={submitResult}
                loading={submitLoading}
                onSubmit={handleRadioSubmit}
                onRetry={handleRadioRetry}
                onLogin={() => navigate(Routes.AUTH)}
                onRefreshLesson={refreshLesson}
              />

            ) : lessonType === 'checkbox' && lessonData ? (
              <CheckboxLesson
                lesson={lessonData}
                selected={selectedBoxes}
                setSelected={setSelectedBoxes}
                submitted={submitted}
                result={submitResult}
                loading={submitLoading}
                onSubmit={handleBoxSubmit}
                onRetry={handleBoxRetry}
                onLogin={() => navigate(Routes.AUTH)}
                onRefreshLesson={refreshLesson}
              />

            ) : lessonType === 'coding' && lessonData ? (
              <CodingLesson
                lesson={lessonData}
                isDone={completed.has(lessonKey('coding', lessonData.public_id))}
                onComplete={() => {
                  markDone('coding', lessonData.public_id);
                  refreshCourseProgress();
                }}
                onLogin={() => navigate(Routes.AUTH)}
                onRefreshLesson={refreshLesson}
              />

            ) : (
              <div className="text-center py-24 text-ink/40">
                <div className="text-5xl mb-4">🎓</div>
                <div className="text-lg font-semibold text-ink/60 mb-2">Выбери урок</div>
                <div className="text-sm">Нажми на любой урок в боковой панели слева</div>
              </div>
            )}

            {/* ── Prev / Next navigation ── */}
            {totalLessons > 0 && (currentIdx > 0 || currentIdx <= totalLessons - 1) && (
              <div className="mt-12 pt-6 border-t border-black/[0.05] flex items-center justify-between gap-4">
                <button onClick={goPrev} disabled={currentIdx === 0}
                  className="flex items-center gap-2 px-4 h-11 rounded-xl border border-black/[0.08] text-sm font-semibold text-ink/60
                    hover:border-violet-300 hover:text-violet-600 transition-colors
                    disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:border-black/[0.08] disabled:hover:text-ink/60">
                  <I.ChevronRight className="w-4 h-4 rotate-180"/>
                  Предыдущий
                </button>
                <button onClick={goNext} disabled={false}
                  className="flex items-center gap-2 px-5 h-11 rounded-xl btn-grad text-white text-sm font-semibold shadow-soft
                    disabled:opacity-30 disabled:cursor-not-allowed">
                  {currentIdx >= totalLessons - 1 ? 'К курсу' : 'Следующий'}
                  <I.ChevronRight className="w-4 h-4"/>
                </button>
              </div>
            )}
          </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Meta for tiles ─────────────────────────────────────────────────────────

const TYPE_META = {
  theory:   { emoji: '📖', label: 'Теория' },
  radio:    { emoji: '🔘', label: 'Один ответ' },
  checkbox: { emoji: '☑️', label: 'Несколько ответов' },
  coding:   { emoji: '💻', label: 'Задача с кодом' },
};

const CODE_POLL_INTERVAL_MS = 1200;
const CODE_POLL_MAX_ATTEMPTS = 90;

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
  throw new Error(
    'Проверка занимает слишком много времени. Обновите страницу и посмотрите историю отправок.',
  );
}

const DEFAULT_PYTHON_CODE = `def solve():
    pass

print(solve())`;

// ─── Theory lesson ───────────────────────────────────────────────────────────

function TheoryLesson({ lesson, isDone, onComplete, onLogin }) {
  return (
    <div>
      <LessonHeader type="theory" title={lesson.title} label="Теоретический урок"/>

      <window.VideoExplanation video={lesson.video} title="Видео-объяснение"/>

      <div
        className="theory-content mt-6"
        dangerouslySetInnerHTML={{ __html: lesson.content || '<p>Содержимое урока ещё добавляется.</p>' }}
      />
      <window.LessonInstructorNote text={lesson.comment} />

      <div className="mt-10">
        {isDone ? (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
            <span className="check-dot"/>
            <span className="text-sm font-semibold text-emerald-700">Прочитано</span>
          </div>
        ) : (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-blue-50 border border-blue-200">
            <span className="w-2 h-2 rounded-full bg-blue-400"/>
            <span className="text-sm font-semibold text-blue-700">Отметится автоматически после открытия</span>
          </div>
        )}
      </div>

      <window.LessonUserComments
        lessonKind="theory"
        lessonId={lesson.public_id}
        onLogin={onLogin}
      />
    </div>
  );
}

// ─── Radio question ──────────────────────────────────────────────────────────

function RadioLesson({ lesson, selected, setSelected, submitted, result, loading, onSubmit, onRetry, onLogin, onRefreshLesson }) {
  const loggedIn  = !!localStorage.getItem('access_token');
  const isCorrect = result?.is_correct;
  const [sessionFails, setSessionFails] = React.useState(0);
  const prevResultId = React.useRef(null);

  React.useEffect(() => {
    setSessionFails(0);
    prevResultId.current = null;
  }, [lesson.public_id]);

  const effectiveFails = loggedIn ? 0 : sessionFails;
  const solutionUnlocked = window.computeSolutionUnlocked(lesson, effectiveFails, isCorrect);

  React.useEffect(() => {
    if (!submitted) return;
    const resultKey = result?.public_id || 'anon';
    if (prevResultId.current === resultKey) return;
    prevResultId.current = resultKey;

    if (loggedIn && result) {
      onRefreshLesson?.();
    } else if (!loggedIn) {
      setSessionFails((n) => n + 1);
    }
  }, [submitted, result, loggedIn, onRefreshLesson]);

  React.useEffect(() => {
    if (!solutionUnlocked || !loggedIn || lesson.reference_solution) return;
    onRefreshLesson?.();
  }, [solutionUnlocked, loggedIn, lesson.public_id, lesson.reference_solution, onRefreshLesson]);

  return (
    <div>
      <LessonHeader type="radio" title={lesson.title} label="Вопрос — один правильный ответ"/>

      <div className="mt-6 p-6 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft">
        <p className="text-[15px] text-ink/80 leading-relaxed">{lesson.question_text}</p>
      </div>

      <window.LessonInstructorNote text={lesson.comment} />

      <div className="mt-5 space-y-3">
        {(lesson.answer_options || []).map(opt => {
          const isSel     = selected === opt.public_id;
          const showOk    = submitted && result && isSel && isCorrect;
          const showBad   = submitted && result && isSel && !isCorrect;

          return (
            <label key={opt.public_id}
              className={`flex items-center gap-4 p-4 rounded-xl cursor-pointer select-none transition-all ring-1
                ${submitted ? 'cursor-default' : 'hover:ring-violet-300 hover:bg-violet-50/60'}
                ${isSel && !submitted          ? 'ring-violet-500 bg-violet-50' : ''}
                ${showOk                        ? 'ring-emerald-400 bg-emerald-50' : ''}
                ${showBad                       ? 'ring-red-400 bg-red-50' : ''}
                ${!isSel                        ? 'ring-black/[0.06] bg-white' : ''}
              `}>
              <input type="radio" className="sr-only"
                name={`rq_${lesson.public_id}`}
                value={opt.public_id}
                checked={isSel}
                onChange={() => !submitted && setSelected(opt.public_id)}
              />
              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all
                ${showOk  ? 'border-emerald-500 bg-emerald-500' : ''}
                ${showBad ? 'border-red-500 bg-red-500' : ''}
                ${isSel && !submitted ? 'border-violet-600 bg-violet-600' : ''}
                ${!isSel  ? 'border-ink/20' : ''}
              `}>
                {isSel && <div className="w-2 h-2 rounded-full bg-white"/>}
              </div>
              <span className={`text-[14px] font-medium leading-snug flex-1
                ${showOk  ? 'text-emerald-800' : ''}
                ${showBad ? 'text-red-800' : ''}
                ${isSel && !submitted ? 'text-violet-800' : 'text-ink/75'}
              `}>{opt.text}</span>
              {showOk  && <I.Check className="w-5 h-5 text-emerald-500 shrink-0"/>}
              {showBad && <I.X    className="w-5 h-5 text-red-500 shrink-0"/>}
            </label>
          );
        })}
      </div>

      <QuizMeta points={lesson.points}/>

      {!submitted && (
        <QuizActions
          disabled={!selected}
          loading={loading}
          loggedIn={loggedIn}
          onSubmit={onSubmit}
          onLogin={onLogin}
        />
      )}

      {submitted && (
        <QuizResult
          isCorrect={isCorrect}
          hasResult={!!result}
          explanation={lesson.explanation}
          pointsEarned={result?.points_earned}
          loggedIn={loggedIn}
          onLogin={onLogin}
          onRetry={!isCorrect ? onRetry : undefined}
          solutionUnlocked={solutionUnlocked}
          hasReferenceSolution={window.hasReferenceSolutionMaterial(lesson)}
        />
      )}

      <window.LessonDiscussionSection
        lessonKind="radio"
        lessonId={lesson.public_id}
        onLogin={onLogin}
        showReferenceSolution={window.hasReferenceSolutionMaterial(lesson)}
        referenceSolution={lesson.reference_solution}
        solutionUnlocked={solutionUnlocked}
        wrongAttempts={lesson.wrong_attempts}
        sessionFails={effectiveFails}
      />
    </div>
  );
}

// ─── Checkbox question ───────────────────────────────────────────────────────

function CheckboxLesson({ lesson, selected, setSelected, submitted, result, loading, onSubmit, onRetry, onLogin, onRefreshLesson }) {
  const loggedIn  = !!localStorage.getItem('access_token');
  const isCorrect = result?.is_correct;
  const [sessionFails, setSessionFails] = React.useState(0);
  const prevSubmitKey = React.useRef(null);

  React.useEffect(() => {
    setSessionFails(0);
    prevSubmitKey.current = null;
  }, [lesson.public_id]);

  const effectiveFails = loggedIn ? 0 : sessionFails;
  const solutionUnlocked = window.computeSolutionUnlocked(lesson, effectiveFails, isCorrect);

  React.useEffect(() => {
    if (!submitted) return;
    const key = JSON.stringify(result || {});
    if (prevSubmitKey.current === key) return;
    prevSubmitKey.current = key;

    if (loggedIn) {
      onRefreshLesson?.();
    } else if (!isCorrect) {
      setSessionFails((n) => n + 1);
    }
  }, [submitted, result, isCorrect, loggedIn, onRefreshLesson]);

  React.useEffect(() => {
    if (!solutionUnlocked || !loggedIn || lesson.reference_solution) return;
    onRefreshLesson?.();
  }, [solutionUnlocked, loggedIn, lesson.public_id, lesson.reference_solution, onRefreshLesson]);

  const toggle = (id) => {
    if (submitted) return;
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  return (
    <div>
      <LessonHeader type="checkbox" title={lesson.title} label="Вопрос — несколько правильных ответов"/>

      <div className="mt-6 p-6 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft">
        <p className="text-[15px] text-ink/80 leading-relaxed">{lesson.question_text}</p>
      </div>

      <window.LessonInstructorNote text={lesson.comment} />

      <div className="mt-4 text-[11px] text-ink/40 flex items-center gap-1.5 mb-4">
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
        </svg>
        Выберите все правильные варианты
      </div>

      <div className="space-y-3">
        {(lesson.answer_options || []).map(opt => {
          const isSel = selected.has(opt.public_id);
          return (
            <label key={opt.public_id}
              className={`flex items-center gap-4 p-4 rounded-xl cursor-pointer select-none transition-all ring-1
                ${submitted ? 'cursor-default' : 'hover:ring-cyan-300 hover:bg-cyan-50/60'}
                ${isSel && !submitted ? 'ring-cyan-500 bg-cyan-50' : ''}
                ${isSel &&  submitted ? 'ring-violet-400 bg-violet-50' : ''}
                ${!isSel              ? 'ring-black/[0.06] bg-white' : ''}
              `}>
              <input type="checkbox" className="sr-only"
                checked={isSel}
                onChange={() => toggle(opt.public_id)}
              />
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-all
                ${isSel
                  ? 'border-cyan-600 bg-cyan-600'
                  : 'border-ink/20 bg-white'}
              `}>
                {isSel && <I.Check className="w-3 h-3 text-white"/>}
              </div>
              <span className={`text-[14px] font-medium leading-snug flex-1 ${isSel ? 'text-ink' : 'text-ink/70'}`}>
                {opt.text}
              </span>
            </label>
          );
        })}
      </div>

      <QuizMeta points={lesson.points}/>

      {!submitted && (
        <QuizActions
          disabled={false}
          loading={loading}
          loggedIn={loggedIn}
          onSubmit={onSubmit}
          onLogin={onLogin}
        />
      )}

      {submitted && (
        <QuizResult
          isCorrect={isCorrect}
          hasResult={!!result}
          explanation={lesson.explanation}
          pointsEarned={result?.points_earned}
          loggedIn={loggedIn}
          onLogin={onLogin}
          onRetry={!isCorrect ? onRetry : undefined}
          solutionUnlocked={solutionUnlocked}
          hasReferenceSolution={window.hasReferenceSolutionMaterial(lesson)}
        />
      )}

      <window.LessonDiscussionSection
        lessonKind="checkbox"
        lessonId={lesson.public_id}
        onLogin={onLogin}
        showReferenceSolution={window.hasReferenceSolutionMaterial(lesson)}
        referenceSolution={lesson.reference_solution}
        solutionUnlocked={solutionUnlocked}
        wrongAttempts={lesson.wrong_attempts}
        sessionFails={effectiveFails}
      />
    </div>
  );
}

// ─── Shared quiz sub-components ──────────────────────────────────────────────

function LessonHeader({ type, title, label, badge, points }) {
  const icons = { theory: '📖', radio: '🔘', checkbox: '☑️', coding: '💻' };
  const tints = { theory: 'bg-blue-50', radio: 'bg-violet-50', checkbox: 'bg-cyan-50', coding: 'bg-purple-50' };
  return (
    <div className="flex items-start gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center text-2xl shrink-0 ${tints[type] || 'bg-paper'}`}>
        {icons[type] || '📄'}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/40 mb-1">{label}</div>
        <h1 className="text-[22px] font-extrabold text-ink leading-tight">{title}</h1>
        {(badge || points != null) && (
          <div className="mt-2 flex flex-wrap gap-2">
            {badge && <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-violet-500/10 text-violet-600">{badge}</span>}
            {points != null && <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-flame-500/10 text-flame-500">+{points} XP</span>}
          </div>
        )}
      </div>
    </div>
  );
}

function QuizMeta({ points }) {
  if (!points) return null;
  return (
    <div className="mt-4 text-[11px] text-ink/40 flex items-center gap-1">
      <I.Star className="w-3 h-3 text-amber-400"/>
      {points} {points === 1 ? 'балл' : points < 5 ? 'балла' : 'баллов'} за правильный ответ
    </div>
  );
}

function QuizActions({ disabled, loading, loggedIn, onSubmit, onLogin }) {
  return (
    <div className="mt-7 flex flex-wrap items-center gap-3">
      <button onClick={onSubmit} disabled={disabled || loading}
        className="btn-grad btn-shimmer h-12 px-7 rounded-xl text-white font-semibold
          inline-flex items-center gap-2 shadow-soft
          disabled:opacity-40 disabled:cursor-not-allowed">
        {loading
          ? <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"/>
          : <I.Send className="w-4 h-4"/>
        }
        {loading ? 'Проверяем…' : 'Проверить ответ'}
      </button>
      {!loggedIn && (
        <button onClick={onLogin}
          className="h-12 px-4 rounded-xl border border-black/[0.08] text-sm text-ink/55 hover:border-violet-300 hover:text-violet-600 transition-colors">
          Войти для сохранения баллов
        </button>
      )}
    </div>
  );
}

function QuizResult({ isCorrect, hasResult, explanation, pointsEarned, loggedIn, onLogin, onRetry, solutionUnlocked, hasReferenceSolution }) {
  const showScore = hasResult && isCorrect !== undefined;
  return (
    <div className={`mt-7 p-5 rounded-2xl border ${
      !showScore
        ? 'bg-blue-50 border-blue-200'
        : isCorrect
          ? 'bg-emerald-50 border-emerald-200'
          : 'bg-rose-50 border-rose-200'
    }`}>
      <div className="flex items-center gap-2 mb-2">
        {!showScore && (
          <span className="text-sm font-semibold text-blue-700">Ответ записан</span>
        )}
        {showScore && isCorrect && (
          <>
            <span className="check-dot"/>
            <span className="font-bold text-emerald-700">Правильно!</span>
            {pointsEarned > 0 && (
              <span className="text-xs font-semibold text-emerald-600 px-2 py-0.5 rounded-full bg-emerald-100">
                +{pointsEarned} {pointsEarned === 1 ? 'балл' : pointsEarned < 5 ? 'балла' : 'баллов'}
              </span>
            )}
          </>
        )}
        {showScore && !isCorrect && (
          <>
            <span className="cross-dot"/>
            <span className="font-bold text-red-700">Неверно</span>
          </>
        )}
      </div>
      {explanation && (
        <p className="text-[13.5px] text-ink/70 leading-relaxed mt-1">{explanation}</p>
      )}
      {solutionUnlocked && hasReferenceSolution && (
        <button type="button" onClick={() => window.scrollToLessonReferenceSolution?.()}
          className="mt-4 h-11 px-5 rounded-xl bg-white border border-violet-200 text-sm font-semibold text-violet-700
            hover:border-violet-300 hover:bg-violet-50 transition-colors inline-flex items-center gap-2">
          <I.Play className="w-4 h-4"/>
          Разбор ниже ↓
        </button>
      )}
      {onRetry && (
        <button type="button" onClick={onRetry}
          className="mt-4 h-11 px-5 rounded-xl bg-white border border-rose-200 text-sm font-semibold text-rose-700
            hover:border-rose-300 hover:bg-rose-50 transition-colors inline-flex items-center gap-2">
          <I.Refresh className="w-4 h-4"/>
          Решить ещё раз
        </button>
      )}
      {!loggedIn && (
        <button onClick={onLogin}
          className="mt-3 text-[12px] text-violet-600 underline underline-offset-2 hover:text-violet-800 transition-colors">
          Войдите, чтобы сохранить прогресс →
        </button>
      )}
    </div>
  );
}

// ─── Coding challenge ────────────────────────────────────────────────────────

function CodeSubmissionResult({ result, points, loggedIn, onLogin, onRetry, solutionUnlocked, hasReferenceSolution }) {
  if (!result) return null;

  const passed = result.status === 'completed';
  const pending = result.status === 'pending' || result.status === 'running';
  const testsLine = result.total_tests > 0
    ? `${result.tests_passed || 0} / ${result.total_tests} тестов`
    : null;

  return (
    <div className={`mt-7 p-5 rounded-2xl border ${
      pending
        ? 'bg-blue-50 border-blue-200'
        : passed
          ? 'bg-emerald-50 border-emerald-200'
          : 'bg-rose-50 border-rose-200'
    }`}>
      <div className="flex flex-wrap items-center gap-2 mb-2">
        {pending && (
          <span className="text-sm font-semibold text-blue-700">Решение в очереди на проверку…</span>
        )}
        {passed && (
          <>
            <span className="check-dot"/>
            <span className="font-bold text-emerald-700">Все тесты пройдены!</span>
            {points > 0 && (
              <span className="text-xs font-semibold text-emerald-600 px-2 py-0.5 rounded-full bg-emerald-100">
                +{points} {points === 1 ? 'балл' : points < 5 ? 'балла' : 'баллов'}
              </span>
            )}
          </>
        )}
        {!pending && !passed && (
          <>
            <span className="cross-dot"/>
            <span className="font-bold text-red-700">Решение не принято</span>
          </>
        )}
      </div>

      {testsLine && (
        <p className="text-[13.5px] text-ink/70">{testsLine}</p>
      )}

      {result.error_message && (
        <pre className="mt-2 text-[13px] text-ink/75 whitespace-pre-wrap font-mono leading-relaxed">
          {result.error_message}
        </pre>
      )}

      {result.failed_test_number != null && (
        <p className="mt-2 text-[13px] text-ink/65">
          Не прошёл тест №{result.failed_test_number}
        </p>
      )}

      {(result.actual_output != null || result.expected_output != null) && (
        <div className="mt-3 space-y-2 text-[13px] font-mono">
          {result.actual_output != null && (
            <div>
              <span className="text-ink/50">ваш вывод: </span>
              <pre className="whitespace-pre-wrap mt-0.5 text-red-800">{result.actual_output}</pre>
            </div>
          )}
          {result.expected_output != null && (
            <div>
              <span className="text-ink/50">ожидалось: </span>
              <pre className="whitespace-pre-wrap mt-0.5 text-emerald-800">{result.expected_output}</pre>
            </div>
          )}
        </div>
      )}

      {!pending && !passed && onRetry && (
        <button type="button" onClick={onRetry}
          className="mt-4 h-11 px-5 rounded-xl bg-white border border-rose-200 text-sm font-semibold text-rose-700
            hover:border-rose-300 hover:bg-rose-50 transition-colors inline-flex items-center gap-2">
          <I.Refresh className="w-4 h-4"/>
          Решить ещё раз
        </button>
      )}

      {solutionUnlocked && hasReferenceSolution && (
        <button type="button" onClick={() => window.scrollToLessonReferenceSolution?.()}
          className="mt-4 h-11 px-5 rounded-xl bg-white border border-violet-200 text-sm font-semibold text-violet-700
            hover:border-violet-300 hover:bg-violet-50 transition-colors inline-flex items-center gap-2">
          <I.Play className="w-4 h-4"/>
          Разбор ниже ↓
        </button>
      )}

      {!loggedIn && (
        <button onClick={onLogin}
          className="mt-3 text-[12px] text-violet-600 underline underline-offset-2 hover:text-violet-800 transition-colors">
          Войдите, чтобы сохранить прогресс →
        </button>
      )}
    </div>
  );
}

function CodingLesson({ lesson, isDone, onComplete, onLogin, onRefreshLesson }) {
  const loggedIn = !!localStorage.getItem('access_token');
  const [code, setCode] = React.useState(lesson.initial_code || DEFAULT_PYTHON_CODE);
  const [submitLoading, setSubmitLoading] = React.useState(false);
  const [submitError, setSubmitError] = React.useState(null);
  const [submitResult, setSubmitResult] = React.useState(null);

  React.useEffect(() => {
    setCode(lesson.initial_code || DEFAULT_PYTHON_CODE);
    setSubmitLoading(false);
    setSubmitError(null);
    setSubmitResult(null);
  }, [lesson.public_id, lesson.initial_code]);

  const tests = (lesson.test_cases || []).slice().sort(
    (a, b) => (a.order_index || 0) - (b.order_index || 0),
  );

  const solved = isDone || submitResult?.status === 'completed';
  const failed = submitResult && isCodeSubmissionFinal(submitResult.status) && submitResult.status !== 'completed';
  const solutionUnlocked = window.computeSolutionUnlocked(lesson, 0, solved);

  React.useEffect(() => {
    if (!solutionUnlocked || !loggedIn || lesson.reference_solution) return;
    onRefreshLesson?.();
  }, [solutionUnlocked, loggedIn, lesson.public_id, lesson.reference_solution, onRefreshLesson]);

  const handleSubmit = async () => {
    if (submitLoading) return;
    if (!loggedIn) {
      onLogin();
      return;
    }
    const trimmed = (code || '').trim();
    if (!trimmed) {
      setSubmitError('Введите код решения.');
      return;
    }

    setSubmitLoading(true);
    setSubmitError(null);
    setSubmitResult(null);

    try {
      const created = await window.fetchApiJson('/api/progress/code/', {
        method: 'POST',
        body: { challenge: lesson.public_id, code: trimmed },
        auth: true,
      });
      setSubmitResult(created);

      if (isCodeSubmissionFinal(created.status)) {
        if (created.status === 'completed') onComplete();
        else onRefreshLesson?.();
        return;
      }

      const final = await pollCodeSubmission(created.public_id);
      setSubmitResult(final);
      if (final.status === 'completed') onComplete();
      else onRefreshLesson?.();
    } catch (e) {
      setSubmitError(e.message || 'Не удалось отправить решение');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleRetry = () => {
    setSubmitResult(null);
    setSubmitError(null);
  };

  return (
    <div>
      <LessonHeader
        type="coding"
        title={lesson.title}
        label="Задача с кодом"
        badge={lesson.difficulty_display || lesson.difficulty}
        points={lesson.points}
      />

      {lesson.description && (
        <div className="mt-6 p-6 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft whitespace-pre-wrap text-[15px] text-ink/80 leading-relaxed">
          {lesson.description}
        </div>
      )}

      <window.LessonInstructorNote text={lesson.comment} />

      {lesson.instructions && (
        <div className="mt-5">
          <div className="text-xs font-semibold uppercase tracking-widest text-ink/60 mb-2">Инструкции</div>
          <div className="rounded-xl bg-black/[0.025] ring-1 ring-black/[0.04] p-4 font-mono text-[13px] whitespace-pre-wrap">
            {lesson.instructions}
          </div>
        </div>
      )}

      {tests.length > 0 && (
        <div className="mt-6 space-y-3">
          <div className="text-xs font-semibold uppercase tracking-widest text-ink/60">
            Публичные тесты ({tests.length})
          </div>
          {tests.map((tc, i) => (
            <div key={tc.public_id || i} className="rounded-xl ring-1 ring-black/[0.06] p-4 bg-black/[0.02] text-[13px] font-mono">
              <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/45 mb-2">Тест {i + 1}</div>
              <div><span className="text-ink/50">вход: </span><pre className="whitespace-pre-wrap mt-0.5">{tc.input_data}</pre></div>
              <div><span className="text-ink/50">ожидается: </span><pre className="whitespace-pre-wrap mt-0.5 text-emerald-700">{tc.expected_output}</pre></div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 rounded-2xl overflow-hidden ring-1 ring-black/[0.06] bg-[#0f172a]">
        <div className="px-4 py-2.5 border-b border-white/10 flex items-center gap-2 text-xs text-slate-400">
          <span className="px-2 py-0.5 rounded bg-white/10">Python</span>
          <span className="ml-auto font-mono">solution.py</span>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck="false"
          disabled={submitLoading}
          className="w-full min-h-[280px] bg-transparent text-slate-100 font-mono text-xs leading-[1.55] p-4 resize-y focus:outline-none disabled:opacity-60"
          style={{ caretColor: '#06B6D4' }}
        />
      </div>

      {(lesson.time_limit_ms || lesson.memory_limit_mb) && (
        <p className="mt-3 text-sm text-ink/50">
          Лимиты: {lesson.time_limit_ms || '—'} мс, {lesson.memory_limit_mb || '—'} МБ.
        </p>
      )}

      {submitError && (
        <p className="mt-4 text-sm text-red-600">{submitError}</p>
      )}

      {(!submitResult || failed) && (
        <QuizActions
          disabled={!code.trim()}
          loading={submitLoading}
          loggedIn={loggedIn}
          onSubmit={handleSubmit}
          onLogin={onLogin}
        />
      )}

      <CodeSubmissionResult
        result={submitResult}
        points={lesson.points}
        loggedIn={loggedIn}
        onLogin={onLogin}
        onRetry={failed ? handleRetry : undefined}
        solutionUnlocked={solutionUnlocked}
        hasReferenceSolution={window.hasReferenceSolutionMaterial(lesson)}
      />

      {solved && !submitLoading && (
        <div className="mt-6 flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
          <span className="check-dot"/>
          <span className="text-sm font-semibold text-emerald-700">Задача решена</span>
        </div>
      )}

      <window.LessonDiscussionSection
        lessonKind="coding"
        lessonId={lesson.public_id}
        onLogin={onLogin}
        showReferenceSolution={window.hasReferenceSolutionMaterial(lesson)}
        referenceSolution={lesson.reference_solution}
        solutionUnlocked={solutionUnlocked}
        wrongAttempts={lesson.wrong_attempts}
        sessionFails={0}
      />
    </div>
  );
}

window.LearnPage = LearnPage;
