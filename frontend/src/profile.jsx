// PROFILE page — student profile with charts (Recharts)

const RC = window.Recharts || {};
const I = window.I;
const FM = window.FM;
const FloatingShapes = window.FloatingShapes;

function ProfilePage({ navigate, hashParams }) {
  const viewUserId = hashParams?.get('user') || null;
  const isOwnProfile = !viewUserId;
  const [user, setUser] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (!isOwnProfile) {
      setLoading(true);
      setError('');
      let cancelled = false;
      (async () => {
        try {
          const data = await window.apiJson(
            `/api/users/${encodeURIComponent(viewUserId)}/`,
            { auth: !!localStorage.getItem('access_token') },
          );
          if (!cancelled) {
            setUser(data);
            setError('');
          }
        } catch (e) {
          if (!cancelled) {
            setUser(null);
            setError(e.status === 404 ? 'not_found' : (e.message || 'load'));
          }
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
      return () => { cancelled = true; };
    }

    if (!localStorage.getItem('access_token')) {
      setLoading(false);
      setUser(null);
      setError('no_token');
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await window.apiJson('/api/users/me/', { auth: true });
        if (!cancelled) {
          setUser(data);
          setError('');
        }
      } catch (e) {
        if (!cancelled) {
          setUser(null);
          setError(e.status === 401 ? 'auth' : (e.message || 'load'));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [viewUserId, isOwnProfile]);

  if (loading) {
    return (
      <div data-screen-label="04 Profile" className="min-h-[50vh] flex flex-col items-center justify-center gap-3 text-ink/60">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">Загружаем профиль…</div>
      </div>
    );
  }

  if (error === 'not_found') {
    return (
      <div data-screen-label="04 Profile" className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Профиль не найден</div>
        <button type="button" onClick={() => navigate(window.Routes.MENTOR)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
          К панели ментора
        </button>
      </div>
    );
  }

  if (error === 'no_token' || error === 'auth' || !user) {
    return (
      <div data-screen-label="04 Profile" className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Нужен вход</div>
        <p className="text-sm text-ink/60 mt-2">Чтобы увидеть профиль, войди или зарегистрируйся.</p>
        <button type="button" onClick={() => navigate(window.Routes.AUTH)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold shadow-soft">
          Перейти ко входу
        </button>
      </div>
    );
  }

  if (error && error !== 'no_token' && error !== 'auth') {
    return (
      <div data-screen-label="04 Profile" className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Не удалось загрузить</div>
        <p className="text-sm text-ink/60 mt-2">{error}</p>
        <button type="button" onClick={() => window.location.reload()}
          className="mt-6 h-11 px-6 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm font-semibold">
          Обновить страницу
        </button>
      </div>
    );
  }

  return (
    <div data-screen-label="04 Profile" className="min-h-screen pb-16">
      <ProfileHeader user={user} navigate={navigate} isOwnProfile={isOwnProfile}/>
      {isOwnProfile ? (
        <>
          <div className="max-w-7xl mx-auto px-5 sm:px-8 mt-10 grid lg:grid-cols-3 gap-6">
            <ActivityChart activity={user.activity}/>
            <SkillsChart enrollments={user.enrollments}/>
            <CoursesProgressChart enrollments={user.enrollments}/>
          </div>
          <MyCourses enrollments={user.enrollments} navigate={navigate}/>
          <Achievements items={user.achievements?.items || []} unlockedCount={user.achievements?.unlocked_count}/>
        </>
      ) : (
        <>
          <div className="max-w-7xl mx-auto px-5 sm:px-8 mt-10 grid sm:grid-cols-3 gap-4">
            <MetricCard tint="#2563EB" Icon={I.Check} label="Решено задач"
              value={user.progress?.tasks_solved ?? 0}
              sub={`код: ${user.progress?.coding_solved ?? 0} · тесты: ${user.progress?.quizzes_solved ?? 0}`}/>
            <MetricCard tint="#06B6D4" Icon={I.Flame} label="Дней подряд"
              value={user.progress?.streak_days ?? 0} sub="активность"/>
            <MetricCard tint="#0EA5E9" Icon={I.Book} label="Курсов пройдено"
              value={user.progress?.courses_completed ?? 0}
              sub={`теорий: ${user.progress?.theories_read ?? 0}`}/>
          </div>
          <Achievements items={user.achievements?.items || []} unlockedCount={user.achievements?.unlocked_count}/>
        </>
      )}
    </div>
  );
}

function initialsFromUser(u) {
  const a = (u.first_name || '').trim().charAt(0);
  const b = (u.last_name || '').trim().charAt(0);
  const s = (a + b).toUpperCase();
  return s || '?';
}

function formatJoined(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
  } catch (_) {
    return String(iso);
  }
}

function roleLabel(role) {
  if (role === 'student') return 'Студент';
  if (role === 'mentor') return 'Ментор';
  if (role === 'admin') return 'Админ';
  return role || '';
}

function ProfileHeader({ user, navigate, isOwnProfile }) {
  const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ').trim() || 'Профиль';
  const initials = initialsFromUser(user);
  const joined = formatJoined(user.date_joined);
  const [callBusy, setCallBusy] = React.useState(false);
  const [callError, setCallError] = React.useState('');

  const isMentorViewer = React.useMemo(() => {
    const t = localStorage.getItem('access_token');
    if (!t) return false;
    const p = window.parseJwtPayload(t);
    return p.role === 'mentor' || p.role === 'admin';
  }, []);

  const startCall = async () => {
    if (!user?.public_id) return;
    setCallBusy(true);
    setCallError('');
    try {
      const conf = await window.createConference(user.public_id);
      window.openConferenceCall(navigate, conf.public_id);
    } catch (e) {
      setCallError(e.message || 'Не удалось создать созвон');
    } finally {
      setCallBusy(false);
    }
  };

  return (
    <section className="relative mesh-bg pt-12 pb-10 border-b border-black/[0.04]">
      <FloatingShapes/>
      <div className="relative max-w-7xl mx-auto px-5 sm:px-8">
        {!isOwnProfile && (
          <button type="button" onClick={() => navigate(window.Routes.MENTOR)}
            className="mb-4 text-sm text-violet-600 font-semibold inline-flex items-center gap-1 hover:underline">
            <I.ChevronRight className="w-4 h-4 rotate-180"/> К панели ментора
          </button>
        )}
        <div className="flex flex-col md:flex-row items-start gap-7">
          <div className="avatar-ring">
            {user.avatar ? (
              <img
                src={window.mediaUrl(user.avatar)}
                alt=""
                className="w-28 h-28 rounded-full object-cover bg-white"
              />
            ) : (
              <div className="w-28 h-28 rounded-full bg-white flex items-center justify-center text-4xl font-extrabold grad-text">
                {initials}
              </div>
            )}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">{fullName}</h1>
              <span className="inline-flex items-center gap-1.5 grad-bg text-white text-xs font-bold px-2.5 py-1 rounded-md uppercase tracking-widest">
                <I.Trophy className="w-3 h-3"/> {roleLabel(user.role)}
              </span>
            </div>
            <div className="mt-2 flex items-center gap-4 text-sm text-ink/60 flex-wrap">
              {user.email && (
                <span className="inline-flex items-center gap-1.5"><I.Mail className="w-3.5 h-3.5"/> {user.email}</span>
              )}
              {joined && (
                <span className="inline-flex items-center gap-1.5"><I.Calendar className="w-3.5 h-3.5"/> С нами с {joined}</span>
              )}
              {user.public_id && (
                <span className="inline-flex items-center gap-1.5 font-mono text-xs text-ink/45">id: {user.public_id}</span>
              )}
            </div>
            {user.bio && (
              <p className="mt-3 text-sm text-ink/70 max-w-2xl leading-relaxed">{user.bio}</p>
            )}
          </div>

          <div className="flex gap-2">
            {isOwnProfile ? (
              <>
                <button type="button" onClick={() => navigate(window.Routes.PROFILE_EDIT)}
                  className="h-10 px-4 rounded-xl bg-white border border-black/[0.06] text-sm font-medium hover:border-violet-300 transition-colors">
                  Настройки
                </button>
                <button type="button" onClick={() => navigate(window.Routes.CATALOG)}
                  className="h-10 px-4 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold inline-flex items-center gap-1.5">
                  <I.Plus className="w-3.5 h-3.5"/> Каталог
                </button>
              </>
            ) : isMentorViewer ? (
              <>
                <button type="button" onClick={() => window.openChatWithUser(navigate, user.public_id)}
                  className="h-10 px-4 rounded-xl bg-white border border-black/[0.06] text-sm font-medium hover:border-violet-300 transition-colors">
                  Написать
                </button>
                <button type="button" disabled={callBusy} onClick={startCall}
                  className="h-10 px-4 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold inline-flex items-center gap-1.5 disabled:opacity-60">
                  <I.Video className="w-3.5 h-3.5"/> {callBusy ? 'Создаём…' : 'Начать созвон'}
                </button>
                <button type="button" onClick={() => navigate(window.Routes.MENTOR)}
                  className="h-10 px-4 rounded-xl bg-white border border-black/[0.06] text-sm font-medium hover:border-violet-300 transition-colors">
                  Панель ментора
                </button>
              </>
            ) : null}
          </div>
        </div>
        {callError && (
          <p className="mt-3 text-sm text-red-600">{callError}</p>
        )}

        {isOwnProfile && (
        <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <MetricCard tint="#2563EB" Icon={I.Check} label="Решено задач"
            value={user.progress?.tasks_solved ?? 0}
            sub={`код: ${user.progress?.coding_solved ?? 0} · тесты: ${user.progress?.quizzes_solved ?? 0}`}/>
          <MetricCard tint="#06B6D4" Icon={I.Flame} label="Дней подряд"
            value={user.progress?.streak_days ?? 0}
            sub="активность по дням" big={user.progress?.streak_days ? '🔥' : null}/>
          <MetricCard tint="#0EA5E9" Icon={I.Book} label="Курсов пройдено"
            value={user.progress?.courses_completed ?? 0}
            sub={`начато: ${(user.enrollments || []).length} · теорий: ${user.progress?.theories_read ?? 0}`}/>
        </div>
        )}
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
function ActivityChart({ activity }) {
  const data = React.useMemo(() => {
    const rows = activity?.last_30_days || [];
    if (rows.length) {
      return rows.map((r) => ({ day: r.label, tasks: r.count }));
    }
    return [{ day: '—', tasks: 0 }];
  }, [activity]);

  const total = activity?.total_month ?? data.reduce((s, x) => s + x.tasks, 0);
  const { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, defs } = RC;

  return (
    <ChartCard
      title="Активность · 30 дней"
      sub={`${total} активностей за месяц`}
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

// ----- SKILLS (RadarChart) — прогресс по начатым курсам -----
function SkillsChart({ enrollments }) {
  const list = enrollments || [];
  const data = list.length
    ? list.slice(0, 5).map((e) => ({
        skill: (e.course_title || 'Курс').slice(0, 14),
        value: e.percent || 0,
      }))
    : [{ skill: 'Нет курсов', value: 0 }];
  const { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } = RC;
  return (
    <ChartCard title="Мои курсы" sub={list.length ? `${list.length} в процессе или завершено` : 'Начните первый курс'} tint="#06B6D4">
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
function CoursesProgressChart({ enrollments }) {
  const list = (enrollments || []).slice(0, 6);
  const palette = ['#2563EB', '#0EA5E9', '#06B6D4', '#7C3AED', '#22C55E', '#F97316'];
  const data = list.length
    ? list.map((e, i) => ({
        name: (e.course_title || 'Курс').slice(0, 16),
        progress: e.percent || 0,
        color: palette[i % palette.length],
      }))
    : [{ name: '—', progress: 0, color: '#2563EB' }];
  const active = list.filter((e) => e.status === 'active').length;
  const { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip, CartesianGrid } = RC;
  return (
    <ChartCard
      title="Прогресс по курсам"
      sub={list.length ? `Активных: ${active}` : 'Запишитесь на курс в каталоге'}
      tint="#0EA5E9">
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

function MyCourses({ enrollments, navigate }) {
  const list = enrollments || [];
  if (!list.length) {
    return (
      <section className="max-w-7xl mx-auto px-5 sm:px-8 mt-10">
        <h2 className="text-2xl font-bold mb-4">Мои курсы</h2>
        <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-8 text-center">
          <p className="text-sm text-ink/55 mb-4">Вы ещё не начали ни одного курса</p>
          <button type="button" onClick={() => navigate(window.Routes.CATALOG)}
            className="h-11 px-6 rounded-xl btn-grad btn-shimmer text-white text-sm font-semibold">
            Открыть каталог ЕГЭ
          </button>
        </div>
      </section>
    );
  }
  return (
    <section className="max-w-7xl mx-auto px-5 sm:px-8 mt-10">
      <h2 className="text-2xl font-bold mb-5">Мои курсы</h2>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {list.map((e) => (
          <button key={e.public_id} type="button"
            onClick={() => navigate(window.Routes.LEARN, { course: e.course_public_id })}
            className="text-left bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-5 hover:shadow-glow transition-shadow">
            <div className="flex items-start justify-between gap-2 mb-3">
              <div className="font-semibold leading-snug">{e.course_title}</div>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase shrink-0 ${
                e.status === 'completed'
                  ? 'bg-emerald-500/12 text-emerald-700'
                  : 'bg-violet-500/10 text-violet-600'
              }`}>
                {e.status === 'completed' ? 'Готов' : 'В процессе'}
              </span>
            </div>
            <div className="text-xs text-ink/50 mb-2">
              {e.completed_steps} / {e.total_steps} шагов
            </div>
            <div className="h-2 bg-black/[0.05] rounded-full overflow-hidden">
              <div className="h-full grad-bg rounded-full" style={{ width: `${e.percent || 0}%` }}/>
            </div>
            <div className="text-xs text-ink/45 mt-2">
              Начат {new Date(e.started_at).toLocaleDateString('ru-RU')}
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

// ----- ACHIEVEMENTS -----
function Achievements({ items, unlockedCount }) {
  const list = items || [];
  const total = list.length;
  const unlocked = typeof unlockedCount === 'number'
    ? unlockedCount
    : list.filter((i) => i.unlocked).length;
  return (
    <section className="max-w-7xl mx-auto px-5 sm:px-8 mt-10">
      <div className="flex items-end justify-between mb-5">
        <h2 className="text-2xl font-bold">Достижения</h2>
        <div className="text-sm text-ink/55">
          <span className="font-semibold text-violet-600">{unlocked}</span> / {total || '—'} открыто
        </div>
      </div>
      <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-6">
        {list.length === 0 ? (
          <p className="text-sm text-ink/55 text-center py-6">Достижения появятся после первой активности</p>
        ) : (
        <div className="grid grid-cols-5 sm:grid-cols-10 gap-3 sm:gap-4">
          {list.map((b, i) => (
            <FM.motion.div key={b.public_id || b.code}
              initial={{ opacity: 0, scale: 0.8 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
              transition={{ duration: 0.4, delay: i * 0.04 }}
              className="group relative aspect-square">
              <div className={`w-full h-full rounded-2xl flex items-center justify-center text-3xl transition-all
                ${b.unlocked ? 'shadow-soft' : 'opacity-40 grayscale'}`}
                style={{ background: b.unlocked ? 'linear-gradient(135deg, #2563EB22, #06B6D408)' : 'rgba(0,0,0,0.04)',
                         border: b.unlocked ? '1px solid #2563EB33' : '1px solid rgba(0,0,0,0.06)' }}>
                {b.unlocked ? (b.emoji || '🏆') : <I.Lock className="w-5 h-5 text-ink/50"/>}
              </div>
              {/* tooltip */}
              <div className="absolute z-10 left-1/2 -translate-x-1/2 -top-2 -translate-y-full opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                <div className="bg-ink text-white text-[11px] px-2.5 py-1.5 rounded-lg whitespace-nowrap">
                  <div className="font-semibold">{b.title}</div>
                  <div className="text-white/65 text-[10px]">{b.description}</div>
                </div>
              </div>
            </FM.motion.div>
          ))}
        </div>
        )}
      </div>
    </section>
  );
}

window.ProfilePage = ProfilePage;
