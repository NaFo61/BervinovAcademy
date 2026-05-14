// LANDING page — hero + why + top courses + footer

function LandingPage({ navigate }) {
  return (
    <div data-screen-label="01 Landing" className="min-h-screen">
      <Hero navigate={navigate} />
      <WhySection />
      <TopCourses navigate={navigate} />
      <CTABand navigate={navigate} />
    </div>
  );
}

function Hero({ navigate }) {
  const M = FM.motion;
  return (
    <section className="relative mesh-bg pt-10 sm:pt-20 pb-24 overflow-hidden">
      <FloatingShapes />
      <div className="relative max-w-7xl mx-auto px-5 sm:px-8 grid lg:grid-cols-[1.1fr,1fr] gap-12 lg:gap-8 items-center">
        {/* LEFT */}
        <div>
          <M.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/70 backdrop-blur border border-violet-500/15 text-xs font-medium text-ink/70 mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-flame-500 animate-pulseDot"/>
            Набор на весенний поток открыт · скидка 30% до 30 мая
          </M.div>
          <M.h1 initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.05 }}
            className="text-[40px] sm:text-[56px] lg:text-[64px] font-extrabold leading-[1.02] tracking-tight">
            Учись у <span className="grad-text">Мирона</span>.<br/>
            Эффективно. Удобно.<br/>
            <span className="relative inline-block">
              По‑настоящему.
              <svg className="absolute -bottom-2 left-0 w-full" height="14" viewBox="0 0 320 14" fill="none" preserveAspectRatio="none">
                <path d="M2 10 Q 80 2 160 7 T 318 6" stroke="url(#hg)" strokeWidth="3" strokeLinecap="round" fill="none"/>
                <defs><linearGradient id="hg" x1="0" y1="0" x2="320" y2="0"><stop stopColor="#7C3AED"/><stop offset="1" stopColor="#F97316"/></linearGradient></defs>
              </svg>
            </span>
          </M.h1>
          <M.p initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg text-ink/65 mt-6 max-w-xl leading-relaxed">
            Курсы программирования с живой проверкой кода и личным ментором. Без воды, без скучных лекций — только то, что реально пригодится в работе.
          </M.p>
          <M.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.32 }}
            className="mt-8 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <button onClick={() => navigate(Routes.AUTH)}
              className="btn-grad btn-shimmer h-14 px-7 rounded-2xl text-white font-semibold shadow-glow inline-flex items-center gap-2">
              Начать учиться <I.ChevronRight className="w-5 h-5"/>
            </button>
            <button onClick={() => navigate(Routes.CATALOG)}
              className="h-14 px-6 rounded-2xl bg-white/70 backdrop-blur border border-black/[0.06] hover:border-violet-300 font-semibold inline-flex items-center gap-2 transition-colors">
              <I.Play className="w-4 h-4 text-violet-600"/> Посмотреть каталог
            </button>
          </M.div>
          {/* social proof */}
          <M.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 0.6 }}
            className="mt-10 flex items-center gap-6">
            <div className="flex -space-x-2">
              {['#7C3AED', '#F97316', '#EC4899', '#06B6D4', '#22C55E'].map((c, i) => (
                <div key={i} className="w-9 h-9 rounded-full border-2 border-white flex items-center justify-center text-white text-[11px] font-bold"
                     style={{ background: `linear-gradient(135deg, ${c}, ${c}99)` }}>
                  {['АК','МС','ДП','ЕН','+'][i]}
                </div>
              ))}
            </div>
            <div className="text-sm">
              <div className="flex items-center gap-1">
                {[0,1,2,3,4].map(i => <I.Star key={i} className="w-3.5 h-3.5 text-flame-500"/>)}
                <span className="ml-1 font-semibold">4.9</span>
              </div>
              <div className="text-ink/55 text-xs mt-0.5">5 600+ выпускников уже работают</div>
            </div>
          </M.div>
        </div>

        {/* RIGHT — interactive lesson card */}
        <HeroLessonCard />
      </div>
    </section>
  );
}

