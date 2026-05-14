// PROFILE page — student profile with charts (Recharts)

const RC = window.Recharts || {};

function ProfilePage({ navigate }) {
  return (
    <div data-screen-label="04 Profile" className="min-h-screen pb-16">
      <ProfileHeader/>
      <div className="max-w-7xl mx-auto px-5 sm:px-8 mt-10 grid lg:grid-cols-3 gap-6">
        <ActivityChart/>
        <SkillsChart/>
        <CoursesProgressChart/>
      </div>
      <Achievements/>
      <ActiveCourses navigate={navigate}/>
    </div>
  );
}

function ProfileHeader() {
  return (
    <section className="relative mesh-bg pt-12 pb-10 border-b border-black/[0.04]">
      <FloatingShapes/>
      <div className="relative max-w-7xl mx-auto px-5 sm:px-8">
        <div className="flex flex-col md:flex-row items-start gap-7">
          <div className="avatar-ring">
            <div className="w-28 h-28 rounded-full bg-white flex items-center justify-center text-4xl font-extrabold grad-text">
              АП
            </div>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">Артём Петров</h1>
              <span className="inline-flex items-center gap-1.5 grad-bg text-white text-xs font-bold px-2.5 py-1 rounded-md uppercase tracking-widest">
                <I.Trophy className="w-3 h-3"/> Уровень 4 · Junior
              </span>
            </div>
            <div className="mt-2 flex items-center gap-4 text-sm text-ink/60 flex-wrap">
              <span className="inline-flex items-center gap-1.5"><I.Mail className="w-3.5 h-3.5"/> artem.petrov@gmail.com</span>
              <span className="inline-flex items-center gap-1.5"><I.Calendar className="w-3.5 h-3.5"/> С нами с 14 декабря 2024</span>
              <span className="inline-flex items-center gap-1.5"><I.Bolt className="w-3.5 h-3.5 text-flame-500"/> 1 240 XP</span>
            </div>

            {/* level progress */}
            <div className="mt-5 max-w-md">
              <div className="flex items-center justify-between text-[11px] uppercase tracking-widest text-ink/55 mb-1.5">
                <span>До уровня 5</span><span className="font-mono">1240 / 1800 XP</span>
              </div>
              <div className="h-2 bg-black/[0.06] rounded-full overflow-hidden">
                <FM.motion.div initial={{ width: 0 }} animate={{ width: '69%' }}
                  transition={{ duration: 1.2, ease: 'easeOut' }}
                  className="h-full grad-bg rounded-full"/>
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <button className="h-10 px-4 rounded-xl bg-white border border-black/[0.06] text-sm font-medium hover:border-violet-300 transition-colors">Настройки</button>
            <button className="h-10 px-4 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold inline-flex items-center gap-1.5">
              <I.Plus className="w-3.5 h-3.5"/> Новый курс
            </button>
          </div>
        </div>

        {/* metrics */}
        <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <MetricCard tint="#2563EB" Icon={I.Check} label="Решено задач" value="127" sub="+4 за неделю"/>
          <MetricCard tint="#06B6D4" Icon={I.Flame} label="Дней подряд" value="23" sub="личный рекорд: 31" big="🔥"/>
          <MetricCard tint="#0EA5E9" Icon={I.Book} label="Курсов пройдено" value="3" sub="из 5 активных"/>
        </div>
      </div>
    </section>
  );
}

function MetricCard({ tint, Icon, label, value, sub, big }) {
  return (
    <FM.motion.div initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="bg-white rounded-2xl p-5 ring-1 ring-black/[0.04] shadow-soft flex items-center gap-4">
      <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl" style={{ background: `${tint}18`, color: tint }}>
        {big || <Icon className="w-7 h-7"/>}
      </div>
      <div className="flex-1">
        <div className="text-xs font-semibold uppercase tracking-widest text-ink/55">{label}</div>
        <div className="text-3xl font-extrabold mt-0.5 tabular-nums">{value}</div>
        <div className="text-xs text-ink/50 mt-0.5">{sub}</div>
      </div>
    </FM.motion.div>
  );
}

