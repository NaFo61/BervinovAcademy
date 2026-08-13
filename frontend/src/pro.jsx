// PRO tariff showcase

const Routes = window.Routes;
const FM = window.FM;
const I = window.I;

function formatProEnds(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('ru-RU', {
      day: 'numeric', month: 'long', year: 'numeric',
    });
  } catch (_) {
    return String(iso);
  }
}

function ProPage({ navigate }) {
  const M = FM.motion || (({ children }) => children);
  const [plan, setPlan] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await window.apiJson('/api/subscriptions/plans/pro/', {
          auth: !!window.getAccessToken(),
        });
        if (!cancelled) {
          setPlan(data);
          setError('');
        }
      } catch (e) {
        if (!cancelled) setError(e.message || 'load');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3 text-ink/60">
        <span className="w-8 h-8 rounded-full border-2 border-violet-500 border-t-transparent animate-spin"/>
        <div className="text-sm">Загружаем тариф…</div>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Не удалось загрузить</div>
        <p className="text-sm text-ink/60 mt-2">{error || 'Ошибка'}</p>
      </div>
    );
  }

  const sub = plan.subscription;
  const isPro = !!sub?.is_pro;
  const endsLabel = formatProEnds(sub?.ends_at);
  const features = Array.isArray(plan.features) ? plan.features : [];

  return (
    <div data-screen-label="Pro" className="min-h-screen pb-16">
      <section className="relative mesh-bg pt-14 pb-16 overflow-hidden border-b border-black/[0.04]">
        <div className="relative max-w-4xl mx-auto px-5 sm:px-8">
          <M.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/70 backdrop-blur ring-1 ring-violet-500/15 text-xs font-semibold text-ink/70 mb-5">
              Тариф · {plan.duration_days || 30} дней
            </div>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight">
              {plan.title || 'Про'}
            </h1>
            <p className="mt-4 text-lg text-ink/65 max-w-2xl leading-relaxed">
              {plan.description
                || 'Чат с ментором, видео-разборы эталонных решений и созвоны. Курсы при этом остаются бесплатными.'}
            </p>
          </M.div>
        </div>
      </section>

      <section className="max-w-4xl mx-auto px-5 sm:px-8 mt-10">
        <div className="grid sm:grid-cols-3 gap-4">
          {features.map((f) => (
            <div key={f.code}
              className="rounded-2xl bg-white ring-1 ring-black/[0.05] shadow-soft p-5">
              <div className="w-10 h-10 rounded-xl bg-violet-500/10 text-violet-700 flex items-center justify-center mb-3">
                {f.code === 'mentor_chat' ? <I.Chat className="w-5 h-5"/>
                  : f.code === 'conference' ? <I.Video className="w-5 h-5"/>
                    : <I.Play className="w-5 h-5"/>}
              </div>
              <div className="font-bold text-[15px]">{f.title}</div>
              <p className="text-[13px] text-ink/55 mt-1.5 leading-relaxed">{f.blurb}</p>
            </div>
          ))}
        </div>

        <div className="mt-10 rounded-2xl bg-white ring-1 ring-black/[0.05] shadow-soft p-6 sm:p-8">
          {isPro ? (
            <>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-800 text-xs font-bold uppercase tracking-widest">
                У вас Про
              </div>
              <p className="mt-3 text-[15px] text-ink/70 leading-relaxed">
                {endsLabel
                  ? <>Действует до <span className="font-semibold text-ink">{endsLabel}</span>.</>
                  : 'Доступ активен.'}
                {' '}Курсы бесплатные — Про открывает менторский сервис вокруг них.
              </p>
              <p className="mt-5 text-sm font-semibold text-ink/70">Продлить другим промокодом</p>
              <PromoRedeemForm
                onGranted={(sub) => setPlan((prev) => ({ ...prev, subscription: sub }))}
                successText="Срок Про продлён."
              />
              <div className="mt-5 flex flex-wrap gap-2">
                <button type="button" onClick={() => navigate(Routes.CATALOG)}
                  className="h-11 px-5 rounded-xl btn-grad text-white text-sm font-semibold">
                  К курсам
                </button>
                <button type="button" onClick={() => navigate(Routes.PROFILE)}
                  className="h-11 px-5 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm font-semibold">
                  В профиль
                </button>
              </div>
            </>
          ) : (
            <>
              <h2 className="text-xl font-extrabold tracking-tight">Промокод</h2>
              <p className="mt-2 text-[15px] text-ink/65 leading-relaxed">
                Введите код — тариф Про включится сразу.
              </p>
              <PromoRedeemForm onGranted={(sub) => setPlan((prev) => ({ ...prev, subscription: sub }))}/>
              <p className="mt-4 text-[13px] text-ink/45 leading-relaxed">
                {plan.cta_text}
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {!window.getAccessToken() ? (
                  <button type="button" onClick={() => navigate(Routes.AUTH)}
                    className="h-11 px-5 rounded-xl btn-grad text-white text-sm font-semibold">
                    Войти
                  </button>
                ) : null}
                <button type="button" onClick={() => navigate(Routes.CATALOG)}
                  className="h-11 px-5 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm font-semibold">
                  Смотреть курсы бесплатно
                </button>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

window.ProPage = ProPage;

function PromoRedeemForm({ onGranted, successText }) {
  const [code, setCode] = React.useState('');
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState('');
  const [ok, setOk] = React.useState('');

  const submit = async (e) => {
    e.preventDefault();
    if (!window.getAccessToken()) {
      setError('Сначала войдите в аккаунт.');
      return;
    }
    const trimmed = (code || '').trim();
    if (!trimmed) {
      setError('Введите промокод.');
      return;
    }
    setBusy(true);
    setError('');
    setOk('');
    try {
      const data = await window.apiJson('/api/subscriptions/redeem/', {
        method: 'POST',
        auth: true,
        body: { code: trimmed },
      });
      setOk(successText || 'Про включён.');
      setCode('');
      if (data?.subscription && onGranted) onGranted(data.subscription);
    } catch (err) {
      setError(err.message || 'Не удалось применить код');
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="mt-5 flex flex-col gap-2">
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Например EGE2026"
          autoComplete="off"
          className="flex-1 h-11 px-4 rounded-xl bg-white ring-1 ring-black/[0.08] text-sm outline-none focus:ring-violet-400"
        />
        <button type="submit" disabled={busy}
          className="h-11 px-5 rounded-xl btn-grad text-white text-sm font-semibold disabled:opacity-60">
          {busy ? 'Проверяем…' : 'Применить'}
        </button>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {ok && <p className="text-sm text-emerald-700 font-semibold">{ok}</p>}
    </form>
  );
}
