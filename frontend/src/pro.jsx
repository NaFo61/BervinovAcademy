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
          auth: !!localStorage.getItem('access_token'),
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
              <h2 className="text-xl font-extrabold tracking-tight">Как подключить</h2>
              <p className="mt-2 text-[15px] text-ink/65 leading-relaxed">
                {plan.cta_text}
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                {!localStorage.getItem('access_token') ? (
                  <button type="button" onClick={() => navigate(Routes.AUTH)}
                    className="h-11 px-5 rounded-xl btn-grad text-white text-sm font-semibold">
                    Войти
                  </button>
                ) : (
                  <button type="button" onClick={() => navigate(Routes.PROFILE)}
                    className="h-11 px-5 rounded-xl btn-grad text-white text-sm font-semibold">
                    Открыть профиль
                  </button>
                )}
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