// ----- ACTIVITY (LineChart) -----
function ActivityChart() {
  const data = React.useMemo(() => {
    const arr = [];
    let v = 2;
    for (let i = 29; i >= 0; i--) {
      v = Math.max(0, v + (Math.random() * 4 - 1.6));
      const d = new Date(); d.setDate(d.getDate() - i);
      arr.push({ day: d.getDate() + '.' + (d.getMonth() + 1), tasks: Math.round(v) });
    }
    return arr;
  }, []);

  const total = data.reduce((s, x) => s + x.tasks, 0);
  const { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, defs } = RC;

  return (
    <ChartCard
      title="Активность · 30 дней"
      sub={`${total} решённых задач за месяц`}
      tint="#2563EB">
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="actLine" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#2563EB"/>
              <stop offset="100%" stopColor="#06B6D4"/>
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(17,24,39,0.06)" vertical={false}/>
          <XAxis dataKey="day" tick={{ fill: '#9CA3AF', fontSize: 10 }} axisLine={false} tickLine={false} interval={4}/>
          <YAxis tick={{ fill: '#9CA3AF', fontSize: 10 }} axisLine={false} tickLine={false} width={28}/>
          <Tooltip content={<ChartTooltip suffix=" задач"/>}/>
          <Line type="monotone" dataKey="tasks" stroke="url(#actLine)" strokeWidth={2.5}
            dot={false} activeDot={{ r: 5, fill: '#2563EB' }}
            animationDuration={1400} animationEasing="ease-out"/>
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ----- SKILLS (RadarChart) -----
function SkillsChart() {
  const data = [
    { skill: 'Python', value: 88 },
    { skill: 'Алгоритмы', value: 64 },
    { skill: 'Web', value: 72 },
    { skill: 'БД', value: 56 },
    { skill: 'ML', value: 28 },
  ];
  const { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } = RC;
  return (
    <ChartCard title="Навыки" sub="Покрытие по категориям" tint="#06B6D4">
      <ResponsiveContainer width="100%" height={220}>
        <RadarChart data={data} outerRadius="78%">
          <defs>
            <linearGradient id="radarFill" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#2563EB" stopOpacity={0.5}/>
              <stop offset="100%" stopColor="#06B6D4" stopOpacity={0.4}/>
            </linearGradient>
          </defs>
          <PolarGrid stroke="rgba(17,24,39,0.08)"/>
          <PolarAngleAxis dataKey="skill" tick={{ fill: '#6B7280', fontSize: 11, fontWeight: 500 }}/>
          <PolarRadiusAxis tick={false} axisLine={false} domain={[0, 100]}/>
          <Radar dataKey="value" stroke="#2563EB" strokeWidth={2}
            fill="url(#radarFill)"
            animationDuration={1400} animationEasing="ease-out"/>
        </RadarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ----- COURSES PROGRESS (BarChart) -----
function CoursesProgressChart() {
  const data = [
    { name: 'Python', progress: 84, color: '#2563EB' },
    { name: 'Алгоритмы', progress: 56, color: '#0EA5E9' },
    { name: 'React+API', progress: 32, color: '#06B6D4' },
    { name: 'SQL', progress: 12, color: '#06B6D4' },
  ];
  const { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip, CartesianGrid } = RC;
  return (
    <ChartCard title="Прогресс по курсам" sub="Активных сейчас: 4" tint="#0EA5E9">
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid stroke="rgba(17,24,39,0.06)" vertical={false}/>
          <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 11 }} axisLine={false} tickLine={false}/>
          <YAxis tick={{ fill: '#9CA3AF', fontSize: 10 }} axisLine={false} tickLine={false} width={28}
            domain={[0, 100]}/>
          <Tooltip content={<ChartTooltip suffix="%"/>}/>
          <Bar dataKey="progress" radius={[8, 8, 4, 4]} animationDuration={1200}>
            {data.map((d, i) => <Cell key={i} fill={d.color}/>)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function ChartTooltip({ active, payload, label, suffix }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="bg-white shadow-glow rounded-xl px-3 py-2 ring-1 ring-black/[0.05]">
      <div className="text-[10px] uppercase tracking-widest text-ink/50">{label}</div>
      <div className="text-sm font-bold grad-text">{payload[0].value}{suffix}</div>
    </div>
  );
}

function ChartCard({ title, sub, tint, children }) {
  return (
    <FM.motion.div initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <div className="text-sm font-bold">{title}</div>
          <div className="text-xs text-ink/55 mt-0.5">{sub}</div>
        </div>
        <div className="w-2 h-2 rounded-full" style={{ background: tint, boxShadow: `0 0 0 4px ${tint}22` }}/>
      </div>
      {children}
    </FM.motion.div>
  );
}

// ----- ACHIEVEMENTS -----
function Achievements() {
  const items = [
    { id: 1, name: 'Первый код', emoji: '👶', tint: '#2563EB', unlocked: true, desc: 'Решил первую задачу' },
    { id: 2, name: 'Серия 7 дней', emoji: '🔥', tint: '#06B6D4', unlocked: true, desc: 'Заходил 7 дней подряд' },
    { id: 3, name: 'Серия 30 дней', emoji: '⚡', tint: '#38BDF8', unlocked: false, desc: 'Заходи 30 дней подряд' },
    { id: 4, name: 'Сотня', emoji: '💯', tint: '#0EA5E9', unlocked: true, desc: '100 решённых задач' },
    { id: 5, name: 'Алгоритмист', emoji: '🧠', tint: '#06B6D4', unlocked: true, desc: 'Прошёл модуль по ДП' },
    { id: 6, name: 'Ночная сова', emoji: '🦉', tint: '#2563EB', unlocked: true, desc: 'Решал задачу после 2 ночи' },
    { id: 7, name: 'Звезда', emoji: '⭐', tint: '#06B6D4', unlocked: false, desc: 'Получи 5 от ментора' },
    { id: 8, name: 'Без багов', emoji: '🪲', tint: '#22C55E', unlocked: false, desc: '20 задач с первой попытки' },
    { id: 9, name: 'Чемпион', emoji: '🏆', tint: '#38BDF8', unlocked: false, desc: 'Топ-10 на лидерборде' },
    { id: 10, name: 'Перфекционист', emoji: '🎯', tint: '#0EA5E9', unlocked: false, desc: 'Решил курс на 100%' },
  ];
  return (
    <section className="max-w-7xl mx-auto px-5 sm:px-8 mt-10">
      <div className="flex items-end justify-between mb-5">
        <h2 className="text-2xl font-bold">Достижения</h2>
        <div className="text-sm text-ink/55">
          <span className="font-semibold text-violet-600">{items.filter(i => i.unlocked).length}</span> / {items.length} открыто
        </div>
      </div>
      <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-6">
        <div className="grid grid-cols-5 sm:grid-cols-10 gap-3 sm:gap-4">
          {items.map((b, i) => (
            <FM.motion.div key={b.id}
              initial={{ opacity: 0, scale: 0.8 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.04 }}
              className="group relative aspect-square">
              <div className={`w-full h-full rounded-2xl flex items-center justify-center text-3xl transition-all
                ${b.unlocked ? 'shadow-soft' : 'opacity-40 grayscale'}`}
                style={{ background: b.unlocked ? `linear-gradient(135deg, ${b.tint}22, ${b.tint}08)` : 'rgba(0,0,0,0.04)',
                         border: b.unlocked ? `1px solid ${b.tint}33` : '1px solid rgba(0,0,0,0.06)' }}>
                {b.unlocked ? b.emoji : <I.Lock className="w-5 h-5 text-ink/50"/>}
              </div>
              {/* tooltip */}
              <div className="absolute z-10 left-1/2 -translate-x-1/2 -top-2 -translate-y-full opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                <div className="bg-ink text-white text-[11px] px-2.5 py-1.5 rounded-lg whitespace-nowrap">
                  <div className="font-semibold">{b.name}</div>
                  <div className="text-white/65 text-[10px]">{b.desc}</div>
                </div>
              </div>
            </FM.motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ----- ACTIVE COURSES -----
function ActiveCourses({ navigate }) {
  const active = [
    { id: 'python-junior', title: 'Python с нуля до Junior', cat: 'Python', progress: 84, lessonsDone: 35, lessons: 42, gradFrom: '#2563EB', gradTo: '#06B6D4', accentEmoji: 'Py', nextLesson: 'Контекстные менеджеры' },
    { id: 'algo', title: 'Алгоритмы и структуры данных', cat: 'Алгоритмы', progress: 56, lessonsDone: 20, lessons: 35, gradFrom: '#1D4ED8', gradTo: '#0EA5E9', accentEmoji: '∑', nextLesson: 'Динамическое программирование' },
    { id: 'web-react-fastapi', title: 'Веб-разработка: React + FastAPI', cat: 'Web', progress: 32, lessonsDone: 19, lessons: 58, gradFrom: '#06B6D4', gradTo: '#2563EB', accentEmoji: '⌘', nextLesson: 'TanStack Query: основы' },
    { id: 'postgres-pro', title: 'PostgreSQL для разработчика', cat: 'Базы данных', progress: 12, lessonsDone: 3, lessons: 24, gradFrom: '#0EA5E9', gradTo: '#22C55E', accentEmoji: 'SQL', nextLesson: 'EXPLAIN: чтение плана' },
  ];
  return (
    <section className="max-w-7xl mx-auto px-5 sm:px-8 mt-10">
      <div className="flex items-end justify-between mb-5">
        <h2 className="text-2xl font-bold">Активные курсы</h2>
        <button onClick={() => navigate(Routes.CATALOG)} className="text-sm font-semibold text-violet-600 hover:underline">
          + Добавить курс
        </button>
      </div>
      <div className="grid md:grid-cols-2 gap-5">
        {active.map((c, i) => (
          <FM.motion.div key={c.id}
            initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.08 }}
            className="bg-white rounded-2xl ring-1 ring-black/[0.05] shadow-soft overflow-hidden flex">
            <div className="w-32 flex-shrink-0 relative" style={{ background: `linear-gradient(135deg, ${c.gradFrom}, ${c.gradTo})` }}>
              <div className="absolute inset-0 flex items-center justify-center text-white font-mono font-bold text-4xl opacity-90">{c.accentEmoji}</div>
              <div className="absolute bottom-2 left-2 text-[10px] uppercase tracking-widest text-white/80">{c.cat}</div>
            </div>
            <div className="flex-1 p-5 flex flex-col justify-between gap-3">
              <div>
                <h3 className="font-bold leading-tight">{c.title}</h3>
                <div className="text-xs text-ink/55 mt-1">Следующий урок · <span className="text-ink/80 font-medium">{c.nextLesson}</span></div>
              </div>
              <div>
                <div className="flex items-center justify-between text-[11px] uppercase tracking-widest text-ink/50 mb-1.5">
                  <span>Урок {c.lessonsDone} из {c.lessons}</span>
                  <span className="font-mono">{c.progress}%</span>
                </div>
                <div className="h-1.5 bg-black/[0.05] rounded-full overflow-hidden">
                  <FM.motion.div initial={{ width: 0 }} whileInView={{ width: `${c.progress}%` }} viewport={{ once: true }}
                    transition={{ duration: 1, delay: 0.2 }} className="h-full grad-bg rounded-full"/>
                </div>
              </div>
              <button onClick={() => navigate(Routes.PROBLEM)}
                className="self-start h-9 px-4 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold inline-flex items-center gap-1.5">
                Продолжить <I.ChevronRight className="w-3.5 h-3.5"/>
              </button>
            </div>
          </FM.motion.div>
        ))}
      </div>
    </section>
  );
}

window.ProfilePage = ProfilePage;
