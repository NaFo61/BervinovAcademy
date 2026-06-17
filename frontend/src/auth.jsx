// AUTH page — login/register swap with sliding panels

const FM = window.FM;
const I = window.I;
const FloatingShapes = window.FloatingShapes;

const AUTH_EASE = [0.16, 1, 0.3, 1];
const AUTH_SWAP_MS = 0.48;
/** Фиксированная высота карточки — не меняется при переключении режима */
const AUTH_CARD_H = 'h-[min(940px,calc(100vh-5.5rem))] lg:h-[940px]';

function AuthPage({ navigate }) {
  const M = FM.motion;
  const [mode, setMode] = React.useState('login');
  const isLogin = mode === 'login';

  return (
    <div data-screen-label="05 Auth" className="min-h-[calc(100vh-64px)] relative overflow-hidden">
      <div className="absolute inset-0 mesh-bg" style={{ transform: 'translateZ(0)' }}/>
      <FloatingShapes/>
      <div className="absolute inset-0 pointer-events-none"
        style={{
          transform: 'translateZ(0)',
          backgroundImage: `
            radial-gradient(at 20% 30%, rgba(37,99,235,0.18), transparent 50%),
            radial-gradient(at 80% 70%, rgba(6,182,212,0.15), transparent 50%)
          `,
        }}/>

      <div className="relative max-w-6xl mx-auto px-5 sm:px-8 py-10 lg:py-12 min-h-[calc(100vh-64px)] flex items-center">
        <div className={`w-full ${AUTH_CARD_H} rounded-3xl shadow-glow ring-1 ring-black/[0.06] overflow-hidden bg-white/[0.96]`}>
          {/* Desktop: колонки едут через transform, без layout/reflow */}
          <div className="hidden lg:block relative h-full isolate">
            <M.div
              className="absolute top-0 bottom-0 w-1/2 p-8 xl:p-10 flex flex-col justify-start overflow-hidden bg-white z-[2]"
              initial={false}
              animate={{ x: isLogin ? 0 : '100%' }}
              transition={{ duration: AUTH_SWAP_MS, ease: AUTH_EASE }}
              style={{ left: 0, willChange: 'transform' }}>
              <AuthForm mode={mode} setMode={setMode} navigate={navigate}/>
            </M.div>

            <M.div
              className="absolute top-0 bottom-0 w-1/2 p-10 xl:p-12 flex items-center justify-center grad-bg-soft z-[1]"
              initial={false}
              animate={{ x: isLogin ? 0 : '-100%' }}
              transition={{ duration: AUTH_SWAP_MS, ease: AUTH_EASE }}
              style={{ left: '50%', willChange: 'transform' }}>
              <AuthIllustration mode={mode}/>
            </M.div>

            <M.div
              className="absolute top-8 bottom-8 w-px bg-black/[0.07] z-[3] pointer-events-none"
              initial={false}
              animate={{ left: '50%' }}
              transition={{ duration: AUTH_SWAP_MS, ease: AUTH_EASE }}
            />
          </div>

          {/* Mobile: без смены мест, фиксированный порядок */}
          <div className="lg:hidden flex flex-col h-full overflow-y-auto scrollbar-thin">
            <div className="p-8 sm:p-10 shrink-0">
              <AuthForm mode={mode} setMode={setMode} navigate={navigate}/>
            </div>
            <div className="grad-bg-soft border-t border-black/[0.06] p-8 sm:p-10 shrink-0">
              <AuthIllustration mode={mode}/>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const FORGOT_STEPS = [
  { id: 'contact', label: 'Контакт' },
  { id: 'code', label: 'Код' },
  { id: 'password', label: 'Пароль' },
];

function ForgotPasswordPanel({ onBack, onDone }) {
  const M = FM.motion;
  const [step, setStep] = React.useState('contact');
  const [login, setLogin] = React.useState('');
  const [code, setCode] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [password2, setPassword2] = React.useState('');
  const [showPass, setShowPass] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [info, setInfo] = React.useState('');
  const [devCode, setDevCode] = React.useState('');

  const stepIdx = FORGOT_STEPS.findIndex((s) => s.id === step);

  const sendCode = async () => {
    const trimmed = login.trim();
    if (!trimmed) {
      setError('Укажите email или номер телефона.');
      return;
    }
    setLoading(true);
    setError('');
    setInfo('');
    try {
      const data = await window.apiJson('/api/auth/password-reset/request/', {
        method: 'POST',
        body: { login: trimmed },
      });
      setInfo(data.message || 'Код отправлен, если аккаунт найден.');
      setDevCode(data.dev_code || '');
      setStep('code');
    } catch (e) {
      setError(e.message || 'Не удалось отправить код.');
    } finally {
      setLoading(false);
    }
  };

  const goToPassword = () => {
    const trimmed = code.trim();
    if (trimmed.length !== 6 || !/^\d+$/.test(trimmed)) {
      setError('Введите 6-значный код.');
      return;
    }
    setError('');
    setStep('password');
  };

  const savePassword = async () => {
    if (password.length < 8) {
      setError('Пароль — минимум 8 символов.');
      return;
    }
    if (password !== password2) {
      setError('Пароли не совпадают.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await window.apiJson('/api/auth/password-reset/confirm/', {
        method: 'POST',
        body: {
          login: login.trim(),
          code: code.trim(),
          password,
          password_confirm: password2,
        },
      });
      onDone();
    } catch (e) {
      setError(e.message || 'Не удалось сменить пароль.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <button type="button" onClick={onBack}
        className="inline-flex items-center gap-1.5 text-sm text-ink/55 hover:text-violet-600 transition-colors mb-5 w-fit">
        <I.ChevronRight className="w-4 h-4 rotate-180"/>
        Назад ко входу
      </button>

      <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
        Восстановление <span className="grad-text">пароля</span>
      </h2>
      <p className="text-sm text-ink/60 mt-2">
        {step === 'contact' && 'Укажи email или телефон — пришлём код для сброса.'}
        {step === 'code' && 'Введи код из письма или SMS.'}
        {step === 'password' && 'Придумай новый надёжный пароль.'}
      </p>

      <div className="mt-5 flex items-center gap-2">
        {FORGOT_STEPS.map((s, i) => (
          <React.Fragment key={s.id}>
            <div className={`flex items-center gap-2 text-xs font-semibold uppercase tracking-widest ${
              i <= stepIdx ? 'text-violet-600' : 'text-ink/35'
            }`}>
              <span className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] ${
                i < stepIdx ? 'bg-emerald-500 text-white' : i === stepIdx ? 'grad-bg text-white' : 'bg-black/[0.06] text-ink/45'
              }`}>
                {i < stepIdx ? <I.Check className="w-3.5 h-3.5"/> : i + 1}
              </span>
              <span className="hidden sm:inline">{s.label}</span>
            </div>
            {i < FORGOT_STEPS.length - 1 && (
              <div className={`flex-1 h-px max-w-[2.5rem] ${i < stepIdx ? 'bg-violet-300' : 'bg-black/[0.08]'}`}/>
            )}
          </React.Fragment>
        ))}
      </div>

      <div className="mt-6 flex-1 flex flex-col min-h-0">
        <M.div
          key={step}
          initial={{ opacity: 0, x: 14 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3, ease: AUTH_EASE }}
          className="flex flex-col flex-1">

          {step === 'contact' && (
            <>
              <Field label="Email или телефон" value={login} onChange={setLogin}
                placeholder="you@bervinov.dev или +7…" Icon={I.Mail}/>
              <p className="text-xs text-ink/50 mt-2 leading-relaxed">
                На email придёт письмо с кодом. Для телефона код появится в консоли сервера в режиме разработки.
              </p>
            </>
          )}

          {step === 'code' && (
            <>
              <Field label="Код подтверждения" value={code} onChange={(v) => setCode(v.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000" inputMode="numeric"/>
              {info && (
                <div className="mt-3 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
                  {info}
                </div>
              )}
              {devCode && (
                <div className="mt-3 text-xs text-violet-700 bg-violet-50 border border-violet-200 rounded-xl px-4 py-3 font-mono">
                  Код для разработки: <strong>{devCode}</strong>
                </div>
              )}
              <button type="button" onClick={sendCode} disabled={loading}
                className="mt-4 text-sm text-violet-600 font-semibold hover:underline w-fit disabled:opacity-50">
                Отправить код ещё раз
              </button>
            </>
          )}

          {step === 'password' && (
            <>
              <Field label="Новый пароль" type={showPass ? 'text' : 'password'} value={password} onChange={setPassword}
                placeholder="••••••••" Icon={I.Lock}
                rightSlot={(
                  <button type="button" onClick={() => setShowPass((s) => !s)} className="text-ink/40 hover:text-ink">
                    <I.Eye className="w-4 h-4"/>
                  </button>
                )}/>
              <div className="mt-3">
                <Field label="Повтори пароль" type="password" value={password2} onChange={setPassword2}
                  placeholder="••••••••" Icon={I.Lock}/>
              </div>
            </>
          )}

          {error && (
            <div className="mt-4 text-sm text-rose-600 bg-rose-50 border border-rose-200 rounded-xl px-4 py-3">
              {error}
            </div>
          )}
        </M.div>
      </div>

      <div className="shrink-0 pt-4">
        {step === 'contact' && (
          <button type="button" onClick={sendCode} disabled={loading}
            className="w-full h-12 rounded-xl btn-grad btn-shimmer text-white font-semibold shadow-glow inline-flex items-center justify-center gap-2 disabled:opacity-50">
            {loading ? <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"/> : <I.Send className="w-4 h-4"/>}
            {loading ? 'Отправляем…' : 'Отправить код'}
          </button>
        )}
        {step === 'code' && (
          <button type="button" onClick={goToPassword} disabled={loading}
            className="w-full h-12 rounded-xl btn-grad text-white font-semibold shadow-glow inline-flex items-center justify-center gap-2">
            Далее <I.ChevronRight className="w-4 h-4"/>
          </button>
        )}
        {step === 'password' && (
          <button type="button" onClick={savePassword} disabled={loading}
            className="w-full h-12 rounded-xl btn-grad btn-shimmer text-white font-semibold shadow-glow inline-flex items-center justify-center gap-2 disabled:opacity-50">
            {loading ? <span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"/> : <I.Check className="w-4 h-4"/>}
            {loading ? 'Сохраняем…' : 'Сохранить пароль'}
          </button>
        )}
      </div>
    </div>
  );
}

// ------- Form -------
function AuthForm({ mode, setMode, navigate }) {
  const isLogin = mode === 'login';
  const [showForgot, setShowForgot] = React.useState(false);
  const [firstName, setFirstName] = React.useState('');
  const [lastName, setLastName] = React.useState('');
  const [email, setEmail] = React.useState('');
  const [pass, setPass] = React.useState('');
  const [pass2, setPass2] = React.useState('');
  const [showPass, setShowPass] = React.useState(false);
  const [touched, setTouched] = React.useState({});
  const [loading, setLoading] = React.useState(false);
  const [serverError, setServerError] = React.useState('');
  const [serverInfo, setServerInfo] = React.useState('');

  const errors = {
    firstName: !isLogin && touched.firstName && firstName.trim().length < 1 ? 'Укажи имя' : null,
    lastName: !isLogin && touched.lastName && lastName.trim().length < 1 ? 'Укажи фамилию' : null,
    email: touched.email && (
      isLogin
        ? !email.trim()
        : !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
    )
      ? (isLogin ? 'Укажи email или телефон' : 'Похоже на неверный email')
      : null,
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
    <div className="max-w-md w-full mx-auto flex flex-col h-full min-h-0">
      <button onClick={() => navigate(window.Routes.LANDING)} className="flex items-center gap-2 mb-6 group shrink-0">
        <I.Logo className="w-10 h-10"/>
        <div className="leading-tight">
          <div className="font-bold tracking-tight text-base">Bervinov<span className="grad-text">Academy</span></div>
          <div className="text-[10px] text-ink/50 uppercase tracking-widest">онлайн‑школа</div>
        </div>
      </button>

      {!showForgot && (
        <div className="h-[5.25rem] shrink-0 relative overflow-hidden">
          <AuthFadePanel show={isLogin} className="absolute inset-0">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
              С возвращением, <span className="grad-text">друг</span>.
            </h1>
            <p className="text-sm text-ink/60 mt-2">Войди — и продолжай с того места, где остановился.</p>
          </AuthFadePanel>
          <AuthFadePanel show={!isLogin} className="absolute inset-0">
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
              Старт. <span className="grad-text">Поехали.</span>
            </h1>
            <p className="text-sm text-ink/60 mt-2">Один аккаунт — десятки курсов и личный ментор.</p>
          </AuthFadePanel>
        </div>
      )}

      {showForgot ? (
        <div className="mt-2 flex flex-col flex-1 min-h-0">
          <ForgotPasswordPanel
            onBack={() => setShowForgot(false)}
            onDone={() => {
              setShowForgot(false);
              setMode('login');
              setServerError('');
              setServerInfo('Пароль изменён. Войди с новым паролем.');
            }}
          />
        </div>
      ) : (
      <>
      <div className="mt-5 flex w-full gap-1.5 p-1 rounded-2xl bg-black/[0.04] ring-1 ring-black/[0.08] shrink-0">
        {['login', 'register'].map((m) => (
          <button key={m} type="button" onClick={() => { setMode(m); setServerError(''); setServerInfo(''); }}
            className={`flex-1 min-w-0 h-10 text-sm font-semibold rounded-xl transition-all duration-200 ${
              mode === m
                ? 'text-white bg-gradient-to-br from-violet-600 via-violet-500 to-cyan-500 shadow-[0_4px_14px_rgba(109,40,217,0.3)]'
                : 'text-ink/70 hover:text-ink hover:bg-white/80'
            }`}>
            {m === 'login' ? 'Вход' : 'Регистрация'}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="mt-5 flex flex-col flex-1 min-h-0">
        <div className="flex-1 min-h-0 overflow-y-auto scrollbar-thin pr-0.5 -mr-0.5">
          {isLogin ? (
            <div className="space-y-3 pb-2">
              <Field label="Email или телефон" value={email} onChange={setEmail}
                onBlur={() => setTouched((t) => ({ ...t, email: true }))}
                placeholder="you@bervinov.dev или +7…" error={errors.email}
                Icon={I.Mail}/>
              <Field label="Пароль" type={showPass ? 'text' : 'password'} value={pass} onChange={setPass}
                onBlur={() => setTouched((t) => ({ ...t, pass: true }))}
                placeholder="••••••••" error={errors.pass}
                Icon={I.Lock}
                rightSlot={(
                  <button type="button" onClick={() => setShowPass((s) => !s)} className="text-ink/40 hover:text-ink">
                    <I.Eye className="w-4 h-4"/>
                  </button>
                )}/>
              <div className="flex items-center justify-between text-sm">
                <label className="flex items-center gap-2 cursor-pointer">
                  <span className="w-4 h-4 rounded bg-black/[0.06] grid place-items-center"/>
                  <span className="text-ink/60">Запомнить меня</span>
                </label>
                <button type="button" onClick={() => { setShowForgot(true); setServerError(''); }}
                  className="text-violet-600 hover:underline font-medium">
                  Забыли пароль?
                </button>
              </div>
              <LoginPerks/>
            </div>
          ) : (
            <div className="space-y-3 pb-2">
              <div className="grid grid-cols-2 gap-3">
                <Field label="Имя" value={firstName} onChange={setFirstName}
                  onBlur={() => setTouched((t) => ({ ...t, firstName: true }))}
                  placeholder="Артём" error={errors.firstName}/>
                <Field label="Фамилия" value={lastName} onChange={setLastName}
                  onBlur={() => setTouched((t) => ({ ...t, lastName: true }))}
                  placeholder="Петров" error={errors.lastName}/>
              </div>
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
                <div className="mt-2 h-7">
                  {pass ? <PassStrength score={passStrength}/> : null}
                </div>
              </div>
              <Field label="Повтори пароль" type="password" value={pass2} onChange={setPass2}
                onBlur={() => setTouched((t) => ({ ...t, pass2: true }))}
                placeholder="••••••••" error={errors.pass2}
                Icon={I.Lock}/>
              <RegisterNote/>
            </div>
          )}
        </div>

        <div className="shrink-0 pt-4 mt-2 border-t border-black/[0.06] bg-white">
          {serverInfo ? (
            <div className="mb-3 text-sm text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2.5">
              {serverInfo}
            </div>
          ) : serverError ? (
            <div className="mb-3 text-sm text-rose-500 bg-rose-50 border border-rose-200 rounded-xl px-4 py-2.5">
              {serverError}
            </div>
          ) : null}
          <button type="submit" disabled={!canSubmit || loading}
            className="w-full h-12 rounded-xl btn-grad btn-shimmer text-white font-semibold shadow-glow inline-flex items-center justify-center gap-2 disabled:opacity-50 disabled:saturate-50 transition-all">
            {loading
              ? <><span className="w-4 h-4 rounded-full border-2 border-white border-t-transparent animate-spin"/> Подождите…</>
              : <>{isLogin ? 'Войти' : 'Создать аккаунт'} <I.ChevronRight className="w-4 h-4"/></>
            }
          </button>
          <div className="relative flex items-center gap-3 py-3">
            <div className="flex-1 h-px bg-black/[0.08]"/>
            <div className="text-[11px] uppercase tracking-widest text-ink/40">или</div>
            <div className="flex-1 h-px bg-black/[0.08]"/>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <button type="button" className="h-10 rounded-xl bg-white ring-1 ring-black/[0.08] hover:ring-violet-300 transition-colors text-sm font-medium inline-flex items-center justify-center gap-2">
              <I.GitHub className="w-4 h-4"/> GitHub
            </button>
            <button type="button" className="h-10 rounded-xl bg-white ring-1 ring-black/[0.08] hover:ring-violet-300 transition-colors text-sm font-medium inline-flex items-center justify-center gap-2">
              <I.Telegram className="w-4 h-4 text-[#229ED9]"/> Telegram
            </button>
          </div>
          <div className="text-center text-sm text-ink/60 pt-2 pb-1">
            {isLogin ? (
              <>Нет аккаунта? <button type="button" onClick={() => setMode('register')} className="text-violet-600 font-semibold hover:underline">Зарегистрируйся</button></>
            ) : (
              <>Уже учишься? <button type="button" onClick={() => setMode('login')} className="text-violet-600 font-semibold hover:underline">Войти</button></>
            )}
          </div>
        </div>
      </form>
      </>
      )}
    </div>
  );
}

function AuthFadePanel({ show, children, className = '' }) {
  return (
    <div
      className={`transition-opacity duration-300 ease-out ${className} ${
        show ? 'opacity-100 z-10 pointer-events-auto' : 'opacity-0 z-0 pointer-events-none'
      }`}
      aria-hidden={!show}>
      {children}
    </div>
  );
}

function LoginPerks() {
  const perks = [
    { emoji: '📊', title: 'Прогресс на месте', desc: 'С последнего урока' },
    { emoji: '🔥', title: 'Серия сохранится', desc: 'День в streak' },
  ];
  return (
    <div className="mt-3">
      <div className="text-[11px] font-semibold uppercase tracking-widest text-ink/45 mb-2">Тебя ждёт</div>
      <div className="grid grid-cols-2 gap-2">
        {perks.map((p) => (
          <div key={p.title} className="p-3 rounded-xl bg-violet-500/[0.05] ring-1 ring-violet-500/10">
            <span className="text-base leading-none">{p.emoji}</span>
            <div className="text-[13px] font-semibold text-ink/85 leading-tight mt-1.5">{p.title}</div>
            <div className="text-[11px] text-ink/55 mt-0.5">{p.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function RegisterNote() {
  return (
    <div className="p-3 rounded-xl bg-cyan-500/[0.06] ring-1 ring-cyan-500/15">
      <div className="text-sm font-semibold text-ink/80">Бесплатный старт</div>
      <p className="text-xs text-ink/55 mt-0.5 leading-relaxed">
        Первый модуль и встреча с ментором — без оплаты. Пароль не короче 8 символов.
      </p>
    </div>
  );
}

function Field({ label, type = 'text', value, onChange, onBlur, placeholder, error, Icon, rightSlot, inputMode }) {
  const id = React.useId();
  return (
    <div>
      <label htmlFor={id} className="text-xs font-semibold uppercase tracking-widest text-ink/60 ml-1">{label}</label>
      <div className={`auth-input-wrap mt-1.5 flex items-center gap-2 px-3.5 h-12 rounded-xl ${error ? 'is-error' : ''}`}>
        {Icon && <Icon className="w-4 h-4 text-ink/40 shrink-0"/>}
        <input id={id} type={type} value={value} onChange={(e) => onChange(e.target.value)} onBlur={onBlur}
          placeholder={placeholder} inputMode={inputMode}
          className="flex-1 min-w-0 bg-transparent text-sm placeholder:text-ink/35 caret-violet-600 selection:bg-violet-200/50 outline-none"/>
        {rightSlot}
      </div>
      <div className="h-5 overflow-hidden">
        {error ? (
          <div className="text-[12px] text-rose-500 mt-1 ml-1 flex items-center gap-1.5">
            <span className="w-1 h-1 rounded-full bg-rose-500"/>{error}
          </div>
        ) : null}
      </div>
    </div>
  );
}

function PassStrength({ score }) {
  const labels = ['слабый', 'средний', 'хороший', 'крепкий'];
  const tints = ['#EF4444', '#06B6D4', '#38BDF8', '#22C55E'];
  return (
    <div className="flex items-center gap-2 h-7">
      <div className="flex gap-1 flex-1">
        {[0, 1, 2, 3].map((i) => (
          <div key={i}
            className="h-1 rounded-full flex-1 transition-colors duration-300"
            style={{ backgroundColor: i < score ? tints[score - 1] : 'rgba(0,0,0,0.06)' }}/>
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
      <div className="relative aspect-square max-h-[340px] mx-auto">
        <M.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 24, ease: 'linear' }}
          className="absolute inset-[18%] rounded-[42%] grad-bg opacity-90 blur-[1px] shadow-glow"/>
        <div className="absolute inset-[26%] rounded-full bg-white shadow-glow grid place-items-center text-center px-3 sm:px-4">
          <div className="min-h-[5.5rem] flex flex-col items-center justify-center relative w-full">
            <AuthFadePanel show={isLogin} className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="grad-text text-5xl font-extrabold leading-none">👋</div>
              <div className="mt-3 text-sm font-bold">Рады видеть</div>
              <div className="text-[11px] text-ink/55">снова в Академии</div>
            </AuthFadePanel>
            <AuthFadePanel show={!isLogin} className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="grad-text text-5xl sm:text-6xl font-extrabold leading-none tracking-tight">42</div>
              <div className="mt-2 text-xs sm:text-sm font-bold leading-snug text-balance">уроков в стартовом треке</div>
              <div className="text-[10px] sm:text-[11px] text-ink/55 mt-1 leading-snug">Python с нуля до Junior</div>
            </AuthFadePanel>
          </div>
        </div>

        <Orbit angle={-15} radius="40%" delay={0}>
          <FloatChip emoji="📚" label="Уроки" tint="#2563EB"/>
        </Orbit>
        <Orbit angle={70} radius="42%" delay={0.5}>
          <FloatChip emoji="🔥" label="Серия 23 дн" tint="#06B6D4"/>
        </Orbit>
        <Orbit angle={155} radius="43%" delay={1}>
          <FloatChip emoji="⚡" label="Задачи" tint="#38BDF8"/>
        </Orbit>
        <Orbit angle={235} radius="42%" delay={1.5}>
          <FloatChip emoji="🎯" label="Топ-3" tint="#0EA5E9"/>
        </Orbit>

        <div className="absolute -bottom-3 -left-3 code-bg rounded-2xl shadow-glow p-3 font-mono text-[11px] leading-tight w-44">
          <div className="text-emerald-300">{'// твой первый шаг'}</div>
          <div><span className="text-violet-300">def</span> <span className="text-amber-300">learn</span>():</div>
          <div className="pl-3"><span className="text-violet-300">return</span> <span className="text-cyan-300">'легко'</span></div>
        </div>

        {[
          { top: '8%', left: '6%', delay: 0 },
          { top: '12%', right: '4%', delay: 0.6 },
          { bottom: '14%', right: '10%', delay: 1.1 },
        ].map((s, i) => (
          <M.div key={i}
            initial={{ scale: 0 }} animate={{ scale: 1 }}
            transition={{ delay: s.delay, duration: 0.6, ease: 'backOut' }}
            className="absolute" style={s}>
            <I.Sparkle className="w-5 h-5 text-flame-500"/>
          </M.div>
        ))}
      </div>

      <div className="mt-6 text-center h-[4.5rem] relative">
        <AuthFadePanel show={isLogin} className="absolute inset-0 flex flex-col items-center justify-start">
          <div className="text-lg font-bold">Продолжай учиться</div>
          <div className="text-sm text-ink/60 mt-1 max-w-xs mx-auto">5 600+ студентов уже растут вместе с Bervinov Academy.</div>
        </AuthFadePanel>
        <AuthFadePanel show={!isLogin} className="absolute inset-0 flex flex-col items-center justify-start">
          <div className="text-lg font-bold">Начни учиться сегодня</div>
          <div className="text-sm text-ink/60 mt-1 max-w-xs mx-auto">Первый урок и встреча с ментором — бесплатно.</div>
        </AuthFadePanel>
      </div>
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
    <div className="bg-white/95 rounded-xl shadow-md ring-1 ring-black/[0.06] px-2 py-1.5 flex items-center gap-1.5 max-w-[7.5rem] sm:max-w-none sm:px-2.5 sm:py-2 sm:rounded-2xl sm:shadow-glow">
      <div className="w-6 h-6 sm:w-7 sm:h-7 rounded-md sm:rounded-lg flex items-center justify-center text-sm sm:text-base shrink-0" style={{ background: `${tint}1A` }}>{emoji}</div>
      <div className="text-[10px] sm:text-xs font-semibold leading-tight truncate sm:whitespace-nowrap">{label}</div>
    </div>
  );
}

window.AuthPage = AuthPage;
