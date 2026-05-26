// COURSE page — course detail from API (modules without lesson pages)

const Routes = window.Routes;
const FM = window.FM;
const I = window.I;
const CourseCover = window.CourseCover;
const mapApiCourseToCourse = window.mapApiCourseToCourse;
const mapApiModules = window.mapApiModules;


// ── CoursePage ──────────────────────────────────────────────────────────────
function CoursePage({ navigate, hashParams }) {
  const courseId = hashParams && hashParams.get ? hashParams.get('id') : null;
  const [apiRow, setApiRow] = React.useState(null);
  const [loadState, setLoadState] = React.useState(() => (courseId ? 'loading' : 'idle'));
  const [loadError, setLoadError] = React.useState('');

  React.useEffect(() => {
    if (!courseId) {
      setApiRow(null);
      setLoadState('idle');
      setLoadError('');
      return;
    }
    let cancelled = false;
    setLoadState('loading');
    setApiRow(null);
    setLoadError('');
    (async () => {
      try {
        const data = await window.apiJson(`/api/content/courses/${encodeURIComponent(courseId)}/`);
        if (!cancelled) {
          setApiRow(data);
          setLoadState('ok');
        }
      } catch (e) {
        if (!cancelled) {
          setLoadError(e.message || 'Не удалось загрузить курс');
          setLoadState('err');
        }
      }
    })();
    return () => { cancelled = true; };
  }, [courseId]);

  const course = apiRow ? mapApiCourseToCourse(apiRow) : null;

  if (loadState === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center gap-3 text-ink/60 bg-paper">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">Загружаем курс…</div>
      </div>
    );
  }

  if (!course || loadState === 'err' || (loadState === 'idle' && !courseId)) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-paper text-center px-6">
        <div className="text-5xl">🔍</div>
        <div className="text-xl font-bold text-ink/80">Курс не найден</div>
        <p className="text-sm text-ink/55 max-w-sm">
          {loadError || 'Возможно, курс был перемещён или ещё не добавлен в каталог.'}
        </p>
        <button onClick={() => navigate(Routes.CATALOG)}
          className="btn-grad btn-shimmer mt-2 h-11 px-6 rounded-xl text-white font-semibold">
          Открыть каталог
        </button>
      </div>
    );
  }

  const modules = mapApiModules(apiRow.modules);
  const totalLessons = modules.reduce((s, m) => s + (m.lessons || 0), 0);
  const totalQuizzes = modules.reduce((s, m) => s + (m.quizzes || 0), 0);
  const totalHours = modules.length;

  return (
    <div data-screen-label="Course" className="min-h-screen bg-paper">
      <CourseHero course={course} navigate={navigate} modules={modules}
        totalLessons={totalLessons} totalQuizzes={totalQuizzes} totalHours={totalHours}/>
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-14 grid lg:grid-cols-[1fr_340px] gap-10">
        <div className="space-y-10">
          <CourseHighlights course={course}/>
          <CourseModulesSection modules={modules} navigate={navigate} course={course}/>
        </div>
        <div>
          <CourseSidebar course={course} navigate={navigate}
            totalLessons={totalLessons} totalQuizzes={totalQuizzes} totalHours={totalHours}/>
        </div>
      </div>
    </div>
  );
}

