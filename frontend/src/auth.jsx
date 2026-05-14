// AUTH page — login/register swap with sliding panels

function AuthPage({ navigate }) {
  const M = FM.motion;
  const [mode, setMode] = React.useState('login'); // 'login' | 'register'
  const isLogin = mode === 'login';

  return (
    <div data-screen-label="05 Auth" className="min-h-[calc(100vh-64px)] relative overflow-hidden">
      <div className="absolute inset-0 mesh-bg"/>
      <FloatingShapes/>
      <div className="absolute inset-0 pointer-events-none"
        style={{ backgroundImage: `
          radial-gradient(at 20% 30%, rgba(124,58,237,0.18), transparent 50%),
          radial-gradient(at 80% 70%, rgba(249,115,22,0.15), transparent 50%)
        `}}/>

      <div className="relative max-w-6xl mx-auto px-5 sm:px-8 py-12 lg:py-16 min-h-[calc(100vh-64px)] flex items-center">
        <div className="w-full glass rounded-3xl shadow-glow ring-1 ring-white/40 overflow-hidden">
          <div className="relative grid lg:grid-cols-2 min-h-[640px]">
            {/* Form half */}
            <FM.AnimatePresence mode="wait" initial={false}>
              <M.div
                key={`form-${mode}`}
                initial={{ x: isLogin ? -40 : 40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: isLogin ? 40 : -40, opacity: 0 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className="p-8 sm:p-12 flex flex-col justify-center order-1"
                style={{ order: isLogin ? 1 : 2 }}>
                <AuthForm mode={mode} setMode={setMode} navigate={navigate}/>
              </M.div>
            </FM.AnimatePresence>

            {/* Illustration half */}
            <FM.AnimatePresence mode="wait" initial={false}>
              <M.div
                key={`illu-${mode}`}
                initial={{ x: isLogin ? 40 : -40, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: isLogin ? -40 : 40, opacity: 0 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className="relative p-8 sm:p-12 flex items-center justify-center overflow-hidden grad-bg-soft border-l border-white/40"
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

function AuthForm({ mode, setMode, navigate }) {
  const isLogin = mode === 'login';
  const [name, setName] = React.useState('');
  const [email, setEmail] = React.useState('');
  const [pass, setPass] = React.useState('');
  const [pass2, setPass2] = React.useState('');
  const [showPass, setShowPass] = React.useState(false);
  const [touched, setTouched] = React.useState({});
  const [loading, setLoading] = React.useState(false);
  const [serverError, setServerError] = React.useState('');

  const errors = {
    name: !isLogin && touched.name && name.trim().length < 2 ? 'Минимум 2 символа' : null,
    email: touched.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? 'Похоже на неверный email' : null,
    pass: touched.pass && pass.length < 6 ? 'Минимум 6 символов' : null,
    pass2: !isLogin && touched.pass2 && pass !== pass2 ? 'Пароли не совпадают' : null,
  };

  const passStrength = React.useMemo(() => {
    let s = 0;
    if (pass.length >= 6) s++;
    if (pass.length >= 10) s++;
    if (/[A-Z]/.test(pass) && /[a-z]/.test(pass)) s++;
    if (/\d/.test(pass) && /[^A-Za-z\d]/.test(pass)) s++;
    return s;
  }, [pass]);

  const canSubmit = isLogin
    ? !errors.email && !errors.pass && email && pass
    : !errors.name && !errors.email && !errors.pass && !errors.pass2 && name && email && pass && pass2;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setTouched({ name: true, email: true, pass: true, pass2: true });
    setServerError('');
    if (!canSubmit) return;

    setLoading(true);
    try {
      const endpoint = isLogin ? '/api/users/login/' : '/api/users/register/';
      const body = isLogin
        ? { email, password: pass }
        : { name, email, password: pass, password2: pass2 };

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.access) localStorage.setItem('access_token', data.access);
        if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
        navigate(Routes.PROFILE);
      } else {
        const err = await res.json().catch(() => ({}));
        const msg = err.detail || err.email?.[0] || err.password?.[0] || err.non_field_errors?.[0] || 'Ошибка. Попробуй ещё раз.';
        setServerError(msg);
      }
    } catch {
      // Fallback to demo navigation if backend is unavailable
      navigate(Routes.PROFILE);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md w-full mx-auto">
      <button onClick={() => navigate(Routes.LANDING)} className="flex items-center gap-2 mb-8 group">
        <I.Logo className="w-10 h-10"/>
        <div className="leading-tight">
          <div className="font-bold tracking-tight text-base">Bervinov<span className="grad-text">Academy</span></div>
          <div className="text-[10px] text-ink/50 uppercase tracking-widest">с Мироном</div>
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

      {/* mode toggle */}
      <div className="mt-6 inline-flex bg-black/[0.04] p-1 rounded-xl">
        {['login', 'register'].map((m) => (
          <button key={m} onClick={() => { setMode(m); setServerError(''); }}
            className={`relative px-4 h-9 text-sm font-medium rounded-lg transition-colors ${
              mode === m ? 'text-white' : 'text-ink/55 hover:text-ink/80'
            }`}>
            {mode === m && (
              <FM.motion.span layoutId="mode-pill" className="absolute inset-0 grad-bg rounded-lg shadow-soft" transition={{ type: 'spring', bounce: 0.18, duration: 0.45 }}/>
            )}
            <span className="relative">{m === 'login' ? 'Вход' : 'Регистрация'}</span>
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        {!isLogin && (
          <Field label="Имя" value={name} onChange={setName}
            onBlur={() => setTouched((t) => ({ ...t, name: true }))}
            placeholder="Артём" error={errors.name}/>
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
          {!isLogin && pass && (
            <PassStrength score={passStrength}/>
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
      </form>
    </div>
  );
}

function Field({ label, type = 'text', value, onChange, onBlur, placeholder, error, Icon, rightSlot }) {
  const id = React.useId();
  return (
    <div>
      <label htmlFor={id} className="text-xs font-semibold uppercase tracking-widest text-ink/60 ml-1">{label}</label>
      <div className={`ring-grad mt-1.5 flex items-center gap-2 px-3.5 h-12 rounded-xl bg-white border transition-all
        ${error ? 'border-rose-300 ring-2 ring-rose-200/60' : 'border-black/[0.08]'}`}>
        {Icon && <Icon className="w-4 h-4 text-ink/40"/>}
        <input id={id} type={type} value={value} onChange={(e) => onChange(e.target.value)} onBlur={onBlur}
          placeholder={placeholder}
          className="flex-1 bg-transparent text-sm placeholder:text-ink/35"/>
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
  const tints = ['#EF4444', '#F97316', '#EAB308', '#22C55E'];
  return (
    <div className="mt-2 flex items-center gap-2">
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

function AuthIllustration({ mode }) {
  const M = FM.motion;
  const isLogin = mode === 'login';
  return (
    <div className="relative w-full max-w-md">
      <div className="relative aspect-square">
        <M.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 24, ease: 'linear' }}
          className="absolute inset-[18%] rounded-[42%] grad-bg opacity-90 blur-[1px] shadow-glow"/>
        <div className="absolute inset-[26%] rounded-full bg-white shadow-glow grid place-items-center text-center">
          <div>
            <div className="grad-text text-5xl font-extrabold leading-none">{isLogin ? '👋' : '🚀'}</div>
            <div className="mt-3 text-sm font-bold">{isLogin ? 'Рады видеть' : 'Запускаемся'}</div>
            <div className="text-[11px] text-ink/55">снова в Академии</div>
          </div>
        </div>

        <Orbit angle={-15} radius="44%" delay={0}>
          <FloatChip emoji="📚" label="42 урока" tint="#7C3AED"/>
        </Orbit>
        <Orbit angle={70} radius="46%" delay={0.5}>
          <FloatChip emoji="🔥" label="Серия 23 дн" tint="#F97316"/>
        </Orbit>
        <Orbit angle={155} radius="48%" delay={1}>
          <FloatChip emoji="⚡" label="+20 XP" tint="#EAB308"/>
        </Orbit>
        <Orbit angle={235} radius="46%" delay={1.5}>
          <FloatChip emoji="🎯" label="Топ-3 курса" tint="#EC4899"/>
        </Orbit>

        <M.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3, duration: 0.6 }}
          className="absolute -bottom-3 -left-3 code-bg rounded-2xl shadow-glow p-3 font-mono text-[11px] leading-tight w-44">
          <div className="text-emerald-300">{'// твой первый шаг'}</div>
          <div><span className="text-violet-300">def</span> <span className="text-amber-300">learn</span>():</div>
          <div className="pl-3"><span className="text-violet-300">return</span> <span className="text-cyan-300">'легко'</span></div>
        </M.div>

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
    <div className="bg-white rounded-2xl shadow-glow ring-1 ring-black/5 px-3 py-2 flex items-center gap-2 whitespace-nowrap">
      <div className="w-7 h-7 rounded-lg flex items-center justify-center text-base" style={{ background: `${tint}1A` }}>{emoji}</div>
      <div className="text-xs font-semibold">{label}</div>
    </div>
  );
}

window.AuthPage = AuthPage;