function HeroLessonCard() {
  const M = FM.motion;
  const [progress, setProgress] = React.useState(0);
  const [achievements, setAchievements] = React.useState([]);

  React.useEffect(() => {
    let raf;
    const start = performance.now();
    const tick = (t) => {
      const dt = (t - start) / 8000;
      const p = (dt % 1) * 100;
      setProgress(p);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  React.useEffect(() => {
    const pool = [
      { icon: '✅', text: 'Задача решена!', tint: '#22C55E' },
      { icon: '🔥', text: 'Серия 7 дней', tint: '#F97316' },
      { icon: '⚡', text: '+15 XP', tint: '#7C3AED' },
      { icon: '🏆', text: 'Урок 3/12', tint: '#EAB308' },
    ];
    let i = 0;
    let uid = 0;
    const id = setInterval(() => {
      uid += 1;
      const a = { ...pool[i % pool.length], key: `ach-${uid}` };
      i++;
      setAchievements((prev) => [...prev, a].slice(-3));
      setTimeout(() => setAchievements((p) => p.filter((x) => x.key !== a.key)), 3200);
    }, 1700);
    return () => clearInterval(id);
  }, []);

  return (
    <M.div initial={{ opacity: 0, scale: 0.95, rotateY: -8 }} animate={{ opacity: 1, scale: 1, rotateY: 0 }}
      transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
      className="relative" style={{ perspective: 1200 }}>
      <div className="absolute -inset-6 -z-10 rounded-[40px] grad-bg-soft blur-2xl"/>

      <div className="relative bg-white rounded-3xl shadow-glow ring-1 ring-black/5 overflow-hidden">
        <div className="grad-bg p-5 text-white relative overflow-hidden">
          <div className="absolute -top-12 -right-8 w-44 h-44 rounded-full bg-white/15 blur-2xl"/>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[11px] uppercase tracking-widest opacity-80">
              <I.Book className="w-3.5 h-3.5"/> Python · Урок 8 из 42
            </div>
            <div className="flex items-center gap-1 text-[11px] bg-white/20 backdrop-blur px-2 py-1 rounded-full">
              <I.Clock className="w-3 h-3"/> 18 мин
            </div>
          </div>
          <div className="mt-3 text-xl font-bold leading-tight">Декораторы: как работают на самом деле</div>
        </div>

        <div className="px-5 pt-4 pb-2">
          <div className="flex items-center justify-between text-[11px] uppercase tracking-widest text-ink/50 mb-2">
            <span>Прогресс урока</span><span className="font-mono text-ink/70">{Math.round(progress)}%</span>
          </div>
          <div className="h-2 bg-black/[0.05] rounded-full overflow-hidden">
            <div className="h-full grad-bg rounded-full transition-[width] duration-100" style={{ width: `${progress}%` }}/>
          </div>
        </div>

        <div className="mx-5 my-4 rounded-xl code-bg p-4 font-mono text-xs leading-relaxed">
          <div className="flex items-center gap-1.5 mb-3">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-400/70"/>
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400/70"/>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/70"/>
            <span className="ml-2 text-slate-400 text-[10px]">decorator.py</span>
          </div>
          <div><span className="text-violet-300">def</span> <span className="text-amber-300">timeit</span>(func):</div>
          <div className="pl-4"><span className="text-violet-300">def</span> <span className="text-amber-300">wrapper</span>(*args, **kw):</div>
          <div className="pl-8"><span className="text-slate-400"># замеряем время</span></div>
          <div className="pl-8">t = <span className="text-cyan-300">time</span>.<span className="text-amber-300">monotonic</span>()</div>
          <div className="pl-8"><span className="text-violet-300">return</span> func(*args, **kw)</div>
          <div className="pl-4"><span className="text-violet-300">return</span> wrapper</div>
        </div>

        <div className="px-5 pb-5 space-y-2">
          {[
            { label: 'Прочитать материал', done: true },
            { label: 'Решить задачу: @cache', done: progress > 35 },
            { label: 'Сдать ментору', done: progress > 78 },
          ].map((t, i) => (
            <div key={i} className="flex items-center gap-3 text-sm">
              <div className={`w-5 h-5 rounded-md flex items-center justify-center transition-all
                ${t.done ? 'grad-bg text-white' : 'bg-black/[0.06] text-transparent'}`}>
                <I.Check className="w-3.5 h-3.5"/>
              </div>
              <span className={t.done ? 'text-ink line-through decoration-violet-500/40' : 'text-ink/60'}>{t.label}</span>
            </div>
          ))}
        </div>

        <div className="border-t border-black/5 px-5 py-3 flex items-center gap-3 bg-paper">
          <div className="avatar-ring"><div className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-xs font-bold grad-text">МБ</div></div>
          <div className="flex-1">
            <div className="text-xs font-semibold">Мирон Бервинов</div>
            <div className="text-[11px] text-ink/55 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulseDot"/> Ментор онлайн
            </div>
          </div>
          <button className="text-xs font-semibold text-violet-600 inline-flex items-center gap-1">
            <I.Chat className="w-3.5 h-3.5"/> Написать
          </button>
        </div>
      </div>

      <div className="absolute inset-0 pointer-events-none">
        <FM.AnimatePresence>
          {achievements.map((a, idx) => (
            <M.div
              key={a.key}
              initial={{ opacity: 0, x: -20, y: 0, scale: 0.8 }}
              animate={{ opacity: 1, x: 0, y: -idx * 12, scale: 1 }}
              exit={{ opacity: 0, x: 30, scale: 0.9 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="absolute bg-white shadow-glow rounded-2xl px-3.5 py-2.5 ring-1 ring-black/5 flex items-center gap-2.5"
              style={{
                top: `${20 + idx * 14}%`,
                left: idx % 2 === 0 ? '-12%' : 'auto',
                right: idx % 2 === 1 ? '-8%' : 'auto',
              }}>
              <div className="w-8 h-8 rounded-xl flex items-center justify-center text-lg" style={{ background: `${a.tint}22` }}>
                {a.icon}
              </div>
              <div>
                <div className="text-sm font-semibold leading-tight">{a.text}</div>
                <div className="text-[10px] text-ink/50">только что</div>
              </div>
            </M.div>
          ))}
        </FM.AnimatePresence>
      </div>
    </M.div>
  );
}

function WhySection() {
  const M = FM.motion;
  const items = [
    {
      title: 'Живая проверка кода',
      desc: 'Ментор открывает твоё решение, прогоняет его, оставляет комментарии прямо в строках. Не «принято», а «смотри, здесь можно проще».',
      Icon: I.Code, tint: '#7C3AED',
    },
    {
      title: 'Объясняю просто',
      desc: 'Без академического жаргона. Метафоры, схемы и примеры из реальных проектов — пока не щёлкнет.',
      Icon: I.Brain, tint: '#F97316',
    },
    {
      title: 'Задачи из реальных проектов',
      desc: 'Не «отсортируй массив N-м способом». Парсер, очередь задач, мини-CRM — то, что встретишь на работе.',
      Icon: I.Layers, tint: '#EC4899',
    },
    {
      title: 'Личный чат с ментором',
      desc: 'Застрял в 23:47? Напиши. Отвечаю в течение суток, обычно — за час. Без скриптов и шаблонов.',
      Icon: I.Chat, tint: '#06B6D4',
    },
  ];
  return (
    <section className="relative bg-white">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-24">
        <div className="flex items-end justify-between flex-wrap gap-6 mb-12">
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest text-violet-600 mb-3">Почему со мной</div>
            <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight max-w-2xl">
              Не курсы «галочкой» — а <span className="grad-text">реальный рост</span> в коде.
            </h2>
          </div>
          <p className="text-ink/60 max-w-sm">
            Я преподаю программирование с 2018 года. Через мои руки прошло 5 600+ учеников — от школьников до тимлидов, которые «перезаливают» себя в новый стек.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {items.map((it, i) => (
            <M.div key={i}
              initial={{ opacity: 0, y: 28 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-80px' }}
              transition={{ duration: 0.5, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              whileHover={{ y: -4 }}
              className="bg-paper rounded-2xl p-6 ring-1 ring-black/[0.04] hover:shadow-soft transition-shadow">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-5"
                style={{ background: `${it.tint}18`, color: it.tint }}>
                <it.Icon className="w-6 h-6"/>
              </div>
              <h3 className="font-bold text-lg leading-tight">{it.title}</h3>
              <p className="text-sm text-ink/60 mt-2 leading-relaxed">{it.desc}</p>
            </M.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TopCourses({ navigate }) {
  const M = FM.motion;
  const top3 = COURSES.slice(0, 3);
  return (
    <section className="relative bg-paper">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 py-24">
        <div className="flex items-end justify-between flex-wrap gap-6 mb-12">
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest text-violet-600 mb-3">Топ-3 курса</div>
            <h2 className="text-4xl sm:text-5xl font-extrabold tracking-tight max-w-2xl">
              С чего обычно <span className="grad-text">начинают</span>
            </h2>
          </div>
          <button onClick={() => navigate(Routes.CATALOG)}
            className="inline-flex items-center gap-2 text-sm font-semibold text-ink hover:text-violet-600 transition-colors">
            Весь каталог <I.ChevronRight className="w-4 h-4"/>
          </button>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {top3.map((c, i) => (
            <CourseCard key={c.id} course={c} delay={i * 0.1} onOpen={() => navigate(Routes.CATALOG)} />
          ))}
        </div>
      </div>
    </section>
  );
}

function CTABand({ navigate }) {
  return (
    <section className="relative bg-white">
      <div className="max-w-7xl mx-auto px-5 sm:px-8 pb-24">
        <div className="relative overflow-hidden rounded-3xl grad-bg p-10 sm:p-14 text-white">
          <div className="absolute -top-20 -right-10 w-72 h-72 rounded-full bg-white/15 blur-3xl"/>
          <div className="absolute -bottom-20 -left-10 w-72 h-72 rounded-full bg-white/10 blur-3xl"/>
          <div className="relative flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div>
              <div className="text-xs uppercase tracking-widest opacity-80 mb-3">Готов начать?</div>
              <h3 className="text-3xl sm:text-4xl font-extrabold leading-tight max-w-2xl">
                Первый урок и встреча с ментором — бесплатно.
              </h3>
              <p className="opacity-85 mt-3 max-w-xl">Зарегистрируйся, выбери курс и через 24 часа получишь персональный план обучения от Мирона.</p>
            </div>
            <div className="flex flex-col sm:flex-row gap-3">
              <button onClick={() => navigate(Routes.AUTH)} className="h-14 px-7 rounded-2xl bg-white text-violet-600 font-bold inline-flex items-center gap-2 hover:scale-[1.02] transition-transform">
                Зарегистрироваться <I.ChevronRight className="w-5 h-5"/>
              </button>
              <button onClick={() => navigate(Routes.CATALOG)} className="h-14 px-6 rounded-2xl bg-white/15 backdrop-blur border border-white/30 text-white font-semibold inline-flex items-center gap-2 hover:bg-white/25 transition-colors">
                Открыть каталог
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

window.LandingPage = LandingPage;
