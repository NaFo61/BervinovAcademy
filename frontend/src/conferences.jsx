// CONFERENCES page — история созвонов

const Routes = window.Routes;
const I = window.I;

const STATUS_LABELS = {
  waiting: 'Ожидание',
  active: 'Идёт',
  completed: 'Завершена',
  declined: 'Отклонена',
  cancelled: 'Отменена',
  expired: 'Истекла',
};

const STATUS_STYLES = {
  waiting: 'bg-amber-500/12 text-amber-800',
  active: 'bg-emerald-500/12 text-emerald-700',
  completed: 'bg-slate-500/12 text-slate-700',
  declined: 'bg-red-500/12 text-red-700',
  cancelled: 'bg-slate-500/12 text-slate-600',
  expired: 'bg-slate-500/12 text-slate-500',
};

function formatDuration(seconds) {
  if (seconds == null || seconds < 0) return '—';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m >= 60) {
    const h = Math.floor(m / 60);
    const rm = m % 60;
    return `${h} ч ${rm} мин`;
  }
  return m > 0 ? `${m} мин ${s} с` : `${s} с`;
}

function participantName(p) {
  if (!p) return '—';
  return [p.first_name, p.last_name].filter(Boolean).join(' ').trim() || 'Участник';
}

function StartCallPanel({ navigate, onCreated }) {
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState([]);
  const [searching, setSearching] = React.useState(false);
  const [creating, setCreating] = React.useState(false);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      return undefined;
    }
    let cancelled = false;
    const t = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await window.fetchApiJson(
          `/api/communication/users/search/?q=${encodeURIComponent(query.trim())}`,
          { auth: true },
        );
        if (!cancelled) setResults(data || []);
      } catch (_) {
        if (!cancelled) setResults([]);
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 300);
    return () => { cancelled = true; clearTimeout(t); };
  }, [query]);

  const startWith = async (publicId) => {
    setCreating(true);
    setError('');
    try {
      const conf = await window.createConference(publicId);
      onCreated?.(conf);
      window.openConferenceCall(navigate, conf.public_id);
    } catch (e) {
      setError(e.message || 'Не удалось создать созвон');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft p-5">
      <div className="font-bold text-lg">Новый созвон</div>
      <p className="text-sm text-ink/55 mt-1">Найдите пользователя по имени или email</p>
      <div className="mt-4 flex gap-2">
        <input type="search" value={query} onChange={(e) => setQuery(e.target.value)}
          placeholder="Имя или email…"
          className="flex-1 h-11 px-4 rounded-xl ring-1 ring-black/[0.08] text-sm outline-none focus:ring-violet-400"/>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      {searching && <p className="mt-3 text-xs text-ink/45">Поиск…</p>}
      {results.length > 0 && (
        <ul className="mt-3 divide-y divide-black/[0.06] rounded-xl ring-1 ring-black/[0.06] overflow-hidden">
          {results.map((u) => (
            <li key={u.public_id} className="flex items-center justify-between gap-3 px-4 py-3 bg-white">
              <div>
                <div className="font-medium text-sm">{participantName(u)}</div>
                <div className="text-xs text-ink/50">{u.email || u.role}</div>
              </div>
              <button type="button" disabled={creating} onClick={() => startWith(u.public_id)}
                className="h-9 px-4 rounded-lg btn-grad text-white text-xs font-semibold disabled:opacity-50">
                Созвон
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ConferencesPage({ navigate }) {
  const WhiteboardPreviewModal = window.WhiteboardPreviewModal;
  const [rows, setRows] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');
  const [previewConf, setPreviewConf] = React.useState(null);
  const token = localStorage.getItem('access_token');
  const payload = token ? window.parseJwtPayload(token) : {};
  const isMentor = payload.role === 'mentor' || payload.role === 'admin';
  const myId = payload.public_id;

  const load = React.useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await window.fetchApiJson('/api/communication/conferences/', { auth: true });
      setRows(Array.isArray(data) ? data : (data.results || []));
    } catch (e) {
      setError(e.message || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!token) return;
    load();
  }, [token, load]);

  if (!token) {
    return (
      <div className="max-w-md mx-auto px-5 py-20 text-center">
        <div className="text-2xl font-bold">Нужен вход</div>
        <button type="button" onClick={() => navigate(Routes.AUTH)}
          className="mt-6 h-11 px-6 rounded-xl btn-grad text-white text-sm font-semibold">
          Войти
        </button>
      </div>
    );
  }

  const otherParty = (row) => {
    if (row.mentor?.public_id === myId) return row.guest;
    return row.mentor;
  };

  const canJoin = (row) => row.status === 'waiting' || row.status === 'active';
  const canRejoin = (row) => canJoin(row);

  return (
    <div data-screen-label="Conferences" className="min-h-screen pb-16 bg-paper">
      {previewConf && WhiteboardPreviewModal && (
        <WhiteboardPreviewModal
          conferenceId={previewConf.public_id}
          title={participantName(otherParty(previewConf))}
          onClose={() => setPreviewConf(null)}
        />
      )}
      <section className="mesh-bg border-b border-black/[0.04] py-10">
        <div className="max-w-4xl mx-auto px-5 sm:px-8">
          <h1 className="text-3xl font-extrabold tracking-tight">Созвоны</h1>
          <p className="text-sm text-ink/60 mt-2">История видеоконференций с менторами и учениками</p>
        </div>
      </section>

      <div className="max-w-4xl mx-auto px-5 sm:px-8 py-8 space-y-6">
        {isMentor && <StartCallPanel navigate={navigate} onCreated={load}/>}

        {error && (
          <div className="p-4 rounded-xl bg-red-50 text-red-700 text-sm ring-1 ring-red-200">{error}</div>
        )}

        <div className="bg-white rounded-2xl ring-1 ring-black/[0.04] shadow-soft overflow-hidden">
          <div className="px-5 py-4 border-b border-black/[0.06] font-bold">История</div>
          {loading ? (
            <div className="p-10 text-center text-sm text-ink/50">Загрузка…</div>
          ) : rows.length === 0 ? (
            <div className="p-10 text-center text-sm text-ink/50">Пока нет созвонов</div>
          ) : (
            <ul className="divide-y divide-black/[0.06]">
              {rows.map((row) => (
                <li key={row.public_id} className="px-5 py-4 flex flex-wrap items-center gap-3">
                  <div className="flex-1 min-w-[200px]">
                    <div className="font-semibold text-sm">{participantName(otherParty(row))}</div>
                    <div className="text-xs text-ink/45 mt-0.5">
                      {new Date(row.created_at).toLocaleString('ru-RU')}
                      {row.duration_seconds != null ? ` · ${formatDuration(row.duration_seconds)}` : ''}
                    </div>
                  </div>
                  <span className={`text-xs font-bold px-2 py-0.5 rounded-md ${STATUS_STYLES[row.status] || ''}`}>
                    {STATUS_LABELS[row.status] || row.status}
                  </span>
                  <div className="flex gap-2">
                    {row.has_whiteboard && (
                      <button type="button"
                        onClick={() => setPreviewConf(row)}
                        className="h-9 px-4 rounded-lg bg-white ring-1 ring-black/[0.08] text-xs font-semibold">
                        Конспект
                      </button>
                    )}
                    {canRejoin(row) && (
                      <button type="button"
                        onClick={() => window.openConferenceCall(navigate, row.public_id)}
                        className="h-9 px-4 rounded-lg btn-grad text-white text-xs font-semibold">
                        {row.status === 'active' ? 'Вернуться' : 'Войти'}
                      </button>
                    )}
                    {isMentor && row.status === 'waiting' && row.mentor?.public_id === myId && (
                      <button type="button"
                        onClick={async () => {
                          await window.fetchApiJson(
                            `/api/communication/conferences/${encodeURIComponent(row.public_id)}/cancel/`,
                            { method: 'POST', auth: true },
                          );
                          load();
                        }}
                        className="h-9 px-4 rounded-lg bg-white ring-1 ring-black/[0.08] text-xs font-semibold">
                        Отменить
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}

window.ConferencesPage = ConferencesPage;
