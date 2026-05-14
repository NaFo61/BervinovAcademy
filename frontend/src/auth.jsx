// AUTH page — login/register swap with sliding panels

const FM = window.FM;
const I = window.I;
const FloatingShapes = window.FloatingShapes;

function AuthPage({ navigate }) {
  const M = FM.motion;
  const [mode, setMode] = React.useState('login'); // 'login' | 'register'
  const isLogin = mode === 'login';

  return (
    <div data-screen-label="05 Auth" className="min-h-[calc(100vh-64px)] relative overflow-hidden">
      {/* Background gradient mesh */}
      <div className="absolute inset-0 mesh-bg"/>
      <FloatingShapes/>
      <div className="absolute inset-0 pointer-events-none"
        style={{ backgroundImage: `
          radial-gradient(at 20% 30%, rgba(37,99,235,0.18), transparent 50%),
          radial-gradient(at 80% 70%, rgba(6,182,212,0.15), transparent 50%)
        `}}/>

      <div className="relative max-w-6xl mx-auto px-5 sm:px-8 py-12 lg:py-16 min-h-[calc(100vh-64px)] flex items-center">
        {/* Две половины: min-height без фиксированной h и без скролла внутри колонок */}
        <div className="w-full glass rounded-3xl shadow-glow ring-1 ring-white/40 overflow-hidden">
          <div className="relative grid lg:grid-cols-2 min-h-[min(800px,calc(100vh-10rem))] lg:min-h-[780px]">
            <FM.AnimatePresence mode="wait" initial={false}>
              <M.div
                key={`form-${mode}`}
                initial={{ x: isLogin ? -40 : 40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: isLogin ? 40 : -40, opacity: 0 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className="p-8 sm:p-12 flex flex-col justify-center order-1 min-h-[min(620px,calc(100vh-12rem))] lg:min-h-0"
                style={{ order: isLogin ? 1 : 2 }}>
                <AuthForm mode={mode} setMode={setMode} navigate={navigate}/>
              </M.div>
            </FM.AnimatePresence>

            <FM.AnimatePresence mode="wait" initial={false}>
              <M.div
                key={`illu-${mode}`}
                initial={{ x: isLogin ? 40 : -40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: isLogin ? -40 : 40, opacity: 0 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className="relative p-8 sm:p-12 flex items-center justify-center overflow-hidden grad-bg-soft border-t border-black/[0.06] lg:border-t-0 lg:border-l lg:border-white/40 min-h-[min(620px,calc(100vh-12rem))] lg:min-h-0"
                style={{ order: isLogin ? 2 : 1 }}>
                <AuthIllustration mode={mode}/>
              </M.div>
            </FM.AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
}

// ------- Form -------
function AuthForm({ mode, setMode, navigate }) {
  const isLogin = mode === 'login';
  const [firstName, setFirstName] = React.useState('');
  const [lastName, setLastName] = React.useState('');
  const [email, setEmail] = React.useState('');
  const [pass, setPass] = React.useState('');
  const [pass2, setPass2] = React.useState('');
  const [showPass, setShowPass] = React.useState(false);
  const [touched, setTouched] = React.useState({});
  const [loading, setLoading] = React.useState(false);
  const [serverError, setServerError] = React.useState('');

  const errors = {
    firstName: !isLogin && touched.firstName && firstName.trim().length < 1 ? 'Укажи имя' : null,
    lastName: !isLogin && touched.lastName && lastName.trim().length < 1 ? 'Укажи фамилию' : null,
    email: touched.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? 'Похоже на неверный email' : null,
    pass: touched.pass && pass.length < 8 ? 'Минимум 8 символов' : null,
    pass2: !isLogin && touched.pass2 && pass !== pass2 ? 'Пароли не совпадают' : null,
  };
  const passStrength = React.useMemo(() => {
    let s = 0;
    if (pass.length >= 8) s++;
    if (pass.length >= 10) s++;
    if (/[A-Z]/.test(pass) && /[a-z]/.test(pass)) s++;
    if (/\d/.test(pass) && /[^A-Za-z\d]/.test(pass)) s++;
    return s;
  }, [pass]);

  const canSubmit = isLogin
    ? !errors.email && !errors.pass && email && pass
    : !errors.firstName && !errors.lastName && !errors.email && !errors.pass && !errors.pass2
      && firstName.trim() && lastName.trim() && email && pass && pass2;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setTouched({
      firstName: true, lastName: true, email: true, pass: true, pass2: true,
    });
    setServerError('');
    if (!canSubmit) return;

    setLoading(true);
    try {
      if (isLogin) {
        const data = await window.apiJson('/api/auth/login/', {
          method: 'POST',
          body: { login: email.trim(), password: pass },
        });
        if (data.access) localStorage.setItem('access_token', data.access);
        if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
      } else {
        const data = await window.apiJson('/api/auth/register/', {
          method: 'POST',
          body: {
            login: email.trim(),
            first_name: firstName.trim(),
            last_name: lastName.trim(),
            password: pass,
            password_confirm: pass2,
          },
        });
        if (data.access) localStorage.setItem('access_token', data.access);
        if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
      }
      window.notifyAuthChanged();
      navigate(window.Routes.PROFILE);
    } catch (err) {
      setServerError(err.message || 'Ошибка. Попробуй ещё раз.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md w-full mx-auto min-h-[min(620px,calc(100vh-14rem))] flex flex-col justify-center">
      <button onClick={() => navigate(window.Routes.LANDING)} className="flex items-center gap-2 mb-8 group">
        <I.Logo className="w-10 h-10"/>
        <div className="leading-tight">
          <div className="font-bold tracking-tight text-base">Bervinov<span className="grad-text">Academy</span></div>
          <div className="text-[10px] text-ink/50 uppercase tracking-widest">онлайн‑школа</div>
        </div>
      </button>

      <FM.AnimatePresence mode="wait" initial={false}>
        <FM.motion.h1 key={`title-${mode}`}
          initial={{ y: 8, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -8, opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
          {isLogin ? <>С возвращением, <span className="grad-text">друг</span>.</> : <>Старт. <span className="grad-text">Поехали.</span></>}
        </FM.motion.h1>
      </FM.AnimatePresence>
      <p className="text-sm text-ink/60 mt-2">
        {isLogin ? 'Войди — и продолжай с того места, где остановился.' : 'Один аккаунт — десятки курсов и личный ментор.'}
      </p>

      <div className="mt-6 inline-flex w-full max-w-[340px] p-1 rounded-2xl bg-gradient-to-b from-white to-black/[0.03] ring-1 ring-black/[0.08] shadow-[inset_0_1px_0_rgba(255,255,255,0.85)]">
        {['login', 'register'].map((m) => (
          <button key={m} type="button" onClick={() => { setMode(m); setServerError(''); }}
            className={`relative flex-1 min-w-0 h-10 text-sm font-semibold rounded-xl transition-colors duration-200 ${
              mode === m ? 'text-white' : 'text-ink/50 hover:text-ink/85'
            }`}>
            {mode === m && (
              <FM.motion.span layoutId="mode-pill"
                className="absolute inset-0 rounded-xl bg-gradient-to-br from-violet-600 via-violet-500 to-cyan-500 shadow-[0_4px_14px_rgba(109,40,217,0.35),inset_0_1px_0_rgba(255,255,255,0.25)]"
                transition={{ type: 'spring', bounce: 0.2, stiffness: 380, damping: 28 }}/>
            )}
            <span className="relative z-10 block truncate px-1">{m === 'login' ? 'Вход' : 'Регистрация'}</span>
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4 md:min-h-[520px] flex flex-col">
        {!isLogin && (
          <>
            <Field label="Имя" value={firstName} onChange={setFirstName}
              onBlur={() => setTouched((t) => ({ ...t, firstName: true }))}
              placeholder="Артём" error={errors.firstName}/>
            <Field label="Фамилия" value={lastName} onChange={setLastName}
              onBlur={() => setTouched((t) => ({ ...t, lastName: true }))}
              placeholder="Петров" error={errors.lastName}/>
          </>
        )}
        <Field label="Email" type="email" value={email} onChange={setEmail}
          onBlur={() => setTouched((t) => ({ ...t, email: true }))}
          placeholder="you@bervinov.dev" error={errors.email}
          Icon={I.Mail}/>
        <div>
          <Field label="Пароль" type={showPass ? 'text' : 'password'} value={pass} onChange={setPass}
            onBlur={() => setTouched((t) => ({ ...t, pass: true }))}
            placeholder="••••••••" error={errors.pass}
            Icon={I.Lock}
            rightSlot={(
              <button type="button" onClick={() => setShowPass((s) => !s)} className="text-ink/40 hover:text-ink">
                <I.Eye className="w-4 h-4"/>
              </button>
            )}/>
          {!isLogin && (
            <div className="mt-2 min-h-[44px]">
              {pass ? <PassStrength score={passStrength}/> : null}
            </div>
          )}
        </div>
        {!isLogin && (
          <Field label="Повтори пароль" type="password" value={pass2} onChange={setPass2}
            onBlur={() => setTouched((t) => ({ ...t, pass2: true }))}
            placeholder="••••••••" error={errors.pass2}
            Icon={I.Lock}/>
        )}

        {isLogin && (
          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 cursor-pointer">
              <span className="w-4 h-4 rounded bg-black/[0.06] grid place-items-center"></span>
              <span className="text-ink/60">Запомнить меня</span>
            </label>
            <a className="text-violet-600 hover:underline font-medium" href="#">Забыли пароль?</a>
          </div>
        )}

        {serverError && (
          <div className="text-sm text-rose-500 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
            {serverError}
          </div>
        )}

        <button type="submit" disabled={!canSubmit || loading}
          className="w-full h-12 rounded-xl btn-grad btn-shimmer text-white font-semibold shadow-glow inline-flex items-center justify-center gap-2 disabled:opacity-50 disabled:saturate-50 transition-all">
          {loading
            ? <><span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"/> Подождите…</>
            : <>{isLogin ? 'Войти' : 'Создать аккаунт'} <I.ChevronRight className="w-4 h-4"/></>
          }
        </button>

        <div className="mt-auto space-y-4 pt-2">
        <div className="relative flex items-center gap-3 py-2">
          <div className="flex-1 h-px bg-black/[0.08]"/>
          <div className="text-[11px] uppercase tracking-widest text-ink/40">или</div>
          <div className="flex-1 h-px bg-black/[0.08]"/>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <button type="button" className="h-11 rounded-xl bg-white ring-1 ring-black/[0.08] hover:ring-violet-300 transition-colors text-sm font-medium inline-flex items-center justify-center gap-2">
            <I.GitHub className="w-4 h-4"/> GitHub
          </button>
          <button type="button" className="h-11 rounded-xl bg-white ring-1 ring-black/[0.08] hover:ring-violet-300 transition-colors text-sm font-medium inline-flex items-center justify-center gap-2">
            <I.Telegram className="w-4 h-4 text-[#229ED9]"/> Telegram
          </button>
        </div>

        <div className="text-center text-sm text-ink/60 pt-2">
          {isLogin ? (
            <>Нет аккаунта? <button type="button" onClick={() => setMode('register')} className="text-violet-600 font-semibold hover:underline">Зарегистрируйся</button></>
          ) : (
            <>Уже учишься? <button type="button" onClick={() => setMode('login')} className="text-violet-600 font-semibold hover:underline">Войти</button></>
          )}
        </div>
        </div>
      </form>
    </div>
  );
}

function Field({ label, type = 'text', value, onChange, onBlur, placeholder, error, Icon, rightSlot }) {
  const id = React.useId();
  return (
    <div>
      <label htmlFor={id} className="text-xs font-semibold uppercase tracking-widest text-ink/60 ml-1">{label}</label>
      <div className={`ring-grad mt-1.5 flex items-center gap-2 px-3.5 h-12 rounded-xl bg-white/95 border transition-[box-shadow,border-color] duration-200
        ${error ? 'border-rose-300 ring-2 ring-rose-200/60' : 'border-black/[0.07] shadow-[inset_0_1px_0_rgba(255,255,255,0.9)]'}`}>
        {Icon && <Icon className="w-4 h-4 text-ink/40"/>}
        <input id={id} type={type} value={value} onChange={(e) => onChange(e.target.value)} onBlur={onBlur}
          placeholder={placeholder}
          className="flex-1 min-w-0 bg-transparent text-sm placeholder:text-ink/35 caret-violet-600 selection:bg-violet-200/50"/>
        {rightSlot}
      </div>
      <FM.AnimatePresence initial={false}>
        {error && (
          <FM.motion.div key="err" initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden">
            <div className="text-[12px] text-rose-500 mt-1.5 ml-1 flex items-center gap-1.5">
              <span className="w-1 h-1 rounded-full bg-rose-500"/>{error}
            </div>
          </FM.motion.div>
        )}
      </FM.AnimatePresence>
    </div>
  );
}

function PassStrength({ score }) {
  const labels = ['слабый', 'средний', 'хороший', 'крепкий'];
  const tints = ['#EF4444', '#06B6D4', '#38BDF8', '#22C55E'];
  return (
    <div className="flex items-center gap-2">
      <div className="flex gap-1 flex-1">
        {[0,1,2,3].map((i) => (
          <FM.motion.div key={i}
            animate={{ width: '100%', backgroundColor: i < score ? tints[score - 1] : 'rgba(0,0,0,0.06)' }}
            className="h-1 rounded-full flex-1"/>
        ))}
      </div>
      <div className="text-[11px] font-medium uppercase tracking-widest" style={{ color: score ? tints[score - 1] : 'rgba(0,0,0,0.4)' }}>
        {score ? labels[score - 1] : '—'}
      </div>
    </div>
  );
}

// ------- Illustration -------
function AuthIllustration({ mode }) {
  const M = FM.motion;
  const isLogin = mode === 'login';
  return (
    <div className="relative w-full max-w-md scale-[0.92] sm:scale-100 origin-center">
      {/* big "stage" with floating learning props */}
      <div className="relative aspect-square">
        {/* central rotating gradient */}
        <M.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 24, ease: 'linear' }}
          className="absolute inset-[18%] rounded-[42%] grad-bg opacity-90 blur-[1px] shadow-glow"/>
        {/* inner halo */}
        <div className="absolute inset-[26%] rounded-full bg-white shadow-glow grid place-items-center text-center px-3 sm:px-4">
          <div className="max-w-[11rem] sm:max-w-none">
            {isLogin ? (
              <>
                <div className="grad-text text-5xl font-extrabold leading-none">👋</div>
                <div className="mt-3 text-sm font-bold">Рады видеть</div>
                <div className="text-[11px] text-ink/55">снова в Академии</div>
              </>
            ) : (
              <>
                <div className="grad-text text-5xl sm:text-6xl font-extrabold leading-none tracking-tight">42</div>
                <div className="mt-2 text-xs sm:text-sm font-bold leading-snug text-balance">уроков в стартовом треке</div>
                <div className="text-[10px] sm:text-[11px] text-ink/55 mt-1 leading-snug">Python с нуля до Junior</div>
              </>
            )}
          </div>
        </div>

        {/* orbiting cards */}
        <Orbit angle={-15} radius="40%" delay={0}>
          <FloatChip emoji="📚" label="Уроки" tint="#2563EB"/>
        </Orbit>
        <Orbit angle={70} radius="42%" delay={0.5}>
          <FloatChip emoji="🔥" label="Серия 23 дн" tint="#06B6D4"/>
        </Orbit>
        <Orbit angle={155} radius="43%" delay={1}>
          <FloatChip emoji="⚡" label="+20 XP" tint="#38BDF8"/>
        </Orbit>
        <Orbit angle={235} radius="42%" delay={1.5}>
          <FloatChip emoji="🎯" label="Топ-3" tint="#0EA5E9"/>
        </Orbit>

        {/* code snippet */}
        <M.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3, duration: 0.6 }}
          className="absolute -bottom-3 -left-3 code-bg rounded-2xl shadow-glow p-3 font-mono text-[11px] leading-tight w-44">
          <div className="text-emerald-300">{'// твой первый шаг'}</div>
          <div><span className="text-violet-300">def</span> <span className="text-amber-300">learn</span>():</div>
          <div className="pl-3"><span className="text-violet-300">return</span> <span className="text-cyan-300">'легко'</span></div>
        </M.div>

        {/* stars */}
        {[
          { top: '8%', left: '6%', delay: 0 },
          { top: '12%', right: '4%', delay: 0.6 },
          { bottom: '14%', right: '10%', delay: 1.1 },
        ].map((s, i) => (
          <M.div key={i}
            initial={{ scale: 0 }} animate={{ scale: [0, 1.2, 1] }}
            transition={{ delay: s.delay, duration: 0.6, ease: 'backOut' }}
            className="absolute" style={s}>
            <I.Sparkle className="w-5 h-5 text-flame-500"/>
          </M.div>
        ))}
      </div>

      <FM.AnimatePresence mode="wait">
        <M.div key={mode}
          initial={{ y: 10, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -10, opacity: 0 }}
          transition={{ duration: 0.4 }}
          className="mt-6 text-center">
          <div className="text-lg font-bold">{isLogin ? 'Продолжай учиться' : 'Начни учиться сегодня'}</div>
          <div className="text-sm text-ink/60 mt-1 max-w-xs mx-auto">
            {isLogin
              ? '5 600+ студентов уже растут вместе с Bervinov Academy.'
              : 'Первый урок и встреча с ментором — бесплатно.'}
          </div>
        </M.div>
      </FM.AnimatePresence>
    </div>
  );
}

function Orbit({ angle, radius, delay, children }) {
  // Position calculation via CSS — uses absolute positioning relative to center
  const rad = (angle * Math.PI) / 180;
  const x = Math.cos(rad);
  const y = Math.sin(rad);
  return (
    <FM.motion.div
      initial={{ scale: 0.6, opacity: 0 }}
      animate={{ scale: 1, opacity: 1, y: [0, -8, 0] }}
      transition={{
        scale: { delay, duration: 0.5, ease: 'backOut' },
        opacity: { delay, duration: 0.4 },
        y: { repeat: Infinity, duration: 4, delay, ease: 'easeInOut' },
      }}
      className="absolute"
      style={{ left: `calc(50% + ${x} * ${radius})`, top: `calc(50% + ${y} * ${radius})`, transform: 'translate(-50%, -50%)' }}>
      {children}
    </FM.motion.div>
  );
}

function FloatChip({ emoji, label, tint }) {
  return (
    <div className="bg-white/95 rounded-xl shadow-md ring-1 ring-black/[0.06] px-2 py-1.5 flex items-center gap-1.5 max-w-[7.5rem] sm:max-w-none sm:px-2.5 sm:py-2 sm:rounded-2xl sm:shadow-glow">
      <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-md sm:rounded-lg flex items-center justify-center text-sm sm:text-base shrink-0" style={{ background: `${tint}1A` }}>{emoji}</div>
      <div className="text-[10px] sm:text-xs font-semibold leading-tight truncate sm:whitespace-nowrap">{label}</div>
    </div>
  );
}

window.AuthPage = AuthPage;