// ── Hero ─────────────────────────────────────────────────────────────────────
function CourseHero({ course, navigate, modules, totalLessons, totalQuizzes, totalHours }) {
  const M = FM.motion;
  return (
    <section className="relative overflow-hidden"
      style={{ background: `linear-gradient(135deg, ${course.gradFrom} 0%, ${course.gradTo} 100%)` }}>
      {/* decorative overlay */}
      <div className="absolute inset-0 opacity-20"
        style={{ backgroundImage: 'repeating-linear-gradient(45deg, rgba(255,255,255,0.1) 0 2px, transparent 2px 48px)' }}/>
      <div className="absolute -top-20 -right-20 w-96 h-96 rounded-full bg-white/20 blur-3xl"/>
      <div className="absolute -bottom-20 -left-10 w-80 h-80 rounded-full bg-white/10 blur-3xl"/>

      <div className="relative max-w-7xl mx-auto px-5 sm:px-8 py-14 pb-16">
        {/* breadcrumb */}
        <M.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
          className="flex items-center gap-2 text-white/70 text-sm mb-8">
          <button onClick={() => navigate(Routes.LANDING)} className="hover:text-white transition-colors">Главная</button>
          <I.ChevronRight className="w-3.5 h-3.5"/>
          <button onClick={() => navigate(Routes.CATALOG)} className="hover:text-white transition-colors">Каталог</button>
          <I.ChevronRight className="w-3.5 h-3.5"/>
          <span className="text-white/90 truncate max-w-[200px]">{course.title}</span>
        </M.div>

        <div className="grid lg:grid-cols-[1fr_auto] gap-8 items-start">
          <div>
            {/* tags */}
            <M.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, delay: 0.05 }}
              className="flex flex-wrap gap-2 mb-5">
              {(course.tags || []).slice(0, 4).map((t) => (
                <span key={t} className="px-3 py-1 rounded-full text-xs font-semibold bg-white/20 text-white backdrop-blur border border-white/30 uppercase tracking-wide">
                  {t}
                </span>
              ))}
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/15 text-white/80 backdrop-blur border border-white/20">
                {course.level}
              </span>
            </M.div>

            {/* title */}
            <M.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.1 }}
              className="text-3xl sm:text-5xl font-extrabold text-white leading-tight mb-4 max-w-2xl">
              {course.title}
            </M.h1>

            {/* desc */}
            <M.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.18 }}
              className="text-white/80 text-lg max-w-xl leading-relaxed mb-8">
              {course.desc}
            </M.p>

            {/* stats row */}
            <M.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.26 }}
              className="flex flex-wrap items-center gap-5 text-white/90 text-sm mb-8">
              {course.rating && course.rating !== '—' && (
                <span className="flex items-center gap-1.5 font-semibold">
                  <I.Star className="w-4 h-4 text-amber-300"/>
                  {course.rating} рейтинг
                </span>
              )}
              {course.students > 0 && (
                <span className="flex items-center gap-1.5">
                  <I.Users className="w-4 h-4"/>
                  {course.students.toLocaleString('ru-RU')} учеников
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <I.Book className="w-4 h-4"/>
                {totalLessons} уроков
              </span>
              {totalQuizzes > 0 && (
                <span className="flex items-center gap-1.5">
                  <I.Code className="w-4 h-4"/>
                  {totalQuizzes} тестов
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <I.Clock className="w-4 h-4"/>
                {totalHours} часов
              </span>
              <span className="flex items-center gap-1.5">
                <I.Layers className="w-4 h-4"/>
                {modules.length} модулей
              </span>
            </M.div>

            {/* CTAs */}
            <M.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.32 }}
              className="flex flex-wrap gap-3">
              <button
                onClick={() => navigate(Routes.LEARN, { course: course.id })}
                className="h-14 px-7 rounded-2xl bg-white text-ink font-bold text-[15px] inline-flex items-center gap-2.5 hover:scale-[1.02] transition-transform shadow-glow">
                <I.Play className="w-5 h-5 text-violet-600"/> Учиться
              </button>
              <button
                onClick={() => navigate(Routes.AUTH)}
                className="h-14 px-6 rounded-2xl bg-white/15 backdrop-blur border border-white/30 text-white font-semibold inline-flex items-center gap-2 hover:bg-white/25 transition-colors">
                Записаться на курс <I.ChevronRight className="w-4 h-4"/>
              </button>
            </M.div>
          </div>

          {/* floating card — course preview */}
          <M.div initial={{ opacity: 0, x: 30, scale: 0.95 }} animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="hidden lg:block w-72 bg-white rounded-3xl shadow-glow ring-1 ring-white/20 overflow-hidden">
            <CourseCover course={course} big/>
            <div className="p-5 space-y-3">
              {[
                { icon: '✅', text: `${totalLessons} уроков с разбором` },
                { icon: '🎯', text: `${totalQuizzes} интерактивных тестов` },
                { icon: '🏆', text: 'Сертификат по итогам' },
                { icon: '💬', text: 'Личный ментор' },
              ].map((it, i) => (
                <div key={i} className="flex items-center gap-3 text-sm text-ink/80">
                  <span className="text-base">{it.icon}</span>
                  {it.text}
                </div>
              ))}
            </div>
          </M.div>
        </div>
      </div>
    </section>
  );
}

// ── Highlights ────────────────────────────────────────────────────────────────
function CourseHighlights({ course }) {
  const M = FM.motion;
  const items = [
    { icon: I.Code,    tint: '#2563EB', title: 'Практика с первого дня',    desc: 'Каждый модуль заканчивается реальной задачей. Не «а вот пример», а «напиши сам».' },
    { icon: I.Chat,    tint: '#06B6D4', title: 'Живое code review',         desc: 'Ментор открывает твоё решение, прогоняет его и оставляет комментарии прямо в строках.' },
    { icon: I.Sparkle, tint: '#0EA5E9', title: 'Без воды',                  desc: 'Никаких 3-часовых лекций. Каждый урок — одна тема, один навык, одна задача.' },
    { icon: I.Trophy,  tint: '#7C3AED', title: 'Сертификат по итогам',      desc: 'После защиты финального проекта получишь именной сертификат.' },
  ];
  return (
    <div>
      <h2 className="text-2xl font-extrabold mb-6 tracking-tight">Чему ты научишься</h2>
      <div className="grid sm:grid-cols-2 gap-4">
        {items.map((it, i) => (
          <M.div key={i}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.45, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
            className="flex gap-4 p-5 bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft hover:shadow-glow transition-shadow">
            <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: `${it.tint}18`, color: it.tint }}>
              <it.icon className="w-5 h-5"/>
            </div>
            <div>
              <div className="font-semibold text-[15px] leading-tight mb-1">{it.title}</div>
              <div className="text-sm text-ink/60 leading-relaxed">{it.desc}</div>
            </div>
          </M.div>
        ))}
      </div>
    </div>
  );
}

// ── Modules accordion ─────────────────────────────────────────────────────────
function CourseModulesSection({ modules, navigate, course }) {
  const M = FM.motion;
  const [open, setOpen] = React.useState(new Set([modules[0]?.id]));

  const toggle = (id) => {
    setOpen((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const totalActivities = modules.reduce((s, m) => s + (m.lessons || 0) + (m.quizzes || 0), 0);

  return (
    <div>
      <div className="flex items-end justify-between mb-6">
        <h2 className="text-2xl font-extrabold tracking-tight">Программа курса</h2>
        <div className="text-sm text-ink/50">
          {modules.length} модулей{totalActivities > 0 ? ` · ${totalActivities} материалов` : ''}
        </div>
      </div>

      <div className="space-y-3">
        {modules.map((mod, mi) => {
          const isOpen = open.has(mod.id);
          const activityCount = (mod.lessons || 0) + (mod.quizzes || 0);
          return (
            <M.div key={mod.id}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.4, delay: mi * 0.06, ease: [0.16, 1, 0.3, 1] }}
              className="bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft overflow-hidden">

              {/* module header */}
              <button type="button" onClick={() => toggle(mod.id)}
                className="w-full text-left px-6 py-5 flex items-center gap-4 hover:bg-black/[0.015] transition-colors group">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl bg-paper shrink-0 ring-1 ring-black/[0.06]">
                  {mod.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[11px] font-semibold uppercase tracking-widest text-ink/40">Модуль {mi + 1}</span>
                    {activityCount > 0 && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-700 font-semibold">
                        {activityCount} материалов
                      </span>
                    )}
                  </div>
                  <div className="font-bold text-[16px] leading-snug truncate">{mod.title}</div>
                  {(mod.lessons > 0 || mod.quizzes > 0) ? (
                    <div className="text-xs text-ink/50 mt-1 flex items-center gap-3 flex-wrap">
                      {mod.lessons > 0 && <span>{mod.lessons} уроков</span>}
                      {mod.lessons > 0 && mod.quizzes > 0 && <span>·</span>}
                      {mod.quizzes > 0 && <span>{mod.quizzes} тестов</span>}
                    </div>
                  ) : mod.description ? (
                    <p className="text-xs text-ink/50 mt-1 line-clamp-2">{mod.description}</p>
                  ) : null}
                </div>
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center transition-all shrink-0
                  ${isOpen ? 'grad-bg text-white' : 'bg-black/[0.04] text-ink/50 group-hover:bg-black/[0.07]'}`}>
                  <I.ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}/>
                </div>
              </button>

              {/* module items */}
              <FM.AnimatePresence initial={false}>
                {isOpen && (
                  <M.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}>
                    <div className="border-t border-black/[0.05]">
                      <p className="px-6 py-4 text-sm text-ink/65 leading-relaxed">
                        {mod.description
                          || (activityCount > 0
                            ? 'Уроки и тесты откроются в следующих версиях интерфейса.'
                            : 'Содержимое модуля скоро появится.')}
                      </p>
                    </div>
                  </M.div>
                )}
              </FM.AnimatePresence>
            </M.div>
          );
        })}
      </div>
    </div>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function CourseSidebar({ course, navigate, totalLessons, totalQuizzes, totalHours }) {
  const M = FM.motion;
  const [sticky, setSticky] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => setSticky(window.scrollY > 280);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const includes = [
    { icon: '📖', text: `${totalLessons} структурированных уроков` },
    { icon: '🎯', text: `${totalQuizzes} тестов в модулях` },
    { icon: '💬', text: 'Личный ментор в чате' },
    { icon: '⏱️', text: `${totalHours} часов контента` },
    { icon: '🏆', text: 'Именной сертификат' },
    { icon: '🔄', text: 'Пожизненный доступ к материалам' },
  ];

  return (
    <div className={`lg:sticky lg:top-20 space-y-5 transition-all`}>
      {/* price card */}
      <M.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
        className="bg-white rounded-3xl ring-1 ring-black/[0.06] shadow-glow overflow-hidden">
        <CourseCover course={course}/>
        <div className="p-6">
          {course.price > 0 && (
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-3xl font-extrabold">{course.price.toLocaleString('ru-RU')} ₽</span>
              <span className="text-sm text-ink/40 line-through">{Math.round(course.price * 1.43).toLocaleString('ru-RU')} ₽</span>
            </div>
          )}
          {course.price > 0 && (
            <div className="text-xs font-semibold text-emerald-600 mb-4 flex items-center gap-1">
              <I.Bolt className="w-3 h-3"/> Скидка 30% — до 30 мая
            </div>
          )}
          <button onClick={() => navigate(Routes.LEARN, { course: course.id })}
            className="btn-grad btn-shimmer w-full h-13 py-3.5 rounded-2xl text-white font-bold text-[15px] inline-flex items-center justify-center gap-2 shadow-glow mb-3">
            <I.Play className="w-4 h-4"/> Учиться
            <I.ChevronRight className="w-4 h-4"/>
          </button>
          <button onClick={() => navigate(Routes.AUTH)}
            className="w-full h-11 rounded-xl border border-black/[0.08] text-sm font-semibold text-ink/70 hover:border-violet-300 hover:text-violet-600 transition-colors inline-flex items-center justify-center gap-2">
            Записаться на курс
          </button>

          <div className="mt-5 pt-5 border-t border-black/[0.05] space-y-2.5">
            <div className="text-xs font-semibold uppercase tracking-widest text-ink/50 mb-3">Курс включает</div>
            {includes.map((it, i) => (
              <div key={i} className="flex items-center gap-3 text-sm text-ink/75">
                <span className="text-base">{it.icon}</span>
                {it.text}
              </div>
            ))}
          </div>
        </div>
      </M.div>

      {/* mentor card */}
      <M.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.18, ease: [0.16, 1, 0.3, 1] }}
        className="bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft p-5">
        <div className="text-xs font-semibold uppercase tracking-widest text-ink/50 mb-4">Ведущий ментор</div>
        <div className="flex items-center gap-3 mb-4">
          <div className="avatar-ring">
            <div className="w-12 h-12 rounded-full bg-white flex items-center justify-center text-sm font-bold grad-text">КБ</div>
          </div>
          <div>
            <div className="font-bold">Кирилл Бервинов</div>
            <div className="text-xs text-ink/55 flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulseDot"/>
              Онлайн · отвечает за 1 час
            </div>
          </div>
        </div>
        <p className="text-sm text-ink/65 leading-relaxed">
          8 лет опыта в Python и системном дизайне. Через меня прошло 5 600+ учеников. Отвечаю лично, без шаблонов.
        </p>
        <div className="mt-4 flex items-center gap-4 text-xs text-ink/55">
          <span className="flex items-center gap-1"><I.Star className="w-3.5 h-3.5 text-amber-400"/> 4.9</span>
          <span className="flex items-center gap-1"><I.Users className="w-3.5 h-3.5"/> 5 600+ учеников</span>
          <span className="flex items-center gap-1"><I.Book className="w-3.5 h-3.5"/> 6 курсов</span>
        </div>
      </M.div>
    </div>
  );
}

window.CoursePage = CoursePage;
